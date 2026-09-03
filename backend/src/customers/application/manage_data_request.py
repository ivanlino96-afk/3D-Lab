from __future__ import annotations

from dataclasses import dataclass, replace
from datetime import datetime
from enum import StrEnum
from typing import Protocol
from uuid import UUID

from src.customers.domain.contact import normalize_email
from src.customers.domain.entities import Customer


class DataRequestType(StrEnum):
    ACCESS = "access"
    CORRECTION = "correction"
    DELETION = "deletion"


class VerificationStatus(StrEnum):
    PENDING = "pending"
    COMPLETED = "completed"


@dataclass(frozen=True, slots=True)
class DataSubjectRequest:
    id: UUID
    customer_id: UUID
    request_type: DataRequestType
    requested_email: str
    verification_status: VerificationStatus
    created_at: datetime
    completed_at: datetime | None = None
    resolution_notes: str | None = None


class DataRequestRepository(Protocol):
    def get_customer(self, customer_id: UUID) -> Customer | None: ...

    def get(self, request_id: UUID) -> DataSubjectRequest | None: ...

    def add(self, request: DataSubjectRequest) -> None: ...

    def complete(self, request: DataSubjectRequest) -> None: ...


class DataRequestError(ValueError):
    pass


@dataclass(frozen=True, slots=True)
class CreateDataRequest:
    repository: DataRequestRepository

    def execute(
        self,
        request_id: UUID,
        customer_id: UUID,
        request_type: DataRequestType,
        requested_email: str,
        now: datetime,
    ) -> DataSubjectRequest:
        if self.repository.get_customer(customer_id) is None:
            raise DataRequestError("El cliente indicado no existe.")
        request = DataSubjectRequest(
            id=request_id,
            customer_id=customer_id,
            request_type=request_type,
            requested_email=requested_email.strip(),
            verification_status=VerificationStatus.PENDING,
            created_at=now,
        )
        self.repository.add(request)
        return request


@dataclass(frozen=True, slots=True)
class CompleteDataRequest:
    repository: DataRequestRepository

    def execute(
        self,
        request_id: UUID,
        verified_email: str,
        resolution_notes: str,
        now: datetime,
    ) -> DataSubjectRequest:
        request = self.repository.get(request_id)
        if request is None:
            raise DataRequestError("La solicitud de datos no existe.")
        customer = self.repository.get_customer(request.customer_id)
        if customer is None or normalize_email(verified_email) != customer.normalized_email:
            raise DataRequestError(
                "El correo verificado no corresponde al cliente asociado; no se ejecutó el cambio."
            )
        completed = replace(
            request,
            verification_status=VerificationStatus.COMPLETED,
            completed_at=now,
            resolution_notes=resolution_notes.strip(),
        )
        self.repository.complete(completed)
        return completed
