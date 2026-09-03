from datetime import datetime
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import Session

from src.quotes.infrastructure.repository import QuoteFileRecord
from src.retention.application.expire_quote_files import ExpirableQuoteFile


class SqlAlchemyQuoteFileRetentionRepository:
    def __init__(self, session: Session) -> None:
        self._session = session

    def list_expired(self, now: datetime) -> list[ExpirableQuoteFile]:
        records = self._session.scalars(
            select(QuoteFileRecord).where(
                QuoteFileRecord.status == "available", QuoteFileRecord.expires_at <= now
            )
        ).all()
        return [
            ExpirableQuoteFile(
                id=record.id,
                quote_id=record.quote_request_id,
                storage_key=record.storage_key,
                expires_at=record.expires_at,
            )
            for record in records
        ]

    def mark_expired(self, file_id: UUID, deleted_at: datetime) -> None:
        record = self._session.get(QuoteFileRecord, file_id)
        if record is None:
            raise LookupError("El archivo de cotización no existe.")
        record.status = "expired"
        record.deleted_at = deleted_at
        self._session.flush()
