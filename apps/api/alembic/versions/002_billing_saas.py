"""billing SaaS tables and plan limits

Revision ID: 002_billing_saas
Revises: 001_initial
Create Date: 2026-06-14
"""

import sqlalchemy as sa
from alembic import op

revision = "002_billing_saas"
down_revision = "001_initial"
branch_labels = None
depends_on = None


def upgrade() -> None:
    with op.batch_alter_table("plans") as batch:
        batch.add_column(sa.Column("duration_days", sa.Integer(), nullable=True))
        batch.add_column(sa.Column("account_limit", sa.Integer(), nullable=False, server_default="1"))
        batch.add_column(sa.Column("active_session_limit", sa.Integer(), nullable=False, server_default="1"))
        batch.add_column(sa.Column("support_level", sa.String(length=80), nullable=False, server_default="community"))
        batch.add_column(sa.Column("features_json", sa.Text(), nullable=False, server_default="[]"))

    op.execute("UPDATE plans SET duration_days = interval_days WHERE duration_days IS NULL")

    with op.batch_alter_table("subscriptions") as batch:
        batch.add_column(sa.Column("plan_id", sa.Integer(), nullable=True))
        batch.add_column(sa.Column("starts_at", sa.DateTime(timezone=True), nullable=True))
        batch.add_column(sa.Column("expires_at", sa.DateTime(timezone=True), nullable=True))
        batch.add_column(sa.Column("canceled_at", sa.DateTime(timezone=True), nullable=True))
        batch.add_column(sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False))
        batch.add_column(sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False))
        batch.create_foreign_key("fk_subscriptions_plan_id_plans", "plans", ["plan_id"], ["id"], ondelete="SET NULL")

    op.execute("UPDATE subscriptions SET expires_at = ends_at WHERE expires_at IS NULL")

    op.create_table(
        "payments",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("user_id", sa.Integer(), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
        sa.Column("plan_id", sa.Integer(), sa.ForeignKey("plans.id", ondelete="SET NULL"), nullable=True),
        sa.Column("provider", sa.String(length=40), nullable=False),
        sa.Column("provider_payment_id", sa.String(length=160), nullable=True),
        sa.Column("idempotency_key", sa.String(length=160), nullable=False, unique=True),
        sa.Column("checkout_url", sa.Text(), nullable=True),
        sa.Column("status", sa.String(length=40), nullable=False),
        sa.Column("amount_cents", sa.Integer(), nullable=False),
        sa.Column("currency", sa.String(length=12), nullable=False),
        sa.Column("metadata_json", sa.Text(), nullable=False, server_default="{}"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )
    op.create_index("ix_payments_user_id", "payments", ["user_id"])
    op.create_index("ix_payments_provider", "payments", ["provider"])
    op.create_index("ix_payments_provider_payment_id", "payments", ["provider_payment_id"])
    op.create_index("ix_payments_idempotency_key", "payments", ["idempotency_key"], unique=True)
    op.create_index("ix_payments_status", "payments", ["status"])

    op.create_table(
        "billing_events",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("payment_id", sa.Integer(), sa.ForeignKey("payments.id", ondelete="SET NULL"), nullable=True),
        sa.Column("provider", sa.String(length=40), nullable=False),
        sa.Column("event_type", sa.String(length=120), nullable=False),
        sa.Column("idempotency_key", sa.String(length=160), nullable=False, unique=True),
        sa.Column("verified", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("payload_json", sa.Text(), nullable=False, server_default="{}"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )
    op.create_index("ix_billing_events_payment_id", "billing_events", ["payment_id"])
    op.create_index("ix_billing_events_provider", "billing_events", ["provider"])
    op.create_index("ix_billing_events_event_type", "billing_events", ["event_type"])
    op.create_index("ix_billing_events_idempotency_key", "billing_events", ["idempotency_key"], unique=True)


def downgrade() -> None:
    op.drop_table("billing_events")
    op.drop_table("payments")

    with op.batch_alter_table("subscriptions") as batch:
        batch.drop_constraint("fk_subscriptions_plan_id_plans", type_="foreignkey")
        batch.drop_column("updated_at")
        batch.drop_column("created_at")
        batch.drop_column("canceled_at")
        batch.drop_column("expires_at")
        batch.drop_column("starts_at")
        batch.drop_column("plan_id")

    with op.batch_alter_table("plans") as batch:
        batch.drop_column("features_json")
        batch.drop_column("support_level")
        batch.drop_column("active_session_limit")
        batch.drop_column("account_limit")
        batch.drop_column("duration_days")
