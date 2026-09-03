from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Protocol

from src.reporting.domain.metrics import CommercialMetrics, QuoteTimeline, calculate_metrics


class MetricsRepository(Protocol):
    def list_timelines(
        self, period_start: datetime, period_end: datetime
    ) -> tuple[QuoteTimeline, ...]: ...


@dataclass(frozen=True, slots=True)
class GetCommercialMetrics:
    repository: MetricsRepository

    def execute(self, period_start: datetime, period_end: datetime) -> CommercialMetrics:
        if period_end <= period_start:
            raise ValueError("El final del periodo debe ser posterior al inicio.")
        timelines = self.repository.list_timelines(period_start, period_end)
        return calculate_metrics(timelines, period_end)
