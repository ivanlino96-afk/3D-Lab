from __future__ import annotations
from dotenv import load_dotenv

load_dotenv()

import datetime
import uuid
from sqlalchemy import select
from sqlalchemy.orm import Session

from src.administration.infrastructure.auth import AdminUserRecord, PasswordHasher
from src.audit.infrastructure.repository import AuditEventRecord  # noqa: F401
from src.catalog.infrastructure.repository import ServiceRecord
from src.customers.infrastructure.repository import CustomerRecord  # noqa: F401
from src.materials.infrastructure.repository import (
    ApplicationRecord,
    CertificationRecord,  # noqa: F401
    MaterialRecord,
    MaterialPropertyValueRecord,
    PropertyDefinitionRecord,
    material_applications,
)
from src.notifications.infrastructure.repository import OutboxEventRecord  # noqa: F401
from src.quotes.infrastructure.repository import (  # noqa: F401
    QuoteFileRecord,
    QuoteRequestRecord,
    UploadItemRecord,
    UploadSessionRecord,
)
from src.quotes.infrastructure.status_repository import QuoteStatusEventRecord  # noqa: F401
from src.customers.infrastructure.repository import (  # noqa: F401
    DataSubjectRequestRecord,
)
from src.shared.config import get_settings
from src.shared.infrastructure.database import Base, build_engine

