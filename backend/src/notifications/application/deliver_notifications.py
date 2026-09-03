from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import Protocol
from uuid import UUID

from src.notifications.domain.entities import Notification


class NotificationDeliveryRepository(Protocol):
    def list_due(self, now: datetime, limit: int = 50) -> list[Notification]: ...

    def mark_sent(self, notification_id: UUID, sent_at: datetime) -> None: ...

    def mark_failed(
        self,
        notification_id: UUID,
        attempts: int,
        next_attempt_at: datetime | None,
        error: str,
        permanent: bool,
    ) -> None: ...


class EmailGateway(Protocol):
    def send(self, recipient: str, subject: str, body: str) -> None: ...


class NotificationTemplates(Protocol):
    def render(self, notification: Notification) -> tuple[str, str]: ...


@dataclass(frozen=True, slots=True)
class DeliverySummary:
    processed: int
    sent: int
    retried: int
    not_delivered: int


@dataclass(frozen=True, slots=True)
class DeliverNotifications:
    repository: NotificationDeliveryRepository
    gateway: EmailGateway
    templates: NotificationTemplates

    def execute(self, now: datetime) -> DeliverySummary:
        sent = retried = not_delivered = 0
        notifications = self.repository.list_due(now)
        for notification in notifications:
            try:
                subject, body = self.templates.render(notification)
                self.gateway.send(notification.recipient, subject, body)
                self.repository.mark_sent(notification.id, now)
                sent += 1
            except Exception as error:
                attempts = notification.attempt_count + 1
                permanent = attempts >= 3
                next_attempt_at = (
                    None if permanent else now + timedelta(minutes=5 * (2 ** (attempts - 1)))
                )
                self.repository.mark_failed(
                    notification.id,
                    attempts,
                    next_attempt_at,
                    str(error)[:500],
                    permanent,
                )
                if permanent:
                    not_delivered += 1
                else:
                    retried += 1
        return DeliverySummary(len(notifications), sent, retried, not_delivered)
