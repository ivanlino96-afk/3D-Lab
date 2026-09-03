from dataclasses import dataclass

from src.catalog.application.ports import ServiceRepository
from src.catalog.domain.entities import Service


@dataclass(frozen=True, slots=True)
class ListPublishedServices:
    repository: ServiceRepository

    def execute(self) -> list[Service]:
        return sorted(
            self.repository.list_published(),
            key=lambda service: (service.display_order, service.name.casefold()),
        )
