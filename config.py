import os
CORS_ORIGINS = [
    "https://www.quiconvert.com",
    "https://quiconvert.com",
    "http://127.0.0.1:5500",
    "http://localhost:5500"
]

MONETIZATION_ACTIVE = False

DAILY_LIMIT_FREE = 5

VALID_API_KEYS = {
    "demo123",
    "test456",
    "admin789"
}

DEV_UNLIMITED_SESSION_IDS = {
    session_id.strip()
    for session_id in os.getenv(
        "DEV_UNLIMITED_SESSION_IDS",
        ""
    ).split(",")
    if session_id.strip()
}

UPLOAD_FIELD = "files"

MAX_UPLOAD_MB = 5
MAX_UPLOAD_BYTES = MAX_UPLOAD_MB * 1024 * 1024
