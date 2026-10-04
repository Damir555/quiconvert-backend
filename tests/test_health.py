import unittest

from app import app
from utils.limits import set_usage_store_for_testing
from utils.usage_store import MemoryUsageStore


class FailingUsageStore:
    def ping(self):
        raise ConnectionError("unavailable")


class HealthTests(unittest.TestCase):
    def setUp(self):
        app.config["TESTING"] = True
        self.client = app.test_client()
        set_usage_store_for_testing(MemoryUsageStore())

    def tearDown(self):
        set_usage_store_for_testing(MemoryUsageStore())

    def test_health_does_not_depend_on_usage_store(self):
        set_usage_store_for_testing(FailingUsageStore())

        response = self.client.get("/health")

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.get_json()["status"], "healthy")

    def test_ready_succeeds_when_usage_store_is_available(self):
        response = self.client.get("/ready")

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.get_json()["status"], "ready")

    def test_ready_returns_503_when_usage_store_is_unavailable(self):
        set_usage_store_for_testing(FailingUsageStore())

        response = self.client.get("/ready")

        self.assertEqual(response.status_code, 503)
        self.assertEqual(response.get_json()["status"], "not_ready")


if __name__ == "__main__":
    unittest.main()
