from datetime import UTC, datetime, timedelta
from uuid import UUID

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from src.administration.infrastructure.auth import AdminUserRecord
from src.customers.infrastructure.repository import CustomerRecord
from src.quotes.infrastructure.repository import QuoteRequestRecord
from src.quotes.infrastructure.status_repository import QuoteStatusEventRecord
from src.reporting.application.get_commercial_metrics import GetCommercialMetrics
from src.reporting.infrastructure.metrics_queries import SqlAlchemyMetricsQueries
from src.shared.infrastructure.database import Base

START = datetime(2026, 9, 1, tzinfo=UTC)
END = datetime(2026, 10, 1, tzinfo=UTC)
ADMIN_ID = UUID(int=301)
CUSTOMER_ID = UUID(int=302)


@pytest.fixture
def session_factory(tmp_path):
    engine = create_engine(f"sqlite:///{tmp_path / 'metrics.db'}")
    Base.metadata.create_all(engine)
    factory = sessionmaker(bind=engine, expire_on_commit=False)
    with factory.begin() as session:
        session.add(
            AdminUserRecord(
                id=ADMIN_ID,
                username="admin",
                password_hash="protected",
                enabled=True,
                created_at=START,
                last_login_at=None,
            )
        )
        session.add(
            CustomerRecord(
                id=CUSTOMER_ID,
                current_name="Ana López",
                original_email="ana@example.com",
                normalized_email="ana@example.com",
                current_phone="5512345678",
                created_at=START,
                updated_at=START,
            )
        )
        for number in range(1, 4):
            session.add(
                QuoteRequestRecord(
                    id=UUID(int=310 + number),
                    public_reference=f"3DLAB-METRIC-{number}",
                    customer_id=CUSTOMER_ID,
                    submission_token=f"metric-{number}",
                    contact_name="Ana López",
                    contact_email="ana@example.com",
                    contact_phone="5512345678",
                    comments=None,
                    selected_material_id=None,
                    status="open",
                    created_at=START + timedelta(days=number),
                    confirmed_at=START + timedelta(days=number),
                    sale_recorded_at=None,
                    completed_at=None,
                )
            )
        transitions = {
            1: (
                (48, "open", "quote_sent"),
                (72, "quote_sent", "in_progress"),
                (96, "in_progress", "closed"),
            ),
            2: (
                (72, "open", "quote_sent"),
                (96, "quote_sent", "in_progress"),
                (120, "in_progress", "canceled"),
            ),
        }
        event_id = 400
        for quote_number, events in transitions.items():
            for hours, previous, new in events:
                event_id += 1
                session.add(
                    QuoteStatusEventRecord(
                        id=UUID(int=event_id),
                        quote_request_id=UUID(int=310 + quote_number),
                        previous_status=previous,
                        new_status=new,
                        admin_user_id=ADMIN_ID,
                        occurred_at=START + timedelta(hours=hours),
                        reason=None,
                    )
                )
    yield factory
    Base.metadata.drop_all(engine)
    engine.dispose()


@pytest.mark.integration
def test_metrics_derive_sales_and_cancellations_from_real_history(session_factory) -> None:
    with session_factory() as session:
        metrics = GetCommercialMetrics(SqlAlchemyMetricsQueries(session)).execute(START, END)

    assert metrics.accepted == 3
    assert metrics.quoted == 2
    assert metrics.effective_sales == 1
    assert metrics.conversion_rate == 33.33
    assert metrics.average_hours_by_status


@pytest.mark.integration
def test_metrics_return_an_empty_period(session_factory) -> None:
    with session_factory() as session:
        metrics = GetCommercialMetrics(SqlAlchemyMetricsQueries(session)).execute(
            datetime(2027, 1, 1, tzinfo=UTC), datetime(2027, 2, 1, tzinfo=UTC)
        )

    assert metrics.accepted == 0
    assert metrics.conversion_rate == 0
