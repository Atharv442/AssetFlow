# AssetFlow ONE — Authentication & RBAC Spec

## 0. Tech Stack (fixed)

- **Password hashing:** bcrypt, cost factor 10–12
- **Tokens:** JWT (HS256, signed with a server-side secret in `.env`, never hardcoded)
  - Access token: 15 min expiry, sent as `Authorization: Bearer` header
  - Refresh token: 7 day expiry, stored as httpOnly + Secure cookie, never exposed to JS
- **No third-party auth provider** (no Firebase Auth/Auth0/Clerk) — this is a self-contained system per the PS's "realistic account creation" requirement; using a third-party identity provider also risks looking like you outsourced the actual auth logic.

---

## 1. Signup Flow (critical PS rule — do not violate)

- `POST /auth/signup` accepts: name, email, password only.
- **No role field accepted from client, ever** — even if sent, server ignores it and hardcodes `role = 'employee'` on insert.
- Email uniqueness enforced at DB level (`UNIQUE` constraint) — return `409` on duplicate, not a generic 500.
- Password requirements: min 8 chars, at least 1 number — validate both client-side (UX) and server-side (source of truth).

## 2. Login Flow

- `POST /auth/login`: email + password → bcrypt compare → issue access + refresh tokens.
- Failed login: generic "Invalid email or password" (never reveal whether email exists — basic security hygiene).
- Rate-limit login attempts per IP/email (simple in-memory counter is fine at hackathon scale — 5 attempts / 15 min lockout).
- Session validation: every protected route runs middleware that verifies JWT signature + expiry before touching any handler logic.

## 3. Forgot Password

- `POST /auth/forgot-password` → generates a short-lived reset token (store hashed token + expiry in a `password_resets` table), emails a reset link (or, if no email service configured for demo, display the reset link directly in a dev-mode response — do not fake "email sent" without actually sending one).
- `POST /auth/reset-password` → validates token, updates password_hash, invalidates the reset token.

```sql
CREATE TABLE password_resets (
  id SERIAL PRIMARY KEY,
  employee_id INT REFERENCES employees(id),
  token_hash TEXT NOT NULL,
  expires_at TIMESTAMP NOT NULL,
  used BOOLEAN DEFAULT false
);
```

## 4. Role Model — the only 4 roles, no others

| Role | Assigned by | Scope |
|---|---|---|
| `employee` | self-signup (default) | own allocations, own bookings, own maintenance requests |
| `department_head` | Admin promotion only | own department's employees/assets/allocations/transfers/bookings |
| `asset_manager` | Admin promotion only | all assets/allocations/transfers/maintenance/audits org-wide |
| `admin` | seeded directly in DB at setup, never via signup or promotion UI | everything |

**Promotion is the only place roles change**, via `PUT /employees/:id/role`, callable only by `admin`. This mirrors the PS's explicit requirement that Organization Setup → Employee Directory is "the only place roles are assigned."

## 5. Authorization Middleware Pattern

Every protected route declares required role(s) explicitly — never infer permission from UI state:

```python
# FastAPI example
def require_role(*allowed_roles):
    def checker(current_user = Depends(get_current_user)):
        if current_user.role not in allowed_roles:
            raise HTTPException(403, "Insufficient permissions")
        return current_user
    return checker

@app.post("/departments")
def create_department(payload: DepartmentIn, user = Depends(require_role("admin"))):
    ...
```

For Department Head scoping (not just role check, but data scoping):

```python
def scope_query_to_department(query, user):
    if user.role == "department_head":
        query = query.filter(department_id == user.department_id)
    # admin and asset_manager see everything; employee sees own records only via separate filter
    return query
```

**Rule:** any endpoint returning a list must apply department/ownership scoping server-side based on `user` from the JWT — a Department Head sending a different `department_id` in the request must be ignored, not honored.

## 6. Permission Matrix (reference for every endpoint)

| Action | Employee | Dept Head | Asset Manager | Admin |
|---|---|---|---|---|
| Signup | ✅ (self, as employee) | – | – | – |
| Promote roles | ❌ | ❌ | ❌ | ✅ |
| Manage departments/categories | ❌ | ❌ | ❌ | ✅ |
| Register asset | ❌ | ❌ | ✅ | ✅ |
| Allocate asset | ❌ | ✅ (own dept) | ✅ (any) | ✅ |
| Approve transfer | ❌ | ✅ (own dept) | ✅ (any) | ✅ |
| Raise maintenance request | ✅ (own asset) | ✅ | ✅ | ✅ |
| Approve maintenance | ❌ | ❌ | ✅ | ✅ |
| Book resource | ✅ | ✅ (on behalf of dept) | ✅ | ✅ |
| Create audit cycle | ❌ | ❌ | ✅ | ✅ |
| Mark audit item | only if assigned as auditor | only if assigned as auditor | ✅ | ✅ |
| Close audit cycle | ❌ | ❌ | ✅ | ✅ |
| View org-wide analytics | ❌ | ❌ (dept only) | ✅ | ✅ |
| View activity logs | ❌ | ❌ | ❌ | ✅ |

Build this matrix as literal middleware checks per route — do not rely on frontend hiding buttons as the actual security boundary.

## 7. Session & Token Handling on Frontend

- Access token kept in memory (React state/Zustand), **never in localStorage** (XSS risk).
- Refresh token is httpOnly cookie — frontend never reads it directly; axios interceptor calls `/auth/refresh` on `401`, retries original request once, then forces logout if refresh also fails.
- On logout: clear in-memory token, call `POST /auth/logout` to invalidate refresh cookie server-side.

## 8. Testing Checklist (run before demo)

- [ ] Signup cannot set any role other than employee, even with a manually crafted request body
- [ ] Non-admin hitting `/employees/:id/role` gets 403
- [ ] Department Head A cannot see Department B's assets/allocations even by guessing IDs in the URL
- [ ] Expired access token triggers refresh flow transparently, not a logout
- [ ] Reused/expired password reset token is rejected
- [ ] Rate limiting actually blocks after 5 failed logins
