from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime
from uuid import UUID

from src.quotes.domain.entities import QuoteStatus


@dataclass(frozen=True, slots=True)
class MetricStatusEvent:
    occurred_at: datetime
    new_status: QuoteStatus


@dataclass(frozen=True, slots=True)
class QuoteTimeline:
    quote_id: UUID
    accepted_at: datetime
    events: tuple[MetricStatusEvent, ...]


@dataclass(frozen=True, slots=True)
class CommercialMetrics:
    accepted: int
    quoted: int
    effective_sales: int
    conversion_rate: float
    average_hours_by_status: dict[QuoteStatus, float]


def calculate_metrics(
    timelines: tuple[QuoteTimeline, ...], period_end: datetime
) -> CommercialMetrics:
    period_end = _aware(period_end)
    quoted = effective_sales = 0
    durations: dict[QuoteStatus, list[float]] = {}
    for timeline in timelines:
        ordered = sorted(
            (item for item in timeline.events if _aware(item.occurred_at) < period_end),
            key=lambda item: _aware(item.occurred_at),
        )
        quoted += any(item.new_status is QuoteStatus.QUOTE_SENT for item in ordered)
        reached_sale = any(item.new_status is QuoteStatus.IN_PROGRESS for item in ordered)
        final_status = ordered[-1].new_status if ordered else QuoteStatus.OPEN
        effective_sales += reached_sale and final_status is not QuoteStatus.CANCELED

        current_status = QuoteStatus.OPEN
        entered_at = _aware(timeline.accepted_at)
        for item in ordered:
            occurred_at = _aware(item.occurred_at)
            elapsed = max(0.0, (occurred_at - entered_at).total_seconds() / 3600)
            durations.setdefault(current_status, []).append(elapsed)
            current_status = item.new_status
            entered_at = occurred_at
        if current_status not in {QuoteStatus.CLOSED, QuoteStatus.CANCELED}:
            elapsed = max(0.0, (period_end - entered_at).total_seconds() / 3600)
            durations.setdefault(current_status, []).append(elapsed)

    accepted = len(timelines)
    return CommercialMetrics(
        accepted,
        quoted,
        effective_sales,
        round((effective_sales / accepted * 100) if accepted else 0.0, 2),
        {
            status: round(sum(values) / len(values), 2)
            for status, values in durations.items()
            if values
        },
    )


def _aware(value: datetime) -> datetime:
    return value if value.tzinfo is not None else value.replace(tzinfo=UTC)
