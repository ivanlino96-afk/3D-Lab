"""Add nylon-based technical materials."""

from collections.abc import Sequence
from datetime import date
from uuid import UUID

import sqlalchemy as sa
from alembic import op

revision: str = "0006_technical_materials"
down_revision: str | None = "0005_notifications"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.execute("UPDATE materials SET display_order = display_order + 2 WHERE display_order >= 4")
    materials = sa.table(
        "materials",
        sa.column("id", sa.Uuid()),
        sa.column("slug", sa.String()),
        sa.column("name", sa.String()),
        sa.column("description", sa.Text()),
        sa.column("advantages", sa.JSON()),
        sa.column("limitations", sa.JSON()),
        sa.column("available", sa.Boolean()),
        sa.column("cost_level", sa.String()),
        sa.column("source_url", sa.String()),
        sa.column("source_updated_at", sa.Date()),
        sa.column("display_order", sa.Integer()),
        sa.column("status", sa.String()),
        sa.column("colors", sa.JSON()),
        sa.column("finishes", sa.JSON()),
    )
    op.bulk_insert(
        materials,
        [
            {
                "id": UUID("40000000-0000-0000-0000-000000000006"),
                "slug": "nylon-pa",
                "name": "Nylon (PA)",
                "description": (
                    "Tenaz y resistente al desgaste para engranes, bisagras y piezas móviles."
                ),
                "advantages": ["Alta tenacidad", "Baja fricción", "Resiste desgaste"],
                "limitations": ["Absorbe humedad", "Requiere secado previo"],
                "available": True,
                "cost_level": "high",
                "source_url": "https://bambulab.com/en/filament/collections",
                "source_updated_at": date(2026, 9, 3),
                "display_order": 4,
                "status": "published",
                "colors": ["Natural", "Negro"],
                "finishes": ["Mate"],
            },
            {
                "id": UUID("40000000-0000-0000-0000-000000000007"),
                "slug": "nylon-cf",
                "name": "Nylon con fibra de carbono (PA-CF)",
                "description": (
                    "Refuerzo estructural para piezas rígidas, precisas y sometidas a carga."
                ),
                "advantages": ["Alta rigidez", "Estabilidad dimensional", "Bajo peso"],
                "limitations": ["Material abrasivo", "Requiere boquilla endurecida"],
                "available": True,
                "cost_level": "high",
                "source_url": "https://bambulab.com/en/filament/collections",
                "source_updated_at": date(2026, 9, 3),
                "display_order": 5,
                "status": "published",
                "colors": ["Negro"],
                "finishes": ["Mate técnico"],
            },
        ],
    )


def downgrade() -> None:
    op.execute("DELETE FROM materials WHERE slug IN ('nylon-pa', 'nylon-cf')")
    op.execute("UPDATE materials SET display_order = display_order - 2 WHERE display_order >= 6")
