from __future__ import annotations

import os
from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[3]


@dataclass(frozen=True, slots=True)
class Settings:
    app_env: str
    secret_key: str
    database_url: str
    private_storage_root: Path
    admin_username: str
    admin_password_hash: str
    admin_email: str
    smtp_host: str
    smtp_port: int
    smtp_username: str
    smtp_password: str
    smtp_from: str

    @classmethod
    def from_environment(cls) -> Settings:
        app_env = os.getenv("APP_ENV", "development")
        secret_key = os.getenv("APP_SECRET_KEY", "development-only-secret-key-change-me")
        if app_env == "production" and len(secret_key) < 32:
            raise ValueError("APP_SECRET_KEY debe tener al menos 32 caracteres en producción.")

        raw_storage_root = os.getenv("PRIVATE_STORAGE_ROOT", "./var/private/stl")
        storage_root = Path(raw_storage_root)
        if not storage_root.is_absolute():
            storage_root = PROJECT_ROOT / storage_root

        return cls(
            app_env=app_env,
            secret_key=secret_key,
            database_url=os.getenv(
                "DATABASE_URL",
                "postgresql+psycopg://threedlab:change-me@localhost:5432/threedlab",
            ),
            private_storage_root=storage_root.resolve(),
            admin_username=os.getenv("ADMIN_USERNAME", "admin").strip().casefold(),
            admin_password_hash=os.getenv("ADMIN_PASSWORD_HASH", ""),
            admin_email=os.getenv("ADMIN_EMAIL", "admin@example.com"),
            smtp_host=os.getenv("SMTP_HOST", ""),
            smtp_port=int(os.getenv("SMTP_PORT", "587")),
            smtp_username=os.getenv("SMTP_USERNAME", ""),
            smtp_password=os.getenv("SMTP_PASSWORD", ""),
            smtp_from=os.getenv("SMTP_FROM", "3D-Lab <cotizaciones@example.com>"),
        )


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    return Settings.from_environment()
