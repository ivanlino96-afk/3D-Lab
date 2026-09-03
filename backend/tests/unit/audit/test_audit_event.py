from dataclasses import FrozenInstanceError
from datetime import UTC, datetime

import pytest

from src.audit.domain.entities import AuditEvent


@pytest.mark.unit
def test_audit_event_is_immutable_and_keeps_required_evidence() -> None:
    occurred_at = datetime(2026, 9, 2, tzinfo=UTC)
    event = AuditEvent(
        actor_type="visitor",
        action="service_catalog_viewed",
        entity_type="catalog",
        entity_id="public",
        result="success",
        occurred_at=occurred_at,
    )

    assert event.occurred_at == occurred_at
    with pytest.raises(FrozenInstanceError):
        event.result = "changed"  # type: ignore[misc]
