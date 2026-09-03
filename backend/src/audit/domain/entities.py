from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime

from src.shared.domain.types import utc_now


@dataclass(frozen=True, slots=True)
class AuditEvent:
    actor_type: str
    action: str
    entity_type: str
    entity_id: str
    result: str
    actor_id: str | None = None
    occurred_at: datetime = field(default_factory=utc_now)
