from flask import Blueprint, request, send_file

from config import UPLOAD_FIELD
from services.pdf_service import merge_pdf_files, split_pdf_file, compress_pdf_file
from utils.responses import error_response
from utils.validation import validate_file_size, file_too_large_message

pdf_routes = Blueprint("pdf_routes", __name__)


@pdf_routes.route("/api/pdf/merge", methods=["POST"])
def merge_pdfs():
    try:
        print("[Merge] Started")

        files = request.files.getlist(UPLOAD_FIELD)

        if not files:
            return error_response("No files uploaded", 400)

        output = merge_pdf_files(files)

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


@pdf_routes.route("/api/pdf/split", methods=["POST"])
def split_pdf():
    try:
        print("[Split] Started")

        file = request.files.get(UPLOAD_FIELD)

        if not file:
            return error_response("No PDF uploaded", 400)

        split_pages = request.form.get("split_pages", "").strip()

        output, mimetype, filename = split_pdf_file(file, split_pages)

        print("[Split] Completed")

        return send_file(
            output,
            mimetype=mimetype,
            as_attachment=True,
            download_name=filename
        )

    except Exception as e:
        print(f"[Split] Failed: {e}")
        return error_response(str(e), 500)


@pdf_routes.route("/api/pdf/compress", methods=["POST"])
def compress_pdf():
    try:
        print("[Compress] Started")

        file = request.files.get(UPLOAD_FIELD)

        if not file:
            return error_response("No PDF uploaded", 400)

        is_valid_size, file_size = validate_file_size(file)

        if not is_valid_size:
            return error_response(file_too_large_message(), 413)

        output = compress_pdf_file(file)

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
