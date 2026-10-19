# Shared rate limits and trusted proxies — September 19, 2026

Status: implementation and isolated tests complete; **real Redis and hosted proxy acceptance pending**. No service provisioned, credentials added, .env file modified, deployment performed or production setting changed. Local preview remains on the local limiter and trusts no proxy headers.

## Implemented

`backend/app/rate_limits.py` now offers RedisRateLimiter beside the existing bounded local fallback. The factory uses Redis only when RATE_LIMIT_REDIS_URL is configured. Invalid configured settings fail startup; runtime connection/script failures return safe 503, Retry-After: 5 and no-store before route work. There is no silent Redis-to-local fallback. Unset Redis configuration intentionally retains local development behavior; it is not sufficient for multi-worker public deployment.

The shared limiter runs one Lua script atomically: use Redis TIME, prune the sorted-set sliding window, check budget, insert a unique member only if allowed, and set TTL. Blocked requests neither add members nor extend the window. Workers share endpoint/IP limits; an explicit environment namespace prevents dev/staging/production collisions. Keys contain a SHA-256 digest of the endpoint/address/budget tuple rather than raw IPs. This is pseudonymization, not anonymization. The script limits members per key, but total Redis cardinality still requires capacity monitoring and edge abuse controls.

The Redis client has one-second connect/read timeouts, no automatic retries and a bounded 20-connection pool per application process. Backend requirements add redis==5.3.1. The test-only `requirements-test.txt` adds fakeredis[lua]==2.38.0, which executes the script in an isolated emulator; it is not a production Redis server.

`backend/app/trusted_proxy.py` wraps Werkzeug ProxyFix only if the original immediate REMOTE_ADDR belongs to an explicitly configured CIDR. It trusts only configured counts of rightmost forwarded IP/scheme values. Forwarded host, port and prefix remain untrusted. Malformed configuration, non-integer/out-of-range hop counts and universal /0 networks fail startup. Defaults trust nothing. Proxy networks must be narrow and inaccessible to arbitrary clients; broad private ranges are not automatically safe.

## Backend configuration (names only; no credentials)

| Name | Default | Requirement |
| --- | --- | --- |
| RATE_LIMIT_REDIS_URL | unset | redis:// or rediss:// connection string; use TLS or a verified private network; never expose through NEXT_PUBLIC_. Query-string options are rejected so they cannot override timeouts/TLS/client settings. |
| RATE_LIMIT_NAMESPACE | unset | Required with Redis; 1–40 ASCII letters, digits, underscores or hyphens; unique per environment, identical across its workers. |
| TRUSTED_PROXY_CIDRS | empty | Comma-separated exact trusted peer IP/CIDR list, established from actual hosting topology. |
| TRUSTED_PROXY_X_FOR | 0 | Verified trusted forwarded-IP hop count, 0–5. Nonzero requires a peer list. |
| TRUSTED_PROXY_X_PROTO | 0 | Verified trusted forwarded-scheme hop count, 0–5. Nonzero requires a peer list. |

Do not copy illustrative proxy counts from tutorials. Incorrect trust can enable IP spoofing, weaken limits or emit HSTS on falsely trusted HTTPS requests. Block direct public access that bypasses the trusted ingress. Hosted settings/service adoption still require user approval. Shared rate limiting adds a network dependency and provider-specific hosting cost, which has not been selected or approved.

## Validation

- 39 disposable-SQLite journey/security tests, eight limiter tests and four import tests pass (51 backend tests).
- Emulator tests run 60 concurrent requests through three limiter clients sharing one server and admit exactly ten; verify namespace separation, expiry, blocked TTL behavior, safe failure and bounded factory configuration.
- Flask tests verify 503 blocks AI calls, trusted peers can set IP/scheme, untrusted peers cannot, and forwarded Host cannot replace the application host.
- Python compilation, pip dependency check and Git whitespace validation pass. Frontend HTTP 200 and backend six cars confirmed.
- No frontend changes in this batch; previous 80 frontend entries/lint/types/build results were not rerun. Cookie rollout stays disabled.

## Mandatory staging acceptance

1. Use a non-production Redis namespace/data store. Choose no-eviction behavior for quota integrity; verify memory capacity, TLS/auth and network access. Evicted keys reset budgets.
2. Run two real backend processes against it: exhaust one endpoint through alternating workers, verify exact 429 behavior and Retry-After, then verify window recovery and independent endpoint budgets.
3. Interrupt Redis connectivity: protected calls must return 503 without executing provider/upload/admin work or leaking connection details; restore connectivity and verify recovery. Health paths should remain reachable.
4. Verify Redis ACLs permit EVAL/TIME/ZREMRANGEBYSCORE/ZCARD/ZRANGE/ZADD/PEXPIRE; test actual Redis version, replication/failover behavior, pool limits and latency under expected load.
5. Verify real proxy peer addresses/hop counts and ingress sanitization; test forged XFF/X-Forwarded-Proto from untrusted ingress, multiple users sharing a proxy, and HTTPS HSTS behavior.
6. Keep cookie/CORS browser acceptance, strict script CSP and per-account/global AI cost budgets on the release checklist. These are not solved by IP quotas.

## Files and rollback

Files: backend app factory/security/rate_limits; new trusted_proxy module; backend requirements and new test requirements; limiter/journey tests; this setup document, SECURITY_HEADERS_RATE_LIMITS.md, readiness and roadmap logs.

Keep the preceding local limiter and header changes. To roll back this slice, remove factory/Redis/proxy integration, dependency entries and its tests together, restoring the prior local limiter initialization. No application-data/schema rollback. Hosted environments must not downgrade to per-process quotas without an equivalent approved edge protection. Remove Redis connectivity only after deciding the safe fallback; no production change is performed here. Disabling proxy handling changes client-IP grouping, so verify that before any rollout.

References: [Redis atomic rate-limit scripting](https://redis.io/docs/latest/commands/incr/) and [Werkzeug ProxyFix trust guidance](https://werkzeug.palletsprojects.com/en/stable/middleware/proxy_fix/).
