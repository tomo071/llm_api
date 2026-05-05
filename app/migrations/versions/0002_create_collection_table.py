"""create collection table

Revision ID: 0002_create_collection_table
Revises: 0001_create_customer_table
Create Date: 2026-04-25

"""

from __future__ import annotations

from alembic import op
import sqlalchemy as sa


revision = "0002_create_collection_table"
down_revision = "0001_create_customer_table"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "collection",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("customer_id", sa.Integer(), sa.ForeignKey("customer.id", ondelete="RESTRICT"), nullable=False),
        sa.Column("collection_name", sa.String(length=100), nullable=False),
        sa.Column("use_type", sa.Integer(), nullable=False),
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
    op.create_index("ix_collection_customer_id", "collection", ["customer_id"], unique=False)
    op.create_index("ix_collection_collection_name", "collection", ["collection_name"], unique=False)


def downgrade() -> None:
    op.drop_index("ix_collection_collection_name", table_name="collection")
    op.drop_index("ix_collection_customer_id", table_name="collection")
    op.drop_table("collection")
