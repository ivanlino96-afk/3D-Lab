from datetime import UTC, datetime, timedelta
from uuid import UUID

import pytest

from src.quotes.domain.entities import QuoteStatus
from src.reporting.application.get_commercial_metrics import GetCommercialMetrics
from src.reporting.domain.metrics import MetricStatusEvent, QuoteTimeline

START = datetime(2026, 9, 1, tzinfo=UTC)
END = datetime(2026, 10, 1, tzinfo=UTC)


class FakeRepository:
    def __init__(self, timelines=()):
        self.timelines = timelines

    def list_timelines(self, start, end):
        assert start == START
        assert end == END
        return self.timelines


def timeline(identifier, events=()):
    return QuoteTimeline(UUID(int=identifier), START + timedelta(days=identifier), tuple(events))


def event(hours, status):
    return MetricStatusEvent(START + timedelta(hours=hours), status)


@pytest.mark.unit
def test_empty_period_returns_zero_metrics_without_division_error() -> None:
    metrics = GetCommercialMetrics(FakeRepository()).execute(START, END)

    assert metrics.accepted == 0
    assert metrics.quoted == 0
    assert metrics.effective_sales == 0
    assert metrics.conversion_rate == 0
    assert metrics.average_hours_by_status == {}


@pytest.mark.unit
def test_quoted_and_effective_sales_calculate_conversion_and_time_by_status() -> None:
    timelines = (
        timeline(
            1,
            (
                event(48, QuoteStatus.QUOTE_SENT),
                event(72, QuoteStatus.IN_PROGRESS),
                event(120, QuoteStatus.CLOSED),
            ),
        ),
        timeline(2, (event(96, QuoteStatus.QUOTE_SENT),)),
    )
    metrics = GetCommercialMetrics(FakeRepository(timelines)).execute(START, END)

    assert metrics.accepted == 2
    assert metrics.quoted == 2
    assert metrics.effective_sales == 1
    assert metrics.conversion_rate == 50.0
    assert metrics.average_hours_by_status[QuoteStatus.QUOTE_SENT] > 0
    assert metrics.average_hours_by_status[QuoteStatus.IN_PROGRESS] == 48


@pytest.mark.unit
def test_sale_later_canceled_keeps_history_but_is_excluded_from_conversion() -> None:
    sold_then_canceled = timeline(
        1,
        (
            event(48, QuoteStatus.QUOTE_SENT),
            event(72, QuoteStatus.IN_PROGRESS),
            event(96, QuoteStatus.CANCELED),
        ),
    )
    metrics = GetCommercialMetrics(FakeRepository((sold_then_canceled,))).execute(START, END)

    assert metrics.accepted == 1
    assert metrics.quoted == 1
    assert metrics.effective_sales == 0
    assert metrics.conversion_rate == 0
    assert QuoteStatus.IN_PROGRESS in metrics.average_hours_by_status


@pytest.mark.unit
def test_invalid_period_is_rejected_in_spanish() -> None:
    with pytest.raises(ValueError, match="periodo"):
        GetCommercialMetrics(FakeRepository()).execute(END, START)
