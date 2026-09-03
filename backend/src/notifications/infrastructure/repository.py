from __future__ import annotations

from datetime import datetime
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import Session

from src.notifications.domain.entities import Notification, NotificationStatus
from src.quotes.infrastructure.repository import OutboxEventRecord
from src.shared.config import get_settings


class SqlAlchemyNotificationRepository:
    def __init__(self, session: Session) -> None:
        self._session = session

    def get_by_dedupe_key(self, key: str) -> Notification | None:
        record = self._session.scalar(
            select(OutboxEventRecord).where(OutboxEventRecord.dedupe_key == key)
        )
        return self._to_domain(record) if record else None

    def add(self, notification: Notification) -> None:
        self._session.add(
            OutboxEventRecord(
                id=notification.id,
                event_type=notification.event_type,
                aggregate_id=notification.quote_id,
                dedupe_key=notification.dedupe_key,
                payload=notification.payload,
                status=notification.status.value,
                created_at=notification.created_at,
                recipient=notification.recipient,
                template_key=notification.template_key,
                attempt_count=notification.attempt_count,
                next_attempt_at=notification.next_attempt_at,
                last_error=notification.last_error,
                sent_at=notification.sent_at,
            )
        )
        self._session.flush()

    def list_due(self, now: datetime, limit: int = 50) -> list[Notification]:
        records = self._session.scalars(
            select(OutboxEventRecord)
            .where(
                OutboxEventRecord.status == NotificationStatus.PENDING.value,
                OutboxEventRecord.next_attempt_at <= now,
            )
            .order_by(OutboxEventRecord.next_attempt_at, OutboxEventRecord.created_at)
            .limit(limit)
            .with_for_update(skip_locked=True)
        ).all()
        return [self._to_domain(record) for record in records]

    def mark_sent(self, notification_id: UUID, sent_at: datetime) -> None:
        record = self._required(notification_id)
        record.status = NotificationStatus.SENT.value
        record.sent_at = sent_at
        record.next_attempt_at = None
        record.last_error = None
        self._session.flush()

    def mark_failed(
        self,
        notification_id: UUID,
        attempts: int,
        next_attempt_at: datetime | None,
        error: str,
        permanent: bool,
    ) -> None:
        record = self._required(notification_id)
        record.attempt_count = attempts
        record.next_attempt_at = next_attempt_at
        record.last_error = error
        if permanent:
            record.status = NotificationStatus.NOT_DELIVERED.value
        self._session.flush()

    def list_not_delivered(self) -> list[Notification]:
        records = self._session.scalars(
            select(OutboxEventRecord)
            .where(OutboxEventRecord.status == NotificationStatus.NOT_DELIVERED.value)
            .order_by(OutboxEventRecord.created_at.desc())
        ).all()
        return [self._to_domain(record) for record in records]

    def _required(self, notification_id: UUID) -> OutboxEventRecord:
        record = self._session.get(OutboxEventRecord, notification_id)
        if record is None:
            raise LookupError("El aviso no existe.")
        return record

    @staticmethod
    def _to_domain(record: OutboxEventRecord) -> Notification:
        recipient = record.recipient
        if recipient == "administrator":
            recipient = get_settings().admin_email
        return Notification(
            record.id,
            record.dedupe_key,
            record.event_type,
            record.aggregate_id,
            recipient,
            record.template_key,
            record.payload,
            NotificationStatus(record.status),
            record.attempt_count,
            record.next_attempt_at,
            record.created_at,
            record.last_error,
            record.sent_at,
        )
