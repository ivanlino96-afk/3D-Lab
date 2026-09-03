from __future__ import annotations

import uuid
from datetime import datetime

from sqlalchemy import JSON, BigInteger, DateTime, ForeignKey, Integer, String, Text, select
from sqlalchemy.orm import Mapped, Session, mapped_column

from src.quotes.application.upload_ports import UploadRepository
from src.quotes.domain.entities import QuoteFile, QuoteRequest, QuoteStatus
from src.quotes.domain.uploads import UploadItem, UploadSession, UploadStatus
from src.shared.config import get_settings
from src.shared.infrastructure.database import Base


class UploadSessionRecord(Base):
    __tablename__ = "upload_sessions"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True)
    token: Mapped[str] = mapped_column(String(120), unique=True, nullable=False)
    confirmed_quote_id: Mapped[uuid.UUID | None] = mapped_column(ForeignKey("quote_requests.id"))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)


class UploadItemRecord(Base):
    __tablename__ = "upload_items"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True)
    session_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("upload_sessions.id", ondelete="CASCADE"), nullable=False
    )
    original_name: Mapped[str] = mapped_column(String(255), nullable=False)
    size_bytes: Mapped[int] = mapped_column(BigInteger, nullable=False)
    status: Mapped[str] = mapped_column(String(12), nullable=False)
    storage_key: Mapped[str | None] = mapped_column(String(200))
    fingerprint: Mapped[str | None] = mapped_column(String(64))
    error_message: Mapped[str | None] = mapped_column(String(300))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)


class QuoteRequestRecord(Base):
    __tablename__ = "quote_requests"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True)
    public_reference: Mapped[str] = mapped_column(String(40), unique=True, nullable=False)
    customer_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("customers.id"), nullable=False)
    submission_token: Mapped[str] = mapped_column(String(120), unique=True, nullable=False)
    contact_name: Mapped[str] = mapped_column(String(100), nullable=False)
    contact_email: Mapped[str] = mapped_column(String(254), nullable=False)
    contact_phone: Mapped[str] = mapped_column(String(16), nullable=False)
    comments: Mapped[str | None] = mapped_column(Text)
    selected_material_id: Mapped[uuid.UUID | None] = mapped_column(ForeignKey("materials.id"))
    status: Mapped[str] = mapped_column(String(20), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    confirmed_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    sale_recorded_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))


class QuoteFileRecord(Base):
    __tablename__ = "quote_files"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True)
    quote_request_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("quote_requests.id", ondelete="CASCADE"), nullable=False
    )
    original_name: Mapped[str] = mapped_column(String(255), nullable=False)
    storage_key: Mapped[str] = mapped_column(String(200), nullable=False)
    size_bytes: Mapped[int] = mapped_column(BigInteger, nullable=False)
    fingerprint: Mapped[str] = mapped_column(String(64), nullable=False)
    uploaded_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    deleted_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    status: Mapped[str] = mapped_column(String(12), nullable=False)


class OutboxEventRecord(Base):
    __tablename__ = "outbox_events"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True)
    event_type: Mapped[str] = mapped_column(String(80), nullable=False)
    aggregate_id: Mapped[uuid.UUID] = mapped_column(nullable=False)
    dedupe_key: Mapped[str] = mapped_column(String(200), unique=True, nullable=False)
    payload: Mapped[dict[str, object]] = mapped_column(JSON, nullable=False)
    status: Mapped[str] = mapped_column(String(12), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    recipient: Mapped[str] = mapped_column(String(254), nullable=False, default="")
    template_key: Mapped[str] = mapped_column(String(80), nullable=False, default="")
    attempt_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    next_attempt_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    last_error: Mapped[str | None] = mapped_column(Text)
    sent_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))


