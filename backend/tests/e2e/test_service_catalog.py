from uuid import UUID

import pytest

from src.catalog.domain.entities import Service
from src.catalog.presentation.routes import get_service_repository


class StaticRepository:
    def __init__(self, services: list[Service]) -> None:
        self._services = services

    def list_published(self) -> list[Service]:
        return self._services


class BrokenRepository:
    def list_published(self) -> list[Service]:
        raise RuntimeError("unavailable")


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

    response = client.get("/")

    assert response.status_code == 200
    assert "Impresión 3D" in response.text
    assert "Solicitar cotización" in response.text
    assert "/cotizaciones/nueva?servicio=impresion-3d" in response.text


@pytest.mark.e2e
def test_catalog_displays_an_empty_state_in_spanish(app, client) -> None:
    app.dependency_overrides[get_service_repository] = lambda: StaticRepository([])

    response = client.get("/")

    assert response.status_code == 200
    assert "Sin resultados" in response.text
    assert "Limpiar filtros" in response.text


@pytest.mark.e2e
def test_catalog_displays_a_recoverable_error_in_spanish(app, client) -> None:
    app.dependency_overrides[get_service_repository] = lambda: BrokenRepository()

    response = client.get("/")

    assert response.status_code == 503
    assert "No pudimos completar la operación" in response.text
    assert "Intentar de nuevo" in response.text
