from datetime import date
from uuid import UUID

import pytest

from src.materials.domain.entities import (
    Application,
    Certification,
    CostLevel,
    Material,
    MaterialPropertyValue,
    PropertyDefinition,
    PublicationStatus,
)
from src.materials.presentation.routes import get_material_repository

APPLICATIONS = [
    Application("prototype", "Prototipos", "Costo, detalle y facilidad de impresión."),
    Application("industrial", "Entorno industrial", "Temperatura, impacto y químicos."),
]
PROPERTIES = [
    PropertyDefinition("impact", "Resistencia al impacto", "kJ/m²"),
    PropertyDefinition("heat", "Resistencia térmica", "°C"),
]


def material(
    slug: str,
    name: str,
    *,
    applications: tuple[Application, ...],
    values: tuple[float | None, float | None],
    status: PublicationStatus = PublicationStatus.PUBLISHED,
    certifications: tuple[Certification, ...] = (),
) -> Material:
    return Material(
        id=UUID(int=len(slug)),
        slug=slug,
        name=name,
        description=f"Descripción técnica de {name}",
        advantages=("Ventaja verificable",),
        limitations=("Limitación verificable",),
        available=True,
        cost_level=CostLevel.LOW if slug == "pla" else CostLevel.MEDIUM,
        source_url="https://example.com/tds",
        source_updated_at=date(2026, 8, 1),
        display_order=1,
        status=status,
        applications=applications,
        properties=tuple(
            MaterialPropertyValue(definition=definition, value=value, source="TDS")
            for definition, value in zip(PROPERTIES, values, strict=True)
        ),
        certifications=certifications,
        colors=("Negro",),
        finishes=("Mate",),
    )


class StaticMaterialRepository:
    def __init__(self, materials: list[Material]) -> None:
        self.materials = materials

    def list_all(self) -> list[Material]:
        return self.materials

    def get_by_slug(self, slug: str) -> Material | None:
        return next((item for item in self.materials if item.slug == slug), None)

    def list_by_slugs(self, slugs: list[str]) -> list[Material]:
        by_slug = {item.slug: item for item in self.materials}
        return [by_slug[slug] for slug in slugs if slug in by_slug]

    def list_applications(self) -> list[Application]:
        return APPLICATIONS

    def list_property_definitions(self) -> list[PropertyDefinition]:
        return PROPERTIES


class BrokenMaterialRepository(StaticMaterialRepository):
    def list_all(self) -> list[Material]:
        raise RuntimeError("database unavailable")


@pytest.fixture
def catalog() -> list[Material]:
    valid = Certification(
        "Uso técnico vigente",
        "Laboratorio",
        "https://example.com/current",
        date(2026, 1, 1),
        date(2027, 1, 1),
    )
    expired = Certification(
        "Uso técnico vencido",
        "Laboratorio",
        "https://example.com/expired",
        date(2024, 1, 1),
        date(2025, 1, 1),
    )
    return [
        material(
            "pla",
            "PLA",
            applications=(APPLICATIONS[0],),
            values=(26.6, 57),
            certifications=(valid, expired),
        ),
        material(
            "abs",
            "ABS",
            applications=(APPLICATIONS[1],),
            values=(39.3, None),
        ),
    ]


@pytest.mark.e2e
def test_filters_materials_and_explains_the_ranking(app, client, catalog) -> None:
    app.dependency_overrides[get_material_repository] = lambda: StaticMaterialRepository(catalog)

    response = client.get("/materiales?aplicacion=industrial&propiedad=impact")

    assert response.status_code == 200
    assert "Filtros activos" in response.text
    assert response.text.index("ABS") < response.text.index("PLA")
    assert "Aplicación: Entorno industrial" in response.text
    assert "Propiedad: Resistencia al impacto" in response.text


@pytest.mark.e2e
def test_shows_empty_state_and_clear_action_when_there_are_no_matches(app, client, catalog) -> None:
    app.dependency_overrides[get_material_repository] = lambda: StaticMaterialRepository(catalog)

    response = client.get("/materiales?aplicacion=medical")

    assert response.status_code == 200
    assert "Sin resultados" in response.text
    assert "Limpiar filtros" in response.text


@pytest.mark.e2e
def test_compares_materials_with_consistent_units_and_missing_values(app, client, catalog) -> None:
    app.dependency_overrides[get_material_repository] = lambda: StaticMaterialRepository(catalog)

    response = client.get("/materiales/comparar?material=pla&material=abs")

    assert response.status_code == 200
    assert "Resistencia térmica" in response.text
    assert "°C" in response.text
    assert "57 °C" in response.text
    assert "No disponible" in response.text


@pytest.mark.e2e
def test_detail_only_displays_current_certification_evidence(app, client, catalog) -> None:
    app.dependency_overrides[get_material_repository] = lambda: StaticMaterialRepository(catalog)

    response = client.get("/materiales/pla")

    assert response.status_code == 200
    assert "Uso técnico vigente" in response.text
    assert "Uso técnico vencido" not in response.text
    assert "Cotizar con PLA" in response.text


@pytest.mark.e2e
def test_selected_published_material_is_forwarded_to_quote(app, client, catalog) -> None:
    app.dependency_overrides[get_material_repository] = lambda: StaticMaterialRepository(catalog)

    response = client.get("/materiales/pla/cotizar", follow_redirects=False)

    assert response.status_code == 303
    assert response.headers["location"] == "/cotizaciones/nueva?material=pla"


@pytest.mark.e2e
def test_archived_selection_is_removed_with_a_spanish_message(app, client, catalog) -> None:
    archived = material(
        "old",
        "Material archivado",
        applications=(APPLICATIONS[0],),
        values=(10, 40),
        status=PublicationStatus.ARCHIVED,
    )
    app.dependency_overrides[get_material_repository] = lambda: StaticMaterialRepository(
        [*catalog, archived]
    )

    redirect = client.get("/materiales/old/cotizar", follow_redirects=False)
    response = client.get(redirect.headers["location"])

    assert redirect.status_code == 303
    assert response.status_code == 200
    assert "El material ya no está disponible" in response.text
    assert "La selección fue retirada" in response.text


@pytest.mark.e2e
def test_repository_failure_has_recoverable_spanish_state(app, client) -> None:
    app.dependency_overrides[get_material_repository] = lambda: BrokenMaterialRepository([])

    response = client.get("/materiales")

    assert response.status_code == 503
    assert "No pudimos completar la operación" in response.text
    assert "Intentar de nuevo" in response.text
