from datetime import UTC, datetime, timedelta
from uuid import UUID

import pytest

from src.customers.domain.contact import Contact
from src.customers.domain.entities import Customer
from src.quotes.application.confirm_quote import (
    ConfirmQuote,
    ConfirmQuoteCommand,
    QuoteSubmissionError,
)
from src.quotes.domain.entities import QuoteRequest, QuoteStatus
from src.quotes.domain.uploads import NoValidFilesError, UploadItem, UploadSession, UploadStatus

NOW = datetime(2026, 9, 2, 12, tzinfo=UTC)


class FakeCustomers:
    def __init__(self) -> None:
        self.by_email: dict[str, Customer] = {}

    def get_by_normalized_email(self, email: str) -> Customer | None:
        return self.by_email.get(email)

    def add(self, customer: Customer) -> None:
        self.by_email[customer.normalized_email] = customer

    def update_current_contact(
        self, customer: Customer, contact: Contact, now: datetime
    ) -> Customer:
        updated = Customer(
            id=customer.id,
            current_name=contact.name,
            original_email=customer.original_email,
            normalized_email=customer.normalized_email,
            current_phone=contact.phone,
            created_at=customer.created_at,
            updated_at=now,
        )
        self.by_email[updated.normalized_email] = updated
        return updated


class FakeUploads:
    def __init__(self, upload_session: UploadSession) -> None:
        self.upload_session = upload_session

    def get_by_token(self, token: str) -> UploadSession | None:
        return self.upload_session if token == self.upload_session.token else None

    def mark_confirmed(self, session_id: UUID, quote_id: UUID) -> None:
        self.upload_session.confirmed_quote_id = quote_id


class FakeQuotes:
    def __init__(self) -> None:
        self.items: list[QuoteRequest] = []
        self.existing_references: set[str] = set()

    def get_by_submission_token(self, token: str) -> QuoteRequest | None:
        return next((item for item in self.items if item.submission_token == token), None)

    def reference_exists(self, reference: str) -> bool:
        return reference in self.existing_references or any(
            item.public_reference == reference for item in self.items
        )

    def add(self, quote: QuoteRequest) -> None:
        self.items.append(quote)


class FakeMaterials:
    def get_by_slug(self, slug: str):
        return None


class FakeOutbox:
    def __init__(self) -> None:
        self.events: list[dict[str, object]] = []

    def add(self, **event) -> None:
        self.events.append(event)


class FakeAudit:
    def __init__(self) -> None:
        self.events = []

    def append(self, event) -> None:
        self.events.append(event)


class FakeUnitOfWork:
    def __init__(self, upload_session: UploadSession) -> None:
        self.customers = FakeCustomers()
        self.uploads = FakeUploads(upload_session)
        self.quotes = FakeQuotes()
        self.materials = FakeMaterials()
        self.outbox = FakeOutbox()
        self.audit = FakeAudit()
        self.exited_with_error = False

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, traceback) -> None:
        self.exited_with_error = exc_type is not None


def valid_session() -> UploadSession:
    return UploadSession(
        id=UUID(int=1),
        token="submission-token",
        items=[
            UploadItem(
                id=UUID(int=2),
                original_name="pieza.stl",
                size_bytes=128,
                status=UploadStatus.VALID,
                storage_key="session/file",
                fingerprint="a" * 64,
                uploaded_at=NOW,
            )
        ],
    )


def command() -> ConfirmQuoteCommand:
    return ConfirmQuoteCommand(
        submission_token="submission-token",
        name="Ana López",
        email="ANA@example.com",
        phone="5512345678",
        comments="Pieza funcional",
    )


@pytest.mark.unit
def test_confirms_once_and_creates_customer_files_audit_and_notifications() -> None:
    unit_of_work = FakeUnitOfWork(valid_session())
    use_case = ConfirmQuote(unit_of_work, lambda: NOW, lambda: "random-reference")

    quote = use_case.execute(command())

    assert quote.status is QuoteStatus.OPEN
    assert quote.public_reference == "3DLAB-RANDOM-REFER"
    assert quote.contact_email == "ANA@example.com"
    assert quote.files[0].expires_at - quote.files[0].uploaded_at == timedelta(days=30)
    assert "ana@example.com" in unit_of_work.customers.by_email
    assert len(unit_of_work.outbox.events) == 2
    assert len(unit_of_work.audit.events) == 1


@pytest.mark.unit
def test_second_activation_returns_existing_quote_without_duplicates() -> None:
    unit_of_work = FakeUnitOfWork(valid_session())
    use_case = ConfirmQuote(unit_of_work, lambda: NOW, lambda: "one-reference")

    first = use_case.execute(command())
    second = use_case.execute(command())

    assert second.id == first.id
    assert len(unit_of_work.quotes.items) == 1
    assert len(unit_of_work.outbox.events) == 2


@pytest.mark.unit
def test_reference_collision_generates_another_reference() -> None:
    unit_of_work = FakeUnitOfWork(valid_session())
    unit_of_work.quotes.existing_references.add("3DLAB-COLLISION")
    references = iter(["collision", "unique-value"])

    quote = ConfirmQuote(unit_of_work, lambda: NOW, references.__next__).execute(command())

    assert quote.public_reference == "3DLAB-UNIQUE-VALUE"


@pytest.mark.unit
def test_rejects_submission_without_valid_stl_and_rolls_back() -> None:
    upload_session = UploadSession(id=UUID(int=1), token="submission-token")
    unit_of_work = FakeUnitOfWork(upload_session)

    with pytest.raises(NoValidFilesError, match="STL válido"):
        ConfirmQuote(unit_of_work, lambda: NOW, lambda: "reference").execute(command())

    assert unit_of_work.exited_with_error is True
    assert unit_of_work.quotes.items == []


@pytest.mark.unit
def test_rejects_missing_upload_session() -> None:
    unit_of_work = FakeUnitOfWork(valid_session())

    with pytest.raises(QuoteSubmissionError, match="sesión de carga"):
        ConfirmQuote(unit_of_work, lambda: NOW, lambda: "reference").execute(
            ConfirmQuoteCommand(
                submission_token="missing",
                name="Ana López",
                email="ana@example.com",
                phone="5512345678",
            )
        )
