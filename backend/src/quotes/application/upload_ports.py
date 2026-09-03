from datetime import datetime
from typing import Protocol
from uuid import UUID

from src.quotes.domain.uploads import UploadItem, UploadSession


class UploadRepository(Protocol):
    def create(self, upload_session: UploadSession, created_at: datetime) -> None: ...

    def get_by_token(self, token: str) -> UploadSession | None: ...

    def add_item(self, session_id: UUID, item: UploadItem, created_at: datetime) -> None: ...

    def mark_removed(self, session_id: UUID, item_id: UUID) -> None: ...

    def mark_confirmed(self, session_id: UUID, quote_id: UUID) -> None: ...
