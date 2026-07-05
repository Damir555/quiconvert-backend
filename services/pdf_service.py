import io
import zipfile
import fitz

from PyPDF2 import PdfMerger, PdfReader, PdfWriter


def merge_pdf_files(files):
    merger = PdfMerger()

    for file in files:
        merger.append(file)

    output = io.BytesIO()
    merger.write(output)
    merger.close()
    output.seek(0)

    return output


def split_pdf_file(file, split_pages):
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
        return zip_buffer, "application/zip", "split_pages.zip"

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

    return output, "application/pdf", "split_selected.pdf"


def compress_pdf_file(file):
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


    return output


def rotate_pdf_file(file, rotation):
    rotation = int(rotation)

    if rotation not in [90, 180, 270]:
        raise ValueError("Rotation must be 90, 180, or 270 degrees.")

    reader = PdfReader(file)
    writer = PdfWriter()

    for page in reader.pages:
        page.rotate(rotation)
        writer.add_page(page)

    output = io.BytesIO()
    writer.write(output)
    writer.close()
    output.seek(0)

    return output

