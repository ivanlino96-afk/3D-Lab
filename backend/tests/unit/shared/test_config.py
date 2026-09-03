from pathlib import Path

import pytest

from src.shared.config import Settings


@pytest.mark.unit
def test_development_settings_have_safe_project_defaults(monkeypatch) -> None:
    monkeypatch.delenv("APP_ENV", raising=False)
    monkeypatch.delenv("PRIVATE_STORAGE_ROOT", raising=False)

    settings = Settings.from_environment()

    assert settings.app_env == "development"
    assert settings.database_url.startswith("postgresql+psycopg://")
    assert settings.private_storage_root.is_absolute()


@pytest.mark.unit
def test_production_rejects_a_short_secret(monkeypatch, tmp_path: Path) -> None:
    monkeypatch.setenv("APP_ENV", "production")
    monkeypatch.setenv("APP_SECRET_KEY", "short")
    monkeypatch.setenv("PRIVATE_STORAGE_ROOT", str(tmp_path))

    with pytest.raises(ValueError, match="32 caracteres"):
        Settings.from_environment()
