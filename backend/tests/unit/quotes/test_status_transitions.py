from datetime import UTC, datetime
from uuid import UUID

import pytest

from src.quotes.domain.entities import QuoteStatus
from src.quotes.domain.status import (
    QuoteStatusEvent,
    StatusTransitionError,
    build_status_event,
    is_effective_sale,
)

NOW = datetime(2026, 9, 2, 12, tzinfo=UTC)


@pytest.mark.unit
@pytest.mark.parametrize(
    ("previous", "new"),
    [
        (QuoteStatus.OPEN, QuoteStatus.QUOTE_SENT),
        (QuoteStatus.QUOTE_SENT, QuoteStatus.IN_PROGRESS),
        (QuoteStatus.IN_PROGRESS, QuoteStatus.CLOSED),
        (QuoteStatus.OPEN, QuoteStatus.CANCELED),
        (QuoteStatus.QUOTE_SENT, QuoteStatus.CANCELED),
        (QuoteStatus.IN_PROGRESS, QuoteStatus.CANCELED),
    ],
)
def test_allowed_transitions_create_an_append_only_event(previous, new) -> None:
    event = build_status_event(UUID(int=1), previous, new, UUID(int=2), NOW, "Seguimiento")

    assert isinstance(event, QuoteStatusEvent)
    assert event.previous_status is previous
    assert event.new_status is new
    assert event.admin_user_id == UUID(int=2)


@pytest.mark.unit
@pytest.mark.parametrize(
    ("previous", "new"),
    [
        (QuoteStatus.OPEN, QuoteStatus.IN_PROGRESS),
        (QuoteStatus.QUOTE_SENT, QuoteStatus.CLOSED),
        (QuoteStatus.CLOSED, QuoteStatus.CANCELED),
        (QuoteStatus.CANCELED, QuoteStatus.OPEN),
        (QuoteStatus.OPEN, QuoteStatus.OPEN),
    ],
)
def test_skipped_repeated_and_terminal_transitions_are_rejected(previous, new) -> None:
    with pytest.raises(StatusTransitionError, match="cambio de estado"):
        build_status_event(UUID(int=1), previous, new, UUID(int=2), NOW)


@pytest.mark.unit
def test_sales_are_counted_only_while_not_canceled() -> None:
    assert is_effective_sale(QuoteStatus.IN_PROGRESS, NOW) is True
    assert is_effective_sale(QuoteStatus.CLOSED, NOW) is True
    assert is_effective_sale(QuoteStatus.CANCELED, NOW) is False
    assert is_effective_sale(QuoteStatus.IN_PROGRESS, None) is False
