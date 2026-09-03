from datetime import UTC, datetime
from uuid import UUID

import pytest
from sqlalchemy import create_engine, func, select
from sqlalchemy.orm import sessionmaker

from src.customers.infrastructure.repository import CustomerRecord
from src.notifications.application.deliver_notifications import DeliverNotifications
from src.notifications.application.enqueue_notification import (
    EnqueueNotification,
    NotificationCommand,
)
from src.notifications.domain.entities import NotificationStatus
from src.notifications.infrastructure.repository import SqlAlchemyNotificationRepository
from src.notifications.presentation.templates import SpanishEmailTemplates
from src.quotes.infrastructure.repository import OutboxEventRecord, QuoteRequestRecord
from src.shared.infrastructure.database import Base

NOW = datetime(2026, 9, 3, 12, tzinfo=UTC)
QUOTE_ID = UUID(int=201)


class RecordingGateway:
    def __init__(self, fail: bool = False) -> None:
        self.fail = fail
        self.messages = []

    def send(self, recipient, subject, body) -> None:
        self.messages.append((recipient, subject, body))
        if self.fail:
            raise ConnectionError("Proveedor temporalmente indisponible")


@pytest.fixture
def session_factory(tmp_path):
    engine = create_engine(f"sqlite:///{tmp_path / 'notifications.db'}")
    Base.metadata.create_all(engine)
    factory = sessionmaker(bind=engine, expire_on_commit=False)
    with factory.begin() as session:
        customer_id = UUID(int=200)
        session.add(
            CustomerRecord(
                id=customer_id,
                current_name="Ana López",
                original_email="ana@example.com",
                normalized_email="ana@example.com",
                current_phone="5512345678",
                created_at=NOW,
                updated_at=NOW,
            )
        )
        session.add(
            QuoteRequestRecord(
                id=QUOTE_ID,
                public_reference="3DLAB-NOTIFY",
                customer_id=customer_id,
                submission_token="notification-token",
                contact_name="Ana López",
                contact_email="ana@example.com",
                contact_phone="5512345678",
                comments=None,
                selected_material_id=None,
                status="open",
                created_at=NOW,
                confirmed_at=NOW,
                sale_recorded_at=None,
                completed_at=None,
            )
        )
    yield factory
    Base.metadata.drop_all(engine)
    engine.dispose()


def command(key="quote_received_customer:notify") -> NotificationCommand:
    return NotificationCommand(
        key,
        "quote_received_customer",
        QUOTE_ID,
        "ana@example.com",
        "quote_received_customer",
        {"reference": "3DLAB-NOTIFY"},
        NOW,
    )


@pytest.mark.integration
def test_notification_is_deduplicated_rendered_in_spanish_and_delivered(session_factory) -> None:
    gateway = RecordingGateway()
    with session_factory.begin() as session:
        repository = SqlAlchemyNotificationRepository(session)
        first = EnqueueNotification(repository).execute(command())
        repeated = EnqueueNotification(repository).execute(command())
        result = DeliverNotifications(repository, gateway, SpanishEmailTemplates()).execute(NOW)

        assert first.id == repeated.id
        assert result.sent == 1
        assert "Recibimos tu solicitud" in gateway.messages[0][1]
        assert "3DLAB-NOTIFY" in gateway.messages[0][2]
        assert session.scalar(select(func.count()).select_from(OutboxEventRecord)) == 1


@pytest.mark.integration
def test_three_provider_failures_do_not_revert_quote_and_are_exposed(session_factory) -> None:
    gateway = RecordingGateway(fail=True)
    with session_factory.begin() as session:
        repository = SqlAlchemyNotificationRepository(session)
        EnqueueNotification(repository).execute(command("quote_received_customer:failure"))
        attempt_at = NOW
        for _ in range(3):
            DeliverNotifications(repository, gateway, SpanishEmailTemplates()).execute(attempt_at)
            notification = repository.get_by_dedupe_key("quote_received_customer:failure")
            attempt_at = notification.next_attempt_at or attempt_at

        failed = repository.list_not_delivered()
        quote = session.get(QuoteRequestRecord, QUOTE_ID)
        assert quote is not None
        assert quote.status == "open"
        assert len(failed) == 1
        assert failed[0].status is NotificationStatus.NOT_DELIVERED
        assert failed[0].attempt_count == 3
        assert "Proveedor" in failed[0].last_error

        DeliverNotifications(repository, gateway, SpanishEmailTemplates()).execute(attempt_at)
        assert len(gateway.messages) == 3
