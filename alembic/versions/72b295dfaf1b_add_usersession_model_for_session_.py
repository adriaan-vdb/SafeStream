"""Add UserSession model for session management

Revision ID: 72b295dfaf1b
Revises: a0b361340092
Create Date: 2025-06-29 20:55:59.487897

"""

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "72b295dfaf1b"
down_revision: str | None = "a0b361340092"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Upgrade schema."""
    # ### commands auto generated by Alembic - please adjust! ###
    op.create_table(
        "user_sessions",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("session_token", sa.String(length=255), nullable=False),
        sa.Column("is_active", sa.Boolean(), nullable=False),
        sa.Column("user_agent", sa.Text(), nullable=True),
        sa.Column("ip_address", sa.String(length=45), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("last_activity", sa.DateTime(), nullable=False),
        sa.Column("expires_at", sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(
            ["user_id"],
            ["users.id"],
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        "idx_user_sessions_expires", "user_sessions", ["expires_at"], unique=False
    )
    op.create_index(
        "idx_user_sessions_token_active",
        "user_sessions",
        ["session_token", "is_active"],
        unique=False,
    )
    op.create_index(
        "idx_user_sessions_user_active",
        "user_sessions",
        ["user_id", "is_active"],
        unique=False,
    )
    op.create_index(
        op.f("ix_user_sessions_expires_at"),
        "user_sessions",
        ["expires_at"],
        unique=False,
    )
    op.create_index(op.f("ix_user_sessions_id"), "user_sessions", ["id"], unique=False)
    op.create_index(
        op.f("ix_user_sessions_is_active"), "user_sessions", ["is_active"], unique=False
    )
    op.create_index(
        op.f("ix_user_sessions_last_activity"),
        "user_sessions",
        ["last_activity"],
        unique=False,
    )
    op.create_index(
        op.f("ix_user_sessions_session_token"),
        "user_sessions",
        ["session_token"],
        unique=True,
    )
    op.create_index(
        op.f("ix_user_sessions_user_id"), "user_sessions", ["user_id"], unique=False
    )
    # ### end Alembic commands ###


def downgrade() -> None:
    """Downgrade schema."""
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_index(op.f("ix_user_sessions_user_id"), table_name="user_sessions")
    op.drop_index(op.f("ix_user_sessions_session_token"), table_name="user_sessions")
    op.drop_index(op.f("ix_user_sessions_last_activity"), table_name="user_sessions")
    op.drop_index(op.f("ix_user_sessions_is_active"), table_name="user_sessions")
    op.drop_index(op.f("ix_user_sessions_id"), table_name="user_sessions")
    op.drop_index(op.f("ix_user_sessions_expires_at"), table_name="user_sessions")
    op.drop_index("idx_user_sessions_user_active", table_name="user_sessions")
    op.drop_index("idx_user_sessions_token_active", table_name="user_sessions")
    op.drop_index("idx_user_sessions_expires", table_name="user_sessions")
    op.drop_table("user_sessions")
    # ### end Alembic commands ###
