from datetime import UTC, datetime, timedelta
from uuid import UUID

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, func, select
from sqlalchemy.orm import sessionmaker

from src.administration.infrastructure.auth import (
    AdminSessionRecord,
    AdminUserRecord,
    PasswordHasher,
)
from src.audit.infrastructure.repository import AuditEventRecord
from src.customers.infrastructure.repository import CustomerRecord, DataSubjectRequestRecord
from src.main import create_app
from src.quotes.infrastructure.repository import (
    OutboxEventRecord,
    QuoteFileRecord,
    QuoteRequestRecord,
)
from src.quotes.infrastructure.status_repository import QuoteStatusEventRecord
from src.shared.config import get_settings
from src.shared.infrastructure.database import Base, get_session
from src.shared.infrastructure.private_storage import FileSystemPrivateStorage

NOW = datetime(2026, 9, 2, 12, tzinfo=UTC)
ADMIN_ID = UUID(int=10)
CUSTOMER_ID = UUID(int=20)
QUOTE_ID = UUID(int=30)
FILE_ID = UUID(int=40)


@pytest.fixture
def admin_environment(tmp_path, monkeypatch):
    database = tmp_path / "admin.db"
    storage_root = tmp_path / "private"
    monkeypatch.setenv("PRIVATE_STORAGE_ROOT", str(storage_root))
    monkeypatch.delenv("ADMIN_PASSWORD_HASH", raising=False)
    get_settings.cache_clear()
    engine = create_engine(f"sqlite:///{database}")
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
            CustomerRecord(
                id=CUSTOMER_ID,
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
                id=QUOTE_ID,
                public_reference="3DLAB-ADMIN-001",
                customer_id=CUSTOMER_ID,
                submission_token="admin-e2e-token",
                contact_name="Ana López",
                contact_email="ana@example.com",
                contact_phone="5512345678",
                comments="Pieza para automatización",
                selected_material_id=None,
                status="open",
                created_at=NOW,
                confirmed_at=NOW,
                sale_recorded_at=None,
                completed_at=None,
            )
        )
        session.add(
            QuoteFileRecord(
                id=FILE_ID,
                quote_request_id=QUOTE_ID,
                original_name="soporte.stl",
                storage_key="quotes/support",
                size_bytes=11,
                fingerprint="a" * 64,
                uploaded_at=NOW,
                expires_at=NOW + timedelta(days=30),
                deleted_at=None,
                status="available",
            )
        )
    FileSystemPrivateStorage(storage_root).save("quotes/support", [b"solid piece"])

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
    get_settings.cache_clear()


def login(client: TestClient) -> None:
    response = client.post(
        "/admin/login",
        data={"username": "admin", "password": "correct-password"},
        follow_redirects=False,
    )
    assert response.status_code == 303
    assert response.headers["location"] == "/admin/cotizaciones"


@pytest.mark.e2e
def test_private_panel_rejects_anonymous_and_accepts_only_valid_credentials(
    admin_environment,
) -> None:
    client, factory = admin_environment
    anonymous = client.get("/admin/cotizaciones", follow_redirects=False)
    invalid = client.post(
        "/admin/login", data={"username": "unknown", "password": "wrong-password"}
    )

    assert anonymous.status_code == 303
    assert anonymous.headers["location"] == "/admin/login"
    assert invalid.status_code == 401
    assert "Las credenciales no son válidas" in invalid.text
    assert "unknown" not in invalid.text

    login(client)
    panel = client.get("/admin/cotizaciones")
    assert panel.status_code == 200
    assert "3DLAB-ADMIN-001" in panel.text
    assert "Ana López" in panel.text

    client.post("/admin/logout")
    assert client.get("/admin/cotizaciones", follow_redirects=False).status_code == 303
    with factory() as session:
        assert session.scalar(select(func.count()).select_from(AdminSessionRecord)) == 1
        assert session.scalar(select(AdminSessionRecord.revoked_at)) is not None


@pytest.mark.e2e
def test_filters_detail_and_private_download(admin_environment) -> None:
    client, _ = admin_environment
    login(client)

    matches = client.get(
        "/admin/cotizaciones",
        params={"q": "ANA@EXAMPLE.COM", "status": "open", "date_from": "2026-09-01"},
    )
    no_matches = client.get("/admin/cotizaciones", params={"q": "otro cliente"})
    detail = client.get(f"/admin/cotizaciones/{QUOTE_ID}")
    download = client.get(f"/admin/archivos/{FILE_ID}")

    assert "3DLAB-ADMIN-001" in matches.text
    assert "Sin coincidencias" in no_matches.text
    assert "Pieza para automatización" in detail.text
    assert download.content == b"solid piece"
    assert "attachment" in download.headers["content-disposition"]


