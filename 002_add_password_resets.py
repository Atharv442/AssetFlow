"""Add password_resets table

Revision ID: 002_add_password_resets
Revises: 001_initial
Create Date: 2026-07-12

"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa

revision: str = "002_add_password_resets"
down_revision: Union[str, None] = "001_initial"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "password_resets",
        sa.Column("id", sa.Integer, primary_key=True, index=True),
        sa.Column("employee_id", sa.Integer, sa.ForeignKey("employees.id"), nullable=False),
        sa.Column("token_hash", sa.Text, nullable=False),
        sa.Column("expires_at", sa.DateTime, nullable=False),
        sa.Column("used", sa.Boolean, server_default="false", nullable=False),
    )


def downgrade() -> None:
    op.drop_table("password_resets")
