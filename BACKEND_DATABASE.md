# AssetFlow ONE — Backend + Database Architecture

## 0. Tech Stack (fixed)

- **Database:** PostgreSQL 15+, self-hosted (Docker container locally or on a college/VM server). No managed cloud DB (no RDS/Supabase/Neon/Cloud SQL) — this is an explicit PS constraint.
- **Backend framework:** FastAPI (Python) — recommended given team's ML/Python background; Node.js + Express is an acceptable alternative if the team is stronger there. Pick one, do not mix.
- **ORM/migrations:** SQLAlchemy + Alembic (if FastAPI) or Prisma (if Node). Never hand-write schema changes outside migrations — every schema change is a migration file, no exceptions, so state is always reproducible.
- **Auth:** JWT (access token 15min + refresh token 7d, refresh stored httpOnly cookie), bcrypt for password hashing.
- **File storage:** local disk volume (`/uploads`) for asset photos/documents/QR codes in dev and demo — no S3/cloud storage dependency.
- **Background jobs (overdue checks, reminders):** APScheduler (Python) or node-cron (Node) — simple in-process scheduler, no Redis/Celery needed at hackathon scale.
- **Realtime notifications:** polling endpoint (`GET /notifications?since=`) every 20s from frontend. Do not build WebSockets unless steps 1–9 below are already fully working with time to spare.

---

## 1. Database Schema

