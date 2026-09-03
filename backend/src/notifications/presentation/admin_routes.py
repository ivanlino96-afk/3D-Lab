from typing import Annotated

from fastapi import APIRouter, Depends, Request
from fastapi.responses import HTMLResponse
from sqlalchemy.orm import Session

from src.administration.application.authenticate_admin import AdminUser
from src.administration.presentation.auth_routes import require_admin
from src.notifications.infrastructure.repository import SqlAlchemyNotificationRepository
from src.shared.infrastructure.database import get_session
from src.shared.presentation.messages import MESSAGES
from src.shared.presentation.templates import templates

router = APIRouter(prefix="/admin/notificaciones", tags=["administración de notificaciones"])


@router.get("", response_class=HTMLResponse, name="admin_notifications")
def failed_notifications(
    request: Request,
    session: Annotated[Session, Depends(get_session)],
    admin: Annotated[AdminUser, Depends(require_admin)],
) -> HTMLResponse:
    notifications = SqlAlchemyNotificationRepository(session).list_not_delivered()
    return templates.TemplateResponse(
        request=request,
        name="admin/notifications.html",
        context={
            "admin": admin,
            "notifications": notifications,
            "message": MESSAGES["empty"] if not notifications else None,
        },
    )
