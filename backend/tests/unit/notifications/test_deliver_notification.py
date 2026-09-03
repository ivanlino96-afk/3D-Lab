from dataclasses import replace
from datetime import UTC, datetime
from uuid import UUID

import pytest

from src.notifications.application.deliver_notifications import DeliverNotifications
from src.notifications.domain.entities import Notification, NotificationStatus

NOW = datetime(2026, 9, 3, 12, tzinfo=UTC)


def pending(attempts=0):
    return Notification(
        UUID(int=1),
        "quote_received_customer:1",
        "quote_received_customer",
        UUID(int=2),
        "ana@example.com",
        "quote_received_customer",
        {"reference": "3DLAB-001"},
        NotificationStatus.PENDING,
        attempts,
        NOW,
        NOW,
    )


class FakeRepository:
    def __init__(self, notification):
        self.notification = notification

    def list_due(self, now, limit=50):
        if self.notification.status is NotificationStatus.PENDING:
            return [self.notification]
        return []

    def mark_sent(self, notification_id, sent_at):
        self.notification = replace(
            self.notification, status=NotificationStatus.SENT, sent_at=sent_at
        )

    def mark_failed(self, notification_id, attempts, next_attempt_at, error, permanent):
        self.notification = replace(
            self.notification,
            status=NotificationStatus.NOT_DELIVERED if permanent else NotificationStatus.PENDING,
            attempt_count=attempts,
            next_attempt_at=next_attempt_at,
            last_error=error,
        )


class FakeTemplates:
    def render(self, notification):
        return "Cotización recibida", f"Folio {notification.payload['reference']}"


class FakeGateway:
    def __init__(self, failures=0):
        self.failures = failures
        self.calls = 0

    def send(self, recipient, subject, body):
        self.calls += 1
        if self.calls <= self.failures:
            raise ConnectionError("SMTP no disponible")


@pytest.mark.unit
def test_initial_delivery_marks_notification_sent() -> None:
    repository = FakeRepository(pending())
    result = DeliverNotifications(repository, FakeGateway(), FakeTemplates()).execute(NOW)

    assert result.sent == 1
    assert repository.notification.status is NotificationStatus.SENT


@pytest.mark.unit
def test_failure_is_scheduled_and_a_later_attempt_can_recover() -> None:
    repository = FakeRepository(pending())
    gateway = FakeGateway(failures=1)
    use_case = DeliverNotifications(repository, gateway, FakeTemplates())

    failed = use_case.execute(NOW)
    recovered = use_case.execute(repository.notification.next_attempt_at)

    assert failed.retried == 1
    assert recovered.sent == 1
    assert repository.notification.status is NotificationStatus.SENT


@pytest.mark.unit
def test_third_failure_is_not_delivered_and_never_attempted_a_fourth_time() -> None:
    repository = FakeRepository(pending(attempts=2))
    gateway = FakeGateway(failures=10)
    use_case = DeliverNotifications(repository, gateway, FakeTemplates())

    result = use_case.execute(NOW)
    next_result = use_case.execute(NOW)

    assert result.not_delivered == 1
    assert repository.notification.status is NotificationStatus.NOT_DELIVERED
    assert repository.notification.attempt_count == 3
    assert repository.notification.next_attempt_at is None
    assert gateway.calls == 1
    assert next_result.processed == 0
