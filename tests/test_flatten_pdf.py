import io
import unittest

import fitz

from app import app
from services.pdf_service import flatten_pdf_file


def create_interactive_pdf():
    document = fitz.open()
    page = document.new_page()
    page.insert_text((72, 72), "Permanent page text")

    widget = fitz.Widget()
    widget.field_name = "customer_name"
    widget.field_type = fitz.PDF_WIDGET_TYPE_TEXT
    widget.field_value = "QuiConvert test"
    widget.rect = fitz.Rect(72, 100, 250, 130)
    page.add_widget(widget)

    page.add_text_annot((72, 170), "Test annotation")

    pdf_bytes = document.tobytes()
    document.close()

    return io.BytesIO(pdf_bytes)


class FlattenPdfFileTests(unittest.TestCase):
    def test_flattens_widgets_and_annotations_without_rasterizing_page(self):
        output = flatten_pdf_file(create_interactive_pdf())

        flattened = fitz.open(stream=output.read(), filetype="pdf")
        try:
            self.assertEqual(flattened.page_count, 1)
            self.assertFalse(flattened.is_form_pdf)

            page = flattened.load_page(0)
            self.assertIsNone(page.first_widget)
            self.assertIsNone(page.first_annot)

            page_text = page.get_text()
            self.assertIn("Permanent page text", page_text)
            self.assertIn("QuiConvert test", page_text)
        finally:
            flattened.close()

    def test_rejects_empty_upload(self):
        with self.assertRaisesRegex(ValueError, "empty"):
            flatten_pdf_file(io.BytesIO())

    def test_endpoint_returns_downloadable_flattened_pdf(self):
        client = app.test_client()

        response = client.post(
            "/api/pdf/flatten",
            data={"files": (create_interactive_pdf(), "interactive.pdf")},
            content_type="multipart/form-data",
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.mimetype, "application/pdf")
        self.assertIn(
            "flattened.pdf",
            response.headers.get("Content-Disposition", ""),
        )

        flattened = fitz.open(stream=response.data, filetype="pdf")
        try:
            self.assertFalse(flattened.is_form_pdf)
            self.assertIsNone(flattened[0].first_widget)
            self.assertIn("QuiConvert test", flattened[0].get_text())
        finally:
            flattened.close()


if __name__ == "__main__":
    unittest.main()
