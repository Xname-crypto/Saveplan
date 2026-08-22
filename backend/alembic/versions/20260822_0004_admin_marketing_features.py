"""admin marketing features

Revision ID: 20260822_0004
Revises: 20260816_0003
Create Date: 2026-08-22 00:00:00.000000
"""
from __future__ import annotations

from alembic import op
import sqlalchemy as sa

revision = "20260822_0004"
down_revision = "20260816_0003"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "redeem_codes",
        sa.Column("id", sa.String(length=36), primary_key=True),
        sa.Column("code", sa.String(length=48), nullable=False),
        sa.Column("batch_name", sa.String(length=120), nullable=False),
        sa.Column("points", sa.Integer(), nullable=False),
        sa.Column("max_redemptions", sa.Integer(), nullable=False, server_default="1"),
        sa.Column("redeemed_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.text("1")),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("note", sa.String(length=300), nullable=True),
        sa.Column("created_by_admin_id", sa.String(length=36), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["created_by_admin_id"], ["admin_users.id"], ondelete="SET NULL"),
    )
    op.create_index("ix_redeem_codes_batch_name", "redeem_codes", ["batch_name"])
    op.create_index("ix_redeem_codes_code", "redeem_codes", ["code"], unique=True)
    op.create_index("ix_redeem_codes_created_at", "redeem_codes", ["created_at"])
    op.create_index("ix_redeem_codes_created_by_admin_id", "redeem_codes", ["created_by_admin_id"])

    op.create_table(
        "broadcast_messages",
        sa.Column("id", sa.String(length=36), primary_key=True),
        sa.Column("channel", sa.String(length=24), nullable=False),
        sa.Column("scope", sa.String(length=24), nullable=False, server_default="global"),
        sa.Column("target_user_id", sa.String(length=36), nullable=True),
        sa.Column("title", sa.String(length=120), nullable=False),
        sa.Column("content", sa.Text(), nullable=False),
        sa.Column("priority", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.text("1")),
        sa.Column("starts_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("ends_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_by_admin_id", sa.String(length=36), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["target_user_id"], ["users.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["created_by_admin_id"], ["admin_users.id"], ondelete="SET NULL"),
    )
    op.create_index("ix_broadcast_messages_channel", "broadcast_messages", ["channel"])
    op.create_index("ix_broadcast_messages_scope", "broadcast_messages", ["scope"])
    op.create_index("ix_broadcast_messages_created_at", "broadcast_messages", ["created_at"])
    op.create_index("ix_broadcast_messages_created_by_admin_id", "broadcast_messages", ["created_by_admin_id"])
    op.create_index("ix_broadcast_messages_target_user_id", "broadcast_messages", ["target_user_id"])


def downgrade() -> None:
    op.drop_index("ix_broadcast_messages_created_by_admin_id", table_name="broadcast_messages")
    op.drop_index("ix_broadcast_messages_created_at", table_name="broadcast_messages")
    op.drop_index("ix_broadcast_messages_target_user_id", table_name="broadcast_messages")
    op.drop_index("ix_broadcast_messages_scope", table_name="broadcast_messages")
    op.drop_index("ix_broadcast_messages_channel", table_name="broadcast_messages")
    op.drop_table("broadcast_messages")

    op.drop_index("ix_redeem_codes_created_by_admin_id", table_name="redeem_codes")
    op.drop_index("ix_redeem_codes_created_at", table_name="redeem_codes")
    op.drop_index("ix_redeem_codes_code", table_name="redeem_codes")
    op.drop_index("ix_redeem_codes_batch_name", table_name="redeem_codes")
    op.drop_table("redeem_codes")
