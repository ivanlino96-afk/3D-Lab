from datetime import UTC, date, datetime
from uuid import UUID

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, func, select
from sqlalchemy.orm import sessionmaker

from src.administration.infrastructure.auth import AdminUserRecord, PasswordHasher
from src.audit.infrastructure.repository import AuditEventRecord
from src.customers.infrastructure.repository import CustomerRecord
from src.main import create_app
from src.materials.infrastructure.repository import (
    ApplicationRecord,
    CertificationRecord,
    MaterialRecord,
    PropertyDefinitionRecord,
)
from src.quotes.infrastructure.repository import QuoteRequestRecord
from src.shared.infrastructure.database import Base, get_session

NOW = datetime(2026, 9, 3, 12, tzinfo=UTC)
ADMIN_ID = UUID(int=101)
APPLICATION_ID = UUID(int=102)
PROPERTY_ID = UUID(int=103)


@pytest.fixture
def material_admin_environment(tmp_path):
    engine = create_engine(f"sqlite:///{tmp_path / 'materials-admin.db'}")
    factory = sessionmaker(bind=engine, expire_on_commit=False)
    Base.metadata.create_all(engine)
    with factory.begin() as session:
        session.add(
            AdminUserRecord(
                id=ADMIN_ID,
                username="admin",
                password_hash=PasswordHasher(iterations=1_000).hash("correct-password"),
                enabled=True,
                created_at=NOW,
                last_login_at=None,
            )
        )
        session.add(
            ApplicationRecord(
                id=APPLICATION_ID,
                slug="mechanical",
                name="Piezas mecánicas",
                factors="Rigidez y estabilidad",
                display_order=1,
            )
        )
        session.add(
            PropertyDefinitionRecord(
                id=PROPERTY_ID,
                slug="heat-resistance",
                name="Resistencia térmica",
                unit="°C",
                display_order=1,
            )
        )

    app = create_app()

    def override_session():
        with factory() as session:
            try:
                yield session
                session.commit()
            except Exception:
                session.rollback()
                raise

    app.dependency_overrides[get_session] = override_session
    with TestClient(app) as client:
        yield client, factory
    Base.metadata.drop_all(engine)
    engine.dispose()


def login(client: TestClient) -> None:
    response = client.post(
        "/admin/login",
        data={"username": "admin", "password": "correct-password"},
        follow_redirects=False,
    )
    assert response.status_code == 303


def material_form(**changes) -> dict[str, str]:
    values = {
        "slug": "nylon-cf",
        "name": "Nylon CF",
        "description": "Material reforzado para componentes mecánicos.",
        "advantages": "Alta rigidez\nBuena estabilidad",
        "limitations": "Requiere secado",
        "available": "yes",
        "cost_level": "high",
        "source_url": "https://example.com/nylon-cf",
        "source_updated_at": "2026-08-01",
        "display_order": "2",
        "status": "published",
        "applications": "mechanical",
        "property_heat-resistance": "105",
        "property_source_heat-resistance": "Ficha técnica",
        "colors": "Negro",
        "finishes": "Mate",
        "certifications": (
            "Uso industrial | Laboratorio | https://example.com/cert | 2026-01-01 | 2027-01-01"
        ),
    }
    values.update(changes)
    return values


@pytest.mark.e2e
def test_material_administration_requires_a_session(material_admin_environment) -> None:
    client, _ = material_admin_environment
    response = client.get("/admin/materiales", follow_redirects=False)

    assert response.status_code == 303
    assert response.headers["location"] == "/admin/login"


@pytest.mark.e2e
def test_complete_material_can_be_published_and_appears_publicly(
    material_admin_environment,
) -> None:
    client, factory = material_admin_environment
    login(client)
    response = client.post("/admin/materiales/guardar", data=material_form())

    assert response.history[0].status_code == 303
    assert "Nylon CF" in response.text
    public = client.get("/materiales")
    assert "Nylon CF" in public.text
    assert "Alta rigidez" in client.get("/materiales/nylon-cf").text
    with factory() as session:
        material = session.scalar(select(MaterialRecord).where(MaterialRecord.slug == "nylon-cf"))
        assert material.status == "published"
        assert material.updated_at is not None
        assert session.scalar(select(func.count()).select_from(AuditEventRecord)) == 1


