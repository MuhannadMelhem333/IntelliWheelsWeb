"""Bounded, thread-safe per-process fallback; not a distributed quota store."""
import math
import time
import hashlib
import json
import re
import secrets
from collections import deque
from threading import Lock


class RateLimitUnavailable(Exception):
    """Safe failure with no service URL, credential or underlying error."""


SLIDING_WINDOW_SCRIPT = """
local now = redis.call('TIME')
local ms = tonumber(now[1]) * 1000 + math.floor(tonumber(now[2]) / 1000)
local window = tonumber(ARGV[2]) * 1000
redis.call('ZREMRANGEBYSCORE', KEYS[1], '-inf', ms - window)
if redis.call('ZCARD', KEYS[1]) >= tonumber(ARGV[1]) then
    local first = redis.call('ZRANGE', KEYS[1], 0, 0, 'WITHSCORES')
    return math.max(1, math.ceil((tonumber(first[2]) + window - ms) / 1000))
end
redis.call('ZADD', KEYS[1], ms, ARGV[3])
redis.call('PEXPIRE', KEYS[1], window)
return 0
"""


class RedisRateLimiter:
    def __init__(self, client, namespace):
        if not isinstance(namespace, str) or not re.fullmatch(r'[A-Za-z0-9_-]{1,40}', namespace):
            raise ValueError('A valid RATE_LIMIT_NAMESPACE is required for Redis')
        self.client = client
        self.prefix = f'iw:limits:{namespace}:'

    def check(self, key, limit, window):
        digest = hashlib.sha256(json.dumps(key, separators=(',', ':')).encode()).hexdigest()
        try:
            result = self.client.eval(SLIDING_WINDOW_SCRIPT, 1, self.prefix + digest,
                                      limit, window, secrets.token_hex(16))
            if not isinstance(result, int) or result < 0 or result > window:
                raise ValueError('Invalid limiter result')
            return result
        except Exception:
            raise RateLimitUnavailable('Rate limiting temporarily unavailable') from None


def build_rate_limiter(config):
    url = config.get('RATE_LIMIT_REDIS_URL')
    if not url:
        return LocalRateLimiter()
    from urllib.parse import urlsplit
    try:
        parsed = urlsplit(url)
        if parsed.scheme not in ('redis', 'rediss') or not parsed.hostname or parsed.query or parsed.fragment:
            raise ValueError()
        import redis
        from redis.backoff import NoBackoff
        from redis.retry import Retry
        client = redis.Redis.from_url(url, socket_connect_timeout=1, socket_timeout=1,
                                      retry=Retry(NoBackoff(), 0), max_connections=20)
        return RedisRateLimiter(client, config.get('RATE_LIMIT_NAMESPACE'))
    except Exception:
        raise ValueError('Invalid Redis rate-limit configuration') from None


class LocalRateLimiter:
    def __init__(self, max_keys=10000, clock=time.monotonic):
        self.max_keys = max_keys
        self.clock = clock
        self.buckets = {}
        self.lock = Lock()

    def check(self, key, limit, window):
        with self.lock:
            now = self.clock()
            bucket = self.buckets.get(key)
            if bucket is None:
                if len(self.buckets) >= self.max_keys:
                    # Evict only expired buckets, never active limits.
                    self.buckets = {k: v for k, v in self.buckets.items() if v[1] > now}
                if len(self.buckets) >= self.max_keys:
                    return window  # Fail closed instead of growing without bound.
                bucket = (deque(), now + window)
            hits = bucket[0]
            while hits and hits[0] <= now - window:
                hits.popleft()
            if len(hits) >= limit:
                return max(1, math.ceil(hits[0] + window - now))
            hits.append(now)
            self.buckets[key] = (hits, now + window)
            return 0
