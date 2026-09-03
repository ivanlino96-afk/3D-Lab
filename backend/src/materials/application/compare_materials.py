from dataclasses import dataclass

from src.materials.application.ports import MaterialCatalogRepository
from src.materials.domain.entities import Material, PropertyDefinition, PublicationStatus


class ComparisonError(ValueError):
    pass


@dataclass(frozen=True, slots=True)
class ComparisonRow:
    definition: PropertyDefinition
    values: tuple[str, ...]


@dataclass(frozen=True, slots=True)
class MaterialComparison:
    materials: tuple[Material, ...]
    rows: tuple[ComparisonRow, ...]


@dataclass(frozen=True, slots=True)
class CompareMaterials:
    repository: MaterialCatalogRepository

    def execute(self, slugs: list[str]) -> MaterialComparison:
        unique_slugs = list(dict.fromkeys(slugs))
        materials = [
            material
            for material in self.repository.list_by_slugs(unique_slugs)
            if material.status is PublicationStatus.PUBLISHED
        ]
        if len(materials) < 2:
            raise ComparisonError("Selecciona al menos dos materiales disponibles para comparar.")

        rows: list[ComparisonRow] = []
        for definition in self.repository.list_property_definitions():
            values: list[str] = []
            for material in materials:
                value = next(
                    (
                        item.display_value
                        for item in material.properties
                        if item.definition.slug == definition.slug
                    ),
                    "No disponible",
                )
                values.append(value)
            rows.append(ComparisonRow(definition=definition, values=tuple(values)))
        return MaterialComparison(materials=tuple(materials), rows=tuple(rows))
