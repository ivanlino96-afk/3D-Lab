from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import Protocol
from uuid import UUID

from src.audit.domain.entities import AuditEvent
from src.customers.application.resolve_customer import CustomerRepository, ResolveCustomer
from src.customers.domain.contact import Contact
from src.materials.application.ports import MaterialCatalogRepository
from src.materials.domain.entities import PublicationStatus
from src.quotes.application.upload_ports import UploadRepository
from src.quotes.domain.entities import QuoteFile, QuoteRequest, QuoteStatus
from src.shared.domain.types import Clock, TokenFactory, new_entity_id


class QuoteRepository(Protocol):
    def get_by_submission_token(self, token: str) -> QuoteRequest | None: ...

    def reference_exists(self, reference: str) -> bool: ...

    def add(self, quote: QuoteRequest) -> None: ...


class OutboxRepository(Protocol):
    def add(
        self,
        *,
        event_id: UUID,
        event_type: str,
        aggregate_id: UUID,
        dedupe_key: str,
        payload: dict[str, object],
        created_at: datetime,
    ) -> None: ...


class AuditRepository(Protocol):
    def append(self, event: AuditEvent) -> None: ...


class QuoteSubmissionUnitOfWork(Protocol):
    customers: CustomerRepository
    uploads: UploadRepository
    quotes: QuoteRepository
    materials: MaterialCatalogRepository
    outbox: OutboxRepository
    audit: AuditRepository

    def __enter__(self) -> QuoteSubmissionUnitOfWork: ...

    def __exit__(self, exc_type: object, exc: object, traceback: object) -> None: ...


class QuoteSubmissionError(ValueError):
    pass


@dataclass(frozen=True, slots=True)
class ConfirmQuoteCommand:
    submission_token: str
    name: str
    email: str
    phone: str
    comments: str | None = None
    selected_material_slug: str | None = None


@dataclass(frozen=True, slots=True)
class ConfirmQuote:
    unit_of_work: QuoteSubmissionUnitOfWork
    clock: Clock
    reference_factory: TokenFactory

    def execute(self, command: ConfirmQuoteCommand) -> QuoteRequest:
        contact = Contact.create(command.name, command.email, command.phone)
        with self.unit_of_work as unit_of_work:
            existing = unit_of_work.quotes.get_by_submission_token(command.submission_token)
            if existing is not None:
                return existing

            upload_session = unit_of_work.uploads.get_by_token(command.submission_token)
            if upload_session is None:
                raise QuoteSubmissionError("La sesión de carga no está disponible.")
            upload_session.ensure_submittable()

            selected_material_id = None
            if command.selected_material_slug:
                material = unit_of_work.materials.get_by_slug(command.selected_material_slug)
                if material is None or material.status is not PublicationStatus.PUBLISHED:
                    raise QuoteSubmissionError(
                        "El material seleccionado ya no está disponible; elige otro material."
                    )
                selected_material_id = material.id

            now = self.clock()
            customer = ResolveCustomer(unit_of_work.customers).execute(
                contact, new_entity_id(), now
            )
            public_reference = self._unique_reference(unit_of_work.quotes)
            quote_id = new_entity_id()
            quote = QuoteRequest(
                id=quote_id,
                public_reference=public_reference,
                customer_id=customer.id,
                submission_token=command.submission_token,
                contact_name=contact.name,
                contact_email=contact.email,
                contact_phone=contact.phone,
                comments=command.comments.strip() if command.comments else None,
                selected_material_id=selected_material_id,
                status=QuoteStatus.OPEN,
                created_at=now,
                files=tuple(
                    QuoteFile(
                        id=new_entity_id(),
                        original_name=item.original_name,
                        storage_key=item.storage_key or "",
                        size_bytes=item.size_bytes,
                        fingerprint=item.fingerprint or "",
                        uploaded_at=item.uploaded_at or now,
                        expires_at=(item.uploaded_at or now) + timedelta(days=30),
                    )
                    for item in upload_session.valid_items
                ),
            )
            unit_of_work.quotes.add(quote)
            unit_of_work.uploads.mark_confirmed(upload_session.id, quote.id)
            self._enqueue_notifications(unit_of_work.outbox, quote, now)
            unit_of_work.audit.append(
                AuditEvent(
                    actor_type="visitor",
                    action="quote_submitted",
                    entity_type="quote_request",
                    entity_id=str(quote.id),
                    result="success",
                    occurred_at=now,
                )
            )
            return quote

    def _unique_reference(self, repository: QuoteRepository) -> str:
        for _ in range(20):
            candidate = f"3DLAB-{self.reference_factory().upper()[:12]}"
            if not repository.reference_exists(candidate):
                return candidate
        raise QuoteSubmissionError("No fue posible generar un folio único. Intenta de nuevo.")

    @staticmethod
    def _enqueue_notifications(
        repository: OutboxRepository, quote: QuoteRequest, created_at: datetime
    ) -> None:
        for event_type, recipient in (
            ("quote_received_customer", quote.contact_email),
            ("quote_received_admin", "administrator"),
        ):
            repository.add(
                event_id=new_entity_id(),
                event_type=event_type,
                aggregate_id=quote.id,
                dedupe_key=f"{event_type}:{quote.id}",
                payload={"reference": quote.public_reference, "recipient": recipient},
                created_at=created_at,
            )
