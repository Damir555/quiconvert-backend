from flask import Flask, jsonify, request
from werkzeug.exceptions import HTTPException, RequestEntityTooLarge
from werkzeug.middleware.proxy_fix import ProxyFix

from config import CORS_ORIGINS, MAX_REQUEST_BYTES, TRUST_PROXY_HEADERS
from routes.pdf_routes import pdf_routes
from utils.limits import enforce_api_key_and_limit, finalize_usage_limit
from utils.responses import error_response
from utils.validation import UploadValidationError, validate_request_uploads

app = Flask(__name__)
app.config["MAX_CONTENT_LENGTH"] = MAX_REQUEST_BYTES

if TRUST_PROXY_HEADERS:
    app.wsgi_app = ProxyFix(
        app.wsgi_app,
        x_for=1,
        x_proto=1,
        x_host=1,
    )

app.before_request(enforce_api_key_and_limit)


@app.before_request
def validate_upload_request():
    try:
        validate_request_uploads(request)
    except UploadValidationError as exc:
        return error_response(str(exc), exc.status_code)

    return None


@app.after_request
def add_cors_headers(response):
    response = finalize_usage_limit(response)
    origin = request.headers.get("Origin")

    if origin in CORS_ORIGINS:
        response.headers["Access-Control-Allow-Origin"] = origin
        response.headers["Vary"] = "Origin"
        response.headers["Access-Control-Allow-Methods"] = (
            "GET, POST, OPTIONS"
        )
        response.headers["Access-Control-Allow-Headers"] = (
            "Content-Type, X-Api-Key, X-Session-Id"
        )
        response.headers["Access-Control-Expose-Headers"] = (
            "Content-Disposition, X-RateLimit-Limit, "
            "X-RateLimit-Remaining"
        )

    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "DENY"
    response.headers["Referrer-Policy"] = "no-referrer"
    response.headers["Permissions-Policy"] = (
        "camera=(), microphone=(), geolocation=()"
    )

    if request.path.startswith("/api/"):
        response.headers["Cache-Control"] = "no-store"

    return response

app.register_blueprint(pdf_routes)


@app.errorhandler(RequestEntityTooLarge)
def handle_request_too_large(_error):
    return error_response("The upload request is too large.", 413)


@app.errorhandler(Exception)
def handle_unexpected_error(error):
    if isinstance(error, HTTPException):
        return error

    app.logger.exception("Unhandled request error")
    return error_response("Unable to process the request.", 500)


@app.route("/")
def home():
    return jsonify({
        "success": True,
        "message": "QuiConvert API is running!"
    })


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
