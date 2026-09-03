from __future__ import annotations

import secrets
from typing import Annotated

from fastapi import APIRouter, Depends, Form, HTTPException, Request
from fastapi.responses import HTMLResponse, RedirectResponse
from sqlalchemy.orm import Session

from src.administration.application.authenticate_admin import (
    AdminUser,
    AuthenticateAdmin,
    AuthenticationError,
    CloseAdminSession,
    ValidateAdminSession,
)
from src.administration.infrastructure.auth import (
    PasswordHasher,
    SqlAlchemyAdminAuthRepository,
    ensure_configured_admin,
)
from src.shared.config import get_settings
from src.shared.domain.types import utc_now
from src.shared.infrastructure.database import get_session
from src.shared.presentation.messages import UiMessage, UiState
from src.shared.presentation.templates import templates

router = APIRouter(prefix="/admin", tags=["administración"])
SESSION_COOKIE = "3dlab_admin_session"


def require_admin(request: Request, session: Annotated[Session, Depends(get_session)]) -> AdminUser:
    user = ValidateAdminSession(SqlAlchemyAdminAuthRepository(session)).execute(
        request.cookies.get(SESSION_COOKIE), utc_now()
    )
    if user is None:
        raise HTTPException(
            status_code=303,
            detail="Se requiere una sesión administrativa.",
            headers={"Location": "/admin/login"},
        )
    return user


@router.get("/login", response_class=HTMLResponse, name="admin_login")
def login_page(request: Request) -> HTMLResponse:
    return templates.TemplateResponse(
        request=request,
        name="admin/login.html",
        context={"message": None},
    )


@router.post("/login", response_class=HTMLResponse)
def login(
    request: Request,
    session: Annotated[Session, Depends(get_session)],
    username: Annotated[str, Form()],
    password: Annotated[str, Form()],
):
    settings = get_settings()
    ensure_configured_admin(
        session, settings.admin_username, settings.admin_password_hash, utc_now()
    )
    try:
        authenticated = AuthenticateAdmin(
            SqlAlchemyAdminAuthRepository(session),
            PasswordHasher(),
            lambda: secrets.token_urlsafe(48),
        ).execute(username, password, utc_now())
    except AuthenticationError as error:
        return templates.TemplateResponse(
            request=request,
            name="admin/login.html",
            context={
                "message": UiMessage(
                    UiState.ERROR,
                    "No fue posible iniciar sesión",
                    str(error),
                    "Verifica los datos e intenta de nuevo",
                )
            },
            status_code=401,
        )
    response = RedirectResponse("/admin/cotizaciones", status_code=303)
    response.set_cookie(
        SESSION_COOKIE,
        authenticated.raw_token,
        max_age=8 * 60 * 60,
        httponly=True,
        secure=settings.app_env == "production",
        samesite="strict",
        path="/",
    )
    return response


@router.post("/logout", name="admin_logout")
def logout(request: Request, session: Annotated[Session, Depends(get_session)]) -> RedirectResponse:
    CloseAdminSession(SqlAlchemyAdminAuthRepository(session)).execute(
        request.cookies.get(SESSION_COOKIE), utc_now()
    )
    response = RedirectResponse("/admin/login", status_code=303)
    response.delete_cookie(SESSION_COOKIE, path="/")
    return response
