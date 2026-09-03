import re

import pytest
from sqlalchemy import create_engine, func, select
from sqlalchemy.orm import sessionmaker

from src.customers.infrastructure.repository import CustomerRecord
from src.quotes.infrastructure.repository import OutboxEventRecord, QuoteRequestRecord
from src.shared.config import get_settings
from src.shared.infrastructure.database import Base, get_session

VALID_STL = b"solid piece\nfacet normal 0 0 0\nendfacet\nendsolid piece"


@pytest.fixture
def quote_http_environment(app, tmp_path, monkeypatch):
    engine = create_engine(f"sqlite:///{tmp_path / 'http-quotes.db'}")
    Base.metadata.create_all(engine)
    session_factory = sessionmaker(bind=engine, expire_on_commit=False)

    def override_session():
        with session_factory() as session:
            try:
                yield session
                session.commit()
            except Exception:
                session.rollback()
                raise

    monkeypatch.setenv("PRIVATE_STORAGE_ROOT", str(tmp_path / "private"))
    get_settings.cache_clear()
    app.dependency_overrides[get_session] = override_session
    yield session_factory
    app.dependency_overrides.pop(get_session, None)
    get_settings.cache_clear()
    Base.metadata.drop_all(engine)
    engine.dispose()


def submission_token(html: str) -> str:
    match = re.search(r'id="submission-token" value="([^"]+)"', html)
    assert match is not None
    return match.group(1)


@pytest.mark.e2e
def test_visitor_uploads_stl_and_confirms_quote_once(client, quote_http_environment) -> None:
    form_page = client.get("/cotizaciones/nueva")
    token = submission_token(form_page.text)

    upload = client.post(
        f"/cotizaciones/cargas/{token}",
        files={"file": ("pieza.stl", VALID_STL, "model/stl")},
    )
    first = client.post(
        "/cotizaciones",
        data={
            "submission_token": token,
            "name": "Ana López",
            "email": "ana@example.com",
            "phone": "5512345678",
            "comments": "Debe resistir carga",
        },
    )
    repeated = client.post(
        "/cotizaciones",
        data={
            "submission_token": token,
            "name": "Ana López",
            "email": "ana@example.com",
            "phone": "5512345678",
        },
    )

    assert form_page.status_code == 200
    assert "0 de 20 archivos" in form_page.text
    assert upload.status_code == 201
    assert upload.json()["status"] == "valid"
    assert first.status_code == 201
    assert repeated.status_code == 201
    assert "Ya tenemos tus archivos" in first.text
    with quote_http_environment() as session:
        assert session.scalar(select(func.count()).select_from(CustomerRecord)) == 1
        assert session.scalar(select(func.count()).select_from(QuoteRequestRecord)) == 1
        assert session.scalar(select(func.count()).select_from(OutboxEventRecord)) == 2


@pytest.mark.e2e
def test_invalid_contact_keeps_request_open_and_explains_error(
    client, quote_http_environment
) -> None:
    token = submission_token(client.get("/cotizaciones/nueva").text)
    client.post(
        f"/cotizaciones/cargas/{token}",
        files={"file": ("pieza.stl", VALID_STL, "model/stl")},
    )

    response = client.post(
        "/cotizaciones",
        data={
            "submission_token": token,
            "name": "A",
            "email": "correo-invalido",
            "phone": "12",
        },
    )

    assert response.status_code == 422
    assert "Revisa la solicitud" in response.text
    assert "nombre debe tener entre 2 y 100" in response.text
    with quote_http_environment() as session:
        assert session.scalar(select(func.count()).select_from(QuoteRequestRecord)) == 0
