import hashlib
import hmac
import threading
from datetime import datetime, timezone
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

from flask import g, request

from config import (
    DAILY_LIMIT_FREE,
    DEV_UNLIMITED_SESSION_IDS,
    MONETIZATION_ACTIVE,
    USAGE_TIMEZONE,
    VALID_API_KEYS,
)
from utils.responses import error_response


USAGE_LOG = {}
USAGE_DAY = None
USAGE_LOCK = threading.Lock()

LOCAL_ADDRESSES = {
    "127.0.0.1",
    "::1",
}


def usage_date():
    try:
        return datetime.now(ZoneInfo(USAGE_TIMEZONE)).date()
    except ZoneInfoNotFoundError:
        return datetime.now(timezone.utc).date()


def is_valid_api_key(key):
    if not key:
        return False

    return any(
        hmac.compare_digest(key, valid_key)
        for valid_key in VALID_API_KEYS
    )


def is_local_request():
    return request.remote_addr in LOCAL_ADDRESSES


def is_unlimited_session():
    token = request.headers.get("x-session-id", "").strip()

    if not token:
        return False

    return any(
        hmac.compare_digest(token, unlimited_token)
        for unlimited_token in DEV_UNLIMITED_SESSION_IDS
    )


def client_usage_key():
    address = request.remote_addr or "unknown"
    return hashlib.sha256(address.encode("utf-8")).hexdigest()


def _daily_bucket(key):
    global USAGE_DAY

    today = usage_date()

    if USAGE_DAY != today:
        USAGE_LOG.clear()
        USAGE_DAY = today

    return USAGE_LOG.setdefault(
        key,
        {
            "completed": 0,
            "pending": 0,
        },
    )


def _remaining_uses(key):
    with USAGE_LOCK:
        bucket = _daily_bucket(key)
        return max(
            DAILY_LIMIT_FREE
            - bucket["completed"]
            - bucket["pending"],
            0,
        )


def enforce_api_key_and_limit():
    if not request.path.startswith("/api/"):
        return None

    if request.method in {"GET", "HEAD", "OPTIONS"}:
        return None

    if is_local_request() or is_unlimited_session():
        g.usage_limit_bypassed = True
        return None

    if MONETIZATION_ACTIVE:
        api_key = request.headers.get("x-api-key")

        if not is_valid_api_key(api_key):
            return error_response("Invalid or missing API key", 403)

    key = client_usage_key()
    g.usage_limit_key = key

    with USAGE_LOCK:
        bucket = _daily_bucket(key)

        if bucket["completed"] + bucket["pending"] >= DAILY_LIMIT_FREE:
            response, status = error_response(
                (
                    "Daily limit reached "
                    f"(Free tier: {DAILY_LIMIT_FREE} successful uses per day)"
                ),
                429,
            )
            response.headers["Retry-After"] = "86400"
            return response, status

        # Reserve a slot so concurrent requests cannot exceed the limit.
        bucket["pending"] += 1
        g.usage_limit_reserved = True

    return None


def finalize_usage_limit(response):
    key = getattr(g, "usage_limit_key", None)
    reserved = getattr(g, "usage_limit_reserved", False)

    if key and reserved:
        with USAGE_LOCK:
            bucket = _daily_bucket(key)
            bucket["pending"] = max(bucket["pending"] - 1, 0)

            if 200 <= response.status_code < 300:
                bucket["completed"] += 1

    if key:
        response.headers["X-RateLimit-Limit"] = str(DAILY_LIMIT_FREE)
        response.headers["X-RateLimit-Remaining"] = str(
            _remaining_uses(key)
        )

    return response


def reset_usage_for_testing():
    global USAGE_DAY

    with USAGE_LOCK:
        USAGE_LOG.clear()
        USAGE_DAY = None
