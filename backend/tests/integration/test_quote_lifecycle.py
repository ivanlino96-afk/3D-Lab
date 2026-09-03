from datetime import UTC, datetime, timedelta
from uuid import UUID

import pytest
from sqlalchemy import create_engine, func, select
from sqlalchemy.orm import sessionmaker

from src.audit.infrastructure.repository import AuditEventRecord, SqlAlchemyAuditRepository
from src.customers.application.manage_data_request import (
    CompleteDataRequest,
    CreateDataRequest,
    DataRequestError,
    DataRequestType,
)
from src.customers.infrastructure.repository import (
    CustomerRecord,
    SqlAlchemyDataRequestRepository,
)
from src.materials.infrastructure.repository import MaterialRecord  # noqa: F401
from src.quotes.application.confirm_quote import ConfirmQuote, ConfirmQuoteCommand
from src.quotes.application.manage_uploads import CreateUploadSession, ReceiveUpload
from src.quotes.infrastructure.repository import (
    OutboxEventRecord,
    QuoteFileRecord,
    QuoteRequestRecord,
    SqlAlchemyUploadRepository,
)
from src.quotes.infrastructure.stl_validator import StlValidator
from src.quotes.infrastructure.unit_of_work import SqlAlchemyQuoteSubmissionUnitOfWork
from src.retention.application.expire_quote_files import ExpireQuoteFiles
from src.retention.infrastructure.repository import SqlAlchemyQuoteFileRetentionRepository
from src.shared.infrastructure.database import Base
from src.shared.infrastructure.private_storage import FileSystemPrivateStorage

NOW = datetime(2026, 9, 2, 12, tzinfo=UTC)
VALID_STL = b"solid piece\nfacet normal 0 0 0\nendfacet\nendsolid piece"


@pytest.fixture
def session_factory(tmp_path):
    engine = create_engine(f"sqlite:///{tmp_path / 'quotes.db'}")
    Base.metadata.create_all(engine)
    yield sessionmaker(bind=engine, expire_on_commit=False)
    Base.metadata.drop_all(engine)
    engine.dispose()


def create_valid_upload(session, storage, token: str):
    repository = SqlAlchemyUploadRepository(session)
    upload_session = CreateUploadSession(repository, lambda: NOW, lambda: token).execute()
    uploaded = ReceiveUpload(repository, storage, StlValidator(), lambda: NOW).execute(
        token,
        "pieza.stl",
        [VALID_STL[:20], VALID_STL[20:]],
        len(VALID_STL),
    )
    return upload_session, uploaded


@pytest.mark.integration
def test_quote_is_idempotent_and_keeps_customer_history_and_contact_snapshots(
    session_factory, tmp_path
) -> None:
    storage = FileSystemPrivateStorage(tmp_path / "private")
    with session_factory.begin() as session:
        create_valid_upload(session, storage, "first-token")
        first_use_case = ConfirmQuote(
            SqlAlchemyQuoteSubmissionUnitOfWork(session), lambda: NOW, lambda: "first-ref"
        )
        first = first_use_case.execute(
            ConfirmQuoteCommand("first-token", "Ana López", "ANA@example.com", "5512345678")
        )
        repeated = first_use_case.execute(
            ConfirmQuoteCommand("first-token", "Ana López", "ANA@example.com", "5512345678")
        )
        create_valid_upload(session, storage, "second-token")
        second = ConfirmQuote(
            SqlAlchemyQuoteSubmissionUnitOfWork(session), lambda: NOW, lambda: "second-ref"
        ).execute(
            ConfirmQuoteCommand("second-token", "Ana Actualizada", "ana@EXAMPLE.com", "5598765432")
        )

        assert repeated.id == first.id
        assert first.customer_id == second.customer_id
        assert session.scalar(select(func.count()).select_from(CustomerRecord)) == 1
        assert session.scalar(select(func.count()).select_from(QuoteRequestRecord)) == 2
        assert session.scalar(select(func.count()).select_from(OutboxEventRecord)) == 4
        snapshots = {
            item.submission_token: item.contact_name
            for item in session.scalars(select(QuoteRequestRecord)).all()
        }
        assert snapshots == {"first-token": "Ana López", "second-token": "Ana Actualizada"}


@pytest.mark.integration
def test_expiration_deletes_private_stl_but_keeps_metadata(session_factory, tmp_path) -> None:
    storage = FileSystemPrivateStorage(tmp_path / "private")
    with session_factory.begin() as session:
        _, uploaded = create_valid_upload(session, storage, "retention-token")
        quote = ConfirmQuote(
            SqlAlchemyQuoteSubmissionUnitOfWork(session), lambda: NOW, lambda: "retention-ref"
        ).execute(
            ConfirmQuoteCommand("retention-token", "Ana López", "ana@example.com", "5512345678")
        )
        assert uploaded.storage_key is not None
        assert storage.path_for(uploaded.storage_key).exists()

        deleted = ExpireQuoteFiles(
            SqlAlchemyQuoteFileRetentionRepository(session),
            storage,
            SqlAlchemyAuditRepository(session),
        ).execute(NOW + timedelta(days=30))
        record = session.scalar(
            select(QuoteFileRecord).where(QuoteFileRecord.quote_request_id == quote.id)
        )

        assert deleted == 1
        assert record is not None
        assert record.original_name == "pieza.stl"
        assert record.size_bytes == len(VALID_STL)
        assert record.status == "expired"
        assert record.deleted_at is not None
        assert not storage.path_for(uploaded.storage_key).exists()
        assert session.scalar(select(func.count()).select_from(AuditEventRecord)) == 2


@pytest.mark.integration
def test_data_change_requires_verified_associated_email(session_factory, tmp_path) -> None:
    with session_factory.begin() as session:
        storage = FileSystemPrivateStorage(tmp_path / "privacy-private")
        create_valid_upload(session, storage, "privacy-token")
        quote = ConfirmQuote(
            SqlAlchemyQuoteSubmissionUnitOfWork(session), lambda: NOW, lambda: "privacy-ref"
        ).execute(
            ConfirmQuoteCommand("privacy-token", "Ana López", "ana@example.com", "5512345678")
        )
        repository = SqlAlchemyDataRequestRepository(session)
        request = CreateDataRequest(repository).execute(
            UUID(int=90), quote.customer_id, DataRequestType.CORRECTION, "ana@example.com", NOW
        )

        with pytest.raises(DataRequestError, match="no corresponde"):
            CompleteDataRequest(repository).execute(
                request.id, "attacker@example.com", "Cambiar teléfono", NOW
            )

        completed = CompleteDataRequest(repository).execute(
            request.id, "ANA@example.com", "Identidad verificada", NOW
        )
        assert completed.verification_status.value == "completed"
