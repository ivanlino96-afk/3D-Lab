"""Create administration sessions and append-only quote status history."""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "0004_administration"
down_revision: str | None = "0003_quotes"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column(
        "quote_requests", sa.Column("sale_recorded_at", sa.DateTime(timezone=True), nullable=True)
    )
    op.add_column(
        "quote_requests", sa.Column("completed_at", sa.DateTime(timezone=True), nullable=True)
    )
    op.create_table(
        "admin_users",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("username", sa.String(80), nullable=False),
        sa.Column("password_hash", sa.String(255), nullable=False),
        sa.Column("enabled", sa.Boolean(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("last_login_at", sa.DateTime(timezone=True), nullable=True),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_admin_users")),
        sa.UniqueConstraint("username", name=op.f("uq_admin_users_username")),
    )
    op.create_table(
        "admin_sessions",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("user_id", sa.Uuid(), nullable=False),
        sa.Column("token_hash", sa.String(64), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("revoked_at", sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(
            ["user_id"], ["admin_users.id"], name=op.f("fk_admin_sessions_user_id_admin_users")
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_admin_sessions")),
        sa.UniqueConstraint("token_hash", name=op.f("uq_admin_sessions_token_hash")),
    )
    op.create_index("ix_admin_sessions_active", "admin_sessions", ["token_hash", "expires_at"])
    op.create_table(
        "quote_status_events",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("quote_request_id", sa.Uuid(), nullable=False),
        sa.Column("previous_status", sa.String(20), nullable=False),
        sa.Column("new_status", sa.String(20), nullable=False),
        sa.Column("admin_user_id", sa.Uuid(), nullable=False),
        sa.Column("occurred_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("reason", sa.Text(), nullable=True),
        sa.ForeignKeyConstraint(
            ["quote_request_id"],
            ["quote_requests.id"],
            name=op.f("fk_quote_status_events_quote_request_id_quote_requests"),
        ),
        sa.ForeignKeyConstraint(
            ["admin_user_id"],
            ["admin_users.id"],
            name=op.f("fk_quote_status_events_admin_user_id_admin_users"),
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_quote_status_events")),
    )
    op.create_index(
        "ix_quote_status_events_history",
        "quote_status_events",
        ["quote_request_id", "occurred_at"],
    )


def downgrade() -> None:
    op.drop_index("ix_quote_status_events_history", table_name="quote_status_events")
    op.drop_table("quote_status_events")
    op.drop_index("ix_admin_sessions_active", table_name="admin_sessions")
    op.drop_table("admin_sessions")
    op.drop_table("admin_users")
    op.drop_column("quote_requests", "completed_at")
    op.drop_column("quote_requests", "sale_recorded_at")
