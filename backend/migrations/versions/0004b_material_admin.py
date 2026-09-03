"""Track material catalog modification dates."""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "0004b_material_admin"
down_revision: str | None = "0004_administration"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column(
        "materials",
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.func.now(),
        ),
    )


def downgrade() -> None:
    op.drop_column("materials", "updated_at")
