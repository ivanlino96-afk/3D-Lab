from typing import Protocol

from src.catalog.domain.entities import Service


class ServiceRepository(Protocol):
    def list_published(self) -> list[Service]: ...