```sql
-- Departments
CREATE TABLE departments (
  id SERIAL PRIMARY KEY,
  name VARCHAR(100) NOT NULL,
  parent_department_id INT REFERENCES departments(id),
  head_employee_id INT, -- FK added after employees table exists
  status VARCHAR(20) DEFAULT 'active' CHECK (status IN ('active','inactive')),
  created_at TIMESTAMP DEFAULT now()
);

-- Employees (all users)
CREATE TABLE employees (
  id SERIAL PRIMARY KEY,
  name VARCHAR(100) NOT NULL,
  email VARCHAR(150) UNIQUE NOT NULL,
  password_hash TEXT NOT NULL,
  department_id INT REFERENCES departments(id),
  role VARCHAR(20) NOT NULL DEFAULT 'employee'
    CHECK (role IN ('employee','department_head','asset_manager','admin')),
  status VARCHAR(20) DEFAULT 'active' CHECK (status IN ('active','inactive')),
  created_at TIMESTAMP DEFAULT now()
);

ALTER TABLE departments
  ADD CONSTRAINT fk_head FOREIGN KEY (head_employee_id) REFERENCES employees(id);

-- Asset Categories
CREATE TABLE asset_categories (
  id SERIAL PRIMARY KEY,
  name VARCHAR(100) NOT NULL,
  custom_fields JSONB DEFAULT '{}', -- e.g. {"warranty_period_months": "number"}
  created_at TIMESTAMP DEFAULT now()
);

-- Assets
CREATE TABLE assets (
  id SERIAL PRIMARY KEY,
  asset_tag VARCHAR(20) UNIQUE NOT NULL, -- AF-0001, generated in app logic on insert
  name VARCHAR(150) NOT NULL,
  category_id INT REFERENCES asset_categories(id),
  serial_number VARCHAR(100),
  acquisition_date DATE,
  acquisition_cost NUMERIC(12,2), -- reporting/ranking only, never linked to accounting module
  condition VARCHAR(30),
  location VARCHAR(150),
  photo_url TEXT,
  documents JSONB DEFAULT '[]',
  is_bookable BOOLEAN DEFAULT false,
  status VARCHAR(20) NOT NULL DEFAULT 'available'
    CHECK (status IN ('available','allocated','reserved','under_maintenance','lost','retired','disposed')),
  created_at TIMESTAMP DEFAULT now()
);

-- Allocations (current + historical)
CREATE TABLE allocations (
  id SERIAL PRIMARY KEY,
  asset_id INT REFERENCES assets(id),
  employee_id INT REFERENCES employees(id),
  department_id INT REFERENCES departments(id),
  allocated_at TIMESTAMP DEFAULT now(),
  expected_return_date DATE,
  returned_at TIMESTAMP,
  return_condition_notes TEXT,
  is_active BOOLEAN DEFAULT true -- only one active allocation per asset, enforced below
);

-- Enforce: only one active allocation per asset at a time
CREATE UNIQUE INDEX one_active_allocation_per_asset
  ON allocations (asset_id) WHERE is_active = true;

-- Transfer Requests
CREATE TABLE transfer_requests (
  id SERIAL PRIMARY KEY,
  asset_id INT REFERENCES assets(id),
  requested_by INT REFERENCES employees(id),
  current_holder_id INT REFERENCES employees(id),
  status VARCHAR(20) DEFAULT 'requested'
    CHECK (status IN ('requested','approved','rejected','reallocated')),
  approved_by INT REFERENCES employees(id),
  created_at TIMESTAMP DEFAULT now(),
  resolved_at TIMESTAMP
);

-- Bookings (resource booking)
CREATE TABLE bookings (
  id SERIAL PRIMARY KEY,
  asset_id INT REFERENCES assets(id), -- must be is_bookable = true
  booked_by INT REFERENCES employees(id),
  slot tsrange NOT NULL, -- e.g. '[2026-07-12 09:00, 2026-07-12 10:00)'
  status VARCHAR(20) DEFAULT 'upcoming'
    CHECK (status IN ('upcoming','ongoing','completed','cancelled')),
  purpose TEXT,
  created_at TIMESTAMP DEFAULT now(),
  EXCLUDE USING gist (asset_id WITH =, slot WITH &&) WHERE (status != 'cancelled')
);
-- ^ This single constraint enforces zero-overlap bookings at the DB level.
-- Requires: CREATE EXTENSION IF NOT EXISTS btree_gist;

-- Maintenance Requests
CREATE TABLE maintenance_requests (
  id SERIAL PRIMARY KEY,
  asset_id INT REFERENCES assets(id),
  raised_by INT REFERENCES employees(id),
  issue_description TEXT,
  priority VARCHAR(20) CHECK (priority IN ('low','medium','high','critical')),
  photo_url TEXT,
  status VARCHAR(30) DEFAULT 'pending'
    CHECK (status IN ('pending','approved','rejected','technician_assigned','in_progress','resolved')),
  approved_by INT REFERENCES employees(id),
  technician_name VARCHAR(100),
  created_at TIMESTAMP DEFAULT now(),
  resolved_at TIMESTAMP
);

-- Audit Cycles
CREATE TABLE audit_cycles (
  id SERIAL PRIMARY KEY,
  scope_department_id INT REFERENCES departments(id),
  scope_location VARCHAR(150),
  start_date DATE,
  end_date DATE,
  status VARCHAR(20) DEFAULT 'open' CHECK (status IN ('open','closed')),
  created_by INT REFERENCES employees(id),
  closed_at TIMESTAMP
);

CREATE TABLE audit_cycle_auditors (
  audit_cycle_id INT REFERENCES audit_cycles(id),
  auditor_id INT REFERENCES employees(id),
  PRIMARY KEY (audit_cycle_id, auditor_id)
);

CREATE TABLE audit_items (
  id SERIAL PRIMARY KEY,
  audit_cycle_id INT REFERENCES audit_cycles(id),
  asset_id INT REFERENCES assets(id),
  result VARCHAR(20) CHECK (result IN ('pending','verified','missing','damaged')) DEFAULT 'pending',
  note TEXT,
  checked_by INT REFERENCES employees(id),
  checked_at TIMESTAMP
);

-- Notifications
CREATE TABLE notifications (
  id SERIAL PRIMARY KEY,
  employee_id INT REFERENCES employees(id),
  type VARCHAR(50), -- e.g. 'asset_assigned','maintenance_approved','booking_reminder'
  message TEXT,
  is_read BOOLEAN DEFAULT false,
  created_at TIMESTAMP DEFAULT now()
);

-- Activity Log (append-only)
CREATE TABLE activity_logs (
  id SERIAL PRIMARY KEY,
  actor_id INT REFERENCES employees(id),
  action VARCHAR(100),
  entity_type VARCHAR(50),
  entity_id INT,
  created_at TIMESTAMP DEFAULT now()
);
```

