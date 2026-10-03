# QuiConvert backend

Flask API used by the QuiConvert PDF tools.

## Security limits

The production service applies the following defaults:

- 5 successful API operations per client IP and calendar day
- 5 MB per uploaded file
- 25 MB combined upload size per request
- 10 files per request
- 250 PDF pages per request

Invalid and failed requests do not consume a daily operation. The current
rate-limit store is held in the running application process, so it resets when
the Render service restarts. A shared persistent store will be required before
running multiple web-service instances or offering paid quotas.

## Environment variables

| Variable | Default | Purpose |
| --- | --- | --- |
| `DAILY_LIMIT_FREE` | `5` | Successful operations allowed per day |
| `USAGE_TIMEZONE` | `Europe/Zagreb` | Calendar day used for the daily reset |
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
