"""Create customers, quote submissions, uploads, data requests and transactional outbox."""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "0003_quotes"
down_revision: str | None = "0002_material_catalog"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "customers",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("current_name", sa.String(100), nullable=False),
        sa.Column("original_email", sa.String(254), nullable=False),
        sa.Column("normalized_email", sa.String(254), nullable=False),
        sa.Column("current_phone", sa.String(16), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_customers")),
        sa.UniqueConstraint("normalized_email", name=op.f("uq_customers_normalized_email")),
    )
    op.create_table(
        "quote_requests",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("public_reference", sa.String(40), nullable=False),
        sa.Column("customer_id", sa.Uuid(), nullable=False),
        sa.Column("submission_token", sa.String(120), nullable=False),
        sa.Column("contact_name", sa.String(100), nullable=False),
        sa.Column("contact_email", sa.String(254), nullable=False),
        sa.Column("contact_phone", sa.String(16), nullable=False),
        sa.Column("comments", sa.Text(), nullable=True),
        sa.Column("selected_material_id", sa.Uuid(), nullable=True),
        sa.Column("status", sa.String(20), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("confirmed_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["customer_id"], ["customers.id"], name=op.f("fk_quote_customer")),
        sa.ForeignKeyConstraint(
            ["selected_material_id"], ["materials.id"], name=op.f("fk_quote_material")
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_quote_requests")),
        sa.UniqueConstraint("public_reference", name=op.f("uq_quote_requests_public_reference")),
        sa.UniqueConstraint("submission_token", name=op.f("uq_quote_requests_submission_token")),
        sa.CheckConstraint(
            "status IN ('open', 'quote_sent', 'in_progress', 'closed', 'canceled')",
            name="quote_status",
        ),
    )
    op.create_table(
        "upload_sessions",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("token", sa.String(120), nullable=False),
        sa.Column("confirmed_quote_id", sa.Uuid(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(
            ["confirmed_quote_id"], ["quote_requests.id"], name=op.f("fk_upload_session_quote")
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_upload_sessions")),
        sa.UniqueConstraint("token", name=op.f("uq_upload_sessions_token")),
    )
    op.create_table(
        "upload_items",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("session_id", sa.Uuid(), nullable=False),
        sa.Column("original_name", sa.String(255), nullable=False),
        sa.Column("size_bytes", sa.BigInteger(), nullable=False),
        sa.Column("status", sa.String(12), nullable=False),
        sa.Column("storage_key", sa.String(200), nullable=True),
        sa.Column("fingerprint", sa.String(64), nullable=True),
        sa.Column("error_message", sa.String(300), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(
            ["session_id"],
            ["upload_sessions.id"],
            name=op.f("fk_upload_item_session"),
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_upload_items")),
        sa.CheckConstraint(
            "status IN ('pending', 'valid', 'invalid', 'removed')", name="upload_status"
        ),
    )
    op.create_table(
        "quote_files",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("quote_request_id", sa.Uuid(), nullable=False),
        sa.Column("original_name", sa.String(255), nullable=False),
        sa.Column("storage_key", sa.String(200), nullable=False),
        sa.Column("size_bytes", sa.BigInteger(), nullable=False),
        sa.Column("fingerprint", sa.String(64), nullable=False),
        sa.Column("uploaded_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("status", sa.String(12), nullable=False),
        sa.ForeignKeyConstraint(
            ["quote_request_id"],
            ["quote_requests.id"],
            name=op.f("fk_quote_file_quote"),
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_quote_files")),
    )
    op.create_index("ix_quote_files_expiration", "quote_files", ["status", "expires_at"])
    op.create_table(
        "outbox_events",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("event_type", sa.String(80), nullable=False),
        sa.Column("aggregate_id", sa.Uuid(), nullable=False),
        sa.Column("dedupe_key", sa.String(200), nullable=False),
        sa.Column("payload", sa.JSON(), nullable=False),
        sa.Column("status", sa.String(12), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_outbox_events")),
        sa.UniqueConstraint("dedupe_key", name=op.f("uq_outbox_events_dedupe_key")),
    )
    op.create_table(
        "data_subject_requests",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("customer_id", sa.Uuid(), nullable=False),
        sa.Column("request_type", sa.String(12), nullable=False),
        sa.Column("requested_email", sa.String(254), nullable=False),
        sa.Column("verification_status", sa.String(12), nullable=False),
        sa.Column("resolution_notes", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("completed_at", sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(
            ["customer_id"], ["customers.id"], name=op.f("fk_data_request_customer")
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_data_subject_requests")),
        sa.CheckConstraint(
            "request_type IN ('access', 'correction', 'deletion')", name="data_request_type"
        ),
        sa.CheckConstraint(
            "verification_status IN ('pending', 'verified', 'completed', 'rejected')",
            name="data_request_status",
        ),
    )


def downgrade() -> None:
    op.drop_table("data_subject_requests")
    op.drop_table("outbox_events")
    op.drop_index("ix_quote_files_expiration", table_name="quote_files")
    op.drop_table("quote_files")
    op.drop_table("upload_items")
    op.drop_table("upload_sessions")
    op.drop_table("quote_requests")
    op.drop_table("customers")
