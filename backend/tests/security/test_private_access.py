import hashlib
from datetime import UTC, datetime, timedelta
from uuid import UUID

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from src.administration.infrastructure.auth import AdminSessionRecord, AdminUserRecord
from src.customers.infrastructure.repository import CustomerRecord
from src.main import create_app
from src.quotes.infrastructure.repository import QuoteFileRecord, QuoteRequestRecord
from src.shared.config import get_settings
from src.shared.infrastructure.database import Base, get_session
from src.shared.infrastructure.private_storage import FileSystemPrivateStorage

NOW = datetime.now(UTC)
ADMIN_ID = UUID(int=701)
CUSTOMER_ID = UUID(int=702)
QUOTE_ID = UUID(int=703)
FILE_ID = UUID(int=704)
EXPIRED_FILE_ID = UUID(int=705)


@pytest.fixture
def private_environment(tmp_path, monkeypatch):
    storage_root = tmp_path / "private"
    monkeypatch.setenv("PRIVATE_STORAGE_ROOT", str(storage_root))
    get_settings.cache_clear()
    engine = create_engine(f"sqlite:///{tmp_path / 'security.db'}")
    factory = sessionmaker(bind=engine, expire_on_commit=False)
    Base.metadata.create_all(engine)
    with factory.begin() as session:
        session.add(
            AdminUserRecord(
                id=ADMIN_ID,
                username="admin",
                password_hash="unused",
                enabled=True,
                created_at=NOW,
                last_login_at=None,
            )
        )
        session.add(
            CustomerRecord(
                id=CUSTOMER_ID,
                current_name="Cliente privado",
                original_email="private@example.com",
                normalized_email="private@example.com",
                current_phone="5512345678",
                created_at=NOW,
                updated_at=NOW,
            )
        )
        session.add(
            QuoteRequestRecord(
                id=QUOTE_ID,
                public_reference="3DLAB-PRIVATE-001",
                customer_id=CUSTOMER_ID,
                submission_token="private-token",
                contact_name="Cliente privado",
                contact_email="private@example.com",
                contact_phone="5512345678",
                comments="Contenido confidencial",
                selected_material_id=None,
                status="open",
                created_at=NOW,
                confirmed_at=NOW,
                sale_recorded_at=None,
                completed_at=None,
            )
        )
        session.add_all(
            [
                QuoteFileRecord(
                    id=FILE_ID,
                    quote_request_id=QUOTE_ID,
                    original_name="private.stl",
                    storage_key="quotes/private",
                    size_bytes=11,
                    fingerprint="a" * 64,
                    uploaded_at=NOW,
                    expires_at=NOW + timedelta(days=30),
                    deleted_at=None,
                    status="available",
                ),
                QuoteFileRecord(
                    id=EXPIRED_FILE_ID,
                    quote_request_id=QUOTE_ID,
                    original_name="expired.stl",
                    storage_key="quotes/expired",
                    size_bytes=11,
                    fingerprint="b" * 64,
                    uploaded_at=NOW - timedelta(days=31),
                    expires_at=NOW - timedelta(days=1),
                    deleted_at=NOW,
                    status="expired",
                ),
            ]
        )
    FileSystemPrivateStorage(storage_root).save("quotes/private", [b"solid piece"])
    app = create_app()

    def override_session():
        with factory() as session:
            yield session
            session.commit()

    app.dependency_overrides[get_session] = override_session
    with TestClient(app) as client:
        yield client, factory
    engine.dispose()
    get_settings.cache_clear()


def _add_session(factory, raw_token: str, *, expires_at: datetime, revoked: bool = False) -> None:
    with factory.begin() as session:
        session.add(
            AdminSessionRecord(
                id=UUID(int=710 if revoked else 711),
                user_id=ADMIN_ID,
                token_hash=hashlib.sha256(raw_token.encode()).hexdigest(),
                created_at=NOW - timedelta(hours=9),
                expires_at=expires_at,
                revoked_at=NOW if revoked else None,
            )
        )


@pytest.mark.security
def test_anonymous_and_forged_references_cannot_read_private_data(private_environment) -> None:
    client, _ = private_environment
    protected = (
        f"/admin/cotizaciones/{QUOTE_ID}",
        f"/admin/clientes/{CUSTOMER_ID}",
        f"/admin/archivos/{FILE_ID}",
        "/admin/materiales",
        "/admin/indicadores",
    )
    for path in protected:
        response = client.get(path, follow_redirects=False)
        assert response.status_code == 303
        assert response.headers["location"] == "/admin/login"

    assert client.get("/quotes/private").status_code == 404
    assert client.get("/static/../private/quotes/private").status_code in (404, 405)
    client.cookies.set("3dlab_admin_session", "forged-token")
    assert client.get(f"/admin/archivos/{FILE_ID}", follow_redirects=False).status_code == 303


@pytest.mark.security
@pytest.mark.parametrize("revoked", [False, True])
def test_expired_or_revoked_sessions_are_rejected(private_environment, revoked: bool) -> None:
    client, factory = private_environment
    raw_token = "revoked-session" if revoked else "expired-session"
    _add_session(factory, raw_token, expires_at=NOW - timedelta(seconds=1), revoked=revoked)
    client.cookies.set("3dlab_admin_session", raw_token)

    response = client.get("/admin/cotizaciones", follow_redirects=False)

    assert response.status_code == 303
    assert response.headers["location"] == "/admin/login"


@pytest.mark.security
def test_valid_admin_still_cannot_download_expired_or_unknown_file(private_environment) -> None:
    client, factory = private_environment
    raw_token = "valid-session"
    _add_session(factory, raw_token, expires_at=NOW + timedelta(hours=1))
    client.cookies.set("3dlab_admin_session", raw_token)

    expired = client.get(f"/admin/archivos/{EXPIRED_FILE_ID}")
    unknown = client.get(f"/admin/archivos/{UUID(int=999_999)}")
    available = client.get(f"/admin/archivos/{FILE_ID}")

    assert expired.status_code == 410
    assert unknown.status_code == 410
    assert expired.text == unknown.text
    assert available.status_code == 200
    assert available.content == b"solid piece"
