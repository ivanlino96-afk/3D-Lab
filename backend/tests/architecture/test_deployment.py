from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[3]


def test_container_runs_migrations_as_non_root_and_keeps_stl_private() -> None:
    dockerfile = (PROJECT_ROOT / "Dockerfile").read_text(encoding="utf-8")

    assert "FROM python:3.12-slim" in dockerfile
    assert "PRIVATE_STORAGE_ROOT=/data/stl" in dockerfile
    assert "python -m alembic upgrade head" in dockerfile
    assert "uvicorn src.main:app" in dockerfile
    assert "--proxy-headers" in dockerfile
    assert "--forwarded-allow-ips='*'" in dockerfile
    assert "USER appuser" in dockerfile
    assert "PASSWORD=" not in dockerfile
    assert "DATABASE_URL=" not in dockerfile


def test_docker_context_excludes_local_secrets_and_generated_data() -> None:
    ignored = (PROJECT_ROOT / ".dockerignore").read_text(encoding="utf-8").splitlines()

    assert ".git" in ignored
    assert ".venv" in ignored
    assert ".env" in ignored
    assert "var/private" in ignored
