import io

import fitz

from config import (
    MAX_FILES_PER_REQUEST,
    MAX_PDF_PAGES,
    MAX_TOTAL_UPLOAD_BYTES,
    MAX_TOTAL_UPLOAD_MB,
    MAX_UPLOAD_BYTES,
    MAX_UPLOAD_MB,
    UPLOAD_FIELD,
)


class UploadValidationError(ValueError):
    def __init__(self, message, status_code=400):
        super().__init__(message)
        self.status_code = status_code


def file_size(file):
    file.seek(0, io.SEEK_END)
    size = file.tell()
    file.seek(0)
    return size


def validate_file_size(file):
    size = file_size(file)
    return size <= MAX_UPLOAD_BYTES, size


def file_too_large_message():
    return f"File is too large. Free limit is {MAX_UPLOAD_MB} MB."


def _read_signature(file, length=12):
    file.seek(0)
    signature = file.read(length)
    file.seek(0)
    return signature


def _is_pdf(file):
    return _read_signature(file, 5) == b"%PDF-"


def _is_supported_image(file):
    signature = _read_signature(file)
    return signature.startswith(b"\xff\xd8\xff")


def _pdf_page_count(file):
    file.seek(0)
    data = file.read()
    file.seek(0)

    try:
        document = fitz.open(stream=data, filetype="pdf")
    except Exception as exc:
        raise UploadValidationError(
            "The uploaded file is not a valid PDF."
        ) from exc

    try:
        if document.page_count < 1:
            raise UploadValidationError("The PDF contains no pages.")

        return document.page_count
    finally:
        document.close()


def validate_request_uploads(request):
    if not request.path.startswith("/api/pdf/"):
        return

    files = [
        file
        for file in request.files.getlist(UPLOAD_FIELD)
        if file and file.filename
    ]

    # Individual routes retain their more specific "no file" messages.
    if not files:
        return

    if len(files) > MAX_FILES_PER_REQUEST:
        raise UploadValidationError(
            (
                "Too many files. "
                f"Maximum is {MAX_FILES_PER_REQUEST} files per request."
            ),
            413,
        )

    sizes = [file_size(file) for file in files]

    if any(size == 0 for size in sizes):
        raise UploadValidationError("Empty files are not supported.")

    if any(size > MAX_UPLOAD_BYTES for size in sizes):
        raise UploadValidationError(file_too_large_message(), 413)

    if sum(sizes) > MAX_TOTAL_UPLOAD_BYTES:
        raise UploadValidationError(
            (
                "The combined upload is too large. "
                f"Free limit is {MAX_TOTAL_UPLOAD_MB} MB per request."
            ),
            413,
        )

    if request.path.endswith("/image-to-pdf"):
        if any(not _is_supported_image(file) for file in files):
            raise UploadValidationError(
                "Only valid JPEG images are currently supported."
            )
        return

    if any(not _is_pdf(file) for file in files):
        raise UploadValidationError("Only valid PDF files are supported.")

    total_pages = sum(_pdf_page_count(file) for file in files)

    if total_pages > MAX_PDF_PAGES:
        raise UploadValidationError(
            (
                "The document has too many pages. "
                f"Free limit is {MAX_PDF_PAGES} pages per request."
            ),
            413,
        )
