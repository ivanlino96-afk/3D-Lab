from datetime import UTC, date, datetime, time, timedelta
from typing import Annotated

from fastapi import APIRouter, Depends, Request
from fastapi.responses import HTMLResponse
from sqlalchemy.orm import Session

from src.administration.application.authenticate_admin import AdminUser
from src.administration.presentation.auth_routes import require_admin
from src.reporting.application.get_commercial_metrics import GetCommercialMetrics
from src.reporting.infrastructure.metrics_queries import SqlAlchemyMetricsQueries
from src.shared.infrastructure.database import get_session
from src.shared.presentation.messages import UiMessage, UiState
from src.shared.presentation.templates import templates

router = APIRouter(prefix="/admin/indicadores", tags=["indicadores comerciales"])


@router.get("", response_class=HTMLResponse, name="admin_metrics")
def metrics_page(
    request: Request,
    session: Annotated[Session, Depends(get_session)],
    admin: Annotated[AdminUser, Depends(require_admin)],
    date_from: str | None = None,
    date_to: str | None = None,
) -> HTMLResponse:
    today = date.today()
    default_start = today.replace(day=1)
    try:
        start_date = date.fromisoformat(date_from) if date_from else default_start
        end_date = date.fromisoformat(date_to) if date_to else today
        period_start = datetime.combine(start_date, time.min, tzinfo=UTC)
        period_end = datetime.combine(end_date + timedelta(days=1), time.min, tzinfo=UTC)
        metrics = GetCommercialMetrics(SqlAlchemyMetricsQueries(session)).execute(
            period_start, period_end
        )
        message = (
            UiMessage(
                UiState.EMPTY,
                "Sin actividad en el periodo",
                "No hay solicitudes aceptadas entre las fechas elegidas.",
                "Elegir otro periodo",
            )
            if metrics.accepted == 0
            else None
        )
        status_code = 200
    except ValueError as error:
        start_date, end_date, metrics = default_start, today, None
        message = UiMessage(
            UiState.ERROR,
            "El periodo no es válido",
            str(error),
            "Seleccionar fechas válidas",
        )
        status_code = 422
    return templates.TemplateResponse(
        request=request,
        name="admin/metrics.html",
        context={
            "admin": admin,
            "metrics": metrics,
            "date_from": start_date.isoformat(),
            "date_to": end_date.isoformat(),
            "message": message,
        },
        status_code=status_code,
    )
