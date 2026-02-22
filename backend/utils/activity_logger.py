"""Helpers for writing activity events used by admin/superadmin timelines."""

import json

from flask_jwt_extended import get_jwt, get_jwt_identity

from app_logging.config import get_logger
from app_logging.utils import safe_extra_fields
from models import ActivityEvent

logger = get_logger(__name__)


def log_activity(
    db_session,
    *,
    event_type,
    entity_type,
    description,
    entity_id=None,
    structure_id=None,
    metadata=None,
):
    """Append an activity event to the current DB transaction.

    The caller owns commit/rollback. This helper never raises to avoid breaking
    business operations because of timeline side effects.
    """
    try:
        claims = get_jwt()
    except Exception:
        claims = {}

    try:
        actor_user_id = int(get_jwt_identity())
    except Exception:
        actor_user_id = None

    actor_role = claims.get("role") if isinstance(claims, dict) else None

    try:
        event = ActivityEvent(
            event_type=event_type,
            entity_type=entity_type,
            entity_id=entity_id,
            structure_id=structure_id,
            actor_user_id=actor_user_id,
            actor_role=str(actor_role).lower() if actor_role is not None else None,
            description=description,
            metadata_json=json.dumps(metadata or {}, ensure_ascii=False),
        )
        db_session.add(event)
    except Exception as exc:
        logger.warning(
            "Failed to append activity event",
            extra=safe_extra_fields(
                {
                    "event_type": event_type,
                    "entity_type": entity_type,
                    "entity_id": entity_id,
                    "structure_id": structure_id,
                    "error": str(exc),
                }
            ),
        )
