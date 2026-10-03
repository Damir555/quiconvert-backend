import os


def env_flag(name, default=False):
    value = os.getenv(name)

    if value is None:
        return default

    return value.strip().lower() in {"1", "true", "yes", "on"}


def env_int(name, default):
    value = os.getenv(name)

    if value is None:
        return default

    try:
        return int(value)
    except ValueError:
        return default


CORS_ORIGINS = [
    "https://www.quiconvert.com",
    "https://quiconvert.com",
]

if env_flag("ALLOW_LOCAL_CORS"):
    CORS_ORIGINS.extend([
        "http://127.0.0.1:5500",
        "http://localhost:5500",
        "http://127.0.0.1:5173",
        "http://localhost:5173",
    ])

MONETIZATION_ACTIVE = env_flag("MONETIZATION_ACTIVE")

DAILY_LIMIT_FREE = max(1, env_int("DAILY_LIMIT_FREE", 5))
USAGE_TIMEZONE = os.getenv("USAGE_TIMEZONE", "Europe/Zagreb")

VALID_API_KEYS = {
    key.strip()
    for key in os.getenv("VALID_API_KEYS", "").split(",")
    if key.strip()
}

DEV_UNLIMITED_SESSION_IDS = {
    session_id.strip()
    for session_id in os.getenv(
        "DEV_UNLIMITED_SESSION_IDS",
        "",
    ).split(",")
    if session_id.strip()
}

TRUST_PROXY_HEADERS = env_flag("TRUST_PROXY_HEADERS")

UPLOAD_FIELD = "files"

MAX_UPLOAD_MB = max(1, env_int("MAX_UPLOAD_MB", 5))
MAX_UPLOAD_BYTES = MAX_UPLOAD_MB * 1024 * 1024
MAX_FILES_PER_REQUEST = max(1, env_int("MAX_FILES_PER_REQUEST", 10))
MAX_TOTAL_UPLOAD_MB = max(
    MAX_UPLOAD_MB,
    env_int("MAX_TOTAL_UPLOAD_MB", 25),
)
MAX_TOTAL_UPLOAD_BYTES = MAX_TOTAL_UPLOAD_MB * 1024 * 1024
MAX_PDF_PAGES = max(1, env_int("MAX_PDF_PAGES", 250))

# Allow enough multipart overhead while rejecting unexpectedly large requests
# before Flask loads them into memory.
MAX_REQUEST_BYTES = MAX_TOTAL_UPLOAD_BYTES + (1024 * 1024)
