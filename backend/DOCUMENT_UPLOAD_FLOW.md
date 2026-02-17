# Document Upload Contract (Beta)

This backend now uses a **two-phase upload** for guest check-in documents.

## Phase 1: Pre-validate documents

- Endpoint: `POST /api/v1/upload/validate-documents`
- Required headers:
  - `X-Upload-Token: <signed-upload-token>`
- Required multipart fields:
  - `reservationId`
  - `frontimage`
  - `backimage`
  - `selfie`

### Success response

- HTTP `200`
- Body:
  - `message`
  - `validation`
  - `document_validation_token`

`document_validation_token` is short-lived and must be used in phase 2.

### Failure response

- HTTP `422` for OCR/document validation failure
- Body:
  - `error: "Document validation failed"`
  - `retryable: true`
  - `invalid_files: [{ field, reason, confidence }]`
  - `validation`

Client should ask the guest to replace only failed images and retry phase 1.

## Phase 2: Final submit

- Endpoint: `POST /api/v1/upload`
- Required headers:
  - `X-Upload-Token: <signed-upload-token>`
  - `X-Document-Validation-Token: <phase-1-token>`
- Required multipart fields:
  - all form fields + image files

When `X-Document-Validation-Token` is valid, OCR is skipped in final submit.

## Token rules

- Upload token salt: `reservation-upload`
- Upload token max age: `2h`
- Document validation token salt: `reservation-document-validation`
- Document validation token max age: `15m`

## Rate limits

- `POST /api/v1/upload/validate-documents`: `20/minute` per client IP
- `POST /api/v1/upload`: `10/minute` per client IP
- `POST /api/v1/admin/login`: `10/minute` per client IP
- `POST /api/v1/admin/change-password`: `5/minute` per client IP
- `POST /api/v1/superadmin/users`: `10/minute` per client IP
- `POST /api/v1/superadmin/users/<id>/reset-password`: `5/minute` per client IP
