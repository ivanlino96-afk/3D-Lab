from __future__ import annotations

from datetime import date
from typing import Annotated
from urllib.parse import quote as url_quote
from uuid import UUID, uuid4

from fastapi import APIRouter, Depends, Form, Request
from fastapi.responses import HTMLResponse, RedirectResponse
from sqlalchemy.orm import Session

from src.administration.application.authenticate_admin import AdminUser
from src.administration.presentation.auth_routes import require_admin
from src.audit.infrastructure.repository import SqlAlchemyAuditRepository
from src.materials.application.manage_material import (
    ManageApplicationDefinition,
    ManageMaterial,
    ManagePropertyDefinition,
    MaterialAdminError,
    ReorderMaterial,
)
from src.materials.domain.entities import Certification, CostLevel, PublicationStatus
from src.materials.domain.publication import (
    AdminPropertyValue,
    MaterialDraft,
    MaterialPublicationError,
)
from src.materials.infrastructure.admin_repository import SqlAlchemyMaterialAdminRepository
from src.shared.domain.types import utc_now
from src.shared.infrastructure.database import get_session
from src.shared.presentation.messages import UiMessage, UiState
from src.shared.presentation.templates import templates

router = APIRouter(prefix="/admin/materiales", tags=["administración de materiales"])


def _lines(value: str) -> tuple[str, ...]:
    return tuple(line.strip() for line in value.splitlines() if line.strip())


def _certifications(value: str) -> tuple[Certification, ...]:
    certifications = []
    for number, line in enumerate(_lines(value), start=1):
        parts = [part.strip() for part in line.split("|")]
        if len(parts) != 5:
            raise MaterialAdminError(
                f"La certificación de la línea {number} debe contener "
                "cinco valores separados por |."
            )
        try:
            valid_from, valid_until = date.fromisoformat(parts[3]), date.fromisoformat(parts[4])
        except ValueError as error:
            raise MaterialAdminError(
                f"Las fechas de certificación de la línea {number} no son válidas."
            ) from error
        certifications.append(
            Certification(parts[0], parts[1], parts[2] or None, valid_from, valid_until)
        )
    return tuple(certifications)


def _property_values(form, definitions) -> tuple[AdminPropertyValue, ...]:
    values = []
    for definition in definitions:
        raw = str(form.get(f"property_{definition.slug}", "")).strip()
        source = str(form.get(f"property_source_{definition.slug}", "")).strip()
        if not raw and not source:
            continue
        try:
            numeric_value = float(raw) if raw else None
        except ValueError as error:
            raise MaterialAdminError(f"El valor de {definition.name} debe ser numérico.") from error
        values.append(AdminPropertyValue(definition.slug, numeric_value, source or None))
    return tuple(values)


def _context(repository, material=None, message=None):
    property_values = (
        {item.definition_slug: item for item in material.property_values} if material else {}
    )
    certification_lines = ""
    if material:
        certification_lines = "\n".join(
            "|".join(
                (
                    item.name,
                    item.issuer,
                    item.evidence_url or "",
                    item.valid_from.isoformat(),
                    item.valid_until.isoformat(),
                )
            )
            for item in material.certifications
        )
    return {
        "material": material,
        "applications": repository.list_applications(),
        "property_definitions": repository.list_property_definitions(),
        "cost_levels": tuple(CostLevel),
        "publication_statuses": tuple(PublicationStatus),
        "message": message,
        "property_values": property_values,
        "certification_lines": certification_lines,
        "form": None,
    }


@router.get("", response_class=HTMLResponse, name="admin_materials")
def material_list(
    request: Request,
    session: Annotated[Session, Depends(get_session)],
    admin: Annotated[AdminUser, Depends(require_admin)],
    result: str | None = None,
    kind: str | None = None,
) -> HTMLResponse:
    repository = SqlAlchemyMaterialAdminRepository(session)
    return templates.TemplateResponse(
        request=request,
        name="admin/materials.html",
        context={
            "admin": admin,
            "materials": repository.list_all(),
            "applications": repository.list_applications(),
            "property_definitions": repository.list_property_definitions(),
            "message": UiMessage(
                UiState.ERROR if kind == "error" else UiState.SUCCESS,
                "No se completó el cambio" if kind == "error" else "Catálogo actualizado",
                result,
                "Revisar el material" if kind == "error" else None,
            )
            if result
            else None,
        },
    )


@router.get("/nuevo", response_class=HTMLResponse, name="admin_new_material")
def new_material(
    request: Request,
    session: Annotated[Session, Depends(get_session)],
    admin: Annotated[AdminUser, Depends(require_admin)],
) -> HTMLResponse:
    repository = SqlAlchemyMaterialAdminRepository(session)
    return templates.TemplateResponse(
        request=request,
        name="admin/material_form.html",
        context={"admin": admin, **_context(repository)},
    )


@router.get("/{material_id}/editar", response_class=HTMLResponse, name="admin_edit_material")
def edit_material(
    material_id: UUID,
    request: Request,
    session: Annotated[Session, Depends(get_session)],
    admin: Annotated[AdminUser, Depends(require_admin)],
) -> HTMLResponse:
    repository = SqlAlchemyMaterialAdminRepository(session)
    material = repository.get(material_id)
    if material is None:
        return templates.TemplateResponse(
            request=request,
            name="admin/not_found.html",
            context={"admin": admin},
            status_code=404,
        )
    return templates.TemplateResponse(
        request=request,
        name="admin/material_form.html",
        context={"admin": admin, **_context(repository, material)},
    )


