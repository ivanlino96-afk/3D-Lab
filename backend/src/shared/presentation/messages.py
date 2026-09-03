from dataclasses import dataclass
from enum import StrEnum


class UiState(StrEnum):
    LOADING = "loading"
    SUCCESS = "success"
    EMPTY = "empty"
    ERROR = "error"


@dataclass(frozen=True, slots=True)
class UiMessage:
    state: UiState
    title: str
    detail: str
    recovery_action: str | None = None


MESSAGES = {
    "loading": UiMessage(UiState.LOADING, "Cargando", "Estamos preparando la información."),
    "success": UiMessage(UiState.SUCCESS, "Listo", "La operación terminó correctamente."),
    "empty": UiMessage(
        UiState.EMPTY,
        "Sin resultados",
        "No encontramos información para esta consulta.",
        "Limpiar filtros",
    ),
    "error": UiMessage(
        UiState.ERROR,
        "No pudimos completar la operación",
        "Ocurrió un problema temporal.",
        "Intentar de nuevo",
    ),
}
