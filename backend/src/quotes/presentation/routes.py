from __future__ import annotations

import secrets
from collections.abc import Iterator
from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, File, Form, Request, UploadFile
from fastapi.responses import HTMLResponse, JSONResponse
from sqlalchemy.orm import Session

from src.customers.domain.contact import ContactValidationError
from src.materials.application.get_material import GetPublishedMaterial, MaterialNotFoundError
from src.materials.infrastructure.repository import SqlAlchemyMaterialCatalogRepository
from src.quotes.application.confirm_quote import (
    ConfirmQuote,
    ConfirmQuoteCommand,
    QuoteSubmissionError,
)
from src.quotes.application.manage_uploads import (
    CreateUploadSession,
    ReceiveUpload,
    RemoveUpload,
    UploadSessionNotFoundError,
)
from src.quotes.domain.uploads import UploadError
from src.quotes.infrastructure.repository import SqlAlchemyUploadRepository
from src.quotes.infrastructure.stl_validator import StlValidator
from src.quotes.infrastructure.unit_of_work import SqlAlchemyQuoteSubmissionUnitOfWork
from src.shared.config import get_settings
from src.shared.domain.types import new_public_token, utc_now
from src.shared.infrastructure.database import get_session
from src.shared.infrastructure.private_storage import FileSystemPrivateStorage
from src.shared.presentation.messages import MESSAGES, UiMessage, UiState
from src.shared.presentation.templates import templates

router = APIRouter(prefix="/cotizaciones", tags=["cotizaciones"])


def _chunks(file: UploadFile, chunk_size: int = 1024 * 1024) -> Iterator[bytes]:
    while chunk := file.file.read(chunk_size):
        yield chunk


def _storage() -> FileSystemPrivateStorage:
    return FileSystemPrivateStorage(get_settings().private_storage_root)


@router.get("/nueva", response_class=HTMLResponse, name="new_quote")
def new_quote(
    request: Request,
    session: Annotated[Session, Depends(get_session)],
    material: str | None = None,
) -> HTMLResponse:
    uploads = SqlAlchemyUploadRepository(session)
    upload_session = CreateUploadSession(uploads, utc_now, new_public_token).execute()
    selected_material = None
    message = None
    if material:
        try:
            selected_material = GetPublishedMaterial(
                SqlAlchemyMaterialCatalogRepository(session)
            ).execute(material)
        except MaterialNotFoundError:
            message = UiMessage(
                UiState.ERROR,
                "El material ya no está disponible",
                "La selección fue retirada. Puedes enviar la solicitud sin material o elegir otro.",
                "Ver materiales",
            )
    return templates.TemplateResponse(
        request=request,
        name="quotes/new.html",
        context={
            "upload_session": upload_session,
            "selected_material": selected_material,
            "message": message,
        },
    )


@router.post("/cargas/{token}", name="upload_quote_file")
def upload_quote_file(
    token: str,
    file: Annotated[UploadFile, File()],
    session: Annotated[Session, Depends(get_session)],
) -> JSONResponse:
    try:
        item = ReceiveUpload(
            SqlAlchemyUploadRepository(session), _storage(), StlValidator(), utc_now
        ).execute(token, file.filename or "archivo.stl", _chunks(file), file.size or 0)
        return JSONResponse(
            {
                "id": str(item.id),
                "name": item.original_name,
                "size": item.size_bytes,
                "status": item.status.value,
                "message": item.error_message or "El archivo STL terminó de cargarse y es válido.",
            },
            status_code=201,
        )
    except (UploadError, UploadSessionNotFoundError) as error:
        return JSONResponse({"status": "error", "message": str(error)}, status_code=422)


@router.delete("/cargas/{token}/{item_id}", name="remove_quote_file")
def remove_quote_file(
    token: str,
    item_id: UUID,
    session: Annotated[Session, Depends(get_session)],
) -> JSONResponse:
    try:
        RemoveUpload(SqlAlchemyUploadRepository(session), _storage()).execute(token, item_id)
        return JSONResponse({"status": "success", "message": "Archivo retirado."})
    except (UploadError, UploadSessionNotFoundError) as error:
        return JSONResponse({"status": "error", "message": str(error)}, status_code=404)


@router.post("", response_class=HTMLResponse, name="submit_quote")
def submit_quote(
    request: Request,
    session: Annotated[Session, Depends(get_session)],
    submission_token: Annotated[str, Form()],
    name: Annotated[str, Form()],
    email: Annotated[str, Form()],
    phone: Annotated[str, Form()],
    comments: Annotated[str | None, Form()] = None,
    material: Annotated[str | None, Form()] = None,
) -> HTMLResponse:
    command = ConfirmQuoteCommand(
        submission_token=submission_token,
        name=name,
        email=email,
        phone=phone,
        comments=comments,
        selected_material_slug=material,
    )
    try:
        quote = ConfirmQuote(
            SqlAlchemyQuoteSubmissionUnitOfWork(session),
            utc_now,
            lambda: secrets.token_hex(8),
        ).execute(command)
    except (ContactValidationError, UploadError, QuoteSubmissionError) as error:
        upload_session = SqlAlchemyUploadRepository(session).get_by_token(submission_token)
        return templates.TemplateResponse(
            request=request,
            name="quotes/new.html",
            context={
                "upload_session": upload_session,
                "selected_material": None,
                "message": UiMessage(
                    UiState.ERROR,
                    "Revisa la solicitud",
                    str(error),
                    "Corregir los datos",
                ),
            },
            status_code=422,
        )
    except Exception:
        return templates.TemplateResponse(
            request=request,
            name="quotes/new.html",
            context={
                "upload_session": None,
                "selected_material": None,
                "message": MESSAGES["error"],
            },
            status_code=503,
        )
    return templates.TemplateResponse(
        request=request,
        name="quotes/confirmed.html",
        context={"quote": quote},
        status_code=201,
    )
