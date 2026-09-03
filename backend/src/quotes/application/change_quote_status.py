from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Protocol
from uuid import UUID, uuid4

from src.audit.domain.entities import AuditEvent
from src.quotes.application.confirm_quote import AuditRepository, OutboxRepository
from src.quotes.domain.entities import QuoteStatus
from src.quotes.domain.status import QuoteStatusEvent, build_status_event


@dataclass(frozen=True, slots=True)
class QuoteState:
    id: UUID
    public_reference: str
    contact_email: str
    status: QuoteStatus
    sale_recorded_at: datetime | None


class QuoteStatusRepository(Protocol):
    def get_for_update(self, quote_id: UUID) -> QuoteState | None: ...

    def apply_status_event(self, event: QuoteStatusEvent) -> QuoteState: ...


class QuoteStatusUnitOfWork(Protocol):
    statuses: QuoteStatusRepository
    outbox: OutboxRepository
    audit: AuditRepository

    def __enter__(self) -> QuoteStatusUnitOfWork: ...

    def __exit__(self, exc_type: object, exc: object, traceback: object) -> None: ...


class QuoteNotFoundError(LookupError):
    pass


@dataclass(frozen=True, slots=True)
class ChangeQuoteStatus:
    unit_of_work: QuoteStatusUnitOfWork

    def execute(
        self,
        quote_id: UUID,
        new_status: QuoteStatus,
        admin_user_id: UUID,
        occurred_at: datetime,
        reason: str | None = None,
    ) -> QuoteState:
        with self.unit_of_work as unit_of_work:
            quote = unit_of_work.statuses.get_for_update(quote_id)
            if quote is None:
                raise QuoteNotFoundError("La solicitud no existe.")
            event = build_status_event(
                quote.id, quote.status, new_status, admin_user_id, occurred_at, reason
            )
            updated = unit_of_work.statuses.apply_status_event(event)
            unit_of_work.outbox.add(
                event_id=uuid4(),
                event_type="quote_status_changed",
                aggregate_id=quote.id,
                dedupe_key=f"quote_status_changed:{event.id}",
                payload={
                    "reference": quote.public_reference,
                    "recipient": quote.contact_email,
                    "status": new_status.value,
                },
                created_at=occurred_at,
            )
            unit_of_work.audit.append(
                AuditEvent(
                    actor_type="administrator",
                    actor_id=str(admin_user_id),
                    action="quote_status_changed",
                    entity_type="quote_request",
                    entity_id=str(quote.id),
                    result=new_status.value,
                    occurred_at=occurred_at,
                )
            )
            return updated
