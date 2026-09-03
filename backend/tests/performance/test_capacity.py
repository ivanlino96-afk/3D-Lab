from datetime import UTC, datetime, timedelta
from io import BytesIO
from time import perf_counter
from uuid import UUID

import pytest
from fastapi import UploadFile
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from src.administration.application.list_quotes import ListQuotes
from src.administration.infrastructure.quote_queries import SqlAlchemyQuoteQueries
from src.catalog.presentation.routes import get_service_repository
from src.customers.infrastructure.repository import CustomerRecord
from src.quotes.infrastructure.repository import QuoteRequestRecord
from src.quotes.presentation.routes import _chunks
from src.shared.infrastructure.database import Base


class EmptyServiceRepository:
    def list_published(self):
        return []


@pytest.mark.performance
def test_public_page_p95_stays_below_two_seconds(app, client) -> None:
    app.dependency_overrides[get_service_repository] = EmptyServiceRepository
    durations = []
    for _ in range(40):
        started = perf_counter()
        response = client.get("/")
        durations.append(perf_counter() - started)
        assert response.status_code == 200

    percentile_95 = sorted(durations)[int(len(durations) * 0.95) - 1]
    assert percentile_95 < 2.0


@pytest.mark.performance
def test_monthly_capacity_is_paginated_to_fifty_and_query_stays_below_two_seconds(tmp_path) -> None:
    engine = create_engine(f"sqlite:///{tmp_path / 'capacity.db'}")
    factory = sessionmaker(bind=engine, expire_on_commit=False)
    Base.metadata.create_all(engine)
    now = datetime.now(UTC)
    customer_id = UUID(int=80_000)
    with factory.begin() as session:
        session.add(
            CustomerRecord(
                id=customer_id,
                current_name="Cliente de capacidad",
                original_email="capacity@example.com",
                normalized_email="capacity@example.com",
                current_phone="5512345678",
                created_at=now,
                updated_at=now,
            )
        )
        session.add_all(
            QuoteRequestRecord(
                id=UUID(int=81_000 + index),
                public_reference=f"3DLAB-CAP-{index:04d}",
                customer_id=customer_id,
                submission_token=f"capacity-{index}",
                contact_name="Cliente de capacidad",
                contact_email="capacity@example.com",
                contact_phone="5512345678",
                comments=None,
                selected_material_id=None,
                status="open",
                created_at=now - timedelta(minutes=index),
                confirmed_at=now - timedelta(minutes=index),
                sale_recorded_at=None,
                completed_at=None,
            )
            for index in range(500)
        )

    with factory() as session:
        started = perf_counter()
        page = ListQuotes(SqlAlchemyQuoteQueries(session)).execute(
            None, (), None, None, page_size=500
        )
        duration = perf_counter() - started

    assert page.total == 500
    assert len(page.items) == 50
    assert page.total_pages == 10
    assert duration < 2.0
    engine.dispose()


@pytest.mark.performance
def test_upload_reader_yields_blocks_and_initial_feedback_is_immediate() -> None:
    upload = UploadFile(filename="large.stl", file=BytesIO(b"x" * (3 * 1024 * 1024 + 17)))
    started = perf_counter()
    iterator = _chunks(upload)
    first = next(iterator)
    feedback_delay = perf_counter() - started
    remaining = list(iterator)

    assert len(first) == 1024 * 1024
    assert all(len(block) <= 1024 * 1024 for block in remaining)
    assert sum(map(len, [first, *remaining])) == 3 * 1024 * 1024 + 17
    assert feedback_delay < 1.0
