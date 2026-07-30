"""admin rbac postgres foundation

Revision ID: 20260731_0001
Revises:
Create Date: 2026-07-31 00:00:00.000000
"""
from __future__ import annotations

from alembic import op
import sqlalchemy as sa

revision = "20260731_0001"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "users",
        sa.Column("id", sa.String(length=36), primary_key=True),
        sa.Column("email", sa.String(length=254), nullable=False),
        sa.Column("password_hash", sa.String(length=128), nullable=False),
        sa.Column("password_salt", sa.String(length=64), nullable=False),
        sa.Column("username", sa.String(length=80), nullable=False),
        sa.Column("job", sa.String(length=120), nullable=True),
        sa.Column("bio", sa.Text(), nullable=True),
        sa.Column("interests", sa.JSON(), nullable=False),
        sa.Column("avatar_name", sa.String(length=255), nullable=True),
        sa.Column("token_version", sa.Integer(), nullable=False),
        sa.Column("point_balance", sa.Integer(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index("ix_users_email", "users", ["email"], unique=True)

    op.create_table(
        "admin_users",
        sa.Column("id", sa.String(length=36), primary_key=True),
        sa.Column("email", sa.String(length=254), nullable=False),
        sa.Column("username", sa.String(length=80), nullable=False),
        sa.Column("password_hash", sa.String(length=128), nullable=False),
        sa.Column("password_salt", sa.String(length=64), nullable=False),
        sa.Column("token_version", sa.Integer(), nullable=False),
        sa.Column("is_active", sa.Boolean(), nullable=False),
        sa.Column("last_login_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index("ix_admin_users_email", "admin_users", ["email"], unique=True)

    op.create_table(
        "permissions",
        sa.Column("id", sa.String(length=36), primary_key=True),
        sa.Column("code", sa.String(length=120), nullable=False),
        sa.Column("name", sa.String(length=120), nullable=False),
        sa.Column("group", sa.String(length=80), nullable=False),
        sa.Column("description", sa.String(length=500), nullable=True),
        sa.Column("is_active", sa.Boolean(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index("ix_permissions_code", "permissions", ["code"], unique=True)
    op.create_index("ix_permissions_group", "permissions", ["group"])

    op.create_table(
        "roles",
        sa.Column("id", sa.String(length=36), primary_key=True),
        sa.Column("code", sa.String(length=80), nullable=False),
        sa.Column("name", sa.String(length=120), nullable=False),
        sa.Column("description", sa.String(length=500), nullable=True),
        sa.Column("is_active", sa.Boolean(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index("ix_roles_code", "roles", ["code"], unique=True)

    op.create_table(
        "admin_user_roles",
        sa.Column("admin_user_id", sa.String(length=36), nullable=False),
        sa.Column("role_id", sa.String(length=36), nullable=False),
        sa.ForeignKeyConstraint(["admin_user_id"], ["admin_users.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["role_id"], ["roles.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("admin_user_id", "role_id"),
    )

    op.create_table(
        "role_permissions",
        sa.Column("role_id", sa.String(length=36), nullable=False),
        sa.Column("permission_id", sa.String(length=36), nullable=False),
        sa.ForeignKeyConstraint(["permission_id"], ["permissions.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["role_id"], ["roles.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("role_id", "permission_id"),
    )

    op.create_table(
        "conversions",
        sa.Column("id", sa.String(length=36), primary_key=True),
        sa.Column("user_id", sa.String(length=36), nullable=False),
        sa.Column("filename", sa.String(length=255), nullable=False),
        sa.Column("stored_path", sa.Text(), nullable=True),
        sa.Column("source_type", sa.String(length=40), nullable=False),
        sa.Column("subject", sa.String(length=40), nullable=False),
        sa.Column("raw_text", sa.Text(), nullable=False),
        sa.Column("text_state", sa.String(length=40), nullable=False),
        sa.Column("status", sa.String(length=40), nullable=False),
        sa.Column("questions_json", sa.JSON(), nullable=False),
        sa.Column("issues_json", sa.JSON(), nullable=False),
        sa.Column("assets_json", sa.JSON(), nullable=False),
        sa.Column("export_text", sa.Text(), nullable=True),
        sa.Column("ocr_provider", sa.String(length=80), nullable=True),
        sa.Column("ocr_provider_job_id", sa.String(length=160), nullable=True),
        sa.Column("ocr_state", sa.String(length=40), nullable=True),
        sa.Column("ocr_total_pages", sa.Integer(), nullable=False),
        sa.Column("ocr_extracted_pages", sa.Integer(), nullable=False),
        sa.Column("ocr_result_url", sa.Text(), nullable=True),
        sa.Column("ocr_error", sa.Text(), nullable=True),
        sa.Column("points_charged", sa.Integer(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
    )
    op.create_index("ix_conversions_created_at", "conversions", ["created_at"])
    op.create_index("ix_conversions_ocr_provider_job_id", "conversions", ["ocr_provider_job_id"])
    op.create_index("ix_conversions_ocr_state", "conversions", ["ocr_state"])
    op.create_index("ix_conversions_source_type", "conversions", ["source_type"])
    op.create_index("ix_conversions_status", "conversions", ["status"])
    op.create_index("ix_conversions_user_id", "conversions", ["user_id"])

    op.create_table(
        "point_transactions",
        sa.Column("id", sa.String(length=36), primary_key=True),
        sa.Column("user_id", sa.String(length=36), nullable=False),
        sa.Column("amount", sa.Integer(), nullable=False),
        sa.Column("balance_after", sa.Integer(), nullable=False),
        sa.Column("reason", sa.String(length=300), nullable=False),
        sa.Column("source", sa.String(length=80), nullable=False),
        sa.Column("admin_id", sa.String(length=36), nullable=True),
        sa.Column("conversion_id", sa.String(length=36), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
    )
    op.create_index("ix_point_transactions_admin_id", "point_transactions", ["admin_id"])
    op.create_index("ix_point_transactions_conversion_id", "point_transactions", ["conversion_id"])
    op.create_index("ix_point_transactions_created_at", "point_transactions", ["created_at"])
    op.create_index("ix_point_transactions_source", "point_transactions", ["source"])
    op.create_index("ix_point_transactions_user_id", "point_transactions", ["user_id"])

    op.create_table(
        "audit_logs",
        sa.Column("id", sa.String(length=36), primary_key=True),
        sa.Column("admin_id", sa.String(length=36), nullable=True),
        sa.Column("action", sa.String(length=120), nullable=False),
        sa.Column("resource", sa.String(length=160), nullable=False),
        sa.Column("detail", sa.JSON(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index("ix_audit_logs_action", "audit_logs", ["action"])
    op.create_index("ix_audit_logs_admin_id", "audit_logs", ["admin_id"])
    op.create_index("ix_audit_logs_created_at", "audit_logs", ["created_at"])
    op.create_index("ix_audit_logs_resource", "audit_logs", ["resource"])


def downgrade() -> None:
    op.drop_index("ix_audit_logs_resource", table_name="audit_logs")
    op.drop_index("ix_audit_logs_created_at", table_name="audit_logs")
    op.drop_index("ix_audit_logs_admin_id", table_name="audit_logs")
    op.drop_index("ix_audit_logs_action", table_name="audit_logs")
    op.drop_table("audit_logs")

    op.drop_index("ix_point_transactions_user_id", table_name="point_transactions")
    op.drop_index("ix_point_transactions_source", table_name="point_transactions")
    op.drop_index("ix_point_transactions_created_at", table_name="point_transactions")
    op.drop_index("ix_point_transactions_conversion_id", table_name="point_transactions")
    op.drop_index("ix_point_transactions_admin_id", table_name="point_transactions")
    op.drop_table("point_transactions")

    op.drop_index("ix_conversions_user_id", table_name="conversions")
    op.drop_index("ix_conversions_status", table_name="conversions")
    op.drop_index("ix_conversions_source_type", table_name="conversions")
    op.drop_index("ix_conversions_ocr_state", table_name="conversions")
    op.drop_index("ix_conversions_ocr_provider_job_id", table_name="conversions")
    op.drop_index("ix_conversions_created_at", table_name="conversions")
    op.drop_table("conversions")

    op.drop_table("role_permissions")
    op.drop_table("admin_user_roles")
    op.drop_index("ix_roles_code", table_name="roles")
    op.drop_table("roles")
    op.drop_index("ix_permissions_group", table_name="permissions")
    op.drop_index("ix_permissions_code", table_name="permissions")
    op.drop_table("permissions")
    op.drop_index("ix_admin_users_email", table_name="admin_users")
    op.drop_table("admin_users")
    op.drop_index("ix_users_email", table_name="users")
    op.drop_table("users")
