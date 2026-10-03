import io
import unittest

import fitz
from PIL import Image

from app import app


def create_pdf(page_count=3):
    document = fitz.open()

    for page_number in range(1, page_count + 1):
        page = document.new_page()
        page.insert_text((72, 72), f"QuiConvert page {page_number}")

    data = document.tobytes()
    document.close()
    return data


def create_jpeg():
    output = io.BytesIO()
    Image.new("RGB", (32, 32), "white").save(output, format="JPEG")
    return output.getvalue()


class ApiSmokeTests(unittest.TestCase):
    def setUp(self):
        app.config["TESTING"] = True
        self.client = app.test_client()
        self.pdf = create_pdf()

    def post_pdf(self, path, fields=None, files=None):
        data = dict(fields or {})
        uploads = files or [(self.pdf, "test.pdf")]
        data["files"] = [
            (io.BytesIO(content), filename)
            for content, filename in uploads
        ]

        return self.client.post(
            path,
            data=data,
            content_type="multipart/form-data",
        )

    def test_existing_pdf_tools_still_return_downloads(self):
        cases = [
            (
                "/api/pdf/merge",
                {},
                [(self.pdf, "one.pdf"), (self.pdf, "two.pdf")],
                "application/pdf",
            ),
            ("/api/pdf/split", {"split_pages": "1-2"}, None, "application/pdf"),
            ("/api/pdf/compress", {}, None, "application/pdf"),
            ("/api/pdf/rotate", {"rotation": "90"}, None, "application/pdf"),
            ("/api/pdf/rearrange", {"page_order": "3,1,2"}, None, "application/pdf"),
            ("/api/pdf/delete-pages", {"pages": "2"}, None, "application/pdf"),
            ("/api/pdf/duplicate-pages", {"pages": "2"}, None, "application/pdf"),
            ("/api/pdf/extract-pages", {"pages": "1,3"}, None, "application/pdf"),
            ("/api/pdf/reverse-pages", {}, None, "application/pdf"),
            (
                "/api/pdf/watermark",
                {"text": "QuiConvert", "opacity": "0.25"},
                None,
                "application/pdf",
            ),
            ("/api/pdf/page-numbers", {}, None, "application/pdf"),
            ("/api/pdf/pdf-to-images", {}, None, "application/zip"),
        ]

        for path, fields, files, mimetype in cases:
            with self.subTest(path=path):
                response = self.post_pdf(path, fields, files)
                self.assertEqual(response.status_code, 200)
                self.assertEqual(response.mimetype, mimetype)
                self.assertTrue(response.data)

    def test_protect_then_unlock_still_works(self):
        protected = self.post_pdf(
            "/api/pdf/protect",
            {"password": "secret123"},
        )
        self.assertEqual(protected.status_code, 200)

        unlocked = self.post_pdf(
            "/api/pdf/unlock",
            {"password": "secret123"},
            [(protected.data, "protected.pdf")],
        )
        self.assertEqual(unlocked.status_code, 200)
        self.assertEqual(unlocked.mimetype, "application/pdf")

    def test_image_to_pdf_still_works_for_jpeg(self):
        response = self.post_pdf(
            "/api/pdf/image-to-pdf",
            files=[(create_jpeg(), "image.jpg")],
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.mimetype, "application/pdf")


if __name__ == "__main__":
    unittest.main()
