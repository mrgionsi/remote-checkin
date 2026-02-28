# Background Jobs (Activity 2)

This app now supports persisted retryable background jobs via table `background_job`.

## State model

- `queued`: waiting to be claimed
- `running`: claimed by a worker
- `retrying`: failed attempt, delayed retry scheduled
- `succeeded`: terminal success
- `failed`: terminal failure (max attempts reached)

## Current job type

- `portale_alloggi_submit`

The admin route `POST /api/v1/admin/reservations/<id>/queue-portale-alloggi-real` enqueues a production Portale Alloggi submission job (instead of doing the request inline).

## Visibility API

`GET /api/v1/admin/jobs/recent`

- admin users: only jobs created by the user or in structures mapped to the user
- superadmin: all jobs
- filters: `status`, `jobType`, `limit`, `offset`

## Worker execution

Run from repository root:

```bash
PYTHONPATH=backend python -m scripts.process_background_jobs --once --max-jobs 20
```

Without `--once`, the script still processes up to `--max-jobs` per run and exits.

## Retry policy

On handler failures:

- attempts increment by 1
- status becomes `retrying` until `attempts >= max_attempts`
- exponential backoff starts at 30s and caps at 30m
- terminal failures move to `failed`

## Schema

- migration: `database/migrations/2026-02-23_add_background_job.sql`
- base SQL: `database/init.sql`
