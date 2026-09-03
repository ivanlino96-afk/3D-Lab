from __future__ import annotations

import base64
import hashlib
import hmac
import os
import uuid
from datetime import datetime

from sqlalchemy import Boolean, DateTime, ForeignKey, String, select
from sqlalchemy.orm import Mapped, Session, mapped_column

from src.administration.application.authenticate_admin import AdminSession, AdminUser
from src.shared.infrastructure.database import Base


class PasswordHasher:
    algorithm = "pbkdf2_sha256"

    def __init__(self, iterations: int = 600_000) -> None:
        self.iterations = iterations
        self._dummy_hash = self.hash("dummy-password-for-timing")

    def hash(self, password: str) -> str:
        salt = os.urandom(16)
        digest = hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), salt, self.iterations)
        return "$".join(
            (
                self.algorithm,
                str(self.iterations),
                base64.urlsafe_b64encode(salt).decode("ascii"),
                base64.urlsafe_b64encode(digest).decode("ascii"),
            )
        )

    def verify(self, password: str, encoded_hash: str) -> bool:
        try:
            algorithm, iterations, salt_text, digest_text = encoded_hash.split("$", 3)
            if algorithm != self.algorithm:
                return False
            salt = base64.urlsafe_b64decode(salt_text)
            expected = base64.urlsafe_b64decode(digest_text)
            actual = hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), salt, int(iterations))
            return hmac.compare_digest(actual, expected)
        except (ValueError, TypeError):
            return False

    def dummy_verify(self, password: str) -> None:
        self.verify(password, self._dummy_hash)


class AdminUserRecord(Base):
    __tablename__ = "admin_users"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True)
    username: Mapped[str] = mapped_column(String(80), unique=True, nullable=False)
    password_hash: Mapped[str] = mapped_column(String(255), nullable=False)
    enabled: Mapped[bool] = mapped_column(Boolean, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    last_login_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))


class AdminSessionRecord(Base):
    __tablename__ = "admin_sessions"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True)
    user_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("admin_users.id"), nullable=False)
    token_hash: Mapped[str] = mapped_column(String(64), unique=True, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    revoked_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))


class SqlAlchemyAdminAuthRepository:
    def __init__(self, session: Session) -> None:
        self._session = session

    def get_enabled_user(self, username: str) -> AdminUser | None:
        record = self._session.scalar(
            select(AdminUserRecord).where(
                AdminUserRecord.username == username, AdminUserRecord.enabled.is_(True)
            )
        )
        return self._to_user(record) if record else None

    def get_enabled_user_by_id(self, user_id: uuid.UUID) -> AdminUser | None:
        record = self._session.get(AdminUserRecord, user_id)
        if record is None or not record.enabled:
            return None
        return self._to_user(record)

    def add_session(self, admin_session: AdminSession) -> None:
        self._session.add(
            AdminSessionRecord(
                id=admin_session.id,
                user_id=admin_session.user_id,
                token_hash=admin_session.token_hash,
                created_at=admin_session.created_at,
                expires_at=admin_session.expires_at,
                revoked_at=None,
            )
        )
        self._session.flush()

    def get_active_session(self, token_hash: str, now: datetime) -> AdminSession | None:
        record = self._session.scalar(
            select(AdminSessionRecord).where(
                AdminSessionRecord.token_hash == token_hash,
                AdminSessionRecord.revoked_at.is_(None),
                AdminSessionRecord.expires_at > now,
            )
        )
        if record is None:
            return None
        return AdminSession(
            record.id,
            record.user_id,
            record.token_hash,
            record.created_at,
            record.expires_at,
            record.revoked_at,
        )

    def revoke_session(self, token_hash: str, revoked_at: datetime) -> bool:
        record = self._session.scalar(
            select(AdminSessionRecord).where(
                AdminSessionRecord.token_hash == token_hash,
                AdminSessionRecord.revoked_at.is_(None),
            )
        )
        if record is None:
            return False
        record.revoked_at = revoked_at
        self._session.flush()
        return True

    def record_login(self, user_id: uuid.UUID, occurred_at: datetime) -> None:
        record = self._session.get(AdminUserRecord, user_id)
        if record is not None:
            record.last_login_at = occurred_at
            self._session.flush()

    @staticmethod
    def _to_user(record: AdminUserRecord) -> AdminUser:
        return AdminUser(record.id, record.username, record.password_hash, record.enabled)


def ensure_configured_admin(
    session: Session, username: str, password_hash: str, created_at: datetime
) -> None:
    if not username or not password_hash:
        return
    existing = session.scalar(select(AdminUserRecord.id).limit(1))
    if existing is not None:
        return
    session.add(
        AdminUserRecord(
            id=uuid.uuid4(),
            username=username,
            password_hash=password_hash,
            enabled=True,
            created_at=created_at,
            last_login_at=None,
        )
    )
    session.flush()
