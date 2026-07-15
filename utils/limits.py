from datetime import date

from flask import request

from config import (
    MONETIZATION_ACTIVE,
    DAILY_LIMIT_FREE,
    VALID_API_KEYS,
    DEV_UNLIMITED_SESSION_IDS
)

from utils.responses import error_response


USAGE_LOG = {}

LOCAL_ADDRESSES = {
    "127.0.0.1",
    "::1",
}


def is_valid_api_key(key):
    return key in VALID_API_KEYS


def is_local_request():
    return request.remote_addr in LOCAL_ADDRESSES

def is_unlimited_session(session_id):
    print("[Limit] Request session:", repr(session_id))
    print(
        "[Limit] Unlimited sessions:",
        repr(DEV_UNLIMITED_SESSION_IDS)
    )

    return session_id in DEV_UNLIMITED_SESSION_IDS

def check_usage_limit(session_id):
    today = date.today()

    user = USAGE_LOG.get(
        session_id,
        {
            "count": 0,
            "last_reset": today
        }
    )

    if user["last_reset"] != today:
        user = {
            "count": 0,
            "last_reset": today
        }

    if user["count"] >= DAILY_LIMIT_FREE:
        return False

    user["count"] += 1
    USAGE_LOG[session_id] = user

    return True


def enforce_api_key_and_limit():
    if not request.path.startswith("/api/"):
        return None

    if request.method == "OPTIONS":
        return None

    # Lokalni razvoj nema dnevno ograničenje.
    session_id = (
        request.headers.get("x-session-id")
        or request.remote_addr
)

    if is_local_request():
        return None

    if is_unlimited_session(session_id):
        return None
    

    if MONETIZATION_ACTIVE:
        api_key = request.headers.get("x-api-key")

        if not is_valid_api_key(api_key):
            return error_response(
                "Invalid or missing API key",
                403
            )

    if not check_usage_limit(session_id):
        return error_response(
            (
                "Daily limit reached "
                f"(Free tier: {DAILY_LIMIT_FREE} per day)"
            ),
            429
        )

    return None
