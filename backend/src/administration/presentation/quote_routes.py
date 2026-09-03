from __future__ import annotations

from datetime import date
from typing import Annotated
from urllib.parse import quote as url_quote
from uuid import UUID, uuid4

from fastapi import APIRouter, Depends, Form, Query, Request
from fastapi.responses import HTMLResponse, RedirectResponse, Response
from sqlalchemy import select
from sqlalchemy.orm import Session

from src.administration.application.authenticate_admin import AdminUser
from src.administration.application.download_quote_file import (
    DownloadQuoteFile,
    QuoteFileUnavailableError,
)
from src.administration.application.get_quote_detail import (
    GetQuoteDetail,
    QuoteDetailNotFoundError,
)
from src.administration.application.list_quotes import ListCustomerQuotes, ListQuotes
from src.administration.infrastructure.quote_queries import SqlAlchemyQuoteQueries
from src.administration.presentation.auth_routes import require_admin
from src.customers.application.manage_data_request import (
    CompleteDataRequest,
    CreateDataRequest,
    DataRequestError,
    DataRequestType,
)
from src.customers.infrastructure.repository import (
    CustomerRecord,
    DataSubjectRequestRecord,
    SqlAlchemyDataRequestRepository,
)
from src.quotes.application.change_quote_status import ChangeQuoteStatus, QuoteNotFoundError
from src.quotes.domain.entities import QuoteStatus
from src.quotes.domain.status import StatusTransitionError
from src.quotes.infrastructure.status_repository import SqlAlchemyQuoteStatusUnitOfWork
from src.shared.config import get_settings
from src.shared.domain.types import utc_now
from src.shared.infrastructure.database import get_session
from src.shared.infrastructure.private_storage import FileSystemPrivateStorage
from src.shared.presentation.messages import UiMessage, UiState
from src.shared.presentation.templates import templates

router = APIRouter(prefix="/admin", tags=["administración"])


def _parse_date(value: str | None) -> date | None:
    if not value:
        return None
    try:
        return date.fromisoformat(value)
    except ValueError as error:
        raise ValueError("La fecha indicada no es válida.") from error


@router.get("/cotizaciones", response_class=HTMLResponse, name="admin_quotes")
def list_quotes(
    request: Request,
    session: Annotated[Session, Depends(get_session)],
    admin: Annotated[AdminUser, Depends(require_admin)],
    q: str | None = None,
    status: Annotated[list[str] | None, Query()] = None,
    date_from: str | None = None,
    date_to: str | None = None,
    page: int = 1,
) -> HTMLResponse:
    try:
        result = ListQuotes(SqlAlchemyQuoteQueries(session)).execute(
            q,
            tuple(status or ()),
            _parse_date(date_from),
            _parse_date(date_to),
            page,
        )
        message = None
    except ValueError:
        result = ListQuotes(SqlAlchemyQuoteQueries(session)).execute(None, (), None, None)
        message = UiMessage(
            UiState.ERROR,
            "Hay un filtro inválido",
            "Se retiró el filtro que no corresponde a un estado disponible.",
            "Revisar filtros",
        )
    return templates.TemplateResponse(
        request=request,
        name="admin/quotes.html",
        context={
            "admin": admin,
            "page": result,
            "statuses": tuple(QuoteStatus),
            "selected_statuses": tuple(status or ()),
            "filters": {"q": q or "", "date_from": date_from or "", "date_to": date_to or ""},
            "message": message,
        },
    )


@router.get("/cotizaciones/{quote_id}", response_class=HTMLResponse, name="admin_quote_detail")
def quote_detail(
    quote_id: UUID,
    request: Request,
    session: Annotated[Session, Depends(get_session)],
    admin: Annotated[AdminUser, Depends(require_admin)],
    result: str | None = None,
) -> HTMLResponse:
    try:
        detail = GetQuoteDetail(SqlAlchemyQuoteQueries(session)).execute(quote_id)
    except QuoteDetailNotFoundError:
        return templates.TemplateResponse(
            request=request,
            name="admin/not_found.html",
            context={"admin": admin},
            status_code=404,
        )
    message = None
    if result == "updated":
        message = UiMessage(
            UiState.SUCCESS,
            "Estado actualizado",
            "El historial, la auditoría y el aviso quedaron registrados.",
        )
    elif result:
        message = UiMessage(UiState.ERROR, "No se cambió el estado", result, "Revisar transición")
    return templates.TemplateResponse(
        request=request,
        name="admin/quote_detail.html",
        context={
            "admin": admin,
            "quote": detail,
            "statuses": tuple(QuoteStatus),
            "message": message,
        },
    )


