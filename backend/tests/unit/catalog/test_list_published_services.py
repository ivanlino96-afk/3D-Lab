from uuid import UUID

import pytest

from src.catalog.application.list_services import ListPublishedServices
from src.catalog.domain.entities import Service


def service(name: str, order: int) -> Service:
    return Service(
        id=UUID(int=order + 1),
        slug=name.casefold().replace(" ", "-"),
        name=name,
        summary=f"Resumen de {name}",
        description=f"Descripción de {name}",
        display_order=order,
        is_published=True,
    )


class InMemoryServiceRepository:
    def __init__(self, services: list[Service]) -> None:
        self.services = services

    def list_published(self) -> list[Service]:
        return self.services


class BrokenServiceRepository:
    def list_published(self) -> list[Service]:
        raise RuntimeError("database unavailable")


@pytest.mark.unit
def test_lists_services_in_display_order() -> None:
    repository = InMemoryServiceRepository([service("Ingeniería", 2), service("Impresión", 1)])

    result = ListPublishedServices(repository).execute()

    assert [item.name for item in result] == ["Impresión", "Ingeniería"]


@pytest.mark.unit
def test_returns_an_empty_catalog_without_error() -> None:
    assert ListPublishedServices(InMemoryServiceRepository([])).execute() == []


@pytest.mark.unit
def test_propagates_repository_errors_to_the_presentation_boundary() -> None:
    with pytest.raises(RuntimeError, match="database unavailable"):
        ListPublishedServices(BrokenServiceRepository()).execute()
