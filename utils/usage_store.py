import threading
import time
from dataclasses import dataclass


@dataclass(frozen=True)
class UsageDecision:
    allowed: bool
    remaining: int


class MemoryUsageStore:
    """Process-local fallback used for development and unit tests."""

    def __init__(self):
        self._buckets = {}
        self._lock = threading.Lock()

    def reserve(
        self,
        bucket_key,
        reservation_id,
        limit,
        reservation_seconds,
        ttl_seconds,
    ):
        del ttl_seconds
        now = time.time()

        with self._lock:
            bucket = self._buckets.setdefault(
                bucket_key,
                {"completed": 0, "pending": {}},
            )
            self._remove_expired(bucket, now)
            used = bucket["completed"] + len(bucket["pending"])

            if used >= limit:
                return UsageDecision(False, 0)

            bucket["pending"][reservation_id] = now + reservation_seconds
            return UsageDecision(True, max(limit - used - 1, 0))

    def finalize(
        self,
        bucket_key,
        reservation_id,
        success,
        limit,
        ttl_seconds,
    ):
        del ttl_seconds
        now = time.time()

        with self._lock:
            bucket = self._buckets.setdefault(
                bucket_key,
                {"completed": 0, "pending": {}},
            )
            self._remove_expired(bucket, now)
            reserved = bucket["pending"].pop(reservation_id, None)

            if reserved is not None and success:
                bucket["completed"] += 1

            used = bucket["completed"] + len(bucket["pending"])
            return max(limit - used, 0)

    def remaining(self, bucket_key, limit):
        now = time.time()

        with self._lock:
            bucket = self._buckets.setdefault(
                bucket_key,
                {"completed": 0, "pending": {}},
            )
            self._remove_expired(bucket, now)
            used = bucket["completed"] + len(bucket["pending"])
            return max(limit - used, 0)

    def reset(self):
        with self._lock:
            self._buckets.clear()

    def ping(self):
        return True

    @staticmethod
    def _remove_expired(bucket, now):
        expired = [
            reservation_id
            for reservation_id, expires_at in bucket["pending"].items()
            if expires_at <= now
        ]

        for reservation_id in expired:
            bucket["pending"].pop(reservation_id, None)


class RedisUsageStore:
    """Atomic shared limiter store for all workers and service instances."""

    RESERVE_SCRIPT = """
local completed_key = KEYS[1]
local pending_key = KEYS[2]
local now = tonumber(ARGV[1])
local reservation_expires = tonumber(ARGV[2])
local reservation_id = ARGV[3]
local limit = tonumber(ARGV[4])
local ttl = tonumber(ARGV[5])

redis.call('ZREMRANGEBYSCORE', pending_key, '-inf', now)

local completed = tonumber(redis.call('GET', completed_key) or '0')
local pending = tonumber(redis.call('ZCARD', pending_key))
local used = completed + pending

if used >= limit then
    redis.call('EXPIRE', completed_key, ttl)
    redis.call('EXPIRE', pending_key, ttl)
    return {0, 0}
end

redis.call('ZADD', pending_key, 'NX', reservation_expires, reservation_id)
redis.call('EXPIRE', completed_key, ttl)
redis.call('EXPIRE', pending_key, ttl)

return {1, limit - used - 1}
"""

    FINALIZE_SCRIPT = """
local completed_key = KEYS[1]
local pending_key = KEYS[2]
local now = tonumber(ARGV[1])
local reservation_id = ARGV[2]
local success = tonumber(ARGV[3])
local limit = tonumber(ARGV[4])
local ttl = tonumber(ARGV[5])

redis.call('ZREMRANGEBYSCORE', pending_key, '-inf', now)
local removed = redis.call('ZREM', pending_key, reservation_id)

if removed == 1 and success == 1 then
    redis.call('INCR', completed_key)
end

redis.call('EXPIRE', completed_key, ttl)
redis.call('EXPIRE', pending_key, ttl)

local completed = tonumber(redis.call('GET', completed_key) or '0')
local pending = tonumber(redis.call('ZCARD', pending_key))
local remaining = limit - completed - pending

if remaining < 0 then
    remaining = 0
end

return remaining
"""

    REMAINING_SCRIPT = """
local completed_key = KEYS[1]
local pending_key = KEYS[2]
local now = tonumber(ARGV[1])
local limit = tonumber(ARGV[2])

redis.call('ZREMRANGEBYSCORE', pending_key, '-inf', now)

local completed = tonumber(redis.call('GET', completed_key) or '0')
local pending = tonumber(redis.call('ZCARD', pending_key))
local remaining = limit - completed - pending

if remaining < 0 then
    remaining = 0
end

return remaining
"""

    def __init__(self, redis_client, prefix):
        self._redis = redis_client
        self._prefix = prefix

    def reserve(
        self,
        bucket_key,
        reservation_id,
        limit,
        reservation_seconds,
        ttl_seconds,
    ):
        now = int(time.time())
        result = self._redis.eval(
            self.RESERVE_SCRIPT,
            2,
            *self._keys(bucket_key),
            now,
            now + reservation_seconds,
            reservation_id,
            limit,
            ttl_seconds,
        )
        return UsageDecision(bool(result[0]), int(result[1]))

    def finalize(
        self,
        bucket_key,
        reservation_id,
        success,
        limit,
        ttl_seconds,
    ):
        return int(
            self._redis.eval(
                self.FINALIZE_SCRIPT,
                2,
                *self._keys(bucket_key),
                int(time.time()),
                reservation_id,
                int(success),
                limit,
                ttl_seconds,
            )
        )

    def remaining(self, bucket_key, limit):
        return int(
            self._redis.eval(
                self.REMAINING_SCRIPT,
                2,
                *self._keys(bucket_key),
                int(time.time()),
                limit,
            )
        )

    def ping(self):
        return bool(self._redis.ping())

    def _keys(self, bucket_key):
        base = f"{self._prefix}:{bucket_key}"
        return f"{base}:completed", f"{base}:pending"
