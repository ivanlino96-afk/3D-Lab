from __future__ import annotations

from dataclasses import dataclass, field, replace
from datetime import datetime
from enum import StrEnum
from uuid import UUID

MAX_FILES = 20
MAX_TOTAL_BYTES = 500 * 1024 * 1024


class UploadStatus(StrEnum):
    PENDING = "pending"
    VALID = "valid"
    INVALID = "invalid"
    REMOVED = "removed"


class UploadError(ValueError):
    pass


class FileLimitError(UploadError):
    pass


class PendingUploadsError(UploadError):
    pass


class NoValidFilesError(UploadError):
    pass


@dataclass(frozen=True, slots=True)
class UploadItem:
    id: UUID
    original_name: str
    size_bytes: int
    status: UploadStatus
    storage_key: str | None = None
    fingerprint: str | None = None
    error_message: str | None = None
    uploaded_at: datetime | None = None


@dataclass(slots=True)
class UploadSession:
    id: UUID
    token: str
    items: list[UploadItem] = field(default_factory=list)
    confirmed_quote_id: UUID | None = None

    @property
    def active_items(self) -> list[UploadItem]:
        return [item for item in self.items if item.status is not UploadStatus.REMOVED]

    @property
    def valid_items(self) -> list[UploadItem]:
        return [item for item in self.items if item.status is UploadStatus.VALID]

    @property
    def total_bytes(self) -> int:
        return sum(item.size_bytes for item in self.active_items)

    def ensure_capacity_for(self, size_bytes: int) -> None:
        if len(self.active_items) >= MAX_FILES:
            raise FileLimitError("Cada solicitud admite como máximo 20 archivos.")
        if size_bytes < 0 or self.total_bytes + size_bytes > MAX_TOTAL_BYTES:
            raise FileLimitError("El tamaño acumulado no puede superar 500 MB.")

    def add(self, item: UploadItem) -> None:
        self.ensure_capacity_for(item.size_bytes)
        self.items.append(item)

    def remove(self, item_id: UUID) -> UploadItem:
        for index, item in enumerate(self.items):
            if item.id == item_id and item.status is not UploadStatus.REMOVED:
                removed = replace(item, status=UploadStatus.REMOVED)
                self.items[index] = removed
                return removed
        raise UploadError("El archivo no existe o ya fue retirado.")

    def ensure_submittable(self) -> None:
        if any(item.status is UploadStatus.PENDING for item in self.active_items):
            raise PendingUploadsError("La solicitud tiene cargas pendientes.")
        if not self.valid_items:
            raise NoValidFilesError("Agrega al menos un archivo STL válido.")
