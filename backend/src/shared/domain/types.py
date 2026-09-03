from __future__ import annotations

import secrets
import uuid
from collections.abc import Callable
from datetime import UTC, datetime
from typing import NewType

EntityId = NewType("EntityId", uuid.UUID)
Clock = Callable[[], datetime]
TokenFactory = Callable[[], str]


def utc_now() -> datetime:
    return datetime.now(UTC)


def new_entity_id() -> EntityId:
    return EntityId(uuid.uuid4())


def new_public_token() -> str:
    return secrets.token_urlsafe(24)
