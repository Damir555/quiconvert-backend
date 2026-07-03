import fitz
from flask import Flask, request, send_file, jsonify
from flask_cors import CORS
from PyPDF2 import PdfMerger, PdfReader, PdfWriter
import io
import zipfile
from datetime import date

app = Flask(__name__)

CORS(
    app,
    resources={r"/api/*": {"origins": ["https://www.quiconvert.com", "https://quiconvert.com"]}},
    supports_credentials=True
)

MONETIZATION_ACTIVE = False
DAILY_LIMIT_FREE = 5
USAGE_LOG = {}
VALID_API_KEYS = {"demo123", "test456", "admin789"}
UPLOAD_FIELD = "files"
MAX_UPLOAD_MB = 5
MAX_UPLOAD_BYTES = MAX_UPLOAD_MB * 1024 * 1024

def error_response(message, status=500):
    def validate_file_size(file):
    file.seek(0, io.SEEK_END)
    size = file.tell()
    file.seek(0)

    if size > MAX_UPLOAD_BYTES:
        return False, size

    return True, size
    return jsonify({"success": False, "error": message}), status


def is_valid_api_key(key):
    return key in VALID_API_KEYS


def check_usage_limit(session_id):
    today = date.today()
    user = USAGE_LOG.get(session_id, {"count": 0, "last_reset": today})

    if user["last_reset"] != today:
        user = {"count": 0, "last_reset": today}

    if user["count"] >= DAILY_LIMIT_FREE:
        return False

    user["count"] += 1
    USAGE_LOG[session_id] = user
    return True


@app.before_request
def enforce_api_key_and_limit():
    if not request.path.startswith("/api/"):
        return

    if request.method == "OPTIONS":
        return

    session_id = request.headers.get("x-session-id") or request.remote_addr

    if MONETIZATION_ACTIVE:
        api_key = request.headers.get("x-api-key")
        if not is_valid_api_key(api_key):
            return error_response("Invalid or missing API key", 403)

    if not check_usage_limit(session_id):
        return error_response("Daily limit reached (Free tier: 5 per day)", 429)


@app.route("/")
def home():
    return jsonify({
        "success": True,
        "message": "QuiConvert API is running!"
    })


# DOC-001 — Merge PDF
@app.route("/api/pdf/merge", methods=["POST"])
def merge_pdfs():
    try:
        print("[Merge] Started")

        files = request.files.getlist(UPLOAD_FIELD)
        if not files:
            return error_response("No files uploaded", 400)

        merger = PdfMerger()

        for file in files:
            merger.append(file)

        output = io.BytesIO()
        merger.write(output)
        merger.close()
        output.seek(0)

        print("[Merge] Completed")

        return send_file(
            output,
            mimetype="application/pdf",
            as_attachment=True,
            download_name="merged.pdf"
        )

    except Exception as e:
        print(f"[Merge] Failed: {e}")
        return error_response(str(e), 500)


# DOC-002 — Split PDF
@app.route("/api/pdf/split", methods=["POST"])
def split_pdf():
    try:
        print("[Split] Started")

        file = request.files.get(UPLOAD_FIELD)
        if not file:
            return error_response("No PDF uploaded", 400)

        split_pages = request.form.get("split_pages", "").strip()
        reader = PdfReader(file)

        if not split_pages:
            zip_buffer = io.BytesIO()

            with zipfile.ZipFile(zip_buffer, "w") as zipf:
                for i, page in enumerate(reader.pages, start=1):
                    writer = PdfWriter()
                    writer.add_page(page)

                    temp_pdf = io.BytesIO()
                    writer.write(temp_pdf)
                    writer.close()
                    temp_pdf.seek(0)

                    zipf.writestr(f"page_{i}.pdf", temp_pdf.read())

            zip_buffer.seek(0)

            print("[Split] Completed: every page")

            return send_file(
                zip_buffer,
                mimetype="application/zip",
                as_attachment=True,
                download_name="split_pages.zip"
            )

        pages_to_extract = []

        for part in split_pages.split(","):
            part = part.strip()

            if "-" in part:
                start, end = part.split("-")
                pages_to_extract.extend(range(int(start), int(end) + 1))
            elif part.isdigit():
                pages_to_extract.append(int(part))

        writer = PdfWriter()

        for page_number in pages_to_extract:
            if 1 <= page_number <= len(reader.pages):
                writer.add_page(reader.pages[page_number - 1])

        output = io.BytesIO()
        writer.write(output)
        writer.close()
        output.seek(0)

        print("[Split] Completed: selected pages")

        return send_file(
            output,
            mimetype="application/pdf",
            as_attachment=True,
            download_name="split_selected.pdf"
        )

    except Exception as e:
        print(f"[Split] Failed: {e}")
        return error_response(str(e), 500)


@app.route("/api/pdf/compress", methods=["POST"])
def compress_pdf():
    try:
        print("[Compress] Started")

        file = request.files.get(UPLOAD_FIELD)
        

        if not file:
            return error_response("No PDF uploaded", 400)
            is_valid_size, file_size = validate_file_size(file)

if not is_valid_size:
    return error_response(
        f"File is too large. Free limit is {MAX_UPLOAD_MB} MB.",
        413
    )

        pdf = fitz.open(stream=file.read(), filetype="pdf")

        output = io.BytesIO()

        pdf.save(
            output,
            garbage=4,
            deflate=True,
            clean=True
        )

        pdf.close()

        output.seek(0)

        print("[Compress] Completed")

        return send_file(
            output,
            mimetype="application/pdf",
            as_attachment=True,
            download_name="compressed.pdf"
        )

    except Exception as e:
        print(f"[Compress] Failed: {e}")
        return error_response(str(e), 500)


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)


