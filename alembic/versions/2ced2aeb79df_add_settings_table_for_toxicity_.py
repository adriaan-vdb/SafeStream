"""add_settings_table_for_toxicity_threshold

Revision ID: 2ced2aeb79df
Revises: 72b295dfaf1b
Create Date: 2025-06-30 11:03:18.426690

"""

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "2ced2aeb79df"
down_revision: str | None = "72b295dfaf1b"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Upgrade schema."""
    # Create settings table
    op.create_table(
        "settings",
        sa.Column("key", sa.String(100), nullable=False),
        sa.Column("value", sa.Text(), nullable=False),
        sa.Column(
            "created_at", sa.DateTime(), nullable=False, server_default=sa.func.now()
        ),
        sa.Column(
            "updated_at", sa.DateTime(), nullable=False, server_default=sa.func.now()
        ),
        sa.PrimaryKeyConstraint("key"),
    )

    # Insert default toxicity threshold setting
    op.execute("INSERT INTO settings (key, value) VALUES ('toxicity_threshold', '0.6')")


def downgrade() -> None:
    """Downgrade schema."""
    # Drop settings table
    op.drop_table("settings")
