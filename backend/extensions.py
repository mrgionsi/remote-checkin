"""Shared Flask extensions."""

import os
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address


limiter = Limiter(
    key_func=get_remote_address,
    storage_uri=os.getenv("RATELIMIT_STORAGE_URI", "memory://"),
    default_limits=[],
)


def validate_limiter_storage(app=None):
    """Ensure production uses a shared limiter storage backend."""
    app_env = str(os.getenv("APP_ENV", "")).strip().lower()
    config_env = ""
    if app is not None:
        config_env = str(
            app.config.get("ENVIRONMENT")
            or app.config.get("ENV")
            or ""
        ).strip().lower()
        if app.config.get("TESTING") or app.config.get("DEBUG"):
            return

    # Enforce only when environment is explicitly marked as production.
    env = app_env or config_env
    if not env:
        return
    storage_uri = os.getenv("RATELIMIT_STORAGE_URI", "memory://")
    if env in {"production", "prod"} and storage_uri == "memory://":
        raise RuntimeError(
            "RATELIMIT_STORAGE_URI is required in production (use shared Redis/Memcached storage)."
        )
