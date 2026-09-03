from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Protocol
from uuid import UUID

from src.audit.domain.entities import AuditEvent
from src.quotes.application.confirm_quote import AuditRepository
from src.shared.application.ports import PrivateStorage


@dataclass(frozen=True, slots=True)
class ExpirableQuoteFile:
    id: UUID
    quote_id: UUID
    storage_key: str
    expires_at: datetime


class QuoteFileRetentionRepository(Protocol):
    def list_expired(self, now: datetime) -> list[ExpirableQuoteFile]: ...

    def mark_expired(self, file_id: UUID, deleted_at: datetime) -> None: ...


@dataclass(frozen=True, slots=True)
class ExpireQuoteFiles:
    repository: QuoteFileRetentionRepository
    storage: PrivateStorage
    audit: AuditRepository

    def execute(self, now: datetime) -> int:
        expired_count = 0
        for quote_file in self.repository.list_expired(now):
            deleted = self.storage.delete(quote_file.storage_key)
            self.repository.mark_expired(quote_file.id, now)
            self.audit.append(
                AuditEvent(
                    actor_type="system",
                    action="quote_file_expired",
                    entity_type="quote_file",
                    entity_id=str(quote_file.id),
                    result="deleted" if deleted else "already_missing",
                    occurred_at=now,
                )
            )
            expired_count += 1
        return expired_count
