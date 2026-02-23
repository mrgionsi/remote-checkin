# Remote Check-in

Remote Check-in is a self-hosted app to manage B&B/hospitality check-ins, rooms, reservations, and guest document upload.

## Stack

- Frontend: Angular
- Backend: Flask + SQLAlchemy
- Database: PostgreSQL (runtime), SQLite (test mode for selected suites)

## Quick Start

1. Clone repository:
```bash
git clone https://github.com/mrgionsi/remote-checkin.git
cd remote-checkin
```

2. Start backend:
```bash
cd backend
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python main.py
```

3. Start frontend (new terminal):
```bash
cd frontend
npm install
npm start
```

Frontend runs on `http://localhost:4200`.

## Required Backend Environment Variables

Set these in `backend/.env` (or shell env):

- `DB_USER`
- `DB_PASSWORD`
- `DB_HOST`
- `DB_PORT`
- `DB_NAME`
- `JWT_SECRET_KEY`

Optional:

- `DATABASE_URL` (if set and valid, used directly)
- `ALLOWED_CORS`
- `APP_ENV` (`production` enables strict production checks)
- `RATELIMIT_STORAGE_URI` (required when `APP_ENV=production`, use shared backend such as Redis)
- `ACTIVITY_RETENTION_DAYS` (default `180`, used by activity cleanup job)
- `ACTIVITY_MAX_ROWS` (default `5000000`, set `0` to disable max-row cap)

## Upload Flow (Guest Check-in)

The backend supports two-phase document upload:

1. `POST /api/v1/upload/validate-documents`
2. `POST /api/v1/upload`

Use:

- `X-Upload-Token`
- `X-Document-Validation-Token` (optional but recommended for phase 2)

When validation token is provided and matches uploaded document fingerprint, OCR is skipped on final submit.  
Full contract is documented in `backend/DOCUMENT_UPLOAD_FLOW.md`.

## Testing

Frontend:
```bash
cd frontend
npm test
npm run test:ci
npm run e2e:smoke
```

Backend:
```bash
PYTHONPATH=backend pytest backend/tests
```

## Additional Docs

- Backend API/notes: `backend/Readme.md`
- Upload contract: `backend/DOCUMENT_UPLOAD_FLOW.md`
- Regression checklist: `backend/QA_TENANT_BOUNDARY_REGRESSION.md`
- Activity retention policy: `docs/ACTIVITY_RETENTION.md`
- Background jobs: `docs/BACKGROUND_JOBS.md`
