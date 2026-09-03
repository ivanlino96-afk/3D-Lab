from __future__ import annotations

from datetime import datetime
from uuid import UUID

from sqlalchemy import DateTime, ForeignKey, String, Text, select
from sqlalchemy.orm import Mapped, Session, mapped_column

from src.audit.infrastructure.repository import SqlAlchemyAuditRepository
from src.quotes.application.change_quote_status import QuoteState
from src.quotes.domain.entities import QuoteStatus
from src.quotes.domain.status import QuoteStatusEvent
from src.quotes.infrastructure.repository import (
    QuoteRequestRecord,
    SqlAlchemyOutboxRepository,
)
from src.shared.infrastructure.database import Base


class QuoteStatusEventRecord(Base):
    __tablename__ = "quote_status_events"

    id: Mapped[UUID] = mapped_column(primary_key=True)
    quote_request_id: Mapped[UUID] = mapped_column(ForeignKey("quote_requests.id"), nullable=False)
    previous_status: Mapped[str] = mapped_column(String(20), nullable=False)
    new_status: Mapped[str] = mapped_column(String(20), nullable=False)
    admin_user_id: Mapped[UUID] = mapped_column(ForeignKey("admin_users.id"), nullable=False)
    occurred_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    reason: Mapped[str | None] = mapped_column(Text)


class SqlAlchemyQuoteStatusRepository:
    def __init__(self, session: Session) -> None:
        self._session = session

    def get_for_update(self, quote_id: UUID) -> QuoteState | None:
        record = self._session.scalar(
            select(QuoteRequestRecord).where(QuoteRequestRecord.id == quote_id).with_for_update()
        )
        return self._to_state(record) if record else None

    def apply_status_event(self, event: QuoteStatusEvent) -> QuoteState:
        record = self._session.get(QuoteRequestRecord, event.quote_id)
        if record is None:
            raise LookupError("La solicitud no existe.")
        record.status = event.new_status.value
        if event.new_status is QuoteStatus.IN_PROGRESS and record.sale_recorded_at is None:
            record.sale_recorded_at = event.occurred_at
        if event.new_status is QuoteStatus.CLOSED:
            record.completed_at = event.occurred_at
        self._session.add(
            QuoteStatusEventRecord(
                id=event.id,
                quote_request_id=event.quote_id,
                previous_status=event.previous_status.value,
                new_status=event.new_status.value,
                admin_user_id=event.admin_user_id,
                occurred_at=event.occurred_at,
                reason=event.reason,
            )
        )
        self._session.flush()
        return self._to_state(record)

    @staticmethod
    def _to_state(record: QuoteRequestRecord) -> QuoteState:
        return QuoteState(
            record.id,
            record.public_reference,
            record.contact_email,
            QuoteStatus(record.status),
            record.sale_recorded_at,
        )


class SqlAlchemyQuoteStatusUnitOfWork:
    def __init__(self, session: Session) -> None:
        self._session = session
        self.statuses = SqlAlchemyQuoteStatusRepository(session)
        self.outbox = SqlAlchemyOutboxRepository(session)
        self.audit = SqlAlchemyAuditRepository(session)
        self._transaction = None

    def __enter__(self):
        self._transaction = self._session.begin_nested()
        return self

    def __exit__(self, exc_type, exc, traceback) -> None:
        if self._transaction is None:
            return
        if exc_type is None:
            self._transaction.commit()
        else:
            self._transaction.rollback()
