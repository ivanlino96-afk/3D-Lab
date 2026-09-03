from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from uuid import UUID, uuid4

from src.quotes.domain.entities import QuoteStatus

ALLOWED_TRANSITIONS = {
    QuoteStatus.OPEN: frozenset((QuoteStatus.QUOTE_SENT, QuoteStatus.CANCELED)),
    QuoteStatus.QUOTE_SENT: frozenset((QuoteStatus.IN_PROGRESS, QuoteStatus.CANCELED)),
    QuoteStatus.IN_PROGRESS: frozenset((QuoteStatus.CLOSED, QuoteStatus.CANCELED)),
    QuoteStatus.CLOSED: frozenset(),
    QuoteStatus.CANCELED: frozenset(),
}


class StatusTransitionError(ValueError):
    pass


@dataclass(frozen=True, slots=True)
class QuoteStatusEvent:
    id: UUID
    quote_id: UUID
    previous_status: QuoteStatus
    new_status: QuoteStatus
    admin_user_id: UUID
    occurred_at: datetime
    reason: str | None = None


def build_status_event(
    quote_id: UUID,
    previous_status: QuoteStatus,
    new_status: QuoteStatus,
    admin_user_id: UUID,
    occurred_at: datetime,
    reason: str | None = None,
) -> QuoteStatusEvent:
    if new_status not in ALLOWED_TRANSITIONS[previous_status]:
        raise StatusTransitionError(
            "El cambio de estado de "
            f"{previous_status.label} a {new_status.label} no está permitido."
        )
    return QuoteStatusEvent(
        uuid4(),
        quote_id,
        previous_status,
        new_status,
        admin_user_id,
        occurred_at,
        reason.strip() if reason and reason.strip() else None,
    )


def is_effective_sale(status: QuoteStatus, sale_recorded_at: datetime | None) -> bool:
    return sale_recorded_at is not None and status in {
        QuoteStatus.IN_PROGRESS,
        QuoteStatus.CLOSED,
    }
