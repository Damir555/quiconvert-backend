import io
import unittest

import fitz

from app import app
from utils.limits import reset_usage_for_testing


TEST_IP = "203.0.113.10"


def create_pdf():
    document = fitz.open()
    page = document.new_page()
    page.insert_text((72, 72), "QuiConvert security test")
    data = document.tobytes()
    document.close()
    return io.BytesIO(data)


class SecurityTests(unittest.TestCase):
    def setUp(self):
        app.config["TESTING"] = True
        self.client = app.test_client()
        reset_usage_for_testing()

    def post_rotate(self, ip=TEST_IP, session_id=None):
        headers = {}

        if session_id:
            headers["X-Session-Id"] = session_id

        return self.client.post(
            "/api/pdf/rotate",
            data={
                "files": (create_pdf(), "test.pdf"),
                "rotation": "90",
            },
            headers=headers,
            environ_base={"REMOTE_ADDR": ip},
            content_type="multipart/form-data",
        )

    def test_allows_five_successful_uses_and_blocks_the_sixth(self):
        for expected_remaining in range(4, -1, -1):
            response = self.post_rotate()
            self.assertEqual(response.status_code, 200)
            self.assertEqual(
                response.headers.get("X-RateLimit-Remaining"),
                str(expected_remaining),
            )

        response = self.post_rotate()

        self.assertEqual(response.status_code, 429)
        self.assertEqual(response.headers.get("X-RateLimit-Remaining"), "0")
        self.assertIn("Daily limit reached", response.get_json()["error"])

    def test_failed_requests_do_not_consume_daily_uses(self):
        for _ in range(3):
            response = self.client.post(
                "/api/pdf/rotate",
                environ_base={"REMOTE_ADDR": TEST_IP},
            )
            self.assertEqual(response.status_code, 400)

        response = self.post_rotate()

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.headers.get("X-RateLimit-Remaining"), "4")

    def test_rotating_session_id_does_not_bypass_ip_limit(self):
        for number in range(5):
            response = self.post_rotate(session_id=f"changed-{number}")
            self.assertEqual(response.status_code, 200)

        response = self.post_rotate(session_id="another-session")
        self.assertEqual(response.status_code, 429)

    def test_rejects_a_file_with_a_fake_pdf_extension(self):
        response = self.client.post(
            "/api/pdf/rotate",
            data={
                "files": (io.BytesIO(b"not a pdf"), "fake.pdf"),
                "rotation": "90",
            },
            environ_base={"REMOTE_ADDR": TEST_IP},
            content_type="multipart/form-data",
        )

        self.assertEqual(response.status_code, 400)
        self.assertEqual(
            response.get_json()["error"],
            "Only valid PDF files are supported.",
        )

    def test_api_responses_include_security_headers(self):
        response = self.post_rotate()

        self.assertEqual(response.headers.get("Cache-Control"), "no-store")
        self.assertEqual(
            response.headers.get("X-Content-Type-Options"),
            "nosniff",
        )
        self.assertEqual(response.headers.get("X-Frame-Options"), "DENY")

    def test_production_cors_is_allowed_and_local_origin_is_not(self):
        production = self.client.options(
            "/api/pdf/rotate",
            headers={"Origin": "https://quiconvert.com"},
            environ_base={"REMOTE_ADDR": TEST_IP},
        )
        local = self.client.options(
            "/api/pdf/rotate",
            headers={"Origin": "http://localhost:5500"},
            environ_base={"REMOTE_ADDR": TEST_IP},
        )

        self.assertEqual(
            production.headers.get("Access-Control-Allow-Origin"),
            "https://quiconvert.com",
        )
        self.assertIsNone(local.headers.get("Access-Control-Allow-Origin"))

    def test_unknown_route_remains_a_404(self):
        response = self.client.get("/missing-route")
        self.assertEqual(response.status_code, 404)

    def test_global_request_size_limit_returns_413(self):
        previous_limit = app.config["MAX_CONTENT_LENGTH"]
        app.config["MAX_CONTENT_LENGTH"] = 256

        try:
            response = self.client.post(
                "/api/pdf/rotate",
                data={
                    "files": (io.BytesIO(b"%PDF-" + b"x" * 1024), "big.pdf"),
                    "rotation": "90",
                },
                environ_base={"REMOTE_ADDR": TEST_IP},
                content_type="multipart/form-data",
            )
        finally:
            app.config["MAX_CONTENT_LENGTH"] = previous_limit

        self.assertEqual(response.status_code, 413)
        self.assertEqual(
            response.get_json()["error"],
            "The upload request is too large.",
        )


if __name__ == "__main__":
    unittest.main()
