from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from enum import StrEnum
from uuid import UUID


class NotificationStatus(StrEnum):
    PENDING = "pending"
    SENT = "sent"
    NOT_DELIVERED = "not_delivered"


@dataclass(frozen=True, slots=True)
class Notification:
    id: UUID
    dedupe_key: str
    event_type: str
    quote_id: UUID
    recipient: str
    template_key: str
    payload: dict[str, object]
    status: NotificationStatus
    attempt_count: int
    next_attempt_at: datetime | None
    created_at: datetime
    last_error: str | None = None
    sent_at: datetime | None = None
