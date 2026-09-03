from dataclasses import dataclass

from src.materials.application.ports import MaterialCatalogRepository
from src.materials.domain.entities import Material, PublicationStatus


class MaterialNotFoundError(LookupError):
    pass


@dataclass(frozen=True, slots=True)
class GetPublishedMaterial:
    repository: MaterialCatalogRepository

    def execute(self, slug: str) -> Material:
        material = self.repository.get_by_slug(slug)
        if material is None or material.status is not PublicationStatus.PUBLISHED:
            raise MaterialNotFoundError("El material solicitado no está disponible.")
        return material
