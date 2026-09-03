from datetime import datetime

from sqlalchemy import select
from sqlalchemy.orm import Session

from src.quotes.domain.entities import QuoteStatus
from src.quotes.infrastructure.repository import QuoteRequestRecord
from src.quotes.infrastructure.status_repository import QuoteStatusEventRecord
from src.reporting.domain.metrics import MetricStatusEvent, QuoteTimeline


class SqlAlchemyMetricsQueries:
    def __init__(self, session: Session) -> None:
        self._session = session

    def list_timelines(
        self, period_start: datetime, period_end: datetime
    ) -> tuple[QuoteTimeline, ...]:
        quotes = self._session.scalars(
            select(QuoteRequestRecord)
            .where(
                QuoteRequestRecord.created_at >= period_start,
                QuoteRequestRecord.created_at < period_end,
            )
            .order_by(QuoteRequestRecord.created_at)
        ).all()
        if not quotes:
            return ()
        quote_ids = [quote.id for quote in quotes]
        events = self._session.scalars(
            select(QuoteStatusEventRecord)
            .where(
                QuoteStatusEventRecord.quote_request_id.in_(quote_ids),
                QuoteStatusEventRecord.occurred_at < period_end,
            )
            .order_by(QuoteStatusEventRecord.occurred_at, QuoteStatusEventRecord.id)
        ).all()
        by_quote = {quote_id: [] for quote_id in quote_ids}
        for event in events:
            by_quote[event.quote_request_id].append(
                MetricStatusEvent(event.occurred_at, QuoteStatus(event.new_status))
            )
        return tuple(
            QuoteTimeline(quote.id, quote.created_at, tuple(by_quote[quote.id])) for quote in quotes
        )
