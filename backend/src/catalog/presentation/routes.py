from typing import Annotated

from fastapi import APIRouter, Depends, Request
from fastapi.responses import HTMLResponse
from sqlalchemy.orm import Session

from src.catalog.application.list_services import ListPublishedServices
from src.catalog.application.ports import ServiceRepository
from src.catalog.infrastructure.repository import SqlAlchemyServiceRepository
from src.shared.infrastructure.database import get_session
from src.shared.presentation.messages import MESSAGES
from src.shared.presentation.templates import templates

router = APIRouter()


def get_service_repository(
    session: Annotated[Session, Depends(get_session)],
) -> ServiceRepository:
    return SqlAlchemyServiceRepository(session)


@router.get("/", response_class=HTMLResponse, name="service_catalog")
def service_catalog(
    request: Request,
    repository: Annotated[ServiceRepository, Depends(get_service_repository)],
) -> HTMLResponse:
    try:
        services = ListPublishedServices(repository).execute()
        message = MESSAGES["empty"] if not services else None
        status_code = 200
    except Exception:
        services = []
        message = MESSAGES["error"]
        status_code = 503

    return templates.TemplateResponse(
        request=request,
        name="catalog/index.html",
        context={"services": services, "message": message},
        status_code=status_code,
    )
