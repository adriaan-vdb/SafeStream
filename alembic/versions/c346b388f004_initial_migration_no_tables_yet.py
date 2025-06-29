"""Initial migration - no tables yet

Revision ID: c346b388f004
Revises:
Create Date: 2025-06-29 12:15:52.439073

"""

from collections.abc import Sequence

# revision identifiers, used by Alembic.
revision: str = "c346b388f004"
down_revision: str | None = None
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Upgrade schema."""
    pass


def downgrade() -> None:
    """Downgrade schema."""
    pass
