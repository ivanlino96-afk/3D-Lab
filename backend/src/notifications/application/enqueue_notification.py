from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Protocol
from uuid import UUID, uuid4

from src.notifications.domain.entities import Notification, NotificationStatus


class NotificationQueueRepository(Protocol):
    def get_by_dedupe_key(self, key: str) -> Notification | None: ...

    def add(self, notification: Notification) -> None: ...


@dataclass(frozen=True, slots=True)
class NotificationCommand:
    event_key: str
    event_type: str
    quote_id: UUID
    recipient: str
    template_key: str
    payload: dict[str, object]
    occurred_at: datetime


@dataclass(frozen=True, slots=True)
class EnqueueNotification:
    repository: NotificationQueueRepository

    def execute(self, command: NotificationCommand) -> Notification:
        existing = self.repository.get_by_dedupe_key(command.event_key)
        if existing is not None:
            return existing
        notification = Notification(
            id=uuid4(),
            dedupe_key=command.event_key,
            event_type=command.event_type,
            quote_id=command.quote_id,
            recipient=command.recipient,
            template_key=command.template_key,
            payload=command.payload,
            status=NotificationStatus.PENDING,
            attempt_count=0,
            next_attempt_at=command.occurred_at,
            created_at=command.occurred_at,
        )
        self.repository.add(notification)
        return notification
