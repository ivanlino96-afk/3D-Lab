from __future__ import annotations

from sqlalchemy.orm import Session

from src.audit.infrastructure.repository import SqlAlchemyAuditRepository
from src.customers.infrastructure.repository import SqlAlchemyCustomerRepository
from src.materials.infrastructure.repository import SqlAlchemyMaterialCatalogRepository
from src.quotes.infrastructure.repository import (
    SqlAlchemyOutboxRepository,
    SqlAlchemyQuoteRepository,
    SqlAlchemyUploadRepository,
)


class SqlAlchemyQuoteSubmissionUnitOfWork:
    def __init__(self, session: Session) -> None:
        self._session = session
        self._transaction = None
        self.customers = SqlAlchemyCustomerRepository(session)
        self.uploads = SqlAlchemyUploadRepository(session)
        self.quotes = SqlAlchemyQuoteRepository(session)
        self.materials = SqlAlchemyMaterialCatalogRepository(session)
        self.outbox = SqlAlchemyOutboxRepository(session)
        self.audit = SqlAlchemyAuditRepository(session)

    def __enter__(self) -> SqlAlchemyQuoteSubmissionUnitOfWork:
        self._transaction = self._session.begin_nested()
        return self

    def __exit__(self, exc_type: object, exc: object, traceback: object) -> None:
        if self._transaction is None:
            return
        if exc_type is None:
            self._transaction.commit()
        else:
            self._transaction.rollback()
