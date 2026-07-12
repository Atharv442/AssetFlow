"""Initial schema — all 13 tables for AssetFlow ONE

Revision ID: 001_initial
Revises: None
Create Date: 2026-07-12

"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import JSONB, TSRANGE

revision: str = "001_initial"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Enable btree_gist extension (required for booking exclusion constraint)
    op.execute("CREATE EXTENSION IF NOT EXISTS btree_gist")

    # --- departments ---
    op.create_table(
        "departments",
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column("name", sa.String(100), nullable=False),
        sa.Column("parent_department_id", sa.Integer, sa.ForeignKey("departments.id"), nullable=True),
        sa.Column("head_employee_id", sa.Integer, nullable=True),  # FK added after employees
        sa.Column("status", sa.String(20), server_default="active", nullable=False),
        sa.Column("created_at", sa.DateTime, server_default=sa.func.now()),
    )
    op.execute("""
        ALTER TABLE departments
        ADD CONSTRAINT chk_departments_status CHECK (status IN ('active','inactive'))
    """)

    # --- employees ---
    op.create_table(
        "employees",
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column("name", sa.String(100), nullable=False),
        sa.Column("email", sa.String(150), nullable=False),
        sa.Column("password_hash", sa.Text, nullable=False),
        sa.Column("department_id", sa.Integer, sa.ForeignKey("departments.id"), nullable=True),
        sa.Column("role", sa.String(20), server_default="employee", nullable=False),
        sa.Column("status", sa.String(20), server_default="active", nullable=False),
        sa.Column("created_at", sa.DateTime, server_default=sa.func.now()),
    )
    op.create_index("ix_employees_email", "employees", ["email"], unique=True)
    op.execute("""
        ALTER TABLE employees
        ADD CONSTRAINT chk_employees_role CHECK (role IN ('employee','department_head','asset_manager','admin'))
    """)
    op.execute("""
        ALTER TABLE employees
        ADD CONSTRAINT chk_employees_status CHECK (status IN ('active','inactive'))
    """)

    # Now add FK from departments.head_employee_id -> employees.id
    op.create_foreign_key("fk_head", "departments", "employees", ["head_employee_id"], ["id"])

    # --- asset_categories ---
    op.create_table(
        "asset_categories",
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column("name", sa.String(100), nullable=False),
        sa.Column("custom_fields", JSONB, server_default="{}"),
        sa.Column("created_at", sa.DateTime, server_default=sa.func.now()),
    )

    # --- assets ---
    op.create_table(
        "assets",
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column("asset_tag", sa.String(20), nullable=False),
        sa.Column("name", sa.String(150), nullable=False),
        sa.Column("category_id", sa.Integer, sa.ForeignKey("asset_categories.id"), nullable=True),
        sa.Column("serial_number", sa.String(100), nullable=True),
        sa.Column("acquisition_date", sa.Date, nullable=True),
        sa.Column("acquisition_cost", sa.Numeric(12, 2), nullable=True),
        sa.Column("condition", sa.String(30), nullable=True),
        sa.Column("location", sa.String(150), nullable=True),
        sa.Column("photo_url", sa.Text, nullable=True),
        sa.Column("documents", JSONB, server_default="[]"),
        sa.Column("is_bookable", sa.Boolean, server_default="false"),
        sa.Column("status", sa.String(20), server_default="available", nullable=False),
        sa.Column("created_at", sa.DateTime, server_default=sa.func.now()),
    )
    op.create_index("ix_assets_asset_tag", "assets", ["asset_tag"], unique=True)
    op.execute("""
        ALTER TABLE assets
        ADD CONSTRAINT chk_assets_status CHECK (
            status IN ('available','allocated','reserved','under_maintenance','lost','retired','disposed')
        )
    """)

    # --- allocations ---
    op.create_table(
        "allocations",
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column("asset_id", sa.Integer, sa.ForeignKey("assets.id"), nullable=False),
        sa.Column("employee_id", sa.Integer, sa.ForeignKey("employees.id"), nullable=False),
        sa.Column("department_id", sa.Integer, sa.ForeignKey("departments.id"), nullable=True),
        sa.Column("allocated_at", sa.DateTime, server_default=sa.func.now()),
        sa.Column("expected_return_date", sa.Date, nullable=True),
        sa.Column("returned_at", sa.DateTime, nullable=True),
        sa.Column("return_condition_notes", sa.Text, nullable=True),
        sa.Column("is_active", sa.Boolean, server_default="true"),
    )
    # Partial unique index: only one active allocation per asset
    op.execute("""
        CREATE UNIQUE INDEX one_active_allocation_per_asset
        ON allocations (asset_id) WHERE is_active = true
    """)

    # --- transfer_requests ---
    op.create_table(
        "transfer_requests",
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column("asset_id", sa.Integer, sa.ForeignKey("assets.id"), nullable=False),
        sa.Column("requested_by", sa.Integer, sa.ForeignKey("employees.id"), nullable=False),
        sa.Column("current_holder_id", sa.Integer, sa.ForeignKey("employees.id"), nullable=False),
        sa.Column("status", sa.String(20), server_default="requested", nullable=False),
        sa.Column("approved_by", sa.Integer, sa.ForeignKey("employees.id"), nullable=True),
        sa.Column("created_at", sa.DateTime, server_default=sa.func.now()),
        sa.Column("resolved_at", sa.DateTime, nullable=True),
    )
    op.execute("""
        ALTER TABLE transfer_requests
        ADD CONSTRAINT chk_transfer_status CHECK (status IN ('requested','approved','rejected','reallocated'))
    """)

    # --- bookings ---
    op.create_table(
        "bookings",
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column("asset_id", sa.Integer, sa.ForeignKey("assets.id"), nullable=False),
        sa.Column("booked_by", sa.Integer, sa.ForeignKey("employees.id"), nullable=False),
        sa.Column("slot", TSRANGE, nullable=False),
        sa.Column("status", sa.String(20), server_default="upcoming", nullable=False),
        sa.Column("purpose", sa.Text, nullable=True),
        sa.Column("created_at", sa.DateTime, server_default=sa.func.now()),
    )
    op.execute("""
        ALTER TABLE bookings
        ADD CONSTRAINT chk_bookings_status CHECK (status IN ('upcoming','ongoing','completed','cancelled'))
    """)
    # Exclusion constraint: prevent overlapping non-cancelled bookings for same asset
    op.execute("""
        ALTER TABLE bookings
        ADD CONSTRAINT no_overlapping_bookings
        EXCLUDE USING gist (asset_id WITH =, slot WITH &&) WHERE (status != 'cancelled')
    """)

    # --- maintenance_requests ---
    op.create_table(
        "maintenance_requests",
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column("asset_id", sa.Integer, sa.ForeignKey("assets.id"), nullable=False),
        sa.Column("raised_by", sa.Integer, sa.ForeignKey("employees.id"), nullable=False),
        sa.Column("issue_description", sa.Text, nullable=True),
        sa.Column("priority", sa.String(20), nullable=True),
        sa.Column("photo_url", sa.Text, nullable=True),
        sa.Column("status", sa.String(30), server_default="pending", nullable=False),
        sa.Column("approved_by", sa.Integer, sa.ForeignKey("employees.id"), nullable=True),
        sa.Column("technician_name", sa.String(100), nullable=True),
        sa.Column("created_at", sa.DateTime, server_default=sa.func.now()),
        sa.Column("resolved_at", sa.DateTime, nullable=True),
    )
    op.execute("""
        ALTER TABLE maintenance_requests
        ADD CONSTRAINT chk_maintenance_priority CHECK (priority IN ('low','medium','high','critical'))
    """)
    op.execute("""
        ALTER TABLE maintenance_requests
        ADD CONSTRAINT chk_maintenance_status CHECK (
            status IN ('pending','approved','rejected','technician_assigned','in_progress','resolved')
        )
    """)

    # --- audit_cycles ---
    op.create_table(
        "audit_cycles",
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column("scope_department_id", sa.Integer, sa.ForeignKey("departments.id"), nullable=True),
        sa.Column("scope_location", sa.String(150), nullable=True),
        sa.Column("start_date", sa.Date, nullable=True),
        sa.Column("end_date", sa.Date, nullable=True),
        sa.Column("status", sa.String(20), server_default="open", nullable=False),
        sa.Column("created_by", sa.Integer, sa.ForeignKey("employees.id"), nullable=False),
        sa.Column("closed_at", sa.DateTime, nullable=True),
    )
    op.execute("""
        ALTER TABLE audit_cycles
        ADD CONSTRAINT chk_audit_cycle_status CHECK (status IN ('open','closed'))
    """)

    # --- audit_cycle_auditors ---
    op.create_table(
        "audit_cycle_auditors",
        sa.Column("audit_cycle_id", sa.Integer, sa.ForeignKey("audit_cycles.id"), primary_key=True),
        sa.Column("auditor_id", sa.Integer, sa.ForeignKey("employees.id"), primary_key=True),
    )

    # --- audit_items ---
    op.create_table(
        "audit_items",
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column("audit_cycle_id", sa.Integer, sa.ForeignKey("audit_cycles.id"), nullable=False),
        sa.Column("asset_id", sa.Integer, sa.ForeignKey("assets.id"), nullable=False),
        sa.Column("result", sa.String(20), server_default="pending", nullable=False),
        sa.Column("note", sa.Text, nullable=True),
        sa.Column("checked_by", sa.Integer, sa.ForeignKey("employees.id"), nullable=True),
        sa.Column("checked_at", sa.DateTime, nullable=True),
    )
    op.execute("""
        ALTER TABLE audit_items
        ADD CONSTRAINT chk_audit_item_result CHECK (result IN ('pending','verified','missing','damaged'))
    """)

    # --- notifications ---
    op.create_table(
        "notifications",
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column("employee_id", sa.Integer, sa.ForeignKey("employees.id"), nullable=False),
        sa.Column("type", sa.String(50), nullable=True),
        sa.Column("message", sa.Text, nullable=True),
        sa.Column("is_read", sa.Boolean, server_default="false"),
        sa.Column("created_at", sa.DateTime, server_default=sa.func.now()),
    )

    # --- activity_logs ---
    op.create_table(
        "activity_logs",
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column("actor_id", sa.Integer, sa.ForeignKey("employees.id"), nullable=False),
        sa.Column("action", sa.String(100), nullable=False),
        sa.Column("entity_type", sa.String(50), nullable=True),
        sa.Column("entity_id", sa.Integer, nullable=True),
        sa.Column("created_at", sa.DateTime, server_default=sa.func.now()),
    )


def downgrade() -> None:
    op.drop_table("activity_logs")
    op.drop_table("notifications")
    op.drop_table("audit_items")
    op.drop_table("audit_cycle_auditors")
    op.drop_table("audit_cycles")
    op.drop_table("maintenance_requests")
    op.drop_table("bookings")
    op.drop_table("transfer_requests")
    op.execute("DROP INDEX IF EXISTS one_active_allocation_per_asset")
    op.drop_table("allocations")
    op.drop_table("assets")
    op.drop_table("asset_categories")
    op.drop_constraint("fk_head", "departments", type_="foreignkey")
    op.drop_table("employees")
    op.drop_table("departments")
    op.execute("DROP EXTENSION IF EXISTS btree_gist")
