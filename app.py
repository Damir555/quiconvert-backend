from flask import Flask, request, send_file, jsonify
from flask_cors import CORS
from PyPDF2 import PdfMerger
import io
from datetime import date

app = Flask(__name__)

# ✅ Dozvoljava komunikaciju s tvoje WordPress domene
CORS(app, resources={r"/api/*": {"origins": ["https://www.quiconvert.com", "https://quiconvert.com"]}},
     supports_credentials=True)

# ✅ Monetizacija je ugrađena, ali trenutno ISKLJUČENA
MONETIZATION_ACTIVE = False

# ✅ Free-tier limit: 5 obrada (merge/split) dnevno
DAILY_LIMIT_FREE = 5

# usage log prema session_id (ili IP ako nema tokena)
USAGE_LOG = {}  # { session_id: { "count": int, "last_reset": date } }

# Hardkodirani testni API ključevi – koristi se tek kad se monetizacija uključi
VALID_API_KEYS = {"demo123", "test456", "admin789"}


def is_valid_api_key(key):
    """Provjera je li ključ valjan."""
    return key in VALID_API_KEYS


def check_usage_limit(session_id):
    """Provjerava dnevni limit korištenja po session-u."""
    today = date.today()
    user = USAGE_LOG.get(session_id, {"count": 0, "last_reset": today})
    # Reset dnevnog brojača ako je novi dan
    if user["last_reset"] != today:
        user = {"count": 0, "last_reset": today}
    if user["count"] >= DAILY_LIMIT_FREE:
        return False
    user["count"] += 1
    USAGE_LOG[session_id] = user
    return True


@app.before_request
def enforce_api_key_and_limit():
    """Opcionalna provjera API ključa i dnevnog limita."""
    if not request.path.startswith("/api/"):
        return
    if MONETIZATION_ACTIVE:
        # Provjera API ključa
        api_key = request.headers.get("x-api-key")
        if not is_valid_api_key(api_key):
            return jsonify({"error": "Invalid or missing API key"}), 403
        # Provjera dnevnog limita
        session_id = request.headers.get("x-session-id") or request.remote_addr
        if not check_usage_limit(session_id):
            return jsonify({"error": "Daily limit reached for Free users"}), 429
    else:
        # Free tier limit je aktivan čak i kad monetizacija nije
        session_id = request.headers.get("x-session-id") or request.remote_addr
        if not check_usage_limit(session_id):
            return jsonify({"error": "Daily limit reached (Free tier: 5 per day)"}), 429


# ✅ Spajanje PDF-ova
@app.route("/api/pdf/merge", methods=["POST"])
def merge_pdfs():
    try:
        files = request.files.getlist("files")
        if not files:
            return jsonify({"error": "No files uploaded"}), 400

        merger = PdfMerger()
        for f in files:
            merger.append(f)

        output = io.BytesIO()
        merger.write(output)
        output.seek(0)
        merger.close()

        return send_file(
            output,
            mimetype="application/pdf",
            as_attachment=True,
            download_name="merged.pdf",
        )

    except Exception as e:
        return jsonify({"error": str(e)}), 500


# ✅ Placeholder ruta za SPLIT (implementirat ćemo uskoro)
@app.route("/api/pdf/split", methods=["POST"])
def split_pdf():
    return jsonify({"message": "Split function coming soon"}), 200


@app.route("/")
def home():
    return jsonify({"message": "QuiConvert API is running!"})


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
