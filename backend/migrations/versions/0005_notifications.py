"""Expand the transactional outbox for reliable email delivery."""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "0005_notifications"
down_revision: str | None = "0004b_material_admin"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column(
        "outbox_events",
        sa.Column("recipient", sa.String(254), nullable=False, server_default=""),
    )
    op.add_column(
        "outbox_events",
        sa.Column("template_key", sa.String(80), nullable=False, server_default=""),
    )
    op.add_column(
        "outbox_events",
        sa.Column("attempt_count", sa.Integer(), nullable=False, server_default="0"),
    )
    op.add_column(
        "outbox_events", sa.Column("next_attempt_at", sa.DateTime(timezone=True), nullable=True)
    )
    op.add_column("outbox_events", sa.Column("last_error", sa.Text(), nullable=True))
    op.add_column("outbox_events", sa.Column("sent_at", sa.DateTime(timezone=True), nullable=True))
    op.execute(
        "UPDATE outbox_events SET "
        "recipient = COALESCE(payload ->> 'recipient', ''), "
        "template_key = event_type, next_attempt_at = created_at"
    )
    op.create_unique_constraint(
        "uq_notification_event_recipient_template",
        "outbox_events",
        ["event_type", "aggregate_id", "recipient", "template_key"],
    )
    op.create_index("ix_outbox_events_due", "outbox_events", ["status", "next_attempt_at"])


def downgrade() -> None:
    op.drop_index("ix_outbox_events_due", table_name="outbox_events")
    op.drop_constraint("uq_notification_event_recipient_template", "outbox_events", type_="unique")
    op.drop_column("outbox_events", "sent_at")
    op.drop_column("outbox_events", "last_error")
    op.drop_column("outbox_events", "next_attempt_at")
    op.drop_column("outbox_events", "attempt_count")
    op.drop_column("outbox_events", "template_key")
    op.drop_column("outbox_events", "recipient")
