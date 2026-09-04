from datetime import date
from uuid import UUID

import pytest

from src.catalog.domain.entities import Service
from src.catalog.presentation.routes import get_material_repository, get_service_repository
from src.materials.domain.entities import CostLevel, Material, PublicationStatus


class StaticRepository:
    def __init__(self, services: list[Service]) -> None:
        self._services = services

    def list_published(self) -> list[Service]:
        return self._services


class BrokenRepository:
    def list_published(self) -> list[Service]:
        raise RuntimeError("unavailable")


class StaticMaterialRepository:
    def list_all(self):
        return [
            Material(
                id=UUID(int=2),
                slug="pla",
                name="PLA+",
                description="Preciso para prototipos.",
                advantages=("Excelente detalle",),
                limitations=(),
                available=True,
                cost_level=CostLevel.LOW,
                source_url="https://example.com",
                source_updated_at=date(2026, 1, 1),
                display_order=1,
                status=PublicationStatus.PUBLISHED,
            )
        ]

    def list_applications(self):
        return []

    def list_property_definitions(self):
        return []


def printed_service() -> Service:
    return Service(
        id=UUID(int=1),
        slug="impresion-3d",
        name="Impresión 3D",
        summary="Prototipos y piezas funcionales",
        description="Fabricamos piezas personalizadas para aplicaciones reales.",
        display_order=1,
        is_published=True,
    )


@pytest.mark.e2e
def test_catalog_displays_published_services_and_quote_action(app, client) -> None:
    app.dependency_overrides[get_service_repository] = lambda: StaticRepository([printed_service()])
    app.dependency_overrides[get_material_repository] = StaticMaterialRepository

    response = client.get("/")

    assert response.status_code == 200
    assert "Impresión 3D" in response.text
    assert "Solicitar cotización" in response.text
    assert "/cotizaciones/nueva?servicio=impresion-3d" in response.text
    assert "Conoce qué podemos imprimir" in response.text
    assert "Ejemplo de pieza impresa con PLA+" in response.text
    assert 'data-material-carousel' in response.text
    assert 'class="service-icon"' in response.text
    assert 'data-project-carousel' in response.text
    assert 'data-material-position' in response.text
    assert 'data-project-position' in response.text
    assert "Ejemplos de proyectos" in response.text
    assert "Preguntas frecuentes" in response.text
    assert "Industria y automatización" in response.text
    assert "Refacciones mecánicas" in response.text
    assert "Consultar a 3D-Lab por WhatsApp" in response.text
    assert "De tu archivo a una pieza terminada" in response.text
    assert "Cotiza con claridad y confianza" in response.text
    assert 'class="menu-toggle"' in response.text
    assert "/contacto" in response.text


@pytest.mark.e2e
def test_contact_page_displays_direct_contact_information(client) -> None:
    response = client.get("/contacto")

    assert response.status_code == 200
    assert "Cda. del Risco 1" in response.text
    assert "442 250 2743" in response.text
    assert "3dlabqro@gmail.com" in response.text
    assert "Google Maps" in response.text
    assert "WhatsApp" in response.text


@pytest.mark.e2e
def test_public_legal_pages_are_available(client) -> None:
    privacy = client.get("/privacidad")
    terms = client.get("/condiciones-servicio")

    assert privacy.status_code == 200
    assert "Aviso de privacidad" in privacy.text
    assert "30 días" in privacy.text
    assert terms.status_code == 200
    assert "Condiciones del servicio" in terms.text
    assert "no procesa pagos" in terms.text


@pytest.mark.e2e
def test_catalog_displays_an_empty_state_in_spanish(app, client) -> None:
    app.dependency_overrides[get_service_repository] = lambda: StaticRepository([])
    app.dependency_overrides[get_material_repository] = StaticMaterialRepository

    response = client.get("/")

    assert response.status_code == 200
    assert "Sin resultados" in response.text
    assert "Limpiar filtros" in response.text


@pytest.mark.e2e
def test_catalog_displays_a_recoverable_error_in_spanish(app, client) -> None:
    app.dependency_overrides[get_service_repository] = lambda: BrokenRepository()
    app.dependency_overrides[get_material_repository] = StaticMaterialRepository

    response = client.get("/")

    assert response.status_code == 503
    assert "No pudimos completar la operación" in response.text
    assert "Intentar de nuevo" in response.text
