from datetime import UTC, datetime
from uuid import UUID

import pytest

from src.notifications.application.enqueue_notification import (
    EnqueueNotification,
    NotificationCommand,
)

NOW = datetime(2026, 9, 3, 12, tzinfo=UTC)


class FakeRepository:
    def __init__(self) -> None:
        self.by_key = {}

    def get_by_dedupe_key(self, key):
        return self.by_key.get(key)

    def add(self, notification):
        self.by_key[notification.dedupe_key] = notification


@pytest.mark.unit
@pytest.mark.parametrize(
    ("event_type", "recipient", "template"),
    [
        ("quote_received_customer", "ana@example.com", "quote_received_customer"),
        ("quote_received_admin", "admin@example.com", "quote_received_admin"),
        ("quote_status_changed", "ana@example.com", "quote_status_changed"),
    ],
)
def test_enqueues_each_required_notification(event_type, recipient, template) -> None:
    repository = FakeRepository()
    notification = EnqueueNotification(repository).execute(
        NotificationCommand(
            event_key=f"{event_type}:quote-1",
            event_type=event_type,
            quote_id=UUID(int=1),
            recipient=recipient,
            template_key=template,
            payload={"reference": "3DLAB-001", "status": "open"},
            occurred_at=NOW,
        )
    )

    assert notification.recipient == recipient
    assert notification.attempt_count == 0
    assert notification.next_attempt_at == NOW


@pytest.mark.unit
def test_repeating_the_same_event_returns_existing_notification_without_duplicate() -> None:
    repository = FakeRepository()
    command = NotificationCommand(
        "quote_received:1",
        "quote_received_customer",
        UUID(int=1),
        "ana@example.com",
        "quote_received_customer",
        {"reference": "3DLAB-001"},
        NOW,
    )

    first = EnqueueNotification(repository).execute(command)
    second = EnqueueNotification(repository).execute(command)

    assert second.id == first.id
    assert len(repository.by_key) == 1
