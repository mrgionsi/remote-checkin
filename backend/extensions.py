"""Shared Flask extensions."""

import os
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address


limiter = Limiter(
    key_func=get_remote_address,
    storage_uri=os.getenv("RATELIMIT_STORAGE_URI", "memory://"),
    default_limits=[],
)


def validate_limiter_storage():
    """Ensure production uses a shared limiter storage backend."""
    env = os.getenv("FLASK_ENV", "").lower()
    storage_uri = os.getenv("RATELIMIT_STORAGE_URI", "memory://")
    if env == "production" and storage_uri == "memory://":
        raise RuntimeError(
            "RATELIMIT_STORAGE_URI is required in production (use shared Redis/Memcached storage)."
        )
