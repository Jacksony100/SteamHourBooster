"""steam account refresh-token column

Revision ID: 007_steam_refresh_token
Revises: 006_steam_data
Create Date: 2026-06-21
"""

import sqlalchemy as sa
from alembic import op

revision = "007_steam_refresh_token"
down_revision = "006_steam_data"
branch_labels = None
depends_on = None


def upgrade() -> None:
    with op.batch_alter_table("steam_accounts") as batch:
        batch.add_column(sa.Column("steam_refresh_token_encrypted", sa.Text(), nullable=True))


def downgrade() -> None:
    with op.batch_alter_table("steam_accounts") as batch:
        batch.drop_column("steam_refresh_token_encrypted")
