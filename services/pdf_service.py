import io
import zipfile
import fitz

from PyPDF2 import PdfMerger, PdfReader, PdfWriter
from reportlab.pdfgen import canvas
from reportlab.lib.colors import Color
from reportlab.lib.units import inch



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


def rearrange_pdf_file(file, page_order):
    reader = PdfReader(file)
    writer = PdfWriter()

    pages = []

    for part in page_order.split(","):
        part = part.strip()

        if not part.isdigit():
            raise ValueError("Page order must contain only page numbers separated by commas.")

        page_number = int(part)

        if page_number < 1 or page_number > len(reader.pages):
            raise ValueError("Page number out of range.")

        pages.append(page_number)

    if not pages:
        raise ValueError("Page order is required.")

    for page_number in pages:
        writer.add_page(reader.pages[page_number - 1])

    output = io.BytesIO()
    writer.write(output)
    writer.close()
    output.seek(0)

    return output


def delete_pages_from_pdf(file, pages_to_delete):
    reader = PdfReader(file)
    writer = PdfWriter()

    pages = []

    for part in pages_to_delete.split(","):
        part = part.strip()

        if not part.isdigit():
            raise ValueError("Pages to delete must contain only page numbers separated by commas.")

        page_number = int(part)

        if page_number < 1 or page_number > len(reader.pages):
            raise ValueError("Page number out of range.")

        pages.append(page_number)

    if not pages:
        raise ValueError("Pages to delete are required.")

    pages_to_delete_set = set(pages)

    for index, page in enumerate(reader.pages, start=1):
        if index not in pages_to_delete_set:
            writer.add_page(page)

    output = io.BytesIO()
    writer.write(output)
    writer.close()
    output.seek(0)

    return output


def duplicate_pages_in_pdf(file, pages_to_duplicate):
    reader = PdfReader(file)
    writer = PdfWriter()

    pages = []

    for part in pages_to_duplicate.split(","):
        part = part.strip()

        if not part.isdigit():
            raise ValueError(
                "Pages to duplicate must contain only page numbers separated by commas."
            )

        page_number = int(part)

        if page_number < 1 or page_number > len(reader.pages):
            raise ValueError("Page number out of range.")

        pages.append(page_number)

    if not pages:
        raise ValueError("Pages to duplicate are required.")

    pages_to_duplicate_set = set(pages)

    for index, page in enumerate(reader.pages, start=1):
        writer.add_page(page)

        if index in pages_to_duplicate_set:
            writer.add_page(page)

    output = io.BytesIO()
    writer.write(output)
    writer.close()
    output.seek(0)

    return output


def reverse_pages_in_pdf(file):
    reader = PdfReader(file)
    writer = PdfWriter()

    for page_number in range(len(reader.pages), 0, -1):
        writer.add_page(reader.pages[page_number - 1])

    output = io.BytesIO()
    writer.write(output)
    writer.close()
    output.seek(0)

    return output


def create_text_watermark(text, color="gray", opacity=0.25, size="large"):
    packet = io.BytesIO()

    c = canvas.Canvas(packet)

    font_size = 80 if size == "large" else 40

    colors = {
        "gray": Color(0.5, 0.5, 0.5, alpha=opacity),
        "red": Color(1, 0, 0, alpha=opacity),
        "blue": Color(0, 0, 1, alpha=opacity),
        "green": Color(0, 0.6, 0, alpha=opacity),
    }

    watermark_color = colors.get(color, colors["gray"])

    c.setFont("Helvetica-Bold", font_size)
    c.setFillColor(watermark_color)

    c.saveState()
    c.translate(300, 400)
    c.rotate(45)

    c.drawCentredString(0, 0, text)

    c.restoreState()
    c.save()

    packet.seek(0)

    return PdfReader(packet)


def watermark_pdf_file(file, text, color="gray", opacity=0.25, size="large"):
    reader = PdfReader(file)
    writer = PdfWriter()

    watermark_reader = create_text_watermark(text, color, opacity, size)
    watermark_page = watermark_reader.pages[0]

    for page in reader.pages:
        page.merge_page(watermark_page)
        writer.add_page(page)

    output = io.BytesIO()
    writer.write(output)
    writer.close()
    output.seek(0)

    return output