class SqlAlchemyUploadRepository(UploadRepository):
    def __init__(self, session: Session) -> None:
        self._session = session

    def create(self, upload_session: UploadSession, created_at: datetime) -> None:
        self._session.add(
            UploadSessionRecord(
                id=upload_session.id,
                token=upload_session.token,
                confirmed_quote_id=None,
                created_at=created_at,
            )
        )
        self._session.flush()

    def get_by_token(self, token: str) -> UploadSession | None:
        record = self._session.scalar(
            select(UploadSessionRecord).where(UploadSessionRecord.token == token)
        )
        if record is None:
            return None
        item_records = self._session.scalars(
            select(UploadItemRecord)
            .where(UploadItemRecord.session_id == record.id)
            .order_by(UploadItemRecord.created_at, UploadItemRecord.id)
        ).all()
        return UploadSession(
            id=record.id,
            token=record.token,
            confirmed_quote_id=record.confirmed_quote_id,
            items=[self._item_to_domain(item) for item in item_records],
        )

    def add_item(self, session_id: uuid.UUID, item: UploadItem, created_at: datetime) -> None:
        self._session.add(
            UploadItemRecord(
                id=item.id,
                session_id=session_id,
                original_name=item.original_name,
                size_bytes=item.size_bytes,
                status=item.status.value,
                storage_key=item.storage_key,
                fingerprint=item.fingerprint,
                error_message=item.error_message,
                created_at=created_at,
            )
        )
        self._session.flush()

    def mark_removed(self, session_id: uuid.UUID, item_id: uuid.UUID) -> None:
        record = self._session.scalar(
            select(UploadItemRecord).where(
                UploadItemRecord.id == item_id, UploadItemRecord.session_id == session_id
            )
        )
        if record is None:
            raise LookupError("El archivo no existe.")
        record.status = UploadStatus.REMOVED.value
        self._session.flush()

    def mark_confirmed(self, session_id: uuid.UUID, quote_id: uuid.UUID) -> None:
        record = self._session.get(UploadSessionRecord, session_id)
        if record is None:
            raise LookupError("La sesión de carga no existe.")
        record.confirmed_quote_id = quote_id
        self._session.flush()

    @staticmethod
    def _item_to_domain(record: UploadItemRecord) -> UploadItem:
        return UploadItem(
            id=record.id,
            original_name=record.original_name,
            size_bytes=record.size_bytes,
            status=UploadStatus(record.status),
            storage_key=record.storage_key,
            fingerprint=record.fingerprint,
            error_message=record.error_message,
            uploaded_at=record.created_at,
        )


class SqlAlchemyQuoteRepository:
    def __init__(self, session: Session) -> None:
        self._session = session

    def get_by_submission_token(self, token: str) -> QuoteRequest | None:
        record = self._session.scalar(
            select(QuoteRequestRecord).where(QuoteRequestRecord.submission_token == token)
        )
        return self._to_domain(record) if record else None

    def reference_exists(self, reference: str) -> bool:
        return (
            self._session.scalar(
                select(QuoteRequestRecord.id).where(
                    QuoteRequestRecord.public_reference == reference
                )
            )
            is not None
        )

    def add(self, quote: QuoteRequest) -> None:
        self._session.add(
            QuoteRequestRecord(
                id=quote.id,
                public_reference=quote.public_reference,
                customer_id=quote.customer_id,
                submission_token=quote.submission_token,
                contact_name=quote.contact_name,
                contact_email=quote.contact_email,
                contact_phone=quote.contact_phone,
                comments=quote.comments,
                selected_material_id=quote.selected_material_id,
                status=quote.status.value,
                created_at=quote.created_at,
                confirmed_at=quote.created_at,
                sale_recorded_at=None,
                completed_at=None,
            )
        )
        self._session.add_all(
            [
                QuoteFileRecord(
                    id=item.id,
                    quote_request_id=quote.id,
                    original_name=item.original_name,
                    storage_key=item.storage_key,
                    size_bytes=item.size_bytes,
                    fingerprint=item.fingerprint,
                    uploaded_at=item.uploaded_at,
                    expires_at=item.expires_at,
                    deleted_at=None,
                    status="available",
                )
                for item in quote.files
            ]
        )
        self._session.flush()

    def _to_domain(self, record: QuoteRequestRecord) -> QuoteRequest:
        files = self._session.scalars(
            select(QuoteFileRecord).where(QuoteFileRecord.quote_request_id == record.id)
        ).all()
        return QuoteRequest(
            id=record.id,
            public_reference=record.public_reference,
            customer_id=record.customer_id,
            submission_token=record.submission_token,
            contact_name=record.contact_name,
            contact_email=record.contact_email,
            contact_phone=record.contact_phone,
            comments=record.comments,
            selected_material_id=record.selected_material_id,
            status=QuoteStatus(record.status),
            created_at=record.created_at,
            files=tuple(
                QuoteFile(
                    id=item.id,
                    original_name=item.original_name,
                    storage_key=item.storage_key,
                    size_bytes=item.size_bytes,
                    fingerprint=item.fingerprint,
                    uploaded_at=item.uploaded_at,
                    expires_at=item.expires_at,
                )
                for item in files
            ),
        )


class SqlAlchemyOutboxRepository:
    def __init__(self, session: Session) -> None:
        self._session = session

    def add(
        self,
        *,
        event_id: uuid.UUID,
        event_type: str,
        aggregate_id: uuid.UUID,
        dedupe_key: str,
        payload: dict[str, object],
        created_at: datetime,
    ) -> None:
        recipient = str(payload.get("recipient", ""))
        if recipient == "administrator":
            recipient = get_settings().admin_email
        self._session.add(
            OutboxEventRecord(
                id=event_id,
                event_type=event_type,
                aggregate_id=aggregate_id,
                dedupe_key=dedupe_key,
                payload=payload,
                status="pending",
                created_at=created_at,
                recipient=recipient,
                template_key=event_type,
                attempt_count=0,
                next_attempt_at=created_at,
                last_error=None,
                sent_at=None,
            )
        )
