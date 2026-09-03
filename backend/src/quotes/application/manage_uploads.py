from __future__ import annotations

from collections.abc import Iterable
from dataclasses import dataclass
from uuid import UUID

from src.quotes.application.upload_ports import UploadRepository
from src.quotes.domain.uploads import (
    MAX_TOTAL_BYTES,
    FileLimitError,
    UploadItem,
    UploadSession,
    UploadStatus,
)
from src.quotes.infrastructure.stl_validator import StlValidator
from src.shared.application.ports import PrivateStorage
from src.shared.domain.types import Clock, TokenFactory, new_entity_id


class UploadSessionNotFoundError(LookupError):
    pass


@dataclass(frozen=True, slots=True)
class CreateUploadSession:
    repository: UploadRepository
    clock: Clock
    token_factory: TokenFactory

    def execute(self) -> UploadSession:
        upload_session = UploadSession(id=new_entity_id(), token=self.token_factory())
        self.repository.create(upload_session, self.clock())
        return upload_session


@dataclass(frozen=True, slots=True)
class ReceiveUpload:
    repository: UploadRepository
    storage: PrivateStorage
    validator: StlValidator
    clock: Clock

    def execute(
        self,
        token: str,
        original_name: str,
        chunks: Iterable[bytes],
        declared_size: int,
    ) -> UploadItem:
        upload_session = self.repository.get_by_token(token)
        if upload_session is None or upload_session.confirmed_quote_id is not None:
            raise UploadSessionNotFoundError("La sesión de carga no está disponible.")
        upload_session.ensure_capacity_for(declared_size)
        item_id = new_entity_id()
        storage_key = f"{upload_session.id}/{item_id}"
        maximum_new_bytes = MAX_TOTAL_BYTES - upload_session.total_bytes
        actual_size = self.storage.save(
            storage_key, self._limited_chunks(chunks, maximum_new_bytes)
        )
        result = self.validator.validate(self.storage.path_for(storage_key), original_name)
        uploaded_at = self.clock()
        item = UploadItem(
            id=item_id,
            original_name=original_name,
            size_bytes=actual_size,
            status=UploadStatus.VALID if result.is_valid else UploadStatus.INVALID,
            storage_key=storage_key if result.is_valid else None,
            fingerprint=result.fingerprint,
            error_message=result.error_message,
            uploaded_at=uploaded_at,
        )
        if not result.is_valid:
            self.storage.delete(storage_key)
        try:
            self.repository.add_item(upload_session.id, item, uploaded_at)
        except Exception:
            if item.storage_key:
                self.storage.delete(item.storage_key)
            raise
        return item

    @staticmethod
    def _limited_chunks(chunks: Iterable[bytes], maximum_bytes: int) -> Iterable[bytes]:
        received = 0
        for chunk in chunks:
            received += len(chunk)
            if received > maximum_bytes:
                raise FileLimitError("El tamaño acumulado no puede superar 500 MB.")
            yield chunk


@dataclass(frozen=True, slots=True)
class RemoveUpload:
    repository: UploadRepository
    storage: PrivateStorage

    def execute(self, token: str, item_id: UUID) -> UploadItem:
        upload_session = self.repository.get_by_token(token)
        if upload_session is None or upload_session.confirmed_quote_id is not None:
            raise UploadSessionNotFoundError("La sesión de carga no está disponible.")
        removed = upload_session.remove(item_id)
        if removed.storage_key:
            self.storage.delete(removed.storage_key)
        self.repository.mark_removed(upload_session.id, item_id)
        return removed
