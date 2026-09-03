from __future__ import annotations

from datetime import UTC, datetime, time, timedelta
from uuid import UUID

from sqlalchemy import and_, exists, func, or_, select
from sqlalchemy.orm import Session

from src.administration.application.download_quote_file import StoredQuoteFile
from src.administration.application.get_quote_detail import (
    QuoteDetail,
    QuoteFileDetail,
    QuoteHistoryItem,
)
from src.administration.application.list_quotes import (
    QuoteListItem,
    QuotePage,
    QuoteSearch,
)
from src.audit.domain.entities import AuditEvent
from src.audit.infrastructure.repository import SqlAlchemyAuditRepository
from src.materials.infrastructure.repository import MaterialRecord
from src.quotes.domain.entities import QuoteStatus
from src.quotes.infrastructure.repository import QuoteFileRecord, QuoteRequestRecord
from src.quotes.infrastructure.status_repository import QuoteStatusEventRecord


class SqlAlchemyQuoteQueries:
    def __init__(self, session: Session) -> None:
        self._session = session

    def search(self, search: QuoteSearch) -> QuotePage:
        filters = self._filters(search)
        total = (
            self._session.scalar(
                select(func.count()).select_from(QuoteRequestRecord).where(*filters)
            )
            or 0
        )
        records = self._session.scalars(
            select(QuoteRequestRecord)
            .where(*filters)
            .order_by(QuoteRequestRecord.created_at.desc(), QuoteRequestRecord.id.desc())
            .offset((search.page - 1) * search.page_size)
            .limit(search.page_size)
        ).all()
        return QuotePage(
            tuple(self._summary(record) for record in records),
            total,
            search.page,
            search.page_size,
        )

    def list_for_customer(self, customer_id: UUID) -> tuple[QuoteListItem, ...]:
        records = self._session.scalars(
            select(QuoteRequestRecord)
            .where(QuoteRequestRecord.customer_id == customer_id)
            .order_by(QuoteRequestRecord.created_at.desc(), QuoteRequestRecord.id.desc())
        ).all()
        return tuple(self._summary(record) for record in records)

    def get_detail(self, quote_id: UUID) -> QuoteDetail | None:
        record = self._session.get(QuoteRequestRecord, quote_id)
        if record is None:
            return None
        files = self._session.scalars(
            select(QuoteFileRecord)
            .where(QuoteFileRecord.quote_request_id == quote_id)
            .order_by(QuoteFileRecord.uploaded_at, QuoteFileRecord.id)
        ).all()
        events = self._session.scalars(
            select(QuoteStatusEventRecord)
            .where(QuoteStatusEventRecord.quote_request_id == quote_id)
            .order_by(QuoteStatusEventRecord.occurred_at, QuoteStatusEventRecord.id)
        ).all()
        selected_material_name = None
        if record.selected_material_id:
            selected_material_name = self._session.scalar(
                select(MaterialRecord.name).where(MaterialRecord.id == record.selected_material_id)
            )
        return QuoteDetail(
            record.id,
            record.customer_id,
            record.public_reference,
            record.contact_name,
            record.contact_email,
            record.contact_phone,
            record.comments,
            selected_material_name,
            QuoteStatus(record.status),
            record.created_at,
            tuple(
                QuoteFileDetail(
                    item.id,
                    item.original_name,
                    item.size_bytes,
                    item.uploaded_at,
                    item.expires_at,
                    item.deleted_at,
                    item.status,
                )
                for item in files
            ),
            tuple(
                QuoteHistoryItem(
                    QuoteStatus(item.previous_status),
                    QuoteStatus(item.new_status),
                    item.occurred_at,
                    item.reason,
                )
                for item in events
            ),
        )

    def get_downloadable(self, file_id: UUID) -> StoredQuoteFile | None:
        record = self._session.scalar(
            select(QuoteFileRecord).where(
                QuoteFileRecord.id == file_id, QuoteFileRecord.status == "available"
            )
        )
        if record is None:
            return None
        return StoredQuoteFile(record.id, record.storage_key, record.original_name)

    def record_download(self, file_id: UUID, admin_id: UUID, occurred_at: datetime) -> None:
        SqlAlchemyAuditRepository(self._session).append(
            AuditEvent(
                actor_type="administrator",
                actor_id=str(admin_id),
                action="quote_file_downloaded",
                entity_type="quote_file",
                entity_id=str(file_id),
                result="success",
                occurred_at=occurred_at,
            )
        )
        self._session.flush()

    def _filters(self, search: QuoteSearch) -> list:
        filters = []
        if search.query:
            pattern = f"%{search.query}%"
            filters.append(
                or_(
                    QuoteRequestRecord.contact_name.ilike(pattern),
                    QuoteRequestRecord.contact_email.ilike(pattern),
                    QuoteRequestRecord.public_reference.ilike(pattern),
                )
            )
        if search.statuses:
            filters.append(QuoteRequestRecord.status.in_([item.value for item in search.statuses]))
        if search.date_from:
            start = datetime.combine(search.date_from, time.min, tzinfo=UTC)
            filters.append(QuoteRequestRecord.created_at >= start)
        if search.date_to:
            end = datetime.combine(search.date_to + timedelta(days=1), time.min, tzinfo=UTC)
            filters.append(QuoteRequestRecord.created_at < end)
        return filters

    def _summary(self, record: QuoteRequestRecord) -> QuoteListItem:
        has_files = bool(
            self._session.scalar(
                select(
                    exists().where(
                        and_(
                            QuoteFileRecord.quote_request_id == record.id,
                            QuoteFileRecord.status == "available",
                        )
                    )
                )
            )
        )
        return QuoteListItem(
            record.id,
            record.public_reference,
            record.contact_name,
            record.contact_email,
            QuoteStatus(record.status),
            record.created_at,
            has_files,
        )
