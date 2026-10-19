"""Pure limiter tests, without importing app and initializing a database."""
import importlib.util
import unittest
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from unittest.mock import Mock, patch
import fakeredis

spec = importlib.util.spec_from_file_location('rate_limits', Path(__file__).parent / 'app' / 'rate_limits.py')
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)


class RateLimitTest(unittest.TestCase):
    def test_redis_workers_share_an_atomic_budget_and_namespace(self):
        server = fakeredis.FakeServer()
        clients = [fakeredis.FakeRedis(server=server) for _ in range(3)]
        workers = [module.RedisRateLimiter(client, 'test') for client in clients]
        key = ('auth.login', '192.0.2.1', 10, 60)
        with ThreadPoolExecutor(max_workers=12) as pool:
            outcomes = list(pool.map(lambda i: workers[i % 3].check(key, 10, 60), range(60)))
        self.assertEqual(outcomes.count(0), 10)
        self.assertTrue(all(0 <= result <= 60 for result in outcomes))
        stored_key = clients[0].keys()[0]
        self.assertNotIn(b'192.0.2.1', stored_key)
        self.assertEqual(clients[0].zcard(stored_key), 10)
        self.assertTrue(0 < clients[0].pttl(stored_key) <= 60000)
        isolated = module.RedisRateLimiter(clients[0], 'other-environment')
        self.assertEqual(isolated.check(key, 10, 60), 0)

    def test_redis_removes_expired_hits_without_extending_blocked_window(self):
        client = fakeredis.FakeRedis()
        limiter = module.RedisRateLimiter(client, 'test')
        self.assertEqual(limiter.check('one', 1, 60), 0)
        key = client.keys()[0]
        before = client.pttl(key)
        self.assertGreater(limiter.check('one', 1, 60), 0)
        self.assertLessEqual(client.pttl(key), before)
        member = client.zrange(key, 0, 0)[0]
        client.zadd(key, {member: 0})
        self.assertEqual(limiter.check('one', 1, 60), 0)
        self.assertEqual(client.zcard(key), 1)

    def test_redis_failure_is_safe_and_has_no_local_fallback(self):
        client = Mock()
        client.eval.side_effect = RuntimeError('fixture-private-connection-details')
        limiter = module.RedisRateLimiter(client, 'test')
        with self.assertRaises(module.RateLimitUnavailable) as caught:
            limiter.check('one', 1, 60)
        self.assertNotIn('fixture-private', str(caught.exception))
        client.eval.assert_called_once()

    def test_redis_configuration_rejects_unsafe_namespace_and_invalid_urls(self):
        self.assertIsInstance(module.build_rate_limiter({}), module.LocalRateLimiter)
        for namespace in (None, '', 'bad namespace', 'bad:namespace'):
            with self.assertRaises(ValueError):
                module.RedisRateLimiter(Mock(), namespace)
        for url in ('https://example.test', 'redis://', 'redis://localhost?socket_timeout=999'):
            with self.assertRaises(ValueError):
                module.build_rate_limiter({'RATE_LIMIT_REDIS_URL': url, 'RATE_LIMIT_NAMESPACE': 'test'})

    def test_redis_factory_is_lazy_bounded_and_uses_configured_store(self):
        with patch('redis.Redis.from_url', return_value=Mock()) as factory:
            limiter = module.build_rate_limiter({
                'RATE_LIMIT_REDIS_URL': 'rediss://fixture.example.test:6379/0',
                'RATE_LIMIT_NAMESPACE': 'fixture-staging',
            })
        self.assertIsInstance(limiter, module.RedisRateLimiter)
        self.assertEqual(factory.call_args.kwargs['socket_timeout'], 1)
        self.assertEqual(factory.call_args.kwargs['socket_connect_timeout'], 1)
        self.assertEqual(factory.call_args.kwargs['max_connections'], 20)
        limiter.client.ping.assert_not_called()

    def test_separate_keys_and_expiry(self):
        now = [100.0]
        limiter = module.LocalRateLimiter(clock=lambda: now[0])
        self.assertEqual(limiter.check('login', 1, 60), 0)
        now[0] = 110.1
        self.assertEqual(limiter.check('login', 1, 60), 50)
        self.assertEqual(limiter.check('reset', 1, 60), 0)
        now[0] = 160
        self.assertEqual(limiter.check('login', 1, 60), 0)

    def test_atomic_concurrent_budget(self):
        limiter = module.LocalRateLimiter(clock=lambda: 100)
        with ThreadPoolExecutor(max_workers=12) as pool:
            outcomes = list(pool.map(lambda _: limiter.check('same', 10, 60), range(100)))
        self.assertEqual(outcomes.count(0), 10)
        self.assertEqual(len(limiter.buckets['same'][0]), 10)

    def test_full_store_fails_closed_and_reclaims_expired_entries(self):
        now = [100]
        limiter = module.LocalRateLimiter(max_keys=2, clock=lambda: now[0])
        self.assertEqual(limiter.check('a', 1, 60), 0)
        self.assertEqual(limiter.check('b', 1, 60), 0)
        self.assertEqual(limiter.check('c', 1, 60), 60)
        self.assertEqual(len(limiter.buckets), 2)
        self.assertEqual(limiter.check('a', 1, 60), 60)
        now[0] = 161
        self.assertEqual(limiter.check('c', 1, 60), 0)
        self.assertEqual(len(limiter.buckets), 1)


if __name__ == '__main__':
    unittest.main()
