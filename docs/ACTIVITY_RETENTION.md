# Activity Timeline Retention

This project stores timeline records in `activity_event`.

## Retention policy

- Time-based retention: keep the last `ACTIVITY_RETENTION_DAYS` days.
- Safety cap: keep at most `ACTIVITY_MAX_ROWS` rows.

Defaults:

- `ACTIVITY_RETENTION_DAYS=180`
- `ACTIVITY_MAX_ROWS=5000000`

Set `ACTIVITY_MAX_ROWS=0` to disable row-cap cleanup.

## Cleanup command

Run from repository root:

```bash
PYTHONPATH=backend python backend/scripts/cleanup_activity_events.py
```

Example with custom limits:

```bash
ACTIVITY_RETENTION_DAYS=90 ACTIVITY_MAX_ROWS=1000000 \
PYTHONPATH=backend python backend/scripts/cleanup_activity_events.py
```

## Schedule (recommended)

Run once per day (example: 03:15):

```cron
15 3 * * * cd /path/to/remote-checkin && \
ACTIVITY_RETENTION_DAYS=180 ACTIVITY_MAX_ROWS=5000000 \
PYTHONPATH=backend /path/to/venv/bin/python backend/scripts/cleanup_activity_events.py >> logs/activity-retention.log 2>&1
```

## CI helper workflow

A GitHub Actions workflow is included:

- `.github/workflows/activity-retention.yml`

It runs on schedule and manual dispatch. Configure environment secrets for DB connectivity:

- `DATABASE_URL`

Optional secrets:

- `ACTIVITY_RETENTION_DAYS`
- `ACTIVITY_MAX_ROWS`