---

## 2. API Contract (route groups — build in this order)

### Auth
- `POST /auth/signup` → creates employee role only
- `POST /auth/login` → returns access token, sets refresh cookie
- `POST /auth/refresh`
- `POST /auth/forgot-password`

### Org Setup (Admin only, enforced via role middleware)
- `GET/POST/PUT /departments`
- `GET/POST/PUT /asset-categories`
- `GET /employees`, `PUT /employees/:id/role` (promote action)

### Assets
- `GET /assets?search=&category=&status=&department=&location=`
- `POST /assets` (auto-generates asset_tag server-side: `AF-` + zero-padded sequence)
- `GET /assets/:id` (includes allocation + maintenance history joins)
- `PUT /assets/:id`

### Allocation & Transfer
- `POST /allocations` → **must run inside a transaction with `SELECT ... FOR UPDATE` on the asset row** before checking `is_active` allocation, to prevent race conditions on simultaneous requests
  - If asset already actively allocated → return `409` with `{ current_holder }`, do not silently fail
- `POST /transfer-requests`
- `PUT /transfer-requests/:id/approve` → reallocates atomically (close old allocation, open new one, in one transaction)
- `PUT /allocations/:id/return`

### Bookings
- `POST /bookings` → attempt insert, catch Postgres exclusion constraint violation (error code `23P01`), translate to `409` with human-readable overlap message
- `GET /bookings?asset_id=&date=`
- `PUT /bookings/:id/cancel`

### Maintenance
- `POST /maintenance-requests`
- `PUT /maintenance-requests/:id/approve` → also updates `assets.status = 'under_maintenance'` in same transaction
- `PUT /maintenance-requests/:id/resolve` → updates `assets.status = 'available'` in same transaction
- `PUT /maintenance-requests/:id/assign-technician`

### Audit
- `POST /audit-cycles`
- `POST /audit-cycles/:id/auditors`
- `PUT /audit-items/:id` (mark verified/missing/damaged)
- `POST /audit-cycles/:id/close` → in one transaction: lock cycle, update `assets.status = 'lost'` for all confirmed-missing items, generate discrepancy summary row

### Dashboard & Reports
- `GET /dashboard` → role-aware aggregate query (Dept Head param auto-scoped server-side from JWT, never trust a client-passed department_id)
- `GET /reports/utilization`, `/reports/maintenance-frequency`, `/reports/booking-heatmap`, `/reports/department-summary` — all real SQL aggregates, no placeholder numbers

### Notifications & Logs
- `GET /notifications?since=`
- `PUT /notifications/:id/read`
- `GET /activity-logs?actor=&entity=&date=` (Admin only)

---

## 3. Critical Business Logic Rules (non-negotiable, test each explicitly)

1. **Allocation conflict:** row lock + check before insert, return current holder's name, never allow two active allocations for one asset.
2. **Booking overlap:** enforced by DB exclusion constraint, not application code — this guarantees correctness even under concurrent requests.
3. **Maintenance status sync:** asset status change and maintenance status change happen in the same DB transaction — never two separate calls that could partially fail.
4. **Audit close is irreversible:** once `status = 'closed'`, reject any further `PUT /audit-items/:id` for that cycle at the API layer.
5. **Role scoping is server-side only source of truth:** every list/report endpoint filters by `req.user.role` and `req.user.department_id` from the JWT — never accept a department filter from the client for a Department Head role.

## 4. Environment & Deployment Notes

- Local dev: `docker-compose.yml` with one Postgres service + `btree_gist` extension enabled on init.
- No cloud DB. If demo needs external access, host Postgres on the same VM as the backend, not a managed DB service.
- Seed script (`seed.sql` or ORM seed) required: realistic demo data — at least 15 assets, 3 departments, 8 employees across roles, a pre-existing allocation and booking to demonstrate the conflict/overlap examples live.
