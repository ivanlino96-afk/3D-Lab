from __future__ import annotations

from dataclasses import dataclass
from datetime import date, datetime
from typing import Protocol
from uuid import UUID

from src.quotes.domain.entities import QuoteStatus


@dataclass(frozen=True, slots=True)
class QuoteSearch:
    query: str | None
    statuses: tuple[QuoteStatus, ...]
    date_from: date | None
    date_to: date | None
    page: int
    page_size: int


@dataclass(frozen=True, slots=True)
class QuoteListItem:
    id: UUID
    public_reference: str
    customer_name: str
    customer_email: str
    status: QuoteStatus
    created_at: datetime
    has_available_files: bool


@dataclass(frozen=True, slots=True)
class QuotePage:
    items: tuple[QuoteListItem, ...]
    total: int
    page: int
    page_size: int

    @property
    def total_pages(self) -> int:
        return max(1, (self.total + self.page_size - 1) // self.page_size)


class QuoteQueries(Protocol):
    def search(self, search: QuoteSearch) -> QuotePage: ...

    def list_for_customer(self, customer_id: UUID) -> tuple[QuoteListItem, ...]: ...


@dataclass(frozen=True, slots=True)
class ListQuotes:
    repository: QuoteQueries

    def execute(
        self,
        query: str | None,
        statuses: tuple[str, ...],
        date_from: date | None,
        date_to: date | None,
        page: int = 1,
        page_size: int = 50,
    ) -> QuotePage:
        cleaned_query = query.strip() if query and query.strip() else None
        valid_statuses = tuple(QuoteStatus(status) for status in statuses)
        search = QuoteSearch(
            cleaned_query,
            valid_statuses,
            date_from,
            date_to,
            max(1, page),
            min(50, max(1, page_size)),
        )
        return self.repository.search(search)


@dataclass(frozen=True, slots=True)
class ListCustomerQuotes:
    repository: QuoteQueries

    def execute(self, customer_id: UUID) -> tuple[QuoteListItem, ...]:
        return tuple(
            sorted(
                self.repository.list_for_customer(customer_id),
                key=lambda item: item.created_at,
                reverse=True,
            )
        )
