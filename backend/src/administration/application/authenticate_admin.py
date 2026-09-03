from __future__ import annotations

import hashlib
from collections.abc import Callable
from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import Protocol
from uuid import UUID, uuid4


@dataclass(frozen=True, slots=True)
class AdminUser:
    id: UUID
    username: str
    password_hash: str
    enabled: bool


@dataclass(frozen=True, slots=True)
class AdminSession:
    id: UUID
    user_id: UUID
    token_hash: str
    created_at: datetime
    expires_at: datetime
    revoked_at: datetime | None = None


@dataclass(frozen=True, slots=True)
class AuthenticatedSession:
    raw_token: str
    expires_at: datetime
    user_id: UUID


class PasswordVerifier(Protocol):
    def verify(self, password: str, encoded_hash: str) -> bool: ...

    def dummy_verify(self, password: str) -> None: ...


class AdminAuthRepository(Protocol):
    def get_enabled_user(self, username: str) -> AdminUser | None: ...

    def get_enabled_user_by_id(self, user_id: UUID) -> AdminUser | None: ...

    def add_session(self, session: AdminSession) -> None: ...

    def get_active_session(self, token_hash: str, now: datetime) -> AdminSession | None: ...

    def revoke_session(self, token_hash: str, revoked_at: datetime) -> bool: ...

    def record_login(self, user_id: UUID, occurred_at: datetime) -> None: ...


class AuthenticationError(ValueError):
    pass


def hash_session_token(raw_token: str) -> str:
    return hashlib.sha256(raw_token.encode("utf-8")).hexdigest()


@dataclass(frozen=True, slots=True)
class AuthenticateAdmin:
    repository: AdminAuthRepository
    passwords: PasswordVerifier
    token_factory: Callable[[], str]
    session_lifetime: timedelta = timedelta(hours=8)

    def execute(self, username: str, password: str, now: datetime) -> AuthenticatedSession:
        normalized_username = username.strip().casefold()
        user = self.repository.get_enabled_user(normalized_username)
        if user is None:
            self.passwords.dummy_verify(password)
            raise AuthenticationError("Las credenciales no son válidas.")
        if not self.passwords.verify(password, user.password_hash):
            raise AuthenticationError("Las credenciales no son válidas.")

        raw_token = self.token_factory()
        expires_at = now + self.session_lifetime
        self.repository.add_session(
            AdminSession(
                id=uuid4(),
                user_id=user.id,
                token_hash=hash_session_token(raw_token),
                created_at=now,
                expires_at=expires_at,
            )
        )
        self.repository.record_login(user.id, now)
        return AuthenticatedSession(raw_token, expires_at, user.id)


@dataclass(frozen=True, slots=True)
class ValidateAdminSession:
    repository: AdminAuthRepository

    def execute(self, raw_token: str | None, now: datetime) -> AdminUser | None:
        if not raw_token:
            return None
        session = self.repository.get_active_session(hash_session_token(raw_token), now)
        if session is None:
            return None
        return self.repository.get_enabled_user_by_id(session.user_id)


@dataclass(frozen=True, slots=True)
class CloseAdminSession:
    repository: AdminAuthRepository

    def execute(self, raw_token: str | None, now: datetime) -> bool:
        if not raw_token:
            return False
        return self.repository.revoke_session(hash_session_token(raw_token), now)
