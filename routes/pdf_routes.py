from flask import Blueprint, request, send_file

from config import UPLOAD_FIELD
from services.pdf_service import (
    merge_pdf_files,
    split_pdf_file,
    compress_pdf_file,
    rotate_pdf_file,
    rearrange_pdf_file,
    delete_pages_from_pdf,
    duplicate_pages_in_pdf,
    reverse_pages_in_pdf,
    watermark_pdf_file,
    protect_pdf_file,
    unlock_pdf_file,
)

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
    

@pdf_routes.route("/api/pdf/rotate", methods=["POST"])
def rotate_pdf():
    try:
        print("[Rotate] Started")

        file = request.files.get(UPLOAD_FIELD)

        if not file:
            return error_response("No PDF uploaded", 400)

        rotation = request.form.get("rotation", "90")

        output = rotate_pdf_file(file, rotation)

        print("[Rotate] Completed")

        return send_file(
            output,
            mimetype="application/pdf",
            as_attachment=True,
            download_name="rotated.pdf"
        )

    except Exception as e:
        print(f"[Rotate] Failed: {e}")
        return error_response(str(e), 500)
    
@pdf_routes.route("/api/pdf/rearrange", methods=["POST"])
def rearrange_pdf():
    try:
        print("[Rearrange] Started")

        file = request.files.get(UPLOAD_FIELD)

        if not file:
            return error_response("No PDF uploaded", 400)

        page_order = request.form.get("page_order", "").strip()

        output = rearrange_pdf_file(file, page_order)

        print("[Rearrange] Completed")

        return send_file(
            output,
            mimetype="application/pdf",
            as_attachment=True,
            download_name="rearranged.pdf"
        )

    except Exception as e:
        print(f"[Rearrange] Failed: {e}")
        return error_response(str(e), 500)
    
@pdf_routes.route("/api/pdf/delete-pages", methods=["POST"])
def delete_pages():
    try:
        print("[Delete Pages] Started")

        file = request.files.get(UPLOAD_FIELD)

        if not file:
            return error_response("No PDF uploaded", 400)

        pages_to_delete = request.form.get("pages", "").strip()

        output = delete_pages_from_pdf(file, pages_to_delete)

        print("[Delete Pages] Completed")

        return send_file(
            output,
            mimetype="application/pdf",
            as_attachment=True,
            download_name="deleted_pages.pdf"
        )

    except Exception as e:
        print(f"[Delete Pages] Failed: {e}")
        return error_response(str(e), 500)

@pdf_routes.route("/api/pdf/duplicate-pages", methods=["POST"])
def duplicate_pages():
    try:
        print("[Duplicate Pages] Started")

        file = request.files.get(UPLOAD_FIELD)

        if not file:
            return error_response("No PDF uploaded", 400)

        pages_to_duplicate = request.form.get("pages", "").strip()

        output = duplicate_pages_in_pdf(file, pages_to_duplicate)

        print("[Duplicate Pages] Completed")

        return send_file(
            output,
            mimetype="application/pdf",
            as_attachment=True,
            download_name="duplicated_pages.pdf"
        )

    except Exception as e:
        print(f"[Duplicate Pages] Failed: {e}")
        return error_response(str(e), 500)

@pdf_routes.route("/api/pdf/reverse-pages", methods=["POST"])
def reverse_pages():
    try:
        print("[Reverse Pages] Started")

        file = request.files.get(UPLOAD_FIELD)

        if not file:
            return error_response("No PDF uploaded", 400)

        output = reverse_pages_in_pdf(file)

        print("[Reverse Pages] Completed")

        return send_file(
            output,
            mimetype="application/pdf",
            as_attachment=True,
            download_name="reversed_pages.pdf"
        )

    except Exception as e:
        print(f"[Reverse Pages] Failed: {e}")
        return error_response(str(e), 500)

@pdf_routes.route("/api/pdf/watermark", methods=["POST"])
def watermark_pdf():
    try:
        print("[Watermark] Started")

        file = request.files.get(UPLOAD_FIELD)

        if not file:
            return error_response("No PDF uploaded", 400)

        text = request.form.get("text", "").strip()

        if not text:
            return error_response("Watermark text is required", 400)

        color = request.form.get("color", "gray").strip().lower()
        size = request.form.get("size", "large").strip().lower()
        opacity = float(request.form.get("opacity", "0.25"))

        output = watermark_pdf_file(file, text, color, opacity, size)

        print("[Watermark] Completed")

        return send_file(
            output,
            mimetype="application/pdf",
            as_attachment=True,
            download_name="watermarked.pdf"
        )

    except Exception as e:
        print(f"[Watermark] Failed: {e}")
        return error_response(str(e), 500)

@pdf_routes.route("/api/pdf/protect", methods=["POST"])
def protect_pdf():
    try:
        print("[Protect PDF] Started")

        file = request.files.get(UPLOAD_FIELD)

        if not file:
            return error_response("No PDF uploaded", 400)

        password = request.form.get("password", "").strip()

        if not password:
            return error_response("Password is required", 400)

        if len(password) < 4:
            return error_response("Password must contain at least 4 characters", 400)

        output = protect_pdf_file(file, password)

        print("[Protect PDF] Completed")

        return send_file(
            output,
            mimetype="application/pdf",
            as_attachment=True,
            download_name="protected.pdf"
        )

    except Exception as e:
        print(f"[Protect PDF] Failed: {e}")
        return error_response(str(e), 500)


@pdf_routes.route("/api/pdf/unlock", methods=["POST"])
def unlock_pdf():
    try:
        print("[Unlock PDF] Started")

        file = request.files.get(UPLOAD_FIELD)

        if not file:
            return error_response("No PDF uploaded", 400)

        password = request.form.get("password", "").strip()

        if not password:
            return error_response("Password is required", 400)

        output = unlock_pdf_file(file, password)

        print("[Unlock PDF] Completed")

        return send_file(
            output,
            mimetype="application/pdf",
            as_attachment=True,
            download_name="unlocked.pdf"
        )

    except Exception as e:
        print(f"[Unlock PDF] Failed: {e}")
        return error_response(str(e), 500)
