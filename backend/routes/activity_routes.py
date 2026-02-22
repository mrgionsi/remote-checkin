"""Timeline API endpoints for admin and superadmin dashboards."""

import json

from flask import Blueprint, jsonify, request
from flask_jwt_extended import jwt_required
from sqlalchemy.exc import SQLAlchemyError

from app_logging.config import get_logger
from app_logging.decorators import log_route
from database import SessionLocal
from models import ActivityEvent
from utils.authz import is_superadmin
from utils.route_helpers import (
    error_response,
    get_current_user_id,
    get_user_structure_ids,
    require_structure_access,
)

logger = get_logger(__name__)

activity_bp = Blueprint("activity", __name__, url_prefix="/api/v1")


@activity_bp.route("/activity/recent", methods=["GET"])
@jwt_required()
@log_route(include_request_data=True)
def get_recent_activity():
    """Return most recent timeline items scoped by role and structure access."""
    db = SessionLocal()
    try:
        current_user_id, user_error = get_current_user_id()
        if user_error:
            return user_error

        limit = request.args.get("limit", default=20, type=int)
        limit = max(1, min(limit, 100))
        page = request.args.get("page", default=1, type=int)
        page = max(1, page)
        offset = (page - 1) * limit
        requested_structure_id = request.args.get("structure_id", type=int)
        requested_actor_role = request.args.get("actor_role", type=str)

        query = db.query(ActivityEvent)

        if is_superadmin():
            if requested_structure_id is not None:
                query = query.filter(ActivityEvent.structure_id == requested_structure_id)
        else:
            allowed_structure_ids = get_user_structure_ids(db, current_user_id)
            if requested_structure_id is not None:
                _, structure_error = require_structure_access(
                    db, requested_structure_id, user_id=current_user_id
                )
                if structure_error:
                    return structure_error
                query = query.filter(ActivityEvent.structure_id == requested_structure_id)
            else:
                if not allowed_structure_ids:
                    return jsonify({"items": []}), 200
                query = query.filter(ActivityEvent.structure_id.in_(allowed_structure_ids))

        if requested_actor_role:
            normalized_roles = [
                role.strip().lower()
                for role in requested_actor_role.split(",")
                if role.strip()
            ]
            if normalized_roles:
                query = query.filter(ActivityEvent.actor_role.in_(normalized_roles))

        total = query.count()
        events = query.order_by(ActivityEvent.created_at.desc()).offset(offset).limit(limit).all()

        payload = []
        for event in events:
            metadata = {}
            if event.metadata_json:
                try:
                    metadata = json.loads(event.metadata_json)
                except json.JSONDecodeError:
                    metadata = {}

            payload.append(
                {
                    "id": event.id,
                    "eventType": event.event_type,
                    "entityType": event.entity_type,
                    "entityId": event.entity_id,
                    "structureId": event.structure_id,
                    "actorUserId": event.actor_user_id,
                    "actorRole": event.actor_role,
                    "description": event.description,
                    "metadata": metadata,
                    "createdAt": event.created_at.isoformat() if event.created_at else None,
                }
            )

        return jsonify(
            {
                "items": payload,
                "pagination": {
                    "page": page,
                    "per_page": limit,
                    "total": total,
                    "pages": (total + limit - 1) // limit if total else 0,
                },
            }
        ), 200
    except SQLAlchemyError:
        logger.exception("Database error while fetching activity timeline")
        return error_response("Database error", 500)
    except Exception:
        logger.exception("Unexpected error while fetching activity timeline")
        return error_response("Internal server error", 500)
    finally:
        db.close()
