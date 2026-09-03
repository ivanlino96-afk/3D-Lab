"""Create and seed the material guide."""

import uuid
from collections.abc import Sequence
from datetime import date

import sqlalchemy as sa
from alembic import context, op

revision: str = "0002_material_catalog"
down_revision: str | None = "0001_initial"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "applications",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("slug", sa.String(80), nullable=False),
        sa.Column("name", sa.String(100), nullable=False),
        sa.Column("factors", sa.Text(), nullable=False),
        sa.Column("display_order", sa.Integer(), nullable=False),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_applications")),
        sa.UniqueConstraint("slug", name=op.f("uq_applications_slug")),
    )
    op.create_table(
        "property_definitions",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("slug", sa.String(80), nullable=False),
        sa.Column("name", sa.String(100), nullable=False),
        sa.Column("unit", sa.String(30), nullable=False),
        sa.Column("display_order", sa.Integer(), nullable=False),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_property_definitions")),
        sa.UniqueConstraint("slug", name=op.f("uq_property_definitions_slug")),
    )
    op.create_table(
        "materials",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("slug", sa.String(80), nullable=False),
        sa.Column("name", sa.String(100), nullable=False),
        sa.Column("description", sa.Text(), nullable=False),
        sa.Column("advantages", sa.JSON(), nullable=False),
        sa.Column("limitations", sa.JSON(), nullable=False),
        sa.Column("available", sa.Boolean(), nullable=False),
        sa.Column("cost_level", sa.String(10), nullable=False),
        sa.Column("source_url", sa.String(500), nullable=False),
        sa.Column("source_updated_at", sa.Date(), nullable=False),
        sa.Column("display_order", sa.Integer(), nullable=False),
        sa.Column("status", sa.String(12), nullable=False),
        sa.Column("colors", sa.JSON(), nullable=False),
        sa.Column("finishes", sa.JSON(), nullable=False),
        sa.CheckConstraint("cost_level IN ('low', 'medium', 'high')", name="cost_level"),
        sa.CheckConstraint(
            "status IN ('draft', 'published', 'archived')", name="publication_status"
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_materials")),
        sa.UniqueConstraint("slug", name=op.f("uq_materials_slug")),
    )
    op.create_index("ix_materials_public_order", "materials", ["status", "display_order"])
    op.create_table(
        "material_applications",
        sa.Column("material_id", sa.Uuid(), nullable=False),
        sa.Column("application_id", sa.Uuid(), nullable=False),
        sa.ForeignKeyConstraint(
            ["application_id"], ["applications.id"], name=op.f("fk_material_application")
        ),
        sa.ForeignKeyConstraint(
            ["material_id"], ["materials.id"], name=op.f("fk_application_material")
        ),
        sa.PrimaryKeyConstraint("material_id", "application_id", name="pk_material_applications"),
    )
    op.create_table(
        "material_property_values",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("material_id", sa.Uuid(), nullable=False),
        sa.Column("property_definition_id", sa.Uuid(), nullable=False),
        sa.Column("value", sa.Float(), nullable=True),
        sa.Column("source", sa.String(500), nullable=True),
        sa.ForeignKeyConstraint(
            ["material_id"], ["materials.id"], name=op.f("fk_property_value_material")
        ),
        sa.ForeignKeyConstraint(
            ["property_definition_id"],
            ["property_definitions.id"],
            name=op.f("fk_property_value_definition"),
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_material_property_values")),
        sa.UniqueConstraint(
            "material_id", "property_definition_id", name="uq_material_property_definition"
        ),
    )
    op.create_table(
        "certifications",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("material_id", sa.Uuid(), nullable=False),
        sa.Column("name", sa.String(140), nullable=False),
        sa.Column("issuer", sa.String(140), nullable=False),
        sa.Column("evidence_url", sa.String(500), nullable=True),
        sa.Column("valid_from", sa.Date(), nullable=False),
        sa.Column("valid_until", sa.Date(), nullable=False),
        sa.ForeignKeyConstraint(
            ["material_id"], ["materials.id"], name=op.f("fk_certification_material")
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_certifications")),
    )
    if not context.is_offline_mode():
        _seed_catalog()


def _seed_catalog() -> None:
    app_ids = {
        "prototype": uuid.UUID("20000000-0000-0000-0000-000000000001"),
        "mechanical": uuid.UUID("20000000-0000-0000-0000-000000000002"),
        "outdoor": uuid.UUID("20000000-0000-0000-0000-000000000003"),
        "flexible": uuid.UUID("20000000-0000-0000-0000-000000000004"),
        "industrial": uuid.UUID("20000000-0000-0000-0000-000000000005"),
    }
    property_ids = {
        "impact-strength": uuid.UUID("30000000-0000-0000-0000-000000000001"),
        "bending-strength": uuid.UUID("30000000-0000-0000-0000-000000000002"),
        "heat-resistance": uuid.UUID("30000000-0000-0000-0000-000000000003"),
        "flexibility": uuid.UUID("30000000-0000-0000-0000-000000000004"),
    }
    material_ids = {
        "pla": uuid.UUID("40000000-0000-0000-0000-000000000001"),
        "petg": uuid.UUID("40000000-0000-0000-0000-000000000002"),
        "abs": uuid.UUID("40000000-0000-0000-0000-000000000003"),
        "asa": uuid.UUID("40000000-0000-0000-0000-000000000004"),
        "tpu": uuid.UUID("40000000-0000-0000-0000-000000000005"),
    }
    applications = sa.table(
        "applications",
        sa.column("id", sa.Uuid()),
        sa.column("slug", sa.String()),
        sa.column("name", sa.String()),
        sa.column("factors", sa.Text()),
        sa.column("display_order", sa.Integer()),
    )
    op.bulk_insert(
        applications,
        [
            {
                "id": app_ids["prototype"],
                "slug": "prototype",
                "name": "Prototipos",
                "factors": "Facilidad de impresión, costo y acabado para iterar con rapidez.",
                "display_order": 1,
            },
            {
                "id": app_ids["mechanical"],
                "slug": "mechanical",
                "name": "Piezas mecánicas",
                "factors": "Resistencia, rigidez y estabilidad dimensional bajo carga.",
                "display_order": 2,
            },
            {
                "id": app_ids["outdoor"],
                "slug": "outdoor",
                "name": "Uso exterior",
                "factors": "Radiación UV, humedad y cambios de temperatura.",
                "display_order": 3,
            },
            {
                "id": app_ids["flexible"],
                "slug": "flexible",
                "name": "Componentes flexibles",
                "factors": "Elasticidad, recuperación y resistencia al desgaste.",
                "display_order": 4,
            },
            {
                "id": app_ids["industrial"],
                "slug": "industrial",
                "name": "Entorno industrial",
                "factors": "Temperatura, impacto y exposición química.",
                "display_order": 5,
            },
        ],
    )
    definitions = sa.table(
        "property_definitions",
        sa.column("id", sa.Uuid()),
        sa.column("slug", sa.String()),
        sa.column("name", sa.String()),
        sa.column("unit", sa.String()),
        sa.column("display_order", sa.Integer()),
    )
    op.bulk_insert(
        definitions,
        [
            {
                "id": property_ids["impact-strength"],
                "slug": "impact-strength",
                "name": "Resistencia al impacto",
                "unit": "kJ/m²",
                "display_order": 1,
            },
            {
                "id": property_ids["bending-strength"],
                "slug": "bending-strength",
                "name": "Resistencia a flexión",
                "unit": "MPa",
                "display_order": 2,
            },
            {
                "id": property_ids["heat-resistance"],
                "slug": "heat-resistance",
                "name": "Resistencia térmica",
                "unit": "°C",
                "display_order": 3,
            },
            {
                "id": property_ids["flexibility"],
                "slug": "flexibility",
                "name": "Flexibilidad",
                "unit": "Shore A",
                "display_order": 4,
            },
        ],
    )
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
    rows = [
        (
            "pla",
            "PLA",
            "Preciso y accesible para validar geometrías y acabados.",
            ["Fácil de imprimir", "Buen detalle"],
            ["Baja resistencia térmica"],
            True,
            "low",
            ["Natural", "Negro", "Blanco"],
            ["Mate", "Satinado"],
        ),
        (
            "petg",
            "PETG",
            "Equilibrio entre facilidad de impresión, tenacidad y resistencia ambiental.",
            ["Buena adhesión entre capas", "Resiste humedad"],
            ["Puede generar hilos"],
            True,
            "medium",
            ["Transparente", "Negro"],
            ["Brillante"],
        ),
        (
            "abs",
            "ABS",
            "Material técnico para piezas funcionales con mayor temperatura de servicio.",
            ["Resistente", "Mecanizable"],
            ["Requiere ambiente controlado"],
            True,
            "medium",
            ["Negro", "Gris"],
            ["Mate"],
        ),
        (
            "asa",
            "ASA",
            "Alternativa estable para componentes expuestos al exterior.",
            ["Resiste radiación UV", "Estable a la intemperie"],
            ["Requiere ambiente controlado"],
            False,
            "high",
            ["Negro", "Blanco"],
            ["Mate"],
        ),
        (
            "tpu",
            "TPU 95A",
            "Elastómero para protectores, sellos y componentes que deben deformarse.",
            ["Flexible", "Resiste abrasión"],
            ["Impresión más lenta"],
            True,
            "high",
            ["Negro"],
            ["Satinado"],
        ),
    ]
    op.bulk_insert(
        materials,
        [
            {
                "id": material_ids[slug],
                "slug": slug,
                "name": name,
                "description": description,
                "advantages": advantages,
                "limitations": limitations,
                "available": available,
                "cost_level": cost,
                "source_url": "https://bambulab.com/en/filament/collections",
                "source_updated_at": date(2026, 9, 2),
                "display_order": index,
                "status": "published",
                "colors": colors,
                "finishes": finishes,
            }
            for index, (
                slug,
                name,
                description,
                advantages,
                limitations,
                available,
                cost,
                colors,
                finishes,
            ) in enumerate(rows, start=1)
        ],
    )
    links = sa.table(
        "material_applications",
        sa.column("material_id", sa.Uuid()),
        sa.column("application_id", sa.Uuid()),
    )
    mapping = {
        "pla": ["prototype"],
        "petg": ["prototype", "mechanical", "outdoor"],
        "abs": ["mechanical", "industrial"],
        "asa": ["outdoor", "industrial"],
        "tpu": ["flexible", "industrial"],
    }
    op.bulk_insert(
        links,
        [
            {"material_id": material_ids[material], "application_id": app_ids[application]}
            for material, assigned in mapping.items()
            for application in assigned
        ],
    )
    values = sa.table(
        "material_property_values",
        sa.column("id", sa.Uuid()),
        sa.column("material_id", sa.Uuid()),
        sa.column("property_definition_id", sa.Uuid()),
        sa.column("value", sa.Float()),
        sa.column("source", sa.String()),
    )
    measured = {
        "pla": {"impact-strength": 26.6, "bending-strength": 76, "heat-resistance": 57},
        "petg": {"impact-strength": 31.5, "bending-strength": 64, "heat-resistance": 69},
        "abs": {"impact-strength": 39.3, "bending-strength": 62, "heat-resistance": 87},
        "asa": {"impact-strength": 41, "bending-strength": 65, "heat-resistance": 93},
        "tpu": {"impact-strength": 123.2, "flexibility": 95},
    }
    counter = 1
    value_rows = []
    for material, properties in measured.items():
        for property_slug, value in properties.items():
            value_rows.append(
                {
                    "id": uuid.UUID(f"50000000-0000-0000-0000-{counter:012d}"),
                    "material_id": material_ids[material],
                    "property_definition_id": property_ids[property_slug],
                    "value": value,
                    "source": "Guía técnica del fabricante; verificar para cada marca y lote.",
                }
            )
            counter += 1
    op.bulk_insert(values, value_rows)


def downgrade() -> None:
    op.drop_table("certifications")
    op.drop_table("material_property_values")
    op.drop_table("material_applications")
    op.drop_index("ix_materials_public_order", table_name="materials")
    op.drop_table("materials")
    op.drop_table("property_definitions")
    op.drop_table("applications")
