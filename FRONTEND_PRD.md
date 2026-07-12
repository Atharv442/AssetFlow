# AssetFlow ONE — Frontend PRD

## 0. Tech Stack (fixed, do not substitute)

- **Framework:** React 18 (Vite, not CRA)
- **Styling:** Tailwind CSS
- **Routing:** React Router v6
- **State:** React Query (server state) + Zustand (light client state — current user, role, sidebar state)
- **Forms:** React Hook Form + Zod (validation)
- **Icons:** lucide-react
- **Charts (Reports screen only):** Recharts
- **Date/Time & calendar (Booking screen):** date-fns + a lightweight calendar grid built manually (no heavy calendar lib)
- **HTTP:** axios with a single configured instance (baseURL + JWT interceptor)

No UI kit (no MUI/AntD/Chakra). Build components from Tailwind directly, per Design System below. This keeps output distinctive instead of templated-default.

---

## 1. Global Rules

- Every screen's visible data and available actions are **role-scoped server-side**, but frontend must also hide/disable irrelevant actions per role (defense in depth, not the source of truth).
- No screen ships until its backend contract (see BACKEND_DATABASE.md) exists. Do not mock data long-term — stub with real API calls returning empty arrays if backend isn't ready yet, never hardcoded fake records left in final build.
- Loading state: skeleton cards, not spinners, for anything showing lists/dashboards.
- Empty state: every list/table has a designed empty state (icon + one line + primary action), never a blank white area.
- Error state: toast notification (top-right, auto-dismiss 4s) for action failures; inline field errors for form validation.

---

## 2. Design System