def seed_database(database_url: str | None = None) -> None:
    engine = build_engine(database_url or get_settings().database_url)
    Base.metadata.create_all(engine)

    with Session(engine) as session:
        if session.scalar(select(ServiceRecord.id).limit(1)) is None:
            session.add_all([
                ServiceRecord(
                    id=uuid.UUID("10000000-0000-0000-0000-000000000001"),
                    slug="impresion-3d",
                    name="Impresión 3D",
                    summary="Prototipos y piezas funcionales bajo demanda.",
                    description="Fabricación aditiva para validar ideas o producir piezas finales con alta precisión.",
                    display_order=1,
                    is_published=True,
                ),
                ServiceRecord(
                    id=uuid.UUID("10000000-0000-0000-0000-000000000002"),
                    slug="diseno-de-piezas",
                    name="Diseño de piezas",
                    summary="Modelado de componentes desde una necesidad o concepto.",
                    description="Diseño orientado a manufactura aditiva y al uso real de la pieza.",
                    display_order=2,
                    is_published=True,
                ),
                ServiceRecord(
                    id=uuid.UUID("10000000-0000-0000-0000-000000000003"),
                    slug="ingenieria-inversa",
                    name="Ingeniería inversa",
                    summary="Reconstrucción digital de componentes existentes.",
                    description="Recuperación y adaptación de geometrías para refacciones y mejoras funcionales.",
                    display_order=3,
                    is_published=True,
                ),
                ServiceRecord(
                    id=uuid.UUID("10000000-0000-0000-0000-000000000004"),
                    slug="asesoria-tecnica",
                    name="Asesoría técnica",
                    summary="Selección informada de material, proceso y acabado.",
                    description="Acompañamiento especializado para reducir costos y riesgos antes de fabricar.",
                    display_order=4,
                    is_published=True,
                ),
            ])

        if session.scalar(select(ApplicationRecord.id).limit(1)) is None:
            app_ids = {
                "prototype": uuid.UUID("20000000-0000-0000-0000-000000000001"),
                "mechanical": uuid.UUID("20000000-0000-0000-0000-000000000002"),
                "outdoor": uuid.UUID("20000000-0000-0000-0000-000000000003"),
                "flexible": uuid.UUID("20000000-0000-0000-0000-000000000004"),
                "industrial": uuid.UUID("20000000-0000-0000-0000-000000000005"),
            }
            session.add_all([
                ApplicationRecord(id=app_ids["prototype"], slug="prototype", name="Prototipos", factors="Facilidad de impresión, costo accesible y buen acabado para iterar con rapidez.", display_order=1),
                ApplicationRecord(id=app_ids["mechanical"], slug="mechanical", name="Piezas mecánicas", factors="Resistencia, rigidez y estabilidad dimensional bajo cargas de trabajo.", display_order=2),
                ApplicationRecord(id=app_ids["outdoor"], slug="outdoor", name="Uso exterior", factors="Resistencia a la radiación UV, humedad y cambios de temperatura.", display_order=3),
                ApplicationRecord(id=app_ids["flexible"], slug="flexible", name="Componentes flexibles", factors="Elasticidad, amortiguación y resistencia al desgaste por fricción.", display_order=4),
                ApplicationRecord(id=app_ids["industrial"], slug="industrial", name="Entorno industrial", factors="Resistencia térmica elevada, impacto severo y exposición química.", display_order=5),
            ])

            prop_ids = {
                "impact-strength": uuid.UUID("30000000-0000-0000-0000-000000000001"),
                "bending-strength": uuid.UUID("30000000-0000-0000-0000-000000000002"),
                "heat-resistance": uuid.UUID("30000000-0000-0000-0000-000000000003"),
                "flexibility": uuid.UUID("30000000-0000-0000-0000-000000000004"),
            }
            session.add_all([
                PropertyDefinitionRecord(id=prop_ids["impact-strength"], slug="impact-strength", name="Resistencia al impacto", unit="kJ/m²", display_order=1),
                PropertyDefinitionRecord(id=prop_ids["bending-strength"], slug="bending-strength", name="Resistencia a flexión", unit="MPa", display_order=2),
                PropertyDefinitionRecord(id=prop_ids["heat-resistance"], slug="heat-resistance", name="Resistencia térmica", unit="°C", display_order=3),
                PropertyDefinitionRecord(id=prop_ids["flexibility"], slug="flexibility", name="Flexibilidad", unit="Shore A", display_order=4),
            ])

            material_ids = {
                "pla": uuid.UUID("40000000-0000-0000-0000-000000000001"),
                "petg": uuid.UUID("40000000-0000-0000-0000-000000000002"),
                "abs": uuid.UUID("40000000-0000-0000-0000-000000000003"),
                "asa": uuid.UUID("40000000-0000-0000-0000-000000000004"),
                "tpu": uuid.UUID("40000000-0000-0000-0000-000000000005"),
                "nylon-pa": uuid.UUID("40000000-0000-0000-0000-000000000006"),
                "nylon-cf": uuid.UUID("40000000-0000-0000-0000-000000000007"),
            }
            rows = [
                ("pla", "PLA+", "Preciso, biodegradable y accesible para validar geometrías, maquetas y prototipos.", ["Fácil de imprimir", "Excelente detalle superficial", "Costo bajo"], ["Baja resistencia térmica (deforma a >55°C)", "Quebradizo bajo impacto"], True, "low", ["Natural", "Negro", "Blanco", "Gris", "Azul"], ["Mate", "Satinado"]),
                ("petg", "PETG", "Equilibrio ideal entre facilidad de impresión, tenacidad y resistencia química y a la humedad.", ["Buena adhesión entre capas", "Resistente al agua", "Baja contracción"], ["Sensible a hilos (stringing)"], True, "medium", ["Transparente", "Negro", "Blanco", "Rojo"], ["Brillante"]),
                ("abs", "ABS Técnico", "Material técnico para piezas funcionales con mayor temperatura de servicio y mecanizado.", ["Resistente a impactos", "Poco desgaste", "Apto para postprocesado químico"], ["Requiere cámara cerrada", "Emite vapores al fundirse"], True, "medium", ["Negro", "Gris", "Blanco"], ["Mate"]),
                ("nylon-pa", "Nylon (PA)", "Tenaz y resistente al desgaste para engranes, bisagras y piezas móviles.", ["Alta tenacidad", "Baja fricción", "Resiste desgaste"], ["Absorbe humedad", "Requiere secado previo"], True, "high", ["Natural", "Negro"], ["Mate"]),
                ("nylon-cf", "Nylon con fibra de carbono (PA-CF)", "Refuerzo estructural para piezas rígidas, precisas y sometidas a carga.", ["Alta rigidez", "Estabilidad dimensional", "Bajo peso"], ["Material abrasivo", "Requiere boquilla endurecida"], True, "high", ["Negro"], ["Mate técnico"]),
                ("asa", "ASA UV", "Excelente resistencia a la radiación solar e intemperie; ideal para piezas exteriores.", ["Resiste radiación UV sin amarillear", "Excelente resistencia ambiental"], ["Requiere cámara cerrada para evitar warping"], False, "high", ["Negro", "Blanco"], ["Mate"]),
                ("tpu", "TPU 95A Flexible", "Elastómero termoplástico para protectores, juntas, sellos y piezas con alta absorción de choque.", ["Gran elasticidad", "Excelente resistencia al desgaste y abrasión"], ["Requiere extrusor directo y velocidad reducida"], True, "high", ["Negro", "Rojo", "Azul"], ["Satinado"]),
            ]
            now = datetime.datetime.now(datetime.timezone.utc)
            mats = [
                MaterialRecord(
                    id=material_ids[slug], slug=slug, name=name, description=desc,
                    advantages=adv, limitations=lim, available=avail, cost_level=cost,
                    source_url="https://bambulab.com/en/filament/collections",
                    source_updated_at=datetime.date(2026, 9, 2),
                    display_order=idx, status="published", colors=cols, finishes=fin,
                    updated_at=now,
                )
                for idx, (slug, name, desc, adv, lim, avail, cost, cols, fin) in enumerate(rows, start=1)
            ]
            session.add_all(mats)

            mapping = {
                "pla": ["prototype"],
                "petg": ["prototype", "mechanical", "outdoor"],
                "abs": ["mechanical", "industrial"],
                "nylon-pa": ["mechanical", "industrial"],
                "nylon-cf": ["mechanical", "industrial"],
                "asa": ["outdoor", "industrial"],
                "tpu": ["flexible", "industrial"],
            }
            session.flush()
            for m, assigned in mapping.items():
                for a in assigned:
                    session.execute(
                        material_applications.insert().values(
                            material_id=material_ids[m],
                            application_id=app_ids[a],
                        )
                    )

            measured = {
                "pla": {"impact-strength": 26.6, "bending-strength": 76.0, "heat-resistance": 57.0},
                "petg": {"impact-strength": 31.5, "bending-strength": 64.0, "heat-resistance": 69.0},
                "abs": {"impact-strength": 39.3, "bending-strength": 62.0, "heat-resistance": 87.0},
                "nylon-pa": {"impact-strength": 52.0, "bending-strength": 70.0, "heat-resistance": 100.0},
                "nylon-cf": {"impact-strength": 45.0, "bending-strength": 110.0, "heat-resistance": 120.0},
                "asa": {"impact-strength": 41.0, "bending-strength": 65.0, "heat-resistance": 93.0},
                "tpu": {"impact-strength": 123.2, "flexibility": 95.0},
            }
            counter = 1
            for m, props in measured.items():
                for p_slug, val in props.items():
                    session.add(
                        MaterialPropertyValueRecord(
                            id=uuid.UUID(f"50000000-0000-0000-0000-{counter:012d}"),
                            material_id=material_ids[m],
                            property_definition_id=prop_ids[p_slug],
                            value=val,
                            source="Ficha técnica del fabricante; validado por laboratorio.",
                        )
                    )
                    counter += 1

        hasher = PasswordHasher()
        admin = session.scalar(select(AdminUserRecord).where(AdminUserRecord.username == "admin"))
        if not admin:
            session.add(
                AdminUserRecord(
                    id=uuid.uuid4(),
                    username="admin",
                    password_hash=hasher.hash("admin123"),
                    enabled=True,
                    created_at=datetime.datetime.now(datetime.timezone.utc),
                    last_login_at=None,
                )
            )

        session.commit()
        print("Base de datos inicializada y catalogada con exito.")

if __name__ == "__main__":
    seed_database()
