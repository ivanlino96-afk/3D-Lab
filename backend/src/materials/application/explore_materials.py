from dataclasses import dataclass

from src.materials.application.ports import MaterialCatalogRepository
from src.materials.domain.entities import Application, MaterialFilters, PropertyDefinition
from src.materials.domain.ranking import MaterialMatch, rank_materials


@dataclass(frozen=True, slots=True)
class MaterialExploration:
    matches: list[MaterialMatch]
    applications: list[Application]
    properties: list[PropertyDefinition]
    filters: MaterialFilters


@dataclass(frozen=True, slots=True)
class ExploreMaterials:
    repository: MaterialCatalogRepository

    def execute(self, filters: MaterialFilters) -> MaterialExploration:
        return MaterialExploration(
            matches=rank_materials(self.repository.list_all(), filters),
            applications=self.repository.list_applications(),
            properties=self.repository.list_property_definitions(),
            filters=filters,
        )
