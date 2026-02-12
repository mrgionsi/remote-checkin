# Tenant Boundary Regression Checklist (Beta)

Run these API checks before each beta release to verify cross-structure isolation and upload token security.

## 1) Admin without mapped structures

- Login as admin user with no `admin_structure` rows.
- Verify:
  - `GET /api/v1/rooms` returns `200 []`
  - `POST /api/v1/reservations` returns `403` with `No structure assigned to this user`
  - `GET /api/v1/reservations/structure/{id}` returns `403`
  - `GET /api/v1/reservations/monthly/{id}` returns `403`

## 2) Admin with mapped structure A only

- Login as admin mapped only to structure A.
- Verify allowed:
  - `GET /api/v1/rooms?structure_id={A}` -> `200`
  - `POST /api/v1/rooms` with `id_structure=A` -> `201`
  - `POST /api/v1/reservations` with room in A -> `201`
- Verify denied:
  - `GET /api/v1/rooms?structure_id={B}` -> `403`
  - `POST /api/v1/rooms` with `id_structure=B` -> `403`
  - `POST /api/v1/reservations` with `structureId=B` -> `403`
  - `PATCH /api/v1/reservations/{id_in_B}` -> `403`
  - `DELETE /api/v1/reservations/{id_in_B}` -> `403`

## 3) Superadmin without mapped structures

- Login as superadmin without structure associations.
- Verify:
  - Reservation creation is blocked (`403`) unless policy changes.
  - Room/Reservation reads still respect explicit route access controls as implemented.

## 4) Upload token security

- Missing token:
  - `POST /api/v1/upload` without `X-Upload-Token` and without `uploadToken` -> `401 Missing upload token`
- Invalid token:
  - `POST /api/v1/upload` with malformed token -> `401 Invalid upload token`
- Expired token:
  - `POST /api/v1/upload` with expired signed token -> `401 Upload token expired`
- Mismatch token:
  - Token signed for reservation X, payload has reservation Y -> `403 Upload token does not match reservation`

## 5) Error hardening checks

- Trigger DB failures (invalid FK, unavailable DB).
- Verify API responses do **not** expose raw Python/SQL exception text.
- Verify server logs still capture full exception details.
