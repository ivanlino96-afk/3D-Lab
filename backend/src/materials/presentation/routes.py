from datetime import date
from typing import Annotated
from urllib.parse import urlencode

from fastapi import APIRouter, Depends, Request
from fastapi.responses import HTMLResponse, RedirectResponse
from sqlalchemy.orm import Session

from src.materials.application.compare_materials import CompareMaterials, ComparisonError
from src.materials.application.explore_materials import ExploreMaterials
from src.materials.application.get_material import GetPublishedMaterial, MaterialNotFoundError
from src.materials.application.ports import MaterialCatalogRepository
from src.materials.application.select_for_quote import (
    MaterialUnavailableError,
    SelectMaterialForQuote,
)
from src.materials.domain.entities import CostLevel, MaterialFilters
from src.materials.infrastructure.repository import SqlAlchemyMaterialCatalogRepository
from src.shared.infrastructure.database import get_session
from src.shared.presentation.messages import MESSAGES, UiMessage, UiState
from src.shared.presentation.templates import templates

router = APIRouter(prefix="/materiales", tags=["materiales"])


def get_material_repository(
    session: Annotated[Session, Depends(get_session)],
) -> MaterialCatalogRepository:
    return SqlAlchemyMaterialCatalogRepository(session)


def _filters_from_request(request: Request) -> MaterialFilters:
    costs: set[CostLevel] = set()
    for raw_cost in request.query_params.getlist("costo"):
        try:
            costs.add(CostLevel(raw_cost))
        except ValueError:
            continue
    availability_value = request.query_params.get("disponible")
    availability = True if availability_value == "si" else None
    return MaterialFilters(
        applications=frozenset(request.query_params.getlist("aplicacion")),
        properties=frozenset(request.query_params.getlist("propiedad")),
        availability=availability,
        costs=frozenset(costs),
    )


@router.get("", response_class=HTMLResponse, name="material_guide")
def material_guide(
    request: Request,
    repository: Annotated[MaterialCatalogRepository, Depends(get_material_repository)],
) -> HTMLResponse:
    try:
        exploration = ExploreMaterials(repository).execute(_filters_from_request(request))
        message: UiMessage | None = MESSAGES["empty"] if not exploration.matches else None
        if request.query_params.get("seleccion") == "no-disponible":
            message = UiMessage(
                UiState.ERROR,
                "El material ya no está disponible",
                "La selección fue retirada antes de iniciar la cotización.",
                "Elegir otro material",
            )
        status_code = 200
    except Exception:
        exploration = None
        message = MESSAGES["error"]
        status_code = 503
    return templates.TemplateResponse(
        request=request,
        name="materials/index.html",
        context={"exploration": exploration, "message": message, "cost_levels": CostLevel},
        status_code=status_code,
    )


@router.get("/comparar", response_class=HTMLResponse, name="compare_materials")
def compare_materials(
    request: Request,
    repository: Annotated[MaterialCatalogRepository, Depends(get_material_repository)],
) -> HTMLResponse:
    try:
        comparison = CompareMaterials(repository).execute(request.query_params.getlist("material"))
        message = None
        status_code = 200
    except ComparisonError as error:
        comparison = None
        message = UiMessage(
            UiState.ERROR, "No se puede comparar", str(error), "Volver a materiales"
        )
        status_code = 400
    except Exception:
        comparison = None
        message = MESSAGES["error"]
        status_code = 503
    return templates.TemplateResponse(
        request=request,
        name="materials/compare.html",
        context={"comparison": comparison, "message": message},
        status_code=status_code,
    )


@router.get("/{slug}/cotizar", name="quote_selected_material")
def quote_selected_material(
    slug: str,
    repository: Annotated[MaterialCatalogRepository, Depends(get_material_repository)],
) -> RedirectResponse:
    try:
        selected = SelectMaterialForQuote(repository).execute(slug)
    except MaterialUnavailableError:
        return RedirectResponse("/materiales?seleccion=no-disponible", status_code=303)
    return RedirectResponse(
        f"/cotizaciones/nueva?{urlencode({'material': selected.slug})}", status_code=303
    )


@router.get("/{slug}", response_class=HTMLResponse, name="material_detail")
def material_detail(
    request: Request,
    slug: str,
    repository: Annotated[MaterialCatalogRepository, Depends(get_material_repository)],
) -> HTMLResponse:
    try:
        material = GetPublishedMaterial(repository).execute(slug)
        message = None
        status_code = 200
    except MaterialNotFoundError as error:
        material = None
        message = UiMessage(UiState.EMPTY, "Material no disponible", str(error), "Ver materiales")
        status_code = 404
    except Exception:
        material = None
        message = MESSAGES["error"]
        status_code = 503
    return templates.TemplateResponse(
        request=request,
        name="materials/detail.html",
        context={
            "material": material,
            "certifications": material.public_certifications(date.today()) if material else (),
            "message": message,
        },
        status_code=status_code,
    )