**Palette:** one primary accent color (pick one: indigo `#4F46E5` or teal `#0D9488` — commit to one, don't mix). Neutral grays for everything else (`slate` Tailwind scale). Status colors: green (Available/Verified/Resolved), amber (Reserved/Pending/In Progress), red (Overdue/Missing/Rejected/Lost), blue (Allocated/In transit).

**Typography:** Inter or system font stack. Headings: semibold, tight tracking. Body: regular, `slate-600`/`slate-900`.

**Cards:** white background, `rounded-xl`, `shadow-sm`, `border border-slate-200`, hover `shadow-md` transition only on clickable cards.

**Layout:** persistent left sidebar (collapsible), top bar with search + notification bell + user menu. Content area max-width constrained, generous padding (`p-6`/`p-8`).

**Motion:** Tailwind transition utilities only (150–200ms). No animation library. No confetti, no glass-morphism — those are decoration, not requirements; skip entirely until every module below works.

**Tables:** zebra-free, row hover highlight, sticky header on scroll, right-aligned numeric columns, status shown as a colored pill not plain text.

---

## 3. Screen Sequence (build in this exact order — matches backend module order)

### Screen 1 — Login / Signup
- Tabs: Login | Sign Up
- Signup fields: Name, Email, Password, Confirm Password → creates Employee role only, no role dropdown
- Login fields: Email, Password, "Forgot password?" link
- On success: redirect to role-appropriate Dashboard (Screen 2)
- Session: JWT stored in memory + httpOnly refresh cookie handled by backend; frontend never persists JWT in localStorage

### Screen 2 — Dashboard (Home)
Layout differs by role but same shell:
- Row 1: Greeting ("Good morning, {name}") + date
- Row 2: KPI card row — Assets Available, Assets Allocated, Maintenance Today, Active Bookings, Pending Transfers, Upcoming Returns (Admin/Asset Manager see org-wide numbers; Dept Head sees department-scoped numbers; Employee sees personal numbers: My Assets, My Bookings, My Requests)
- Row 3: Two-column — left: Overdue items (red-bordered card, separate from upcoming), right: Quick Actions (Register Asset / Book Resource / Raise Maintenance Request — buttons shown per role permission)
- Row 4 (Asset Manager/Admin only): Pending Approvals list (transfers, maintenance, audit discrepancies) with inline Approve/Reject buttons

### Screen 3 — Organization Setup (Admin only, 3 tabs)
- **Tab A — Departments:** table (Name, Head, Parent Dept, Status) + "New Department" modal (Name, Parent dropdown, Status toggle; Head assigned after creation via Tab C promote action)
- **Tab B — Asset Categories:** table (Name, # of assets, custom fields) + "New Category" modal (Name, dynamic key-value custom field builder e.g. "Warranty Period: number")
- **Tab C — Employee Directory:** table (Name, Email, Department, Role, Status) with filter by department/role; row action menu → "Promote to Department Head" / "Promote to Asset Manager" / "Deactivate"

### Screen 4 — Asset Registration & Directory
- Top: search bar (tag/serial/QR) + filter chips (category, status, department, location)
- Table view + toggle to Card/Grid view (asset photo thumbnail visible)
- "Register Asset" button → modal/full form: Name, Category (dropdown from Screen 3B), Serial Number, Acquisition Date, Acquisition Cost, Condition (dropdown), Location, Photo upload, Documents upload, "Shared/Bookable" toggle. Asset Tag auto-generated, shown read-only after save (AF-0001 format).
- Click a row → **Asset Detail Page**: header (photo, tag, name, status pill, QR code render), tabs within: Overview | Allocation History | Maintenance History | Documents

### Screen 5 — Asset Allocation & Transfer
- List of assets filterable by status (Available/Allocated/Reserved)
- "Allocate" action on an Available asset → modal: select Employee/Department, optional Expected Return Date
- If asset already held: modal instead shows "Currently held by {name}" + single button "Request Transfer" (this exact flow is a graded PS requirement — build precisely, no generic error toast here)
- Transfer Requests sub-tab: table of pending/approved/rejected transfers, Approve/Reject buttons visible only to Asset Manager/Dept Head
- Return flow: on an Allocated asset row, "Mark Returned" → modal with Condition Check-in Notes textarea

### Screen 6 — Resource Booking
- Left: list of bookable resources (from assets flagged shared/bookable)
- Right: calendar/day-grid view of selected resource's existing bookings (color blocks per booking status)
- "New Booking" form: resource (pre-filled if selected), date, start time, end time, purpose
- On submit, if overlap → inline error directly under the time fields: "This slot overlaps with an existing booking (9:00–10:00)." No silent failure.
- Booking list table: status pill (Upcoming/Ongoing/Completed/Cancelled), Cancel/Reschedule row actions

### Screen 7 — Maintenance Management
- Kanban-style board: columns = Pending, Approved, Technician Assigned, In Progress, Resolved (Rejected shown as a filterable collapsed column, not a live board column)
- Card per request: asset thumbnail + tag, issue summary, priority pill (Low/Med/High/Critical)
- "Raise Request" button (all roles): asset select, issue description, priority, photo upload
- Card click → detail drawer: full issue, approve/reject buttons (Asset Manager only), assign technician field, status-advance button

### Screen 8 — Asset Audit
- "Create Audit Cycle" button (Asset Manager/Admin): scope (department or location dropdown), date range, assign auditor(s) multi-select
- Active cycles list: cycle name, scope, date range, progress bar (assets verified / total)
- Auditor view: checklist of assets in scope, each row has Verified / Missing / Damaged buttons + optional note
- On "Close Cycle": confirmation modal showing auto-generated discrepancy summary (count of missing/damaged) before final lock

### Screen 9 — Reports & Analytics
- Filter bar: date range, department
- Chart grid (Recharts): Utilization trend (line), Most-used vs idle assets (bar), Maintenance frequency by category (bar), Department allocation summary (stacked bar), Booking heatmap (day×hour grid, color intensity)
- "Export" button per chart (CSV/PDF) — export real underlying data only

### Screen 10 — Notifications & Activity Log
- Bell icon dropdown (top bar, all screens): last 5 notifications, "View All" link
- Full Notifications page: filterable list (type, read/unread), mark-as-read
- Activity Log (Admin only): table — Actor, Action, Entity, Timestamp, filterable by user/date/module

---

## 4. Component Inventory (build once, reuse everywhere)

`KpiCard`, `StatusPill`, `DataTable` (sortable, paginated, filterable — generic), `Modal`, `Drawer`, `EmptyState`, `SkeletonCard`, `FileUpload`, `SearchBar`, `FilterChipGroup`, `ConfirmDialog`, `Toast`, `RoleGate` (wraps children, hides if role mismatch)

Build `DataTable` and `RoleGate` first — every screen from 3 onward depends on them.

## 5. What NOT to build

No chatbot UI. No confetti/celebration animations. No AI percentage displays unless the number comes from a real backend aggregate query (see BACKEND_DATABASE.md §Reports). No glass-morphism effects. These are explicitly deprioritized until all 10 screens function correctly end-to-end.
