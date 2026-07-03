from flask import Flask, jsonify
from flask_cors import CORS

from config import CORS_ORIGINS
from routes.pdf_routes import pdf_routes
from utils.limits import enforce_api_key_and_limit

app = Flask(__name__)

CORS(
    app,
    resources={r"/api/*": {"origins": CORS_ORIGINS}},
    supports_credentials=True
)

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
