"""Process queued background jobs.

Usage:
    PYTHONPATH=backend python -m scripts.process_background_jobs --once --max-jobs 20
"""

import argparse
import json
from socket import gethostname
import time

# pylint: disable=C0411
from app_logging.config import get_logger
from database import SessionLocal
from services.background_job_handlers import JobExecutionError, execute_job_by_type
from utils.activity_logger import log_activity
from utils.job_queue import claim_next_job, mark_job_failed, mark_job_running, mark_job_succeeded

logger = get_logger(__name__)


def _load_payload(payload_json):
    try:
        return json.loads(payload_json or "{}")
    except (TypeError, ValueError):
        return {}


def _process_one(worker_id):
    db_session = SessionLocal()
    try:
        job = claim_next_job(db_session)
        if not job:
            db_session.rollback()
            return False

        mark_job_running(db_session, job, worker_id=worker_id)
        payload = _load_payload(job.payload_json)

        try:
            result = execute_job_by_type(db_session, job_type=job.job_type, payload=payload)
            mark_job_succeeded(db_session, job, result=result)
            log_activity(
                db_session,
                event_type="job.succeeded",
                entity_type="background_job",
                entity_id=job.id,
                structure_id=job.structure_id,
                description=f"Background job completed ({job.job_type})",
                metadata={"job_type": job.job_type, "reservation_id": payload.get("reservation_id")},
            )
            db_session.commit()
            logger.info("Background job succeeded", extra={"job_id": job.id, "job_type": job.job_type})
        except JobExecutionError as exc:
            mark_job_failed(db_session, job, error_message=str(exc))
            log_activity(
                db_session,
                event_type="job.failed" if job.status == "failed" else "job.retrying",
                entity_type="background_job",
                entity_id=job.id,
                structure_id=job.structure_id,
                description=f"Background job {job.status} ({job.job_type})",
                metadata={"error": str(exc), "job_type": job.job_type},
            )
            db_session.commit()
            logger.warning(
                "Background job execution error",
                extra={"job_id": job.id, "job_type": job.job_type, "status": job.status, "error": str(exc)},
            )
        except Exception as exc:  # pylint: disable=broad-exception-caught
            mark_job_failed(db_session, job, error_message=str(exc))
            db_session.commit()
            logger.exception("Unexpected background job failure", extra={"job_id": job.id, "job_type": job.job_type})

        return True
    finally:
        db_session.close()


def main():
    """CLI entrypoint."""
    parser = argparse.ArgumentParser(description="Process queued background jobs")
    parser.add_argument("--once", action="store_true", help="Process at most --max-jobs jobs then exit")
    parser.add_argument("--max-jobs", type=int, default=20, help="Maximum jobs to process in a run")
    args = parser.parse_args()

    worker_id = f"{gethostname()}-job-worker"
    processed = 0
    max_jobs = max(1, args.max_jobs)

    if args.once:
        while processed < max_jobs:
            has_processed = _process_one(worker_id)
            if not has_processed:
                break
            processed += 1
        logger.info("Background job processor finished", extra={"processed_jobs": processed, "mode": "once"})
        return

    idle_sleep_seconds = 1
    max_idle_sleep_seconds = 30
    try:
        while True:
            has_processed = _process_one(worker_id)
            if has_processed:
                processed += 1
                idle_sleep_seconds = 1
                continue

            time.sleep(idle_sleep_seconds)
            idle_sleep_seconds = min(idle_sleep_seconds * 2, max_idle_sleep_seconds)
    except KeyboardInterrupt:
        logger.info(
            "Background job processor stopped by signal",
            extra={"processed_jobs": processed, "mode": "continuous"},
        )


if __name__ == "__main__":
    main()
