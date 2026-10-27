# Authentication email: Resend HTTPS setup

Approved scope (October 26, 2026): free-tier HTTPS email integration; no purchase, DNS change or production promotion. This supports password resets only. Other contact-email transports are unchanged.

## Implementation

`backend/app/routes/auth.py:send_auth_email` selects `AUTH_EMAIL_PROVIDER` (default `smtp`). `resend` uses the already-installed requests library against the fixed `https://api.resend.com/emails` endpoint with certificate validation, no redirects and a 10-second socket timeout. It accepts only HTTP 200 with a nonempty string message ID. This is provider acceptance, not inbox delivery. Errors, quota limits, malformed responses and uncertain network outcomes return false with generic logs; there is no automatic retry or SMTP fallback. Recipients, reset links, provider response bodies and credentials are not logged. Unknown providers fail closed.

The existing reset token, canonical frontend origin, template and indistinguishable known/unknown-account JSON responses remain unchanged. Synchronous delivery still has a timing-enumeration limitation; the socket timeout is not a total request deadline. No new dependency or queue was added.

## Secure setup

1. Sign in to Resend with the intended owner account and keep the Free plan. Do not enable paid upgrades or overages. Published allowance at review: 3,000 emails/month, 100/day; verify in the account before activation.
2. Use an already-verified sender domain if available. New domain DNS records require separate owner approval. The provider's test sender is restricted and does not establish public readiness.
3. Create a sending-only API key restricted to the sender domain where supported. Store it directly in the approved staging backend's environment, never in chat, repository files, public frontend variables, logs or screenshots.
4. Configure these backend-only variables:

   | Variable | Value |
   | --- | --- |
   | `AUTH_EMAIL_PROVIDER` | `resend` |
   | `RESEND_API_KEY` | Secret sending key |
   | `AUTH_EMAIL_FROM` | Verified sender, e.g. `IntelliWheels <reset@YOUR_VERIFIED_DOMAIN>` |

5. Keep the existing `PASSWORD_RESET_ORIGIN` pointing at the correct HTTPS frontend. Run `python backend/check_release_config.py --component backend` in the securely configured process. It checks presence, not account validity, sender verification, quota or delivery.
6. Deploy the tested `dev` backend revision only to the existing staging service. Environment saves can trigger a deployment; do not assume an earlier revision contains this transport. Never promote production as part of this setup.

## Required hosted acceptance

- Use one approved disposable account/mailbox; explicitly request one reset. Confirm provider acceptance and actual inbox delivery without exposing the reset URL in logs or screenshots.
- Confirm the link opens the expected frontend origin, changes the password once, rejects reuse/expiry, revokes old sessions, and permits login with the new password.
- Confirm an unknown account gets the same public response and no email.
- Verify the Free quota and sender status in the dashboard. Local mocked 429/failure tests do not prove hosted quota handling or deliverability.
- Record results and delete only explicitly disposable fixtures through approved application workflows. Do not delete real users or database rows.

## Rollback

The default SMTP path remains available on SMTP-capable infrastructure. Do not switch Render Free back to SMTP and claim delivery works: its usual SMTP ports are blocked. If Resend must be disabled, unset the Resend secret/selector or revert the isolated code commit, and explicitly report reset delivery unavailable until a supported transport is restored. Preserve database contents and reset/session security.

Sources: [Resend send-email API](https://resend.com/docs/api-reference/emails/send-email), [Free plan](https://resend.com/pricing), [Render Free limitations](https://render.com/docs/free#other-limitations).
