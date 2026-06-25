"""FACEIT watch/ELO snapshots + Steam OpenID login (users.steam_id)

Revision ID: 008_faceit_and_steam_login
Revises: 007_steam_refresh_token
Create Date: 2026-06-23
"""

import sqlalchemy as sa
from alembic import op

revision = "008_faceit_and_steam_login"
down_revision = "007_steam_refresh_token"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("users", sa.Column("steam_id", sa.String(length=32), nullable=True))
    op.create_index("ix_users_steam_id", "users", ["steam_id"], unique=True)

    op.create_table(
        "faceit_elo_snapshots",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("player_id", sa.String(length=64), nullable=False),
        sa.Column("nickname", sa.String(length=80), nullable=True),
        sa.Column("elo", sa.Integer(), nullable=False),
        sa.Column("skill_level", sa.Integer(), nullable=True),
        sa.Column("captured_on", sa.String(length=10), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.UniqueConstraint("player_id", "captured_on", name="uq_faceit_elo_snapshot_day"),
    )
    op.create_index("ix_faceit_elo_snapshots_player_id", "faceit_elo_snapshots", ["player_id"])
    op.create_index("ix_faceit_elo_snapshots_captured_on", "faceit_elo_snapshots", ["captured_on"])

    op.create_table(
        "faceit_watches",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("user_id", sa.Integer(), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
        sa.Column("player_id", sa.String(length=64), nullable=False),
        sa.Column("nickname", sa.String(length=80), nullable=True),
        sa.Column("country", sa.String(length=8), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.UniqueConstraint("user_id", "player_id", name="uq_faceit_watch"),
    )
    op.create_index("ix_faceit_watches_user_id", "faceit_watches", ["user_id"])
    op.create_index("ix_faceit_watches_player_id", "faceit_watches", ["player_id"])


def downgrade() -> None:
    op.drop_index("ix_faceit_watches_player_id", table_name="faceit_watches")
    op.drop_index("ix_faceit_watches_user_id", table_name="faceit_watches")
    op.drop_table("faceit_watches")
    op.drop_index("ix_faceit_elo_snapshots_captured_on", table_name="faceit_elo_snapshots")
    op.drop_index("ix_faceit_elo_snapshots_player_id", table_name="faceit_elo_snapshots")
    op.drop_table("faceit_elo_snapshots")
    op.drop_index("ix_users_steam_id", table_name="users")
    op.drop_column("users", "steam_id")
