"""create customer table

Revision ID: 0001_create_customer_table
Revises:
Create Date: 2026-04-25

"""

from __future__ import annotations

from alembic import op
import sqlalchemy as sa


revision = "0001_create_customer_table"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "customer",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("customer_id", sa.String(length=255), nullable=False),
        sa.Column("total_use_token", sa.Integer(), nullable=True),
        sa.Column("monthly_use_token", sa.Integer(), nullable=True),
        sa.Column("daily_use_token", sa.Integer(), nullable=True),
        sa.Column("delete_flag", sa.Boolean(), nullable=False, server_default=sa.text("false")),
        sa.Column("deleted_at", sa.DateTime(), nullable=True),
        sa.Column(
            "updated_at",
            sa.DateTime(),
            nullable=False,
            server_default=sa.text("CURRENT_TIMESTAMP"),
            server_onupdate=sa.text("CURRENT_TIMESTAMP"),
        ),
        sa.Column(
            "created_at",
            sa.DateTime(),
            nullable=False,
            server_default=sa.text("CURRENT_TIMESTAMP"),
        ),
        mysql_charset="utf8mb4",
    )
    op.create_index("ix_customer_customer_id", "customer", ["customer_id"], unique=False)


def downgrade() -> None:
    op.drop_index("ix_customer_customer_id", table_name="customer")
    op.drop_table("customer")
