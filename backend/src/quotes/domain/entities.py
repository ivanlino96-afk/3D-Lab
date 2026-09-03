from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from enum import StrEnum
from uuid import UUID


class QuoteStatus(StrEnum):
    OPEN = "open"
    QUOTE_SENT = "quote_sent"
    IN_PROGRESS = "in_progress"
    CLOSED = "closed"
    CANCELED = "canceled"

    @property
    def label(self) -> str:
        return {
            self.OPEN: "Abierta",
            self.QUOTE_SENT: "Cotización enviada",
            self.IN_PROGRESS: "En proceso",
            self.CLOSED: "Cerrada",
            self.CANCELED: "Cancelada",
        }[self]


@dataclass(frozen=True, slots=True)
class QuoteFile:
    id: UUID
    original_name: str
    storage_key: str
    size_bytes: int
    fingerprint: str
    uploaded_at: datetime
    expires_at: datetime


@dataclass(frozen=True, slots=True)
class QuoteRequest:
    id: UUID
    public_reference: str
    customer_id: UUID
    submission_token: str
    contact_name: str
    contact_email: str
    contact_phone: str
    comments: str | None
    selected_material_id: UUID | None
    status: QuoteStatus
    created_at: datetime
    files: tuple[QuoteFile, ...]
