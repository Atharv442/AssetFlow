"""
Seed script for AssetFlow ONE — realistic demo data.

Creates:
  - 3 departments (Engineering, Operations, Marketing)
  - 8 employees across all 4 roles
  - 5 asset categories
  - 15+ assets
  - Pre-existing allocations (5 active) to demonstrate conflict
  - Pre-existing booking on a bookable asset for today
  - 1 pending + 1 resolved maintenance request
  - 1 open audit cycle with items
  - Sample notifications and activity logs

Usage:
  python seed.py
"""

import sys
import os
from datetime import date, datetime, timedelta, timezone

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app.database import SessionLocal, engine
from app.models import (
    Department, Employee, AssetCategory, Asset, Allocation,
    Booking, MaintenanceRequest, AuditCycle, AuditCycleAuditor,
    AuditItem, Notification, ActivityLog,
)
from app.services.auth_service import hash_password


def seed():
    db = SessionLocal()

    try:
        # Check if already seeded
        if db.query(Employee).first():
            print("[Seed] Database already has data. Skipping seed.")
            print("[Seed] To re-seed, drop all tables first: alembic downgrade base && alembic upgrade head")
            return

        print("[Seed] Starting database seed...")

        # --- Departments ----------------------------------------------
        dept_eng = Department(name="Engineering", status="active")
        dept_ops = Department(name="Operations", status="active")
        dept_mkt = Department(name="Marketing", status="active")
        db.add_all([dept_eng, dept_ops, dept_mkt])
        db.flush()
        print(f"  [OK] 3 departments created")

        # --- Employees (8 across all roles) ---------------------------
        # Password for all seed users: "password123"
        pw = hash_password("password123")

        emp_admin = Employee(
            name="Arjun Mehta", email="admin@assetflow.dev",
            password_hash=pw, department_id=dept_eng.id, role="admin",
        )
        emp_asset_mgr = Employee(
            name="Priya Sharma", email="priya@assetflow.dev",
            password_hash=pw, department_id=dept_ops.id, role="asset_manager",
        )
        emp_head_eng = Employee(
            name="Rahul Verma", email="rahul@assetflow.dev",
            password_hash=pw, department_id=dept_eng.id, role="department_head",
        )
        emp_head_ops = Employee(
            name="Sneha Patel", email="sneha@assetflow.dev",
            password_hash=pw, department_id=dept_ops.id, role="department_head",
        )
        emp1 = Employee(
            name="Vikram Singh", email="vikram@assetflow.dev",
            password_hash=pw, department_id=dept_eng.id, role="employee",
        )
        emp2 = Employee(
            name="Ananya Rao", email="ananya@assetflow.dev",
            password_hash=pw, department_id=dept_eng.id, role="employee",
        )
        emp3 = Employee(
            name="Kiran Desai", email="kiran@assetflow.dev",
            password_hash=pw, department_id=dept_ops.id, role="employee",
        )
        emp4 = Employee(
            name="Meera Nair", email="meera@assetflow.dev",
            password_hash=pw, department_id=dept_mkt.id, role="employee",
        )

        all_employees = [emp_admin, emp_asset_mgr, emp_head_eng, emp_head_ops, emp1, emp2, emp3, emp4]
        db.add_all(all_employees)
        db.flush()
        print(f"  [OK] 8 employees created (password: password123)")

        # Set department heads
        dept_eng.head_employee_id = emp_head_eng.id
        dept_ops.head_employee_id = emp_head_ops.id
        db.flush()

        # --- Asset Categories -----------------------------------------
        cat_laptop = AssetCategory(
            name="Laptops",
            custom_fields={"warranty_period_months": "number", "processor": "text"},
        )
        cat_monitor = AssetCategory(
            name="Monitors",
            custom_fields={"screen_size": "number", "resolution": "text"},
        )
        cat_projector = AssetCategory(
            name="Projectors",
            custom_fields={"lumens": "number", "type": "text"},
        )
        cat_furniture = AssetCategory(
            name="Furniture",
            custom_fields={"material": "text", "color": "text"},
        )
        cat_vehicle = AssetCategory(
            name="Vehicles",
            custom_fields={"make": "text", "fuel_type": "text", "mileage_km": "number"},
        )
        db.add_all([cat_laptop, cat_monitor, cat_projector, cat_furniture, cat_vehicle])
        db.flush()
        print(f"  [OK] 5 asset categories created")

        # --- Assets (15+) ---------------------------------------------
        assets_data = [
            # Laptops
            Asset(asset_tag="AF-0001", name="MacBook Pro 14 M3", category_id=cat_laptop.id,
                  serial_number="MBP14-2024-001", acquisition_date=date(2024, 3, 15),
                  acquisition_cost=189999, condition="Excellent", location="Building A, Floor 2"),
            Asset(asset_tag="AF-0002", name="ThinkPad X1 Carbon Gen 11", category_id=cat_laptop.id,
                  serial_number="TPX1-2024-002", acquisition_date=date(2024, 5, 20),
                  acquisition_cost=145000, condition="Good", location="Building A, Floor 2"),
            Asset(asset_tag="AF-0003", name="Dell XPS 15 9530", category_id=cat_laptop.id,
                  serial_number="DXPS-2024-003", acquisition_date=date(2024, 1, 10),
                  acquisition_cost=165000, condition="Good", location="Building B, Floor 1"),
            Asset(asset_tag="AF-0004", name="HP EliteBook 840 G10", category_id=cat_laptop.id,
                  serial_number="HPEB-2023-004", acquisition_date=date(2023, 8, 1),
                  acquisition_cost=112000, condition="Fair", location="Building A, Floor 3"),
            Asset(asset_tag="AF-0005", name="MacBook Air M2", category_id=cat_laptop.id,
                  serial_number="MBA2-2024-005", acquisition_date=date(2024, 6, 1),
                  acquisition_cost=99999, condition="Excellent", location="Building B, Floor 2"),
            # Monitors
            Asset(asset_tag="AF-0006", name="Dell UltraSharp U2723QE 27\"", category_id=cat_monitor.id,
                  serial_number="DU27-2024-006", acquisition_date=date(2024, 2, 1),
                  acquisition_cost=45000, condition="Excellent", location="Building A, Floor 2"),
            Asset(asset_tag="AF-0007", name="LG 32UN880-B 32\" 4K", category_id=cat_monitor.id,
                  serial_number="LG32-2024-007", acquisition_date=date(2024, 2, 1),
                  acquisition_cost=52000, condition="Good", location="Building A, Floor 2"),
            Asset(asset_tag="AF-0008", name="Samsung Odyssey G7 27\"", category_id=cat_monitor.id,
                  serial_number="SOG7-2023-008", acquisition_date=date(2023, 11, 15),
                  acquisition_cost=38000, condition="Good", location="Building B, Floor 1"),
            # Projectors (bookable)
            Asset(asset_tag="AF-0009", name="Epson EB-L200F Laser Projector", category_id=cat_projector.id,
                  serial_number="EPSL-2024-009", acquisition_date=date(2024, 1, 20),
                  acquisition_cost=175000, condition="Excellent", location="Conference Room A",
                  is_bookable=True),
            Asset(asset_tag="AF-0010", name="BenQ MH733 Full HD Projector", category_id=cat_projector.id,
                  serial_number="BQMH-2023-010", acquisition_date=date(2023, 6, 10),
                  acquisition_cost=85000, condition="Good", location="Conference Room B",
                  is_bookable=True),
            # Furniture
            Asset(asset_tag="AF-0011", name="Herman Miller Aeron Chair", category_id=cat_furniture.id,
                  serial_number="HMA-2024-011", acquisition_date=date(2024, 4, 1),
                  acquisition_cost=95000, condition="Excellent", location="Building A, Floor 2"),
            Asset(asset_tag="AF-0012", name="Standing Desk - FlexiSpot E7", category_id=cat_furniture.id,
                  serial_number="FXE7-2024-012", acquisition_date=date(2024, 4, 1),
                  acquisition_cost=42000, condition="Good", location="Building A, Floor 2"),
            Asset(asset_tag="AF-0013", name="Meeting Table - 8 Seater", category_id=cat_furniture.id,
                  serial_number="MT8S-2022-013", acquisition_date=date(2022, 1, 15),
                  acquisition_cost=65000, condition="Good", location="Conference Room A",
                  is_bookable=True),
            # Vehicles
            Asset(asset_tag="AF-0014", name="Toyota Innova Crysta", category_id=cat_vehicle.id,
                  serial_number="TIC-2023-014", acquisition_date=date(2023, 3, 1),
                  acquisition_cost=2050000, condition="Good", location="Parking Lot A",
                  is_bookable=True),
            Asset(asset_tag="AF-0015", name="Maruti Suzuki Ertiga", category_id=cat_vehicle.id,
                  serial_number="MSE-2024-015", acquisition_date=date(2024, 1, 15),
                  acquisition_cost=1200000, condition="Excellent", location="Parking Lot A",
                  is_bookable=True),
            Asset(asset_tag="AF-0016", name="Dell Latitude 5540", category_id=cat_laptop.id,
                  serial_number="DL55-2024-016", acquisition_date=date(2024, 7, 1),
                  acquisition_cost=98000, condition="Excellent", location="Building A, Floor 1"),
        ]

        db.add_all(assets_data)
        db.flush()
        print(f"  [OK] {len(assets_data)} assets created")

        # --- Active Allocations (5 — to demonstrate conflict) ---------
        alloc1 = Allocation(
            asset_id=assets_data[0].id, employee_id=emp1.id,
            department_id=dept_eng.id, expected_return_date=date.today() + timedelta(days=30),
            is_active=True,
        )
        alloc2 = Allocation(
            asset_id=assets_data[1].id, employee_id=emp2.id,
            department_id=dept_eng.id, expected_return_date=date.today() + timedelta(days=60),
            is_active=True,
        )
        alloc3 = Allocation(
            asset_id=assets_data[2].id, employee_id=emp3.id,
            department_id=dept_ops.id, expected_return_date=date.today() + timedelta(days=15),
            is_active=True,
        )
        alloc4 = Allocation(
            asset_id=assets_data[5].id, employee_id=emp1.id,
            department_id=dept_eng.id, is_active=True,
        )
        alloc5 = Allocation(
            asset_id=assets_data[10].id, employee_id=emp_head_eng.id,
            department_id=dept_eng.id, is_active=True,
        )

        # Update asset statuses
        assets_data[0].status = "allocated"
        assets_data[1].status = "allocated"
        assets_data[2].status = "allocated"
        assets_data[5].status = "allocated"
        assets_data[10].status = "allocated"

        # Historical allocation (returned)
        alloc_hist = Allocation(
            asset_id=assets_data[3].id, employee_id=emp4.id,
            department_id=dept_mkt.id,
            allocated_at=datetime(2024, 1, 15, tzinfo=timezone.utc),
            returned_at=datetime(2024, 6, 15, tzinfo=timezone.utc),
            return_condition_notes="Minor scratch on lid",
            is_active=False,
        )

        db.add_all([alloc1, alloc2, alloc3, alloc4, alloc5, alloc_hist])
        db.flush()
        print(f"  [OK] 5 active allocations + 1 historical")

        # --- Booking (on bookable asset, today — to demonstrate overlap) --
        today = date.today()
        booking_start = datetime(today.year, today.month, today.day, 10, 0)
        booking_end = datetime(today.year, today.month, today.day, 12, 0)
        booking1 = Booking(
            asset_id=assets_data[8].id,  # Epson projector
            booked_by=emp1.id,
            slot=f"[{booking_start.isoformat()}, {booking_end.isoformat()})",
            status="upcoming",
            purpose="Sprint demo presentation",
        )

        afternoon_start = datetime(today.year, today.month, today.day, 14, 0)
        afternoon_end = datetime(today.year, today.month, today.day, 16, 0)
        booking2 = Booking(
            asset_id=assets_data[9].id,  # BenQ projector
            booked_by=emp3.id,
            slot=f"[{afternoon_start.isoformat()}, {afternoon_end.isoformat()})",
            status="upcoming",
            purpose="Client presentation",
        )

        db.add_all([booking1, booking2])
        db.flush()
        print(f"  [OK] 2 bookings created (today, to test overlap)")

        # --- Maintenance Requests -------------------------------------
        maint_pending = MaintenanceRequest(
            asset_id=assets_data[3].id,  # HP EliteBook
            raised_by=emp4.id,
            issue_description="Keyboard keys sticking, trackpad intermittently unresponsive",
            priority="medium",
            status="pending",
        )
        maint_resolved = MaintenanceRequest(
            asset_id=assets_data[7].id,  # Samsung monitor
            raised_by=emp2.id,
            issue_description="Screen flickering at 144Hz, works fine at 60Hz",
            priority="low",
            status="resolved",
            approved_by=emp_asset_mgr.id,
            technician_name="Rajesh Kumar",
            resolved_at=datetime(2024, 6, 20, tzinfo=timezone.utc),
        )
        db.add_all([maint_pending, maint_resolved])
        db.flush()
        print(f"  [OK] 2 maintenance requests (1 pending, 1 resolved)")

        # --- Audit Cycle ----------------------------------------------
        audit_cycle = AuditCycle(
            scope_department_id=dept_eng.id,
            scope_location="Building A",
            start_date=today - timedelta(days=2),
            end_date=today + timedelta(days=5),
            created_by=emp_admin.id,
            status="open",
        )
        db.add(audit_cycle)
        db.flush()

        # Add auditors
        db.add(AuditCycleAuditor(audit_cycle_id=audit_cycle.id, auditor_id=emp_asset_mgr.id))
        db.add(AuditCycleAuditor(audit_cycle_id=audit_cycle.id, auditor_id=emp_head_eng.id))

        # Add audit items for engineering assets
        for asset in assets_data[:6]:
            item = AuditItem(
                audit_cycle_id=audit_cycle.id,
                asset_id=asset.id,
                result="pending",
            )
            db.add(item)
        db.flush()
        print(f"  [OK] 1 open audit cycle with 6 items and 2 auditors")

        # --- Sample Notifications -------------------------------------
        notifications = [
            Notification(
                employee_id=emp1.id, type="asset_assigned",
                message=f"Asset 'MacBook Pro 14 M3' (AF-0001) has been assigned to you.",
            ),
            Notification(
                employee_id=emp2.id, type="asset_assigned",
                message=f"Asset 'ThinkPad X1 Carbon' (AF-0002) has been assigned to you.",
            ),
            Notification(
                employee_id=emp_asset_mgr.id, type="maintenance_raised",
                message="New maintenance request raised for HP EliteBook 840 (AF-0004).",
            ),
            Notification(
                employee_id=emp_head_eng.id, type="audit_assigned",
                message=f"You have been assigned as an auditor for audit cycle #{audit_cycle.id}.",
            ),
        ]
        db.add_all(notifications)
        db.flush()
        print(f"  [OK] {len(notifications)} sample notifications")

        # --- Activity Logs --------------------------------------------
        logs = [
            ActivityLog(actor_id=emp_admin.id, action="asset_created", entity_type="asset", entity_id=assets_data[0].id),
            ActivityLog(actor_id=emp_admin.id, action="asset_created", entity_type="asset", entity_id=assets_data[1].id),
            ActivityLog(actor_id=emp_admin.id, action="asset_allocated", entity_type="asset", entity_id=assets_data[0].id),
            ActivityLog(actor_id=emp_admin.id, action="asset_allocated", entity_type="asset", entity_id=assets_data[1].id),
            ActivityLog(actor_id=emp_admin.id, action="department_created", entity_type="department", entity_id=dept_eng.id),
            ActivityLog(actor_id=emp_admin.id, action="audit_cycle_created", entity_type="audit_cycle", entity_id=audit_cycle.id),
        ]
        db.add_all(logs)
        db.flush()
        print(f"  [OK] {len(logs)} activity log entries")

        db.commit()
        print("\n[Seed] Database seeded successfully!")
        print("\n  Login credentials (all users):")
        print("  ---------------------------------------------")
        print("  Admin:        admin@assetflow.dev / password123")
        print("  Asset Mgr:    priya@assetflow.dev / password123")
        print("  Dept Head:    rahul@assetflow.dev / password123")
        print("  Dept Head:    sneha@assetflow.dev / password123")
        print("  Employee:     vikram@assetflow.dev / password123")
        print("  Employee:     ananya@assetflow.dev / password123")
        print("  Employee:     kiran@assetflow.dev / password123")
        print("  Employee:     meera@assetflow.dev / password123")
        print("")
        print("  To test allocation conflict: POST /allocations with asset_id=1")
        print("  To test booking overlap: POST /bookings with asset_id=9, slot overlapping 10:00-12:00 today")

    except Exception as e:
        db.rollback()
        print(f"\n[Seed] Error: {e}")
        raise
    finally:
        db.close()


if __name__ == "__main__":
    seed()
