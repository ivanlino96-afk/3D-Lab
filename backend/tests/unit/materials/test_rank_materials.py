from datetime import date
from uuid import UUID

import pytest

from src.materials.domain.entities import (
    Application,
    CostLevel,
    Material,
    MaterialFilters,
    MaterialPropertyValue,
    PropertyDefinition,
    PublicationStatus,
)
from src.materials.domain.ranking import rank_materials


def make_material(
    name: str,
    *,
    applications: tuple[str, ...],
    properties: tuple[str, ...],
    available: bool,
    cost: CostLevel,
    status: PublicationStatus = PublicationStatus.PUBLISHED,
) -> Material:
    definitions = {
        slug: PropertyDefinition(slug=slug, name=slug.title(), unit="MPa") for slug in properties
    }
    return Material(
        id=UUID(int=len(name)),
        slug=name.casefold(),
        name=name,
        description=f"Descripción de {name}",
        advantages=("Ventaja",),
        limitations=("Limitación",),
        available=available,
        cost_level=cost,
        source_url="https://example.com/source",
        source_updated_at=date(2026, 1, 1),
        display_order=1,
        status=status,
        applications=tuple(
            Application(slug=slug, name=slug.title(), factors="Factores") for slug in applications
        ),
        properties=tuple(
            MaterialPropertyValue(definition=definitions[slug], value=10, source="TDS")
            for slug in properties
        ),
    )


@pytest.mark.unit
def test_ranks_by_matches_then_availability_then_cost() -> None:
    filters = MaterialFilters(
        applications=frozenset({"industrial"}),
        properties=frozenset({"thermal"}),
    )
    materials = [
        make_material(
            "ABS",
            applications=("industrial",),
            properties=("thermal",),
            available=True,
            cost=CostLevel.MEDIUM,
        ),
        make_material(
            "PC",
            applications=("industrial",),
            properties=("thermal",),
            available=False,
            cost=CostLevel.LOW,
        ),
        make_material(
            "PLA",
            applications=("prototype",),
            properties=("thermal",),
            available=True,
            cost=CostLevel.LOW,
        ),
    ]

    ranked = rank_materials(materials, filters)

    assert [match.material.name for match in ranked] == ["ABS", "PC", "PLA"]
    assert ranked[0].matched_count == 2
    assert set(ranked[0].reasons) == {"Aplicación: Industrial", "Propiedad: Thermal"}


@pytest.mark.unit
def test_excludes_unpublished_and_honors_strict_cost_and_availability_filters() -> None:
    filters = MaterialFilters(
        availability=True,
        costs=frozenset({CostLevel.LOW}),
    )
    materials = [
        make_material(
            "PLA",
            applications=("prototype",),
            properties=("stiffness",),
            available=True,
            cost=CostLevel.LOW,
        ),
        make_material(
            "TPU",
            applications=("flexible",),
            properties=("flexibility",),
            available=False,
            cost=CostLevel.LOW,
        ),
        make_material(
            "Hidden",
            applications=("prototype",),
            properties=("stiffness",),
            available=True,
            cost=CostLevel.LOW,
            status=PublicationStatus.ARCHIVED,
        ),
    ]

    ranked = rank_materials(materials, filters)

    assert [match.material.name for match in ranked] == ["PLA"]


@pytest.mark.unit
def test_returns_empty_when_no_material_matches_any_selected_criterion() -> None:
    filters = MaterialFilters(applications=frozenset({"medical"}))
    materials = [
        make_material(
            "PLA",
            applications=("prototype",),
            properties=("stiffness",),
            available=True,
            cost=CostLevel.LOW,
        )
    ]

    assert rank_materials(materials, filters) == []
