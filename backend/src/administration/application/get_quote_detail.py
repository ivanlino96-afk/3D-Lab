from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Protocol
from uuid import UUID

from src.quotes.domain.entities import QuoteStatus


@dataclass(frozen=True, slots=True)
class QuoteFileDetail:
    id: UUID
    original_name: str
    size_bytes: int
    uploaded_at: datetime
    expires_at: datetime
    deleted_at: datetime | None
    status: str


@dataclass(frozen=True, slots=True)
class QuoteHistoryItem:
    previous_status: QuoteStatus
    new_status: QuoteStatus
    occurred_at: datetime
    reason: str | None


@dataclass(frozen=True, slots=True)
class QuoteDetail:
    id: UUID
    customer_id: UUID
    public_reference: str
    contact_name: str
    contact_email: str
    contact_phone: str
    comments: str | None
    selected_material_name: str | None
    status: QuoteStatus
    created_at: datetime
    files: tuple[QuoteFileDetail, ...]
    history: tuple[QuoteHistoryItem, ...]


class QuoteDetailRepository(Protocol):
    def get_detail(self, quote_id: UUID) -> QuoteDetail | None: ...


class QuoteDetailNotFoundError(LookupError):
    pass


@dataclass(frozen=True, slots=True)
class GetQuoteDetail:
    repository: QuoteDetailRepository

    def execute(self, quote_id: UUID) -> QuoteDetail:
        detail = self.repository.get_detail(quote_id)
        if detail is None:
            raise QuoteDetailNotFoundError("La solicitud no existe.")
        return detail