@router.post("/cotizaciones/{quote_id}/estado")
def change_status(
    quote_id: UUID,
    session: Annotated[Session, Depends(get_session)],
    admin: Annotated[AdminUser, Depends(require_admin)],
    status: Annotated[str, Form()],
    reason: Annotated[str | None, Form()] = None,
) -> RedirectResponse:
    try:
        ChangeQuoteStatus(SqlAlchemyQuoteStatusUnitOfWork(session)).execute(
            quote_id, QuoteStatus(status), admin.id, utc_now(), reason
        )
        result = "updated"
    except (ValueError, StatusTransitionError, QuoteNotFoundError) as error:
        result = str(error)
    return RedirectResponse(
        f"/admin/cotizaciones/{quote_id}?result={url_quote(result)}", status_code=303
    )


@router.get("/archivos/{file_id}", name="admin_download_quote_file")
def download_file(
    file_id: UUID,
    session: Annotated[Session, Depends(get_session)],
    admin: Annotated[AdminUser, Depends(require_admin)],
) -> Response:
    try:
        downloaded = DownloadQuoteFile(
            SqlAlchemyQuoteQueries(session),
            FileSystemPrivateStorage(get_settings().private_storage_root),
        ).execute(file_id, admin.id, utc_now())
    except QuoteFileUnavailableError as error:
        return Response(str(error), status_code=410, media_type="text/plain")
    encoded_name = url_quote(downloaded.original_name)
    return Response(
        downloaded.content,
        media_type="model/stl",
        headers={"Content-Disposition": f"attachment; filename*=UTF-8''{encoded_name}"},
    )


@router.get("/clientes/{customer_id}", response_class=HTMLResponse, name="admin_customer")
def customer_detail(
    customer_id: UUID,
    request: Request,
    session: Annotated[Session, Depends(get_session)],
    admin: Annotated[AdminUser, Depends(require_admin)],
    result: str | None = None,
) -> HTMLResponse:
    customer = session.get(CustomerRecord, customer_id)
    if customer is None:
        return templates.TemplateResponse(
            request=request,
            name="admin/not_found.html",
            context={"admin": admin},
            status_code=404,
        )
    requests = session.scalars(
        select(DataSubjectRequestRecord)
        .where(DataSubjectRequestRecord.customer_id == customer_id)
        .order_by(DataSubjectRequestRecord.created_at.desc())
    ).all()
    return templates.TemplateResponse(
        request=request,
        name="admin/customer_detail.html",
        context={
            "admin": admin,
            "customer": customer,
            "quotes": ListCustomerQuotes(SqlAlchemyQuoteQueries(session)).execute(customer_id),
            "data_requests": requests,
            "message": UiMessage(UiState.SUCCESS, "Operación registrada", result)
            if result
            else None,
        },
    )


@router.post("/clientes/{customer_id}/solicitudes-datos")
def create_data_request(
    customer_id: UUID,
    session: Annotated[Session, Depends(get_session)],
    admin: Annotated[AdminUser, Depends(require_admin)],
    request_type: Annotated[str, Form()],
    requested_email: Annotated[str, Form()],
) -> RedirectResponse:
    del admin
    try:
        CreateDataRequest(SqlAlchemyDataRequestRepository(session)).execute(
            uuid4(), customer_id, DataRequestType(request_type), requested_email, utc_now()
        )
        result = "La solicitud de datos quedó pendiente de verificación."
    except (ValueError, DataRequestError) as error:
        result = str(error)
    return RedirectResponse(
        f"/admin/clientes/{customer_id}?result={url_quote(result)}", status_code=303
    )


@router.post("/solicitudes-datos/{request_id}/completar")
def complete_data_request(
    request_id: UUID,
    session: Annotated[Session, Depends(get_session)],
    admin: Annotated[AdminUser, Depends(require_admin)],
    verified_email: Annotated[str, Form()],
    resolution_notes: Annotated[str, Form()],
) -> RedirectResponse:
    del admin
    repository = SqlAlchemyDataRequestRepository(session)
    pending = repository.get(request_id)
    if pending is None:
        return RedirectResponse("/admin/cotizaciones", status_code=303)
    try:
        CompleteDataRequest(repository).execute(
            request_id, verified_email, resolution_notes, utc_now()
        )
        result = "La identidad fue verificada y la solicitud quedó completada."
    except DataRequestError as error:
        result = str(error)
    return RedirectResponse(
        f"/admin/clientes/{pending.customer_id}?result={url_quote(result)}", status_code=303
    )
