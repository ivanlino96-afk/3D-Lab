from dataclasses import dataclass
from datetime import datetime
from typing import Protocol
from uuid import UUID

from src.customers.domain.contact import Contact
from src.customers.domain.entities import Customer


class CustomerRepository(Protocol):
    def get_by_normalized_email(self, email: str) -> Customer | None: ...

    def add(self, customer: Customer) -> None: ...

    def update_current_contact(
        self, customer: Customer, contact: Contact, now: datetime
    ) -> Customer: ...


@dataclass(frozen=True, slots=True)
class ResolveCustomer:
    repository: CustomerRepository

    def execute(self, contact: Contact, customer_id: UUID, now: datetime) -> Customer:
        existing = self.repository.get_by_normalized_email(contact.normalized_email)
        if existing is not None:
            return self.repository.update_current_contact(existing, contact, now)
        customer = Customer(
            id=customer_id,
            current_name=contact.name,
            original_email=contact.email,
            normalized_email=contact.normalized_email,
            current_phone=contact.phone,
            created_at=now,
            updated_at=now,
        )
        self.repository.add(customer)
        return customer
