# Security headers and endpoint budgets — September 19, 2026

Follow-up: optional Redis-backed atomic shared limits and explicitly peer-allowlisted proxy handling are now implemented. Configuration, 51-test checkpoint, rollout gates and rollback are in SHARED_LIMITER_PROXY_SETUP.md. The local fallback described below remains the preview default; real Redis/proxy staging acceptance is not complete. Historical statements below that a shared implementation is still needed are superseded by that follow-up, not by a production activation.

## Delivered batch

This combines compatible Phase 2D header work and Phase 2E local rate-limit corrections. It is not completion of distributed rate limiting or all security work. No deployment, DNS, hosted settings, paid infrastructure or schema changes.

### Headers

- Next.js sends enforced CSP `base-uri 'self'; object-src 'none'; frame-ancestors 'self'`, matching existing SAMEORIGIN framing. Existing referrer, permissions and nosniff headers remain. No script/style/connect restrictions were added without browser inventory; this is deliberately **not a complete XSS policy**.
- Production Next.js emits HSTS `max-age=31536000`; development does not. No includeSubDomains or preload, so unreviewed sibling domains are not enrolled.
- Flask sends baseline `base-uri 'none'; object-src 'none'; frame-ancestors 'none'`, DENY framing, nosniff, permissions restrictions and existing referrer policy. JSON responses additionally use `default-src 'none'; form-action 'none'`.
- Swagger HTML/static assets and uploaded media use the compatibility baseline, preserving required rendering. The obsolete browser XSS auditor is explicitly disabled (`X-XSS-Protection: 0`). Flask emits HSTS only for a trusted HTTPS request, never just because a client supplies X-Forwarded-Proto.
- The previous fix letting Next.js manage development CSS caching remains untouched.

### Rate limiting

The previous global dictionary keyed solely by a client-controlled X-Forwarded-For value allowed spoofing, mixed unrelated endpoint budgets and had no concurrency lock or key bound. It is replaced by one `LocalRateLimiter` per Flask application, with monotonic sliding windows and a lock covering check/record.

Keys combine endpoint, request.remote_addr and limit/window. URL IDs share the endpoint budget, so changing IDs does not reset it. Raw forwarding headers are ignored. Blocked requests return JSON 429 with matching `retry_after` and standard Retry-After, plus no-store. OPTIONS does not consume a budget. A maximum of 10,000 keys is retained: expired keys are reclaimed at capacity; active keys are never evicted to permit bypass. If capacity remains exhausted, new keys fail closed. Requests rejected by authentication/validation still consume their endpoint budget.

| Endpoint group | Requests per IP per 60 seconds |
| --- | --- |
| Signup / login / Google / forgot / reset | Existing 5 / 10 / 10 / 3 / 5, now independent |
| Existing profile and messaging routes | Existing decorator limits retained, now independent |
| Chat, price estimate, listing assistant, AI insights | 10 each |
| Vision | 5 |
| Semantic search | 30 |
| Public listings search | 120 |
| Image / video uploads | 30 / 5 |
| Dealer application submission | 5 |
| Admin application list / detail | 60 each |
| Admin approve / reject | 20 each |

API change: newly limited endpoints may now return 429 before performing work. Models, request validation, successful payloads, authentication rules, database queries and rendering are otherwise unchanged. These conservative initial budgets require tuning with staging usage, especially shared-NAT users and multi-image uploads.

## Verified

- 80 frontend test entries, project lint and TypeScript pass. Two new tests execute the actual Next config (only the Sentry wrapper is replaced) in development/production modes and check headers plus preservation of cache ownership.
- 37 disposable-SQLite journey/security tests, three pure limiter tests and four import tests pass (44 total). New coverage includes spoofed IPs, independent auth budgets, upload preflight, AI call suppression at quota, admin authorization, HTTPS/header/error behavior, exact expiry, concurrent limits and capacity recovery.
- Python compilation passes. HTTP checks confirm both live previews return 200, both send the new CSP headers, and backend still serves six cars.
- Production build passes (24 pages), with network access for the existing Google Fonts. Existing Browserslist-age and Git CRLF notices remain. Git whitespace validation passes.
- No real AI, SMTP, cloud upload, production database or browser interactions are exercised by these tests. The injected transaction failure logs its expected fixed event only.

## Remaining launch gates

1. **Shared store:** this is a process-local fallback. Multiple workers each have their own allowance and restarts clear it. Implement/test a shared atomic store before claiming cluster-wide enforcement. No Redis service has been provisioned or paid for. Per-account/global cost budgets also remain future work.
2. **Proxy topology:** deploy behind a trusted, explicitly configured proxy chain or edge rate limiter before enabling public traffic. Without that configuration, a reverse proxy can group many users under one remote_addr. Do not restore blind first-XFF trust. Correct proxy counts and direct-origin access controls require staging evidence.
3. **Strict CSP:** inventory Next inline scripts, Google OAuth/Analytics, maps, API/media and Sentry origins in a connected browser before adding nonce/hash script policy. Baseline CSP does not block script injection. Test English/Arabic, upload preview, Google login, maps and mobile UI.
4. **HTTPS:** verify actual frontend/backend edge HSTS and TLS behavior in staging. Flask behind TLS termination needs trusted scheme handling or an edge-owned HSTS header; this patch does not assume it.
5. **Broader security:** cookie rollout, legacy sessions, distributed abuse/cost budgets and operational logging review remain outstanding.

References: [Flask trusted proxy guidance](https://flask.palletsprojects.com/en/stable/deploying/proxy_fix/) and [MDN CSP directives](https://developer.mozilla.org/en-US/docs/Web/HTTP/Reference/Headers/Content-Security-Policy).

## Files and rollback

Changed: next.config.ts; backend app factory/security; AI, cars, system and dealers routes; new backend/app/rate_limits.py; journey tests; new backend/test_rate_limits.py; new tests/security-headers.test.mjs; this document and readiness/roadmap logs.

Also added a narrow .gitignore exception so the new permanent limiter test is not excluded by the repository's broad test_*.py rule.

Rollback only this batch's header entries, limiter integration and route decorators/tests together. Preserve earlier endpoint security, cookie/hash changes and Next cache repair. Reverting to the old limiter reintroduces confirmed vulnerabilities, so do not use that as a public-deployment fix. No data rollback is needed. Removing an HSTS header does not clear a browser's cached policy: if it has been deployed, serve max-age=0 over valid HTTPS for a deliberate rollback; no such deployment was performed here.
