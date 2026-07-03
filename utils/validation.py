import io
from config import MAX_UPLOAD_BYTES, MAX_UPLOAD_MB


def validate_file_size(file):
    file.seek(0, io.SEEK_END)
    size = file.tell()
    file.seek(0)

    if size > MAX_UPLOAD_BYTES:
        return False, size

    return True, size


def file_too_large_message():
    return f"File is too large. Free limit is {MAX_UPLOAD_MB} MB."
