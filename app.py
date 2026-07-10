from flask import Flask, jsonify, request

from config import CORS_ORIGINS
from routes.pdf_routes import pdf_routes
from utils.limits import enforce_api_key_and_limit

app = Flask(__name__)


@app.after_request
def add_cors_headers(response):
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
            "Content-Disposition"
        )

    return response


app.before_request(enforce_api_key_and_limit)
app.register_blueprint(pdf_routes)


@app.route("/")
def home():
    return jsonify({
        "success": True,
        "message": "QuiConvert API is running!"
    })


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)