# QuiConvert backend

Flask API used by the QuiConvert PDF tools.

## Security limits

The production service applies the following defaults:

- 5 successful API operations per client IP and calendar day
- 5 MB per uploaded file
- 25 MB combined upload size per request
- 10 files per request
- 250 PDF pages per request

Invalid and failed requests do not consume a daily operation. Production uses
a Redis-compatible shared store so every Gunicorn worker and web-service
instance sees the same atomic counter. In-flight operations reserve a slot and
release it after a failed response.

Local development falls back to an in-process store when `REDIS_URL` is not
set. Production should set `REQUIRE_SHARED_RATE_LIMIT=true`, which prevents the
service from starting without a shared store.

## Environment variables

| Variable | Default | Purpose |
| --- | --- | --- |
| `DAILY_LIMIT_FREE` | `5` | Successful operations allowed per day |
| `USAGE_TIMEZONE` | `Europe/Zagreb` | Calendar day used for the daily reset |
| `REDIS_URL` | empty | Redis-compatible shared-store connection URL |
| `REQUIRE_SHARED_RATE_LIMIT` | `false` | Refuse startup unless `REDIS_URL` is configured |
| `RATE_LIMIT_PREFIX` | `quiconvert:usage` | Namespace for usage keys |
| `RATE_LIMIT_RESERVATION_SECONDS` | `900` | Expiry for an interrupted in-flight operation |
| `MAX_UPLOAD_MB` | `5` | Maximum size of one uploaded file |
| `MAX_TOTAL_UPLOAD_MB` | `25` | Maximum combined upload size |
| `MAX_FILES_PER_REQUEST` | `10` | Maximum number of uploaded files |
| `MAX_PDF_PAGES` | `250` | Maximum combined PDF page count |
| `TRUST_PROXY_HEADERS` | `false` | Trust one reverse proxy for client IPs |
| `ALLOW_LOCAL_CORS` | `false` | Allow the local development origins |
| `DEV_UNLIMITED_SESSION_IDS` | empty | Optional high-entropy test tokens |
| `MONETIZATION_ACTIVE` | `false` | Require configured API keys |
| `VALID_API_KEYS` | empty | Comma-separated API keys from the environment |

Never commit real tokens, passwords, certificates, or `.env` files.

## Render deployment

The included Blueprint creates a private Render Key Value instance and injects
its internal connection string as `REDIS_URL`. If the web service is managed
manually instead of by this Blueprint, create a Key Value instance in the same
region, add its internal URL as `REDIS_URL`, and set
`REQUIRE_SHARED_RATE_LIMIT=true` before deploying this version.

The Free Key Value plan keeps counters shared across workers, but Render can
erase them when that free datastore restarts. Use a paid persistent Key Value
plan before relying on the limiter for paid quotas or strict production
accounting.
