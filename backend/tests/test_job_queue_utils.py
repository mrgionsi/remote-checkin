"""Unit tests for background job queue state transitions."""

# pylint: disable=import-error,redefined-outer-name,C0411

import pytest

from database import Base, SessionLocal, engine
from models import BackgroundJob
from utils.job_queue import (
    JOB_STATUS_FAILED,
    JOB_STATUS_RETRYING,
    JOB_STATUS_RUNNING,
    JOB_STATUS_SUCCEEDED,
    claim_next_job,
    enqueue_job,
    mark_job_failed,
    mark_job_succeeded,
)


@pytest.fixture(scope="module", autouse=True)
def schema():
    """Create/drop schema for this module."""
    Base.metadata.create_all(bind=engine)
    yield
    Base.metadata.drop_all(bind=engine)
    engine.dispose()


@pytest.fixture()
def db_session():
    """Provide a DB session and cleanup background jobs."""
    db = SessionLocal()
    yield db
    db.query(BackgroundJob).delete()
    db.commit()
    db.close()


def test_claim_next_job_moves_to_running(db_session):
    """Queued job is claimed and moved to running."""
    enqueue_job(
        db_session,
        job_type="portale_alloggi_submit",
        payload={"reservation_id": 1, "user_id": 2},
    )
    db_session.commit()

    claimed = claim_next_job(db_session)
    assert claimed is not None
    assert claimed.status == JOB_STATUS_RUNNING


def test_failed_job_retries_then_becomes_terminal(db_session):
    """Failed jobs retry until max attempts then become failed."""
    job = enqueue_job(
        db_session,
        job_type="portale_alloggi_submit",
        payload={"reservation_id": 2, "user_id": 3},
        max_attempts=2,
    )
    db_session.commit()

    mark_job_failed(db_session, job, error_message="temporary failure")
    assert job.status == JOB_STATUS_RETRYING
    assert job.attempts == 1

    mark_job_failed(db_session, job, error_message="final failure")
    assert job.status == JOB_STATUS_FAILED
    assert job.attempts == 2


def test_mark_job_succeeded_sets_terminal_state(db_session):
    """Successful job stores result and terminal status."""
    job = enqueue_job(
        db_session,
        job_type="portale_alloggi_submit",
        payload={"reservation_id": 3, "user_id": 4},
    )
    mark_job_succeeded(db_session, job, result={"ok": True})
    assert job.status == JOB_STATUS_SUCCEEDED
    assert job.result_json is not None
