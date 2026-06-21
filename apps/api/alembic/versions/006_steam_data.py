"""steam profile/game asset cache + index hardening

Revision ID: 006_steam_data
Revises: 005_account_security
Create Date: 2026-06-21
"""

import sqlalchemy as sa
from alembic import op

revision = "006_steam_data"
down_revision = "005_account_security"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "steam_profile_cache",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("account_id", sa.Integer(), sa.ForeignKey("steam_accounts.id", ondelete="CASCADE"), nullable=False),
        sa.Column("steamid64", sa.String(length=32), nullable=True),
        sa.Column("persona_name", sa.String(length=255), nullable=True),
        sa.Column("profile_url", sa.String(length=255), nullable=True),
        sa.Column("avatar_small", sa.String(length=512), nullable=True),
        sa.Column("avatar_medium", sa.String(length=512), nullable=True),
        sa.Column("avatar_full", sa.String(length=512), nullable=True),
        sa.Column("persona_state", sa.Integer(), nullable=True),
        sa.Column("visibility", sa.String(length=32), server_default="unknown", nullable=False),
        sa.Column("fetch_status", sa.String(length=32), server_default="ok", nullable=False),
        sa.Column("error_message", sa.Text(), nullable=True),
        sa.Column("last_fetched_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )
    op.create_index("ix_steam_profile_cache_account_id", "steam_profile_cache", ["account_id"], unique=True)
    op.create_index("ix_steam_profile_cache_steamid64", "steam_profile_cache", ["steamid64"])
    op.create_index("ix_steam_profile_cache_fetch_status", "steam_profile_cache", ["fetch_status"])

    op.create_table(
        "steam_game_assets",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("app_id", sa.Integer(), nullable=False),
        sa.Column("name", sa.String(length=255), nullable=True),
        sa.Column("header_image_url", sa.String(length=512), nullable=True),
        sa.Column("capsule_image_url", sa.String(length=512), nullable=True),
        sa.Column("library_image_url", sa.String(length=512), nullable=True),
        sa.Column("icon_url", sa.String(length=512), nullable=True),
        sa.Column("store_url", sa.String(length=512), nullable=True),
        sa.Column("source", sa.String(length=40), server_default="steam_cdn", nullable=False),
        sa.Column("last_fetched_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )
    op.create_index("ix_steam_game_assets_app_id", "steam_game_assets", ["app_id"], unique=True)

    op.create_table(
        "steam_owned_games_cache",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("account_id", sa.Integer(), sa.ForeignKey("steam_accounts.id", ondelete="CASCADE"), nullable=False),
        sa.Column("app_id", sa.Integer(), nullable=False),
        sa.Column("name", sa.String(length=255), nullable=True),
        sa.Column("playtime_forever", sa.Integer(), server_default="0", nullable=False),
        sa.Column("img_icon_hash", sa.String(length=120), nullable=True),
        sa.Column("last_fetched_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.UniqueConstraint("account_id", "app_id", name="uq_owned_game_cache"),
    )
    op.create_index("ix_steam_owned_games_cache_account_id", "steam_owned_games_cache", ["account_id"])
    op.create_index("ix_steam_owned_games_cache_app_id", "steam_owned_games_cache", ["app_id"])

    # Index hardening for findings raised in the audit (missing FK/lookup indexes).
    op.create_index("ix_audit_logs_actor_user_id", "audit_logs", ["actor_user_id"])
    op.create_index("ix_audit_logs_target_id", "audit_logs", ["target_id"])
    op.create_index("ix_payments_plan_id", "payments", ["plan_id"])
    op.create_index("ix_subscriptions_plan_id", "subscriptions", ["plan_id"])


def downgrade() -> None:
    op.drop_index("ix_subscriptions_plan_id", table_name="subscriptions")
    op.drop_index("ix_payments_plan_id", table_name="payments")
    op.drop_index("ix_audit_logs_target_id", table_name="audit_logs")
    op.drop_index("ix_audit_logs_actor_user_id", table_name="audit_logs")
    op.drop_index("ix_steam_owned_games_cache_app_id", table_name="steam_owned_games_cache")
    op.drop_index("ix_steam_owned_games_cache_account_id", table_name="steam_owned_games_cache")
    op.drop_table("steam_owned_games_cache")
    op.drop_index("ix_steam_game_assets_app_id", table_name="steam_game_assets")
    op.drop_table("steam_game_assets")
    op.drop_index("ix_steam_profile_cache_fetch_status", table_name="steam_profile_cache")
    op.drop_index("ix_steam_profile_cache_steamid64", table_name="steam_profile_cache")
    op.drop_index("ix_steam_profile_cache_account_id", table_name="steam_profile_cache")
    op.drop_table("steam_profile_cache")
