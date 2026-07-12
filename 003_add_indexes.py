"""Add missing indexes and password_resets constraints

Revision ID: 003_add_indexes
Revises: 002_add_password_resets
Create Date: 2026-07-12

"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa

revision: str = "003_add_indexes"
down_revision: Union[str, None] = "002_add_password_resets"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # --- password_resets: add UNIQUE + indexes ---
    op.create_index("ix_password_resets_token_hash", "password_resets", ["token_hash"], unique=True)
    op.create_index("ix_password_resets_employee_id", "password_resets", ["employee_id"])

    # --- allocations: add indexes on FK columns ---
    op.create_index("ix_allocations_employee_id", "allocations", ["employee_id"])
    op.create_index("ix_allocations_asset_id", "allocations", ["asset_id"])

    # --- notifications: add index on employee_id ---
    op.create_index("ix_notifications_employee_id", "notifications", ["employee_id"])

    # --- activity_logs: add indexes ---
    op.create_index("ix_activity_logs_actor_id", "activity_logs", ["actor_id"])
    op.create_index("ix_activity_logs_created_at", "activity_logs", ["created_at"])

    # --- transfer_requests: add indexes on FK columns ---
    op.create_index("ix_transfer_requests_requested_by", "transfer_requests", ["requested_by"])
    op.create_index("ix_transfer_requests_current_holder_id", "transfer_requests", ["current_holder_id"])

    # --- bookings: add index on booked_by ---
    op.create_index("ix_bookings_booked_by", "bookings", ["booked_by"])

    # --- maintenance_requests: add indexes ---
    op.create_index("ix_maintenance_requests_raised_by", "maintenance_requests", ["raised_by"])
    op.create_index("ix_maintenance_requests_asset_id", "maintenance_requests", ["asset_id"])

    # --- audit_items: add indexes ---
    op.create_index("ix_audit_items_audit_cycle_id", "audit_items", ["audit_cycle_id"])
    op.create_index("ix_audit_items_asset_id", "audit_items", ["asset_id"])


def downgrade() -> None:
    op.drop_index("ix_audit_items_asset_id", "audit_items")
    op.drop_index("ix_audit_items_audit_cycle_id", "audit_items")
    op.drop_index("ix_maintenance_requests_asset_id", "maintenance_requests")
    op.drop_index("ix_maintenance_requests_raised_by", "maintenance_requests")
    op.drop_index("ix_bookings_booked_by", "bookings")
    op.drop_index("ix_transfer_requests_current_holder_id", "transfer_requests")
    op.drop_index("ix_transfer_requests_requested_by", "transfer_requests")
    op.drop_index("ix_activity_logs_created_at", "activity_logs")
    op.drop_index("ix_activity_logs_actor_id", "activity_logs")
    op.drop_index("ix_notifications_employee_id", "notifications")
    op.drop_index("ix_allocations_asset_id", "allocations")
    op.drop_index("ix_allocations_employee_id", "allocations")
    op.drop_index("ix_password_resets_employee_id", "password_resets")
    op.drop_index("ix_password_resets_token_hash", "password_resets")
