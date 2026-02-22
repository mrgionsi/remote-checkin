"""Cleanup utility for activity_event retention and max-row cap.

Usage:
  PYTHONPATH=backend python backend/scripts/cleanup_activity_events.py

Environment variables:
  ACTIVITY_RETENTION_DAYS (default: 180)
  ACTIVITY_MAX_ROWS (default: 5000000, set 0 to disable cap)
"""

from __future__ import annotations

import os
from datetime import datetime, timedelta

from sqlalchemy import func

from database import SessionLocal
from models import ActivityEvent


def _int_env(name: str, default: int) -> int:
    raw = os.getenv(name)
    if raw is None:
        return default
    try:
        return int(str(raw).strip())
    except (TypeError, ValueError):
        return default


def cleanup_activity_events() -> dict[str, int | str]:
    """Apply retention + max-row cap cleanup and return execution summary."""
    retention_days = max(1, _int_env("ACTIVITY_RETENTION_DAYS", 180))
    max_rows = max(0, _int_env("ACTIVITY_MAX_ROWS", 5_000_000))

    cutoff = datetime.utcnow() - timedelta(days=retention_days)

    db = SessionLocal()
    deleted_by_age = 0
    deleted_by_cap = 0

    try:
        deleted_by_age = (
            db.query(ActivityEvent)
            .filter(ActivityEvent.created_at < cutoff)
            .delete(synchronize_session=False)
        )
        db.commit()

        total_after_age = db.query(func.count(ActivityEvent.id)).scalar() or 0

        if max_rows > 0 and total_after_age > max_rows:
            overflow = total_after_age - max_rows
            oldest_ids = [
                row[0]
                for row in (
                    db.query(ActivityEvent.id)
                    .order_by(ActivityEvent.created_at.asc(), ActivityEvent.id.asc())
                    .limit(overflow)
                    .all()
                )
            ]
            if oldest_ids:
                deleted_by_cap = (
                    db.query(ActivityEvent)
                    .filter(ActivityEvent.id.in_(oldest_ids))
                    .delete(synchronize_session=False)
                )
                db.commit()

        total_after = db.query(func.count(ActivityEvent.id)).scalar() or 0

        return {
            "status": "ok",
            "retention_days": retention_days,
            "max_rows": max_rows,
            "deleted_by_age": deleted_by_age,
            "deleted_by_cap": deleted_by_cap,
            "remaining": total_after,
        }
    finally:
        db.close()


if __name__ == "__main__":
    summary = cleanup_activity_events()
    print(summary)
