# Backend Test Coverage Roadmap (Pytest)

This roadmap defines how to extend backend API coverage in ordered phases.

## Phase 1 (P0): Auth + Tenant Isolation Matrix

Goal: enforce structure boundaries at API level for all protected routes.

Required matrix per route:
- No JWT token -> `401`
- Invalid JWT token -> `401`
- Admin mapped to structure -> success (`200/201`)
- Admin not mapped to structure -> `403`
- Superadmin -> success according to policy

Routes to cover first:
- `GET /api/v1/rooms`
- `GET /api/v1/rooms?structure_id={id}`
- `GET /api/v1/rooms/{room_id}`
- `PUT /api/v1/rooms/{room_id}`
- `DELETE /api/v1/rooms/{room_id}`
- `POST /api/v1/reservations`
- `PATCH /api/v1/reservations/{reservation_id}`
- `DELETE /api/v1/reservations/{reservation_id}`
- `GET /api/v1/reservations/structure/{structure_id}`
- `GET /api/v1/reservations/monthly/{structure_id}`
- `GET /api/v1/reservations/{reservation_id}/clients`
- `GET /api/v1/images/{reservation_ref}/{filename}`

Guest upload security coverage:
- `POST /api/v1/upload` with missing/invalid/expired/mismatched token.

## Phase 2 (P0): Validation + Error Contract Tests

Goal: stable request validation and safe error payloads.

Per mutating endpoint:
- Missing required fields
- Invalid types
- Invalid IDs / malformed IDs
- Boundary values (`number_of_people`, room `capacity`, dates)

Cross-cutting:
- Assert response error envelope is consistent (`{"error": "..."}`).
- Assert no internal exception text in client responses.

## Phase 3 (P1): Business Rule and State Tests

- Reservation status transitions and invalid transitions.
- Room activation/deactivation effects.
- Capacity and room-change constraints.
- Association constraints and role-change edge cases.

## Phase 4 (P1): Integration Flows

End-to-end backend flows with deterministic fixtures:
- Create reservation -> retrieve -> update -> status change.
- Guest upload flow -> client-reservation linkage verification.
- Superadmin association management -> admin access changes.

## Phase 5 (P2): Resilience + Regression

- Inject DB faults and assert generic `500` errors.
- Fuzz-style payload tests for parsers/validators.
- Regression snapshots for selected response schemas.

## Tooling and CI

- Run in CI:
  - `pytest` for all API suites.
  - `pylint` for routes/helpers/tests.
- Keep data isolation deterministic:
  - Cleanup fixtures per module/function.
  - Explicitly recreate role/user/structure mappings in fixtures.
