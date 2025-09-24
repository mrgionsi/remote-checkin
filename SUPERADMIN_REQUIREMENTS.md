### Superadmin Requirements and Use Cases

#### Overview

Introduce a Superadmin role with a dedicated page in the admin area to manage the application globally. Superadmin can create structures, create admin users, and associate admin users to structures. Superadmin may also perform oversight across all structures and administrators.

#### Current State (observed)

- Backend models include `Role`, `User` with `id_role`, and `AdminStructure` for user↔structure associations.
- Admin-access endpoints exist under `/api/v1/admin/*` with role checks accepting `administrator`, and `superadmin`.
- Admin login returns JWT with `role` claim and the list of structures associated to the user.
- There is an endpoint to create a user (admin) given an `id_role`.

#### Assumptions

- Roles are stored in `role` table and referenced by `user.id_role`.
- A `SUPERADMIN` role value exists or will be seeded.
- Structures are represented by `structure` table; associations are maintained by `admin_structure`.

#### Goals

- Provide a dedicated Superadmin page in the admin area.
- Allow Superadmin to manage structures, admin users, and their associations.
- Ensure Superadmin has read access across all structures and related data.

#### Functional Requirements

- Superadmin Portal

  - Dedicated route/page under admin area (e.g., `/admin/superadmin`).
  - Visible only to users with role `superadmin`.
  - Dashboard widgets: total structures, total admins, unassigned admins, recent activity/errors (optional).

- Authentication & Authorization

  - JWT continues to include `role` claim; guards enforce `superadmin` for Superadmin pages and actions.
  - Superadmin can access all admin endpoints; certain endpoints may be elevated for Superadmin only.

- Role Management (optional minimal scope)

  - Seed roles: `superadmin`, `administrator` (and any existing names kept for compatibility).
  - View roles; editing/creating roles is optional unless needed.

- Structure Management (Superadmin-only)

  - Create structure (name, address, city, province, etc.).
  - Update structure details.
  - Archive/deactivate structure (soft delete) and reactivate.
  - View list/search/paginate all structures.

- Admin User Management (Superadmin-only)

  - Create admin user (username, password, name, contact, role=admin by default; role can be chosen if needed).
  - Update admin user details; reset password; activate/deactivate admin.
  - View/search/paginate all admin users.
  - Optionally create other superadmins (configurable; default allowed).

- Association Management (Superadmin-only)

  - Assign admin(s) to one or more structures.
  - Remove admin↔structure association.
  - View admins for a structure and structures for an admin.

- Global Oversight (read-only unless specified)

  - View reservations across all structures (filters by structure/date/status).
  - View system email configuration per user/structure where applicable (read-only unless allowed).
  - View Portale Alloggi credential presence per user/structure (values masked; ability to clear/reset optional).

- Audit & Activity (optional, recommended)
  - Log Superadmin changes (user created, structure created, association changes).
  - Expose recent change log in Superadmin dashboard.

#### Non-Functional Requirements

- Enforce least-privilege: only `superadmin` can perform global create/update/delete for structures and associations.
- Sensitive data masked in responses (e.g., external passwords/keys).
- All new endpoints require JWT with `superadmin` role.
- Paginate list endpoints; server-side filtering and sorting.

#### API Additions/Changes (backend)

- Auth/Me

  - GET `/api/v1/admin/me` already returns role; ensure it supports `superadmin` and does not limit structures (for superadmin may return empty association list or all structures via separate endpoint).

- Roles

  - GET `/api/v1/admin/roles` (Superadmin): list roles. (Optional)

- Structures (Superadmin-only)

  - GET `/api/v1/admin/structures` (list with filters/pagination).
  - POST `/api/v1/admin/structures` (create structure).
  - PUT `/api/v1/admin/structures/:id` (update structure).
  - DELETE `/api/v1/admin/structures/:id` (archive/deactivate; soft delete).

- Admin Users (Superadmin-only)

  - GET `/api/v1/admin/users` (list/search admin and superadmin users).
  - POST `/api/v1/admin/users` (create user; default role=admin unless specified).
  - PUT `/api/v1/admin/users/:id` (update user metadata, reset password).
  - PATCH `/api/v1/admin/users/:id/status` (activate/deactivate).

- Associations (Superadmin-only)

  - GET `/api/v1/admin/associations` (query by user or structure).
  - POST `/api/v1/admin/associations` (assign user↔structure: `user_id`, `structure_id`).
  - DELETE `/api/v1/admin/associations` (remove association by composite keys).

- Oversight (optional)
  - GET `/api/v1/admin/reservations` (list across structures with filters/pagination).

Notes:

- Existing `/api/v1/admin/login` remains unchanged; its role check already includes `superadmin`.
- Existing create-user endpoint may be repurposed under `/api/v1/admin/users` with stricter role checks.

#### Frontend Additions/Changes

- Routes/Navigation

  - Add `SuperadminGuard` checking JWT `role === 'superadmin'`.
  - Add route `/admin/superadmin` with nested pages: Structures, Users, Associations, Activity.
  - Hide Superadmin menu for non-superadmins.

