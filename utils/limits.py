import hashlib
import hmac
import uuid
from datetime import datetime, timedelta, timezone
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

from flask import current_app, g, request

from config import (
    DAILY_LIMIT_FREE,
    DEV_UNLIMITED_SESSION_IDS,
    MONETIZATION_ACTIVE,
    RATE_LIMIT_PREFIX,
    RATE_LIMIT_RESERVATION_SECONDS,
    REDIS_URL,
    REQUIRE_SHARED_RATE_LIMIT,
    USAGE_TIMEZONE,
    VALID_API_KEYS,
)
from utils.responses import error_response
from utils.usage_store import MemoryUsageStore, RedisUsageStore


LOCAL_ADDRESSES = {
    "127.0.0.1",
    "::1",
}


def _usage_timezone():
    try:
        return ZoneInfo(USAGE_TIMEZONE)
    except ZoneInfoNotFoundError:
        return timezone.utc


def usage_date():
    return datetime.now(_usage_timezone()).date()


def _seconds_until_bucket_expiry():
    now = datetime.now(_usage_timezone())
    next_midnight = datetime.combine(
        now.date() + timedelta(days=1),
        datetime.min.time(),
        tzinfo=now.tzinfo,
    )
    return max(int((next_midnight - now).total_seconds()) + 3600, 3600)


def _build_usage_store():
    if REDIS_URL:
        from redis import Redis

        return RedisUsageStore(
            Redis.from_url(
                REDIS_URL,
                decode_responses=True,
                socket_connect_timeout=2,
                socket_timeout=2,
                health_check_interval=30,
            ),
            RATE_LIMIT_PREFIX,
        )

    if REQUIRE_SHARED_RATE_LIMIT:
        raise RuntimeError(
            "REDIS_URL is required when REQUIRE_SHARED_RATE_LIMIT is enabled."
        )

    return MemoryUsageStore()


USAGE_STORE = _build_usage_store()


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


def usage_bucket_key(client_key):
    return f"{usage_date().isoformat()}:{client_key}"


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

    client_key = client_usage_key()
    bucket_key = usage_bucket_key(client_key)
    reservation_id = uuid.uuid4().hex
    g.usage_limit_bucket_key = bucket_key

    try:
        decision = USAGE_STORE.reserve(
            bucket_key,
            reservation_id,
            DAILY_LIMIT_FREE,
            RATE_LIMIT_RESERVATION_SECONDS,
            _seconds_until_bucket_expiry(),
        )
    except Exception:
        current_app.logger.exception("Shared usage limiter unavailable")
        return error_response(
            "Usage limit service is temporarily unavailable.",
            503,
        )

    if not decision.allowed:
        response, status = error_response(
            (
                "Daily limit reached "
                f"(Free tier: {DAILY_LIMIT_FREE} successful uses per day)"
            ),
            429,
        )
        response.headers["Retry-After"] = str(
            max(_seconds_until_bucket_expiry() - 3600, 1)
        )
        return response, status

    g.usage_limit_reservation_id = reservation_id
    g.usage_limit_reserved = True
    return None


def finalize_usage_limit(response):
    bucket_key = getattr(g, "usage_limit_bucket_key", None)
    reservation_id = getattr(g, "usage_limit_reservation_id", None)
    reserved = getattr(g, "usage_limit_reserved", False)

    if bucket_key and reserved and reservation_id:
        try:
            remaining = USAGE_STORE.finalize(
                bucket_key,
                reservation_id,
                200 <= response.status_code < 300,
                DAILY_LIMIT_FREE,
                _seconds_until_bucket_expiry(),
            )
        except Exception:
            current_app.logger.exception(
                "Unable to finalize shared usage reservation"
            )
            remaining = 0
    elif bucket_key:
        try:
            remaining = USAGE_STORE.remaining(
                bucket_key,
                DAILY_LIMIT_FREE,
            )
        except Exception:
            current_app.logger.exception(
                "Unable to read shared usage limit"
            )
            remaining = 0
    else:
        return response

    response.headers["X-RateLimit-Limit"] = str(DAILY_LIMIT_FREE)
    response.headers["X-RateLimit-Remaining"] = str(remaining)
    return response


def set_usage_store_for_testing(store):
    global USAGE_STORE
    USAGE_STORE = store


def reset_usage_for_testing():
    reset = getattr(USAGE_STORE, "reset", None)

    if reset:
        reset()
