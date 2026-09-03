from datetime import UTC, date, datetime
from uuid import UUID

import pytest

from src.administration.application.download_quote_file import (
    DownloadQuoteFile,
    QuoteFileUnavailableError,
)
from src.administration.application.list_quotes import (
    ListCustomerQuotes,
    ListQuotes,
    QuoteListItem,
    QuotePage,
    QuoteSearch,
)
from src.quotes.domain.entities import QuoteStatus

NOW = datetime(2026, 9, 2, 12, tzinfo=UTC)


class FakeQueries:
    def __init__(self) -> None:
        self.last_search = None
        self.customer_id = None

    def search(self, search: QuoteSearch) -> QuotePage:
        self.last_search = search
        return QuotePage((summary(1),), 1, search.page, search.page_size)

    def list_for_customer(self, customer_id: UUID) -> tuple[QuoteListItem, ...]:
        self.customer_id = customer_id
        return (summary(2), summary(1))


def summary(day: int) -> QuoteListItem:
    return QuoteListItem(
        UUID(int=day),
        f"3DLAB-{day}",
        "Ana López",
        "ana@example.com",
        QuoteStatus.OPEN,
        datetime(2026, 9, day, tzinfo=UTC),
        True,
    )


@pytest.mark.unit
def test_combined_filters_are_cleaned_and_page_size_is_capped_at_fifty() -> None:
    repository = FakeQueries()
    result = ListQuotes(repository).execute(
        query="  ANA@example.com ",
        statuses=("open", "quote_sent"),
        date_from=date(2026, 8, 1),
        date_to=date(2026, 9, 2),
        page=2,
        page_size=200,
    )

    assert result.page_size == 50
    assert repository.last_search.query == "ANA@example.com"
    assert repository.last_search.statuses == (
        QuoteStatus.OPEN,
        QuoteStatus.QUOTE_SENT,
    )


@pytest.mark.unit
def test_empty_filters_and_invalid_pages_use_safe_defaults() -> None:
    repository = FakeQueries()
    ListQuotes(repository).execute("  ", (), None, None, page=0, page_size=0)

    assert repository.last_search.query is None
    assert repository.last_search.page == 1
    assert repository.last_search.page_size == 1


@pytest.mark.unit
def test_customer_history_is_returned_newest_first() -> None:
    repository = FakeQueries()
    items = ListCustomerQuotes(repository).execute(UUID(int=10))

    assert [item.created_at.day for item in items] == [2, 1]


class FakeFileRepository:
    def __init__(self, status: str) -> None:
        self.status = status
        self.audited = False

    def get_downloadable(self, file_id: UUID):
        if self.status != "available":
            return None
        return type(
            "StoredFile",
            (),
            {"id": file_id, "storage_key": "private/key", "original_name": "pieza.stl"},
        )()

    def record_download(self, file_id: UUID, admin_id: UUID, occurred_at: datetime) -> None:
        self.audited = True


class FakeStorage:
    def open(self, key: str):
        return b"solid piece"


@pytest.mark.unit
def test_download_returns_only_an_available_private_file_and_audits() -> None:
    repository = FakeFileRepository("available")
    result = DownloadQuoteFile(repository, FakeStorage()).execute(UUID(int=1), UUID(int=2), NOW)

    assert result.original_name == "pieza.stl"
    assert result.content == b"solid piece"
    assert repository.audited is True


@pytest.mark.unit
def test_expired_file_download_is_rejected() -> None:
    with pytest.raises(QuoteFileUnavailableError, match="ya no está disponible"):
        DownloadQuoteFile(FakeFileRepository("expired"), FakeStorage()).execute(
            UUID(int=1), UUID(int=2), NOW
        )
