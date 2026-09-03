"""Create the initial catalog and append-only audit tables."""

import uuid
from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "0001_initial"
down_revision: str | None = None
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "services",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("slug", sa.String(length=100), nullable=False),
        sa.Column("name", sa.String(length=120), nullable=False),
        sa.Column("summary", sa.String(length=240), nullable=False),
        sa.Column("description", sa.Text(), nullable=False),
        sa.Column("display_order", sa.Integer(), nullable=False),
        sa.Column("is_published", sa.Boolean(), nullable=False),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_services")),
        sa.UniqueConstraint("slug", name=op.f("uq_services_slug")),
    )
    op.create_index("ix_services_public_order", "services", ["is_published", "display_order"])
    services = sa.table(
        "services",
        sa.column("id", sa.Uuid()),
        sa.column("slug", sa.String()),
        sa.column("name", sa.String()),
        sa.column("summary", sa.String()),
        sa.column("description", sa.Text()),
        sa.column("display_order", sa.Integer()),
        sa.column("is_published", sa.Boolean()),
    )
    op.bulk_insert(
        services,
        [
            {
                "id": uuid.UUID("10000000-0000-0000-0000-000000000001"),
                "slug": "impresion-3d",
                "name": "Impresión 3D",
                "summary": "Prototipos y piezas funcionales bajo demanda.",
                "description": "Fabricación aditiva para validar ideas o producir piezas finales.",
                "display_order": 1,
                "is_published": True,
            },
            {
                "id": uuid.UUID("10000000-0000-0000-0000-000000000002"),
                "slug": "diseno-de-piezas",
                "name": "Diseño de piezas",
                "summary": "Modelado de componentes desde una necesidad o concepto.",
                "description": "Diseño orientado a manufactura aditiva y al uso real de la pieza.",
                "display_order": 2,
                "is_published": True,
            },
            {
                "id": uuid.UUID("10000000-0000-0000-0000-000000000003"),
                "slug": "ingenieria-inversa",
                "name": "Ingeniería inversa",
                "summary": "Reconstrucción digital de componentes existentes.",
                "description": (
                    "Recuperación y adaptación de geometrías para refacciones y mejoras."
                ),
                "display_order": 3,
                "is_published": True,
            },
            {
                "id": uuid.UUID("10000000-0000-0000-0000-000000000004"),
                "slug": "asesoria-tecnica",
                "name": "Asesoría técnica",
                "summary": "Selección informada de material, proceso y acabado.",
                "description": "Acompañamiento para reducir riesgos antes de fabricar.",
                "display_order": 4,
                "is_published": True,
            },
        ],
    )
    op.create_table(
        "audit_events",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("actor_type", sa.String(length=30), nullable=False),
        sa.Column("actor_id", sa.String(length=100), nullable=True),
        sa.Column("action", sa.String(length=100), nullable=False),
        sa.Column("entity_type", sa.String(length=60), nullable=False),
        sa.Column("entity_id", sa.String(length=100), nullable=False),
        sa.Column("result", sa.String(length=30), nullable=False),
        sa.Column("occurred_at", sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_audit_events")),
    )
    op.create_index("ix_audit_entity", "audit_events", ["entity_type", "entity_id"])


def downgrade() -> None:
    op.drop_index("ix_audit_entity", table_name="audit_events")
    op.drop_table("audit_events")
    op.drop_index("ix_services_public_order", table_name="services")
    op.drop_table("services")
