from typing import Annotated

from fastapi import APIRouter, Depends, Request
from fastapi.responses import HTMLResponse
from sqlalchemy.orm import Session

from src.catalog.application.list_services import ListPublishedServices
from src.catalog.application.ports import ServiceRepository
from src.catalog.infrastructure.repository import SqlAlchemyServiceRepository
from src.materials.application.explore_materials import ExploreMaterials
from src.materials.application.ports import MaterialCatalogRepository
from src.materials.domain.entities import MaterialFilters
from src.materials.infrastructure.repository import SqlAlchemyMaterialCatalogRepository
from src.shared.infrastructure.database import get_session
from src.shared.presentation.messages import MESSAGES
from src.shared.presentation.templates import templates

router = APIRouter()

FEATURED_MATERIAL_FALLBACKS = (
    {
        "slug": "pla",
        "name": "PLA+",
        "description": "Preciso y accesible para validar geometrías, maquetas y prototipos.",
        "advantages": ("Fácil de imprimir", "Excelente detalle superficial", "Costo bajo"),
        "available": True,
    },
    {
        "slug": "petg",
        "name": "PETG",
        "description": (
            "Equilibrio entre facilidad de impresión, tenacidad y resistencia a la humedad."
        ),
        "advantages": ("Buena adhesión entre capas", "Resistente al agua", "Baja contracción"),
        "available": True,
    },
    {
        "slug": "abs",
        "name": "ABS Técnico",
        "description": "Material funcional con mayor temperatura de servicio y buen mecanizado.",
        "advantages": ("Resistente a impactos", "Poco desgaste", "Permite postprocesado"),
        "available": True,
    },
    {
        "slug": "nylon-pa",
        "name": "Nylon (PA)",
        "description": "Tenaz y resistente al desgaste para engranes, bisagras y piezas móviles.",
        "advantages": ("Alta tenacidad", "Baja fricción", "Resiste desgaste"),
        "available": True,
    },
    {
        "slug": "nylon-cf",
        "name": "Nylon con fibra de carbono (PA-CF)",
        "description": "Refuerzo estructural para piezas rígidas, precisas y sometidas a carga.",
        "advantages": ("Alta rigidez", "Estabilidad dimensional", "Bajo peso"),
        "available": True,
    },
    {
        "slug": "asa",
        "name": "ASA UV",
        "description": "Resiste la radiación solar y la intemperie en piezas para exteriores.",
        "advantages": ("Resistencia UV", "Uso exterior", "Acabado mate"),
        "available": False,
    },
    {
        "slug": "tpu",
        "name": "TPU 95A Flexible",
        "description": "Flexible para protectores, juntas, sellos y absorción de impactos.",
        "advantages": ("Gran elasticidad", "Resistencia a la abrasión", "Absorbe impactos"),
        "available": True,
    },
)


def get_service_repository(
    session: Annotated[Session, Depends(get_session)],
) -> ServiceRepository:
    return SqlAlchemyServiceRepository(session)


def get_material_repository(
    session: Annotated[Session, Depends(get_session)],
) -> MaterialCatalogRepository:
    return SqlAlchemyMaterialCatalogRepository(session)


@router.get("/", response_class=HTMLResponse, name="service_catalog")
def service_catalog(
    request: Request,
    repository: Annotated[ServiceRepository, Depends(get_service_repository)],
    material_repository: Annotated[MaterialCatalogRepository, Depends(get_material_repository)],
) -> HTMLResponse:
    try:
        services = ListPublishedServices(repository).execute()
        message = MESSAGES["empty"] if not services else None
        status_code = 200
    except Exception:
        services = []
        message = MESSAGES["error"]
        status_code = 503

    try:
        exploration = ExploreMaterials(material_repository).execute(MaterialFilters())
        featured_materials = [match.material for match in exploration.matches[:7]]
    except Exception:
        featured_materials = []
    if not featured_materials:
        featured_materials = FEATURED_MATERIAL_FALLBACKS

    material_images = {
        "pla": "material-pla.png",
        "petg": "material-petg.png",
        "abs": "material-abs.png",
        "nylon-pa": "material-nylon.png",
        "nylon-cf": "material-nylon-cf.png",
        "asa": "material-abs.png",
        "tpu": "material-tpu.png",
    }

    return templates.TemplateResponse(
        request=request,
        name="catalog/index.html",
        context={
            "services": services,
            "message": message,
            "featured_materials": featured_materials,
            "material_images": material_images,
        },
        status_code=status_code,
    )


@router.get("/contacto", response_class=HTMLResponse, name="contact")
def contact(request: Request) -> HTMLResponse:
    return templates.TemplateResponse(request=request, name="catalog/contact.html")
