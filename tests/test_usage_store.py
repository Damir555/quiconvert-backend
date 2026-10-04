import unittest
from unittest.mock import Mock, patch

from utils.usage_store import (
    MemoryUsageStore,
    RedisUsageStore,
)


class MemoryUsageStoreTests(unittest.TestCase):
    def test_reservations_prevent_concurrent_oversubscription(self):
        store = MemoryUsageStore()

        first = store.reserve("client", "one", 2, 60, 3600)
        second = store.reserve("client", "two", 2, 60, 3600)
        third = store.reserve("client", "three", 2, 60, 3600)

        self.assertTrue(first.allowed)
        self.assertTrue(second.allowed)
        self.assertFalse(third.allowed)
        self.assertEqual(third.remaining, 0)

    def test_failed_operation_releases_reservation(self):
        store = MemoryUsageStore()
        store.reserve("client", "failed", 1, 60, 3600)

        remaining = store.finalize(
            "client",
            "failed",
            False,
            1,
            3600,
        )
        retry = store.reserve("client", "retry", 1, 60, 3600)

        self.assertEqual(remaining, 1)
        self.assertTrue(retry.allowed)


class RedisUsageStoreTests(unittest.TestCase):
    @patch("utils.usage_store.time.time", return_value=1000)
    def test_reserve_uses_atomic_script_and_shared_keys(self, _time):
        redis_client = Mock()
        redis_client.eval.return_value = [1, 4]
        store = RedisUsageStore(redis_client, "qc")

        decision = store.reserve(
            "2026-10-04:client",
            "reservation",
            5,
            900,
            3600,
        )

        self.assertTrue(decision.allowed)
        self.assertEqual(decision.remaining, 4)
        call = redis_client.eval.call_args.args
        self.assertEqual(call[1], 2)
        self.assertEqual(
            call[2:4],
            (
                "qc:2026-10-04:client:completed",
                "qc:2026-10-04:client:pending",
            ),
        )

    @patch("utils.usage_store.time.time", return_value=1000)
    def test_finalize_counts_only_a_successful_reserved_operation(self, _time):
        redis_client = Mock()
        redis_client.eval.return_value = 3
        store = RedisUsageStore(redis_client, "qc")

        remaining = store.finalize(
            "2026-10-04:client",
            "reservation",
            True,
            5,
            3600,
        )

        self.assertEqual(remaining, 3)
        call = redis_client.eval.call_args.args
        self.assertEqual(call[6], 1)


if __name__ == "__main__":
    unittest.main()
