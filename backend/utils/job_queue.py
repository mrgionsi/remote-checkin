"""Background job queue helpers with retry-aware state transitions."""

import json
from datetime import datetime, timedelta, timezone

from sqlalchemy import func, or_

from models import BackgroundJob

JOB_STATUS_QUEUED = "queued"
JOB_STATUS_RUNNING = "running"
JOB_STATUS_RETRYING = "retrying"
JOB_STATUS_SUCCEEDED = "succeeded"
JOB_STATUS_FAILED = "failed"


VALID_TERMINAL_STATES = {JOB_STATUS_SUCCEEDED, JOB_STATUS_FAILED}


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


def enqueue_job(
    db_session,
    *,
    job_type,
    payload,
    created_by_user_id=None,
    structure_id=None,
    max_attempts=3,
    available_at=None,
):  # pylint: disable=too-many-arguments
    """Persist a new queued background job."""
    next_id = None
    bind = db_session.get_bind()
    if bind is not None and bind.dialect.name == "sqlite":
        next_id = (db_session.query(func.max(BackgroundJob.id)).scalar() or 0) + 1

    job = BackgroundJob(
        id=next_id,
        job_type=job_type,
        status=JOB_STATUS_QUEUED,
        payload_json=json.dumps(payload, ensure_ascii=False),
        attempts=0,
        max_attempts=max(1, int(max_attempts)),
        available_at=available_at or _utcnow(),
        created_by_user_id=created_by_user_id,
        structure_id=structure_id,
    )
    db_session.add(job)
    db_session.flush()
    return job


def claim_next_job(db_session, *, job_types=None):
    """Claim the next available queued/retrying job and mark it running."""
    query = db_session.query(BackgroundJob).filter(
        BackgroundJob.status.in_([JOB_STATUS_QUEUED, JOB_STATUS_RETRYING]),
        BackgroundJob.available_at <= _utcnow(),
    )

    if job_types:
        query = query.filter(BackgroundJob.job_type.in_(job_types))

    query = query.order_by(BackgroundJob.available_at.asc(), BackgroundJob.created_at.asc())

    # with_for_update(skip_locked=True) works on PostgreSQL and is ignored on SQLite.
    job = query.with_for_update(skip_locked=True).first()
    if not job:
        return None

    job.status = JOB_STATUS_RUNNING
    job.started_at = _utcnow()
    job.worker_id = None
    db_session.flush()
    return job


def mark_job_running(db_session, job, *, worker_id=None):
    """Mark an already-claimed job as running on a specific worker."""
    if worker_id:
        job.worker_id = worker_id
    job.status = JOB_STATUS_RUNNING
    if job.started_at is None:
        job.started_at = _utcnow()
    db_session.flush()


def mark_job_succeeded(db_session, job, *, result=None):
    """Set job to succeeded and persist optional JSON result."""
    job.status = JOB_STATUS_SUCCEEDED
    job.finished_at = _utcnow()
    job.result_json = json.dumps(result or {}, ensure_ascii=False)
    job.error_message = None
    db_session.flush()


def mark_job_failed(
    db_session,
    job,
    *,
    error_message,
    retry_base_seconds=30,
    retry_cap_seconds=1800,
):
    """Fail job permanently or reschedule it with exponential backoff."""
    next_attempt = int(job.attempts) + 1
    job.attempts = next_attempt
    job.error_message = str(error_message)
    job.finished_at = _utcnow()

    if next_attempt >= int(job.max_attempts):
        job.status = JOB_STATUS_FAILED
    else:
        delay_seconds = min(retry_base_seconds * (2 ** (next_attempt - 1)), retry_cap_seconds)
        job.status = JOB_STATUS_RETRYING
        job.available_at = _utcnow() + timedelta(seconds=delay_seconds)

    db_session.flush()


def get_visible_jobs_query(db_session, *, user_id, is_superadmin, allowed_structure_ids):
    """Return role-aware jobs query for listing endpoints."""
    query = db_session.query(BackgroundJob)
    if is_superadmin:
        return query

    filters = [BackgroundJob.created_by_user_id == user_id]
    if allowed_structure_ids:
        filters.append(BackgroundJob.structure_id.in_(allowed_structure_ids))

    return query.filter(or_(*filters))
