from dataclasses import dataclass

from src.materials.application.ports import MaterialCatalogRepository
from src.materials.domain.entities import PublicationStatus


class MaterialUnavailableError(ValueError):
    pass


@dataclass(frozen=True, slots=True)
class SelectedMaterial:
    slug: str
    name: str


@dataclass(frozen=True, slots=True)
class SelectMaterialForQuote:
    repository: MaterialCatalogRepository

    def execute(self, slug: str) -> SelectedMaterial:
        material = self.repository.get_by_slug(slug)
        if material is None or material.status is not PublicationStatus.PUBLISHED:
            raise MaterialUnavailableError("El material seleccionado ya no está disponible.")
        return SelectedMaterial(slug=material.slug, name=material.name)
