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


from PyPDF2 import PdfReader, PdfWriter
import zipfile, io

@app.route("/api/pdf/split", methods=["POST"])
def split_pdf():
    try:
        file = request.files.get("files")
        if not file:
            return jsonify({"error": "No PDF uploaded"}), 400

        split_pages = request.form.get("split_pages", "").strip()
        reader = PdfReader(file)
        output_buffer = io.BytesIO()

        # Ako nije unesen split_pages -> split every page
        if not split_pages:
            # Kreiraj ZIP s jednom stranicom po PDF-u
            zip_buffer = io.BytesIO()
            with zipfile.ZipFile(zip_buffer, "w") as zipf:
                for i, page in enumerate(reader.pages, start=1):
                    writer = PdfWriter()
                    writer.add_page(page)
                    temp_pdf = io.BytesIO()
                    writer.write(temp_pdf)
                    temp_pdf.seek(0)
                    zipf.writestr(f"page_{i}.pdf", temp_pdf.read())
            zip_buffer.seek(0)
            return send_file(zip_buffer, mimetype="application/zip",
                             as_attachment=True, download_name="split_pages.zip")

     

        # Ako je unesen split_pages -> obradi raspon(e)
        pages_to_extract = []
        for part in split_pages.split(","):
            part = part.strip()
            if "-" in part:
                start, end = part.split("-")
                pages_to_extract.extend(range(int(start), int(end) + 1))
            elif part.isdigit():
                pages_to_extract.append(int(part))

        writer = PdfWriter()
        for p in pages_to_extract:
            if 1 <= p <= len(reader.pages):
                writer.add_page(reader.pages[p - 1])

        # ispravljeno: upis u novi buffer + reset
        output_buffer = io.BytesIO()
        writer.write(output_buffer)
        writer.close()
        output_buffer.seek(0)

        return send_file(
            output_buffer,
            mimetype="application/pdf",
            as_attachment=True,
            download_name="split_selected.pdf"
        )

     
    except Exception as e:
        return jsonify({"error": str(e)}), 500



@app.route("/")
def home():
    return jsonify({"message": "QuiConvert API is running!"})


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)



