from __future__ import annotations

import uuid
from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, String, Text, select
from sqlalchemy.orm import Mapped, Session, mapped_column

from src.customers.application.manage_data_request import (
    DataRequestRepository,
    DataRequestType,
    DataSubjectRequest,
    VerificationStatus,
)
from src.customers.application.resolve_customer import CustomerRepository
from src.customers.domain.contact import Contact
from src.customers.domain.entities import Customer
from src.shared.infrastructure.database import Base


class CustomerRecord(Base):
    __tablename__ = "customers"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True)
    current_name: Mapped[str] = mapped_column(String(100), nullable=False)
    original_email: Mapped[str] = mapped_column(String(254), nullable=False)
    normalized_email: Mapped[str] = mapped_column(String(254), unique=True, nullable=False)
    current_phone: Mapped[str] = mapped_column(String(16), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)


class DataSubjectRequestRecord(Base):
    __tablename__ = "data_subject_requests"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True)
    customer_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("customers.id"), nullable=False)
    request_type: Mapped[str] = mapped_column(String(12), nullable=False)
    requested_email: Mapped[str] = mapped_column(String(254), nullable=False)
    verification_status: Mapped[str] = mapped_column(String(12), nullable=False)
    resolution_notes: Mapped[str | None] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))


class SqlAlchemyCustomerRepository(CustomerRepository):
    def __init__(self, session: Session) -> None:
        self._session = session

    def get_by_normalized_email(self, email: str) -> Customer | None:
        record = self._session.scalar(
            select(CustomerRecord).where(CustomerRecord.normalized_email == email)
        )
        return self._to_domain(record) if record else None

    def add(self, customer: Customer) -> None:
        self._session.add(
            CustomerRecord(
                id=customer.id,
                current_name=customer.current_name,
                original_email=customer.original_email,
                normalized_email=customer.normalized_email,
                current_phone=customer.current_phone,
                created_at=customer.created_at,
                updated_at=customer.updated_at,
            )
        )
        self._session.flush()

    def update_current_contact(
        self, customer: Customer, contact: Contact, now: datetime
    ) -> Customer:
        record = self._session.get(CustomerRecord, customer.id)
        if record is None:
            raise LookupError("El cliente no existe.")
        record.current_name = contact.name
        record.current_phone = contact.phone
        record.updated_at = now
        self._session.flush()
        return self._to_domain(record)

    @staticmethod
    def _to_domain(record: CustomerRecord) -> Customer:
        return Customer(
            id=record.id,
            current_name=record.current_name,
            original_email=record.original_email,
            normalized_email=record.normalized_email,
            current_phone=record.current_phone,
            created_at=record.created_at,
            updated_at=record.updated_at,
        )


class SqlAlchemyDataRequestRepository(DataRequestRepository):
    def __init__(self, session: Session) -> None:
        self._session = session

    def get_customer(self, customer_id: uuid.UUID) -> Customer | None:
        record = self._session.get(CustomerRecord, customer_id)
        return SqlAlchemyCustomerRepository._to_domain(record) if record else None

    def get(self, request_id: uuid.UUID) -> DataSubjectRequest | None:
        record = self._session.get(DataSubjectRequestRecord, request_id)
        if record is None:
            return None
        return self._to_domain(record)

    def add(self, request: DataSubjectRequest) -> None:
        self._session.add(
            DataSubjectRequestRecord(
                id=request.id,
                customer_id=request.customer_id,
                request_type=request.request_type.value,
                requested_email=request.requested_email,
                verification_status=request.verification_status.value,
                resolution_notes=request.resolution_notes,
                created_at=request.created_at,
                completed_at=request.completed_at,
            )
        )
        self._session.flush()

    def complete(self, request: DataSubjectRequest) -> None:
        record = self._session.get(DataSubjectRequestRecord, request.id)
        if record is None:
            raise LookupError("La solicitud de datos no existe.")
        record.verification_status = request.verification_status.value
        record.resolution_notes = request.resolution_notes
        record.completed_at = request.completed_at
        self._session.flush()

    @staticmethod
    def _to_domain(record: DataSubjectRequestRecord) -> DataSubjectRequest:
        return DataSubjectRequest(
            id=record.id,
            customer_id=record.customer_id,
            request_type=DataRequestType(record.request_type),
            requested_email=record.requested_email,
            verification_status=VerificationStatus(record.verification_status),
            resolution_notes=record.resolution_notes,
            created_at=record.created_at,
            completed_at=record.completed_at,
        )
