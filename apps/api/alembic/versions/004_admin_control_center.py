"""admin control center fields

Revision ID: 004_admin_control_center
Revises: 003_session_manager
Create Date: 2026-06-14
"""

import sqlalchemy as sa
from alembic import op

revision = "004_admin_control_center"
down_revision = "003_session_manager"
branch_labels = None
depends_on = None


def upgrade() -> None:
    with op.batch_alter_table("users") as batch:
        batch.add_column(sa.Column("last_ip", sa.String(length=80), nullable=True))


def downgrade() -> None:
    with op.batch_alter_table("users") as batch:
        batch.drop_column("last_ip")
