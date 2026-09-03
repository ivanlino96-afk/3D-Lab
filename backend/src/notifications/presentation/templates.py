from __future__ import annotations

from pathlib import Path

from src.notifications.domain.entities import Notification

TEMPLATE_ROOT = Path(__file__).with_suffix("")


class SpanishEmailTemplates:
    def render(self, notification: Notification) -> tuple[str, str]:
        reference = str(notification.payload.get("reference", "Sin folio"))
        status_label = {
            "open": "Abierta",
            "quote_sent": "Cotización enviada",
            "in_progress": "En proceso",
            "closed": "Cerrada",
            "canceled": "Cancelada",
        }.get(str(notification.payload.get("status")), "Actualizada")
        path = TEMPLATE_ROOT / f"{notification.template_key}.txt"
        if not path.is_file():
            raise ValueError("No existe una plantilla para este aviso.")
        rendered = path.read_text(encoding="utf-8").format(
            reference=reference, status_label=status_label
        )
        subject, body = rendered.split("\n", 1)
        return subject.strip(), body.strip()
