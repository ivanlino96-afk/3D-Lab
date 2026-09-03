from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Protocol
from uuid import UUID


@dataclass(frozen=True, slots=True)
class StoredQuoteFile:
    id: UUID
    storage_key: str
    original_name: str


@dataclass(frozen=True, slots=True)
class DownloadedQuoteFile:
    original_name: str
    content: bytes


class QuoteFileAccessRepository(Protocol):
    def get_downloadable(self, file_id: UUID) -> StoredQuoteFile | None: ...

    def record_download(self, file_id: UUID, admin_id: UUID, occurred_at: datetime) -> None: ...


class PrivateFileReader(Protocol):
    def open(self, key: str): ...


class QuoteFileUnavailableError(LookupError):
    pass


@dataclass(frozen=True, slots=True)
class DownloadQuoteFile:
    repository: QuoteFileAccessRepository
    storage: PrivateFileReader

    def execute(self, file_id: UUID, admin_id: UUID, occurred_at: datetime) -> DownloadedQuoteFile:
        stored_file = self.repository.get_downloadable(file_id)
        if stored_file is None:
            raise QuoteFileUnavailableError("El archivo ya no está disponible para descargar.")
        resource = self.storage.open(stored_file.storage_key)
        if hasattr(resource, "__enter__"):
            with resource as stream:
                content = stream.read()
        else:
            content = bytes(resource)
        self.repository.record_download(file_id, admin_id, occurred_at)
        return DownloadedQuoteFile(stored_file.original_name, content)