@pytest.mark.e2e
def test_status_cycle_records_sale_history_notifications_and_terminal_rule(
    admin_environment,
) -> None:
    client, factory = admin_environment
    login(client)

    for status in ("quote_sent", "in_progress", "closed"):
        response = client.post(
            f"/admin/cotizaciones/{QUOTE_ID}/estado",
            data={"status": status, "reason": "Avance confirmado"},
            follow_redirects=False,
        )
        assert response.status_code == 303

    terminal = client.post(
        f"/admin/cotizaciones/{QUOTE_ID}/estado",
        data={"status": "canceled"},
        follow_redirects=True,
    )
    assert "no está permitido" in terminal.text

    with factory() as session:
        quote = session.get(QuoteRequestRecord, QUOTE_ID)
        assert quote.status == "closed"
        assert quote.sale_recorded_at is not None
        assert quote.completed_at is not None
        assert session.scalar(select(func.count()).select_from(QuoteStatusEventRecord)) == 3
        assert session.scalar(select(func.count()).select_from(OutboxEventRecord)) == 3
        assert session.scalar(select(func.count()).select_from(AuditEventRecord)) == 3


@pytest.mark.e2e
def test_canceled_sale_keeps_its_sale_timestamp_but_is_no_longer_effective(
    admin_environment,
) -> None:
    client, factory = admin_environment
    login(client)
    for status in ("quote_sent", "in_progress", "canceled"):
        client.post(
            f"/admin/cotizaciones/{QUOTE_ID}/estado",
            data={"status": status},
            follow_redirects=False,
        )

    with factory() as session:
        quote = session.get(QuoteRequestRecord, QUOTE_ID)
        assert quote.status == "canceled"
        assert quote.sale_recorded_at is not None
        assert quote.completed_at is None
        assert session.scalar(select(func.count()).select_from(QuoteStatusEventRecord)) == 3


@pytest.mark.e2e
def test_customer_history_and_verified_data_request(admin_environment) -> None:
    client, factory = admin_environment
    login(client)
    customer = client.get(f"/admin/clientes/{CUSTOMER_ID}")
    assert "Historial del cliente" in customer.text
    assert "3DLAB-ADMIN-001" in customer.text

    client.post(
        f"/admin/clientes/{CUSTOMER_ID}/solicitudes-datos",
        data={"request_type": "correction", "requested_email": "ana@example.com"},
    )
    with factory() as session:
        request = session.scalar(select(DataSubjectRequestRecord))
        request_id = request.id

    rejected = client.post(
        f"/admin/solicitudes-datos/{request_id}/completar",
        data={"verified_email": "otro@example.com", "resolution_notes": "No aplicar"},
        follow_redirects=True,
    )
    assert "no corresponde" in rejected.text
    client.post(
        f"/admin/solicitudes-datos/{request_id}/completar",
        data={"verified_email": "ANA@example.com", "resolution_notes": "Teléfono corregido"},
    )
    with factory() as session:
        request = session.get(DataSubjectRequestRecord, request_id)
        assert request.verification_status == "completed"


@pytest.mark.e2e
def test_failed_notifications_are_visible_only_inside_admin_panel(admin_environment) -> None:
    client, factory = admin_environment
    anonymous = client.get("/admin/notificaciones", follow_redirects=False)
    assert anonymous.status_code == 303

    with factory.begin() as session:
        session.add(
            OutboxEventRecord(
                id=UUID(int=99),
                event_type="quote_received_customer",
                aggregate_id=QUOTE_ID,
                dedupe_key="failed-notification:e2e",
                payload={"reference": "3DLAB-ADMIN-001"},
                status="not_delivered",
                created_at=NOW,
                recipient="ana@example.com",
                template_key="quote_received_customer",
                attempt_count=3,
                next_attempt_at=None,
                last_error="Buzón rechazado",
                sent_at=None,
            )
        )
    login(client)
    page = client.get("/admin/notificaciones")
    assert page.status_code == 200
    assert "3DLAB-ADMIN-001" in page.text
    assert "ana@example.com" in page.text
    assert "Buzón rechazado" in page.text


@pytest.mark.e2e
def test_admin_can_choose_a_metrics_period_and_get_recoverable_errors(
    admin_environment,
) -> None:
    client, _ = admin_environment
    login(client)
    report = client.get(
        "/admin/indicadores",
        params={"date_from": "2026-09-01", "date_to": "2026-09-30"},
    )
    invalid = client.get(
        "/admin/indicadores",
        params={"date_from": "2026-10-01", "date_to": "2026-09-01"},
    )

    assert report.status_code == 200
    assert "Solicitudes aceptadas" in report.text
    assert "Conversión efectiva" in report.text
    assert invalid.status_code == 422
    assert "El periodo no es válido" in invalid.text
