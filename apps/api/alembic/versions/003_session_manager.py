"""session manager tables

Revision ID: 003_session_manager
Revises: 002_billing_saas
Create Date: 2026-06-14
"""

import sqlalchemy as sa
from alembic import op

revision = "003_session_manager"
down_revision = "002_billing_saas"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "account_status",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("account_id", sa.Integer(), sa.ForeignKey("steam_accounts.id", ondelete="CASCADE"), nullable=False, unique=True),
        sa.Column("status", sa.String(length=32), nullable=False, server_default="offline"),
        sa.Column("last_event", sa.String(length=120), nullable=True),
        sa.Column("last_heartbeat_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("error_message", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )
    op.create_index("ix_account_status_account_id", "account_status", ["account_id"], unique=True)
    op.create_index("ix_account_status_status", "account_status", ["status"])

    op.create_table(
        "steam_sessions",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("user_id", sa.Integer(), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
        sa.Column("account_id", sa.Integer(), sa.ForeignKey("steam_accounts.id", ondelete="CASCADE"), nullable=False),
        sa.Column("status", sa.String(length=32), nullable=False, server_default="starting"),
        sa.Column("selected_games", sa.Text(), nullable=False, server_default="[]"),
        sa.Column("worker_job_id", sa.String(length=120), nullable=True),
        sa.Column("started_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("stopped_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("last_heartbeat_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("error_message", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )
    op.create_index("ix_steam_sessions_user_id", "steam_sessions", ["user_id"])
    op.create_index("ix_steam_sessions_account_id", "steam_sessions", ["account_id"])
    op.create_index("ix_steam_sessions_status", "steam_sessions", ["status"])

    op.create_table(
        "session_events",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("session_id", sa.Integer(), sa.ForeignKey("steam_sessions.id", ondelete="CASCADE"), nullable=True),
        sa.Column("user_id", sa.Integer(), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
        sa.Column("account_id", sa.Integer(), sa.ForeignKey("steam_accounts.id", ondelete="SET NULL"), nullable=True),
        sa.Column("event_type", sa.String(length=120), nullable=False),
        sa.Column("message", sa.Text(), nullable=False),
        sa.Column("metadata_json", sa.Text(), nullable=False, server_default="{}"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )
    op.create_index("ix_session_events_session_id", "session_events", ["session_id"])
    op.create_index("ix_session_events_user_id", "session_events", ["user_id"])
    op.create_index("ix_session_events_account_id", "session_events", ["account_id"])
    op.create_index("ix_session_events_event_type", "session_events", ["event_type"])


def downgrade() -> None:
    op.drop_table("session_events")
    op.drop_table("steam_sessions")
    op.drop_table("account_status")