- Pages

  - Superadmin Dashboard: KPIs, recent activity.
  - Structures: list/create/edit/archive.
  - Users: list/create/edit/reset password/activate-deactivate.
  - Associations: assign/remove; dual-list or table UI with filters.

- Services
  - `SuperadminService` calling the new backend endpoints listed above.
  - Reuse existing `admin-login` flow; ensure role is exposed and stored.

#### Data Model Impact

- Ensure `role` table contains `superadmin` and `administrator` entries.
- No schema change required for associations (`admin_structure`) if already present.
- Consider `structure.is_active` boolean for archival (if not present).

#### Permissions Matrix (summary)

- Superadmin: full read across app; create/update/delete structures; manage users; manage associations.
- Admin: limited to own associated structures; no ability to create structures or assign admins.

#### Use Cases

1. Create Structure

   - Actor: Superadmin
   - Trigger: Click “New Structure”
   - Flow: Fill details → Save → Structure appears in list

2. Create Admin User

   - Actor: Superadmin
   - Trigger: Click “New Admin”
   - Flow: Enter user details → Save → User created with role=admin

3. Associate Admin to Structure

   - Actor: Superadmin
   - Trigger: From structure or user page, choose associate
   - Flow: Select target(s) → Confirm → Association persisted

4. Remove Admin from Structure

   - Actor: Superadmin
   - Trigger: Remove association action
   - Flow: Confirm → Association deleted

5. Edit Structure

   - Actor: Superadmin
   - Trigger: Edit action on structure
   - Flow: Update fields → Save → Changes applied

6. Reset Admin Password

   - Actor: Superadmin
   - Trigger: Reset password on user
   - Flow: Generate/set new password → Notify admin

7. Deactivate/Reactivate Structure

   - Actor: Superadmin
   - Flow: Toggle status → Affects availability for admins

8. View All Reservations (Read-only)
   - Actor: Superadmin
   - Flow: Open reservations oversight → Filter/search across structures

#### Edge Cases & Constraints

- Prevent removal of last superadmin.
- Prevent duplicate admin↔structure associations.
- Validate strong passwords and unique usernames.
- Mask sensitive credentials; never return raw external service passwords.

#### Migration/Seeding

- Seed roles table with `superadmin` and `administrator`.
- Create initial superadmin user (out-of-band or via migration/seed script).

#### Telemetry & Audit (recommended)

- Log who performed create/update/delete on structures, users, associations.
- Expose recent changes to superadmins.

#### MVP vs Later Phases

- MVP

  - Superadmin login access and guard.
  - Superadmin Dashboard (basic KPIs).
  - CRUD on Structures (create, edit, archive/reactivate).
  - CRUD on Admin Users (create, edit basics, reset password, activate/deactivate).
  - Manage Associations user↔structure (assign/remove, list).
  - List Reservations across structures (read-only with filters).
  - Role seeding for `superadmin` and `administrator`.

- Later Phases
  - Audit trail UI and export.
  - Bulk operations (bulk assign admins, bulk deactivate structures).
  - Advanced search/saved filters and reporting.
  - Role management UI (create custom roles/permissions) if needed.
  - Email/notification workflows on admin creation/reset.
  - Rate limiting and IP allowlist for superadmin portal.

#### Implementation Map

- Backend

  - Routes (extend `backend/routes/admin_routes.py` or add `superadmin_routes.py`)
    - GET `/api/v1/admin/structures`
    - POST `/api/v1/admin/structures`
    - PUT `/api/v1/admin/structures/:id`
    - DELETE `/api/v1/admin/structures/:id`
    - GET `/api/v1/admin/users`
    - POST `/api/v1/admin/users`
    - PUT `/api/v1/admin/users/:id`
    - PATCH `/api/v1/admin/users/:id/status`
    - GET `/api/v1/admin/associations`
    - POST `/api/v1/admin/associations`
    - DELETE `/api/v1/admin/associations`
    - GET `/api/v1/admin/reservations` (read-only)
  - Middleware/Guards
    - Reuse JWT auth; add helper `verify_superadmin_access()` similar to `verify_admin_access()`.
  - Models
    - Ensure `Role` contains `superadmin` and `administrator`.
    - Optionally add `Structure.is_active` if not present.
  - Seeds/Migrations
    - Seed roles; create initial superadmin.

- Frontend (Angular)
  - Routing: add `/admin/superadmin` with children `structures`, `users`, `associations`, `activity`.
  - Guards: `SuperadminGuard` using `auth.service.ts` JWT `role`.
  - Components (under `frontend/src/app/admin/superadmin/`)
    - `superadmin-dashboard` (KPIs)
    - `structures` (list/form)
    - `users` (list/form)
    - `associations` (assignment UI)
  - Services
    - `superadmin.service.ts` calling new endpoints.
  - Navigation
    - Add menu item for Superadmin section, hidden unless role=superadmin.

#### Additional Use Cases

9. View Unassigned Admins

   - Actor: Superadmin
   - Flow: Filter users with no structures → Assign as needed

10. Archive and Restore Structure

    - Actor: Superadmin
    - Flow: Toggle structure status; prevents new reservations if archived (business rule dependent)

11. Force Password Reset on Next Login (optional)
    - Actor: Superadmin
    - Flow: Mark user to reset password; frontend enforces at next login
