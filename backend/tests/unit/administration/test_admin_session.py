from datetime import UTC, datetime, timedelta
from uuid import UUID

import pytest

from src.administration.application.authenticate_admin import (
    AdminSession,
    AdminUser,
    AuthenticateAdmin,
    AuthenticationError,
    CloseAdminSession,
    ValidateAdminSession,
)
from src.administration.infrastructure.auth import PasswordHasher

NOW = datetime(2026, 9, 2, 12, tzinfo=UTC)


class FakeAuthRepository:
    def __init__(self, password_hash: str) -> None:
        self.user = AdminUser(UUID(int=1), "admin", password_hash, True)
        self.sessions: dict[str, AdminSession] = {}

    def get_enabled_user(self, username: str) -> AdminUser | None:
        return self.user if username == self.user.username and self.user.enabled else None

    def get_enabled_user_by_id(self, user_id: UUID) -> AdminUser | None:
        return self.user if user_id == self.user.id and self.user.enabled else None

    def add_session(self, session: AdminSession) -> None:
        self.sessions[session.token_hash] = session

    def get_active_session(self, token_hash: str, now: datetime) -> AdminSession | None:
        session = self.sessions.get(token_hash)
        if session is None or session.revoked_at is not None or session.expires_at <= now:
            return None
        return session

    def revoke_session(self, token_hash: str, revoked_at: datetime) -> bool:
        session = self.sessions.get(token_hash)
        if session is None or session.revoked_at is not None:
            return False
        self.sessions[token_hash] = AdminSession(
            session.id,
            session.user_id,
            session.token_hash,
            session.created_at,
            session.expires_at,
            revoked_at,
        )
        return True

    def record_login(self, user_id: UUID, occurred_at: datetime) -> None:
        assert user_id == self.user.id


@pytest.fixture
def hasher() -> PasswordHasher:
    return PasswordHasher(iterations=1_000)


@pytest.mark.unit
def test_valid_credentials_create_a_protected_session_and_logout(hasher) -> None:
    repository = FakeAuthRepository(hasher.hash("correct-password"))
    result = AuthenticateAdmin(repository, hasher, lambda: "raw-session-token").execute(
        "admin", "correct-password", NOW
    )

    assert result.raw_token == "raw-session-token"
    assert "raw-session-token" not in repository.sessions
    assert ValidateAdminSession(repository).execute(result.raw_token, NOW).id == UUID(int=1)
    assert CloseAdminSession(repository).execute(result.raw_token, NOW) is True
    assert ValidateAdminSession(repository).execute(result.raw_token, NOW) is None


@pytest.mark.unit
@pytest.mark.parametrize(
    ("username", "password"),
    [("admin", "wrong-password"), ("unknown", "correct-password")],
)
def test_invalid_credentials_always_return_the_same_message(hasher, username, password) -> None:
    repository = FakeAuthRepository(hasher.hash("correct-password"))

    with pytest.raises(AuthenticationError) as error:
        AuthenticateAdmin(repository, hasher, lambda: "token").execute(username, password, NOW)

    assert str(error.value) == "Las credenciales no son válidas."
    assert repository.sessions == {}


@pytest.mark.unit
def test_anonymous_expired_and_revoked_sessions_are_rejected(hasher) -> None:
    repository = FakeAuthRepository(hasher.hash("correct-password"))
    repository.sessions["expired"] = AdminSession(
        UUID(int=2), UUID(int=1), "expired", NOW - timedelta(days=2), NOW - timedelta(days=1)
    )

    validator = ValidateAdminSession(repository)
    assert validator.execute(None, NOW) is None
    assert validator.execute("not-a-token", NOW) is None