@router.post("/guardar", response_class=HTMLResponse)
async def save_material(
    request: Request,
    session: Annotated[Session, Depends(get_session)],
    admin: Annotated[AdminUser, Depends(require_admin)],
):
    form = await request.form()
    repository = SqlAlchemyMaterialAdminRepository(session)
    try:
        material_id = UUID(str(form["id"])) if form.get("id") else uuid4()
        material = MaterialDraft(
            id=material_id,
            slug=str(form.get("slug", "")),
            name=str(form.get("name", "")),
            description=str(form.get("description", "")),
            advantages=_lines(str(form.get("advantages", ""))),
            limitations=_lines(str(form.get("limitations", ""))),
            available=form.get("available") == "yes",
            cost_level=CostLevel(str(form.get("cost_level", "medium"))),
            source_url=str(form.get("source_url", "")),
            source_updated_at=date.fromisoformat(str(form.get("source_updated_at", ""))),
            display_order=int(str(form.get("display_order", "1"))),
            status=PublicationStatus(str(form.get("status", "draft"))),
            application_slugs=tuple(
                str(item) for item in form.getlist("applications") if str(item).strip()
            ),
            property_values=_property_values(form, repository.list_property_definitions()),
            certifications=_certifications(str(form.get("certifications", ""))),
            colors=_lines(str(form.get("colors", ""))),
            finishes=_lines(str(form.get("finishes", ""))),
        )
        saved = ManageMaterial(repository, SqlAlchemyAuditRepository(session)).save(
            material, admin.id, utc_now()
        )
    except (
        KeyError,
        ValueError,
        MaterialAdminError,
        MaterialPublicationError,
        LookupError,
    ) as error:
        message = UiMessage(
            UiState.ERROR,
            "No se guardó el material",
            str(error),
            "Revisar los campos marcados",
        )
        return templates.TemplateResponse(
            request=request,
            name="admin/material_form.html",
            context={"admin": admin, **_context(repository, None, message), "form": form},
            status_code=422,
        )
    return RedirectResponse(
        f"/admin/materiales?result={url_quote(f'{saved.name} quedó guardado.')}", status_code=303
    )


@router.post("/{material_id}/estado")
def change_material_status(
    material_id: UUID,
    session: Annotated[Session, Depends(get_session)],
    admin: Annotated[AdminUser, Depends(require_admin)],
    status: Annotated[str, Form()],
) -> RedirectResponse:
    try:
        changed = ManageMaterial(
            SqlAlchemyMaterialAdminRepository(session), SqlAlchemyAuditRepository(session)
        ).change_status(material_id, PublicationStatus(status), admin.id, utc_now())
        result = f"{changed.name} ahora está {changed.status.value}."
    except (ValueError, MaterialAdminError, MaterialPublicationError) as error:
        result = str(error)
        return RedirectResponse(
            f"/admin/materiales?kind=error&result={url_quote(result)}", status_code=303
        )
    return RedirectResponse(f"/admin/materiales?result={url_quote(result)}", status_code=303)


@router.post("/{material_id}/orden")
def reorder_material(
    material_id: UUID,
    session: Annotated[Session, Depends(get_session)],
    admin: Annotated[AdminUser, Depends(require_admin)],
    display_order: Annotated[int, Form()],
) -> RedirectResponse:
    try:
        ReorderMaterial(
            SqlAlchemyMaterialAdminRepository(session), SqlAlchemyAuditRepository(session)
        ).execute(material_id, display_order, admin.id, utc_now())
        result = "El orden del material quedó actualizado."
    except MaterialAdminError as error:
        result = str(error)
        return RedirectResponse(
            f"/admin/materiales?kind=error&result={url_quote(result)}", status_code=303
        )
    return RedirectResponse(f"/admin/materiales?result={url_quote(result)}", status_code=303)


@router.post("/aplicaciones")
def save_application(
    session: Annotated[Session, Depends(get_session)],
    admin: Annotated[AdminUser, Depends(require_admin)],
    slug: Annotated[str, Form()],
    name: Annotated[str, Form()],
    factors: Annotated[str, Form()],
    display_order: Annotated[int, Form()],
) -> RedirectResponse:
    try:
        ManageApplicationDefinition(
            SqlAlchemyMaterialAdminRepository(session), SqlAlchemyAuditRepository(session)
        ).execute(slug, name, factors, display_order, admin.id, utc_now())
        result = "La aplicación quedó guardada."
    except MaterialAdminError as error:
        result = str(error)
        return RedirectResponse(
            f"/admin/materiales?kind=error&result={url_quote(result)}", status_code=303
        )
    return RedirectResponse(f"/admin/materiales?result={url_quote(result)}", status_code=303)


@router.post("/propiedades")
def save_property_definition(
    session: Annotated[Session, Depends(get_session)],
    admin: Annotated[AdminUser, Depends(require_admin)],
    slug: Annotated[str, Form()],
    name: Annotated[str, Form()],
    unit: Annotated[str, Form()],
    display_order: Annotated[int, Form()],
) -> RedirectResponse:
    try:
        ManagePropertyDefinition(
            SqlAlchemyMaterialAdminRepository(session), SqlAlchemyAuditRepository(session)
        ).execute(slug, name, unit, display_order, admin.id, utc_now())
        result = "La propiedad quedó guardada."
    except MaterialAdminError as error:
        result = str(error)
        return RedirectResponse(
            f"/admin/materiales?kind=error&result={url_quote(result)}", status_code=303
        )
    return RedirectResponse(f"/admin/materiales?result={url_quote(result)}", status_code=303)