@pytest.mark.e2e
def test_missing_fields_and_expired_evidence_block_publication(
    material_admin_environment,
) -> None:
    client, factory = material_admin_environment
    login(client)
    missing = client.post(
        "/admin/materiales/guardar",
        data=material_form(name="", description="", advantages="", applications=""),
    )
    expired = client.post(
        "/admin/materiales/guardar",
        data=material_form(
            slug="expired-cert",
            certifications=(
                "Uso regulado | Laboratorio | https://example.com/old | 2024-01-01 | 2025-01-01"
            ),
        ),
    )

    assert missing.status_code == 422
    assert "Faltan o son inválidos" in missing.text
    assert expired.status_code == 422
    assert "certifications" in expired.text
    with factory() as session:
        assert session.scalar(select(func.count()).select_from(MaterialRecord)) == 0


@pytest.mark.e2e
def test_archiving_keeps_historical_quote_reference_and_removes_public_selection(
    material_admin_environment,
) -> None:
    client, factory = material_admin_environment
    login(client)
    client.post("/admin/materiales/guardar", data=material_form())
    with factory.begin() as session:
        material = session.scalar(select(MaterialRecord).where(MaterialRecord.slug == "nylon-cf"))
        customer_id = UUID(int=110)
        session.add(
            CustomerRecord(
                id=customer_id,
                current_name="Ana López",
                original_email="ana@example.com",
                normalized_email="ana@example.com",
                current_phone="5512345678",
                created_at=NOW,
                updated_at=NOW,
            )
        )
        session.add(
            QuoteRequestRecord(
                id=UUID(int=111),
                public_reference="3DLAB-MATERIAL",
                customer_id=customer_id,
                submission_token="material-history",
                contact_name="Ana López",
                contact_email="ana@example.com",
                contact_phone="5512345678",
                comments=None,
                selected_material_id=material.id,
                status="open",
                created_at=NOW,
                confirmed_at=NOW,
                sale_recorded_at=None,
                completed_at=None,
            )
        )
        material_id = material.id

    archived = client.post(
        f"/admin/materiales/{material_id}/estado",
        data={"status": "archived"},
        follow_redirects=True,
    )
    assert "Catálogo actualizado" in archived.text
    assert "Nylon CF" not in client.get("/materiales").text
    unavailable = client.get("/materiales/nylon-cf/cotizar", follow_redirects=False)
    assert "seleccion=no-disponible" in unavailable.headers["location"]
    assert "Nylon CF" in client.get(f"/admin/cotizaciones/{UUID(int=111)}").text
    with factory() as session:
        quote = session.get(QuoteRequestRecord, UUID(int=111))
        assert quote.selected_material_id == material_id
        assert session.get(MaterialRecord, material_id).status == "archived"


@pytest.mark.e2e
def test_expired_certification_is_not_claimed_on_a_published_detail(
    material_admin_environment,
) -> None:
    client, factory = material_admin_environment
    with factory.begin() as session:
        material = MaterialRecord(
            id=UUID(int=120),
            slug="legacy-material",
            name="Material legado",
            description="Ficha histórica publicada.",
            advantages=["Estable"],
            limitations=["Validar lote"],
            available=True,
            cost_level="medium",
            source_url="https://example.com/legacy",
            source_updated_at=date(2025, 1, 1),
            display_order=1,
            status="published",
            colors=[],
            finishes=[],
            updated_at=NOW,
        )
        session.add(material)
        session.flush()
        session.add(
            CertificationRecord(
                id=UUID(int=121),
                material_id=material.id,
                name="Certificación expirada visible",
                issuer="Laboratorio",
                evidence_url="https://example.com/expired",
                valid_from=date(2024, 1, 1),
                valid_until=date(2025, 1, 1),
            )
        )

    detail = client.get("/materiales/legacy-material")
    assert detail.status_code == 200
    assert "Certificación expirada visible" not in detail.text
