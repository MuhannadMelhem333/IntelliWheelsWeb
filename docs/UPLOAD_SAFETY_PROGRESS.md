# Upload safety — September 22, 2026

Status: validation and non-development persistence guards implemented; Phase 4 is NOT complete. No cloud account, hosted environment, database, deployment or frontend styling changed.

## Account reservations and quota enforcement — September 22

Added transactionally reserved source-byte/count budgets to both existing upload endpoints, integrated ledger completion, concurrency/failure tests, and an explicit quota migration. Locally enabled after backup; 80 backend tests pass. No frontend changes or hosted rollout. See UPLOAD_QUOTAS.md for exact limits, fail-closed behavior, pending-reservation recovery requirements and rollback. Cloudinary is not configured locally; signed uploads are not implemented by this batch. Launch estimate 59/100.

## Integrated asset flow — September 22

Ledger IDs now flow from upload responses through editor state and listing saves. Enabled backend enforcement checks owner/type/exact URL, blocks URL-only bypasses, stores verified IDs with the listing write, and preserves same-listing legacy references. Removal drops references without deleting objects. Seventy-three backend and 85 frontend tests, lint/types/build/compilation pass. Local database backed up and additive ledger migration applied; preview backend restarted with process-local enforcement enabled. No hosted rollout. Browser discovery empty; manual QA remains. Details and rollback: MEDIA_ASSET_LEDGER.md. Readiness estimate 58/100; signed uploads, quotas, duration and cleanup still unfinished.

## Asset ledger foundation — September 22

An explicit additive migration, backup-first SQLite migration command, gated upload provenance records and owner-scoped asset lookup are now implemented. The flag remains false; no live schema or response changed. Seventy backend tests pass. This does not yet enforce listing asset ownership or storage quotas. Details, exact API, rollout, limitations and rollback: MEDIA_ASSET_LEDGER.md. Next: atomic asset/listing association and editor ID propagation before signed uploads/reservations. Launch estimate stays 56/100 until the gated foundation delivers a verified flow.

## Listing-media follow-up — September 22

Implemented `backend/app/listing_media.py:validate_listing_media` in car create/update routes. Limits match the existing editor: 12 unique image references and two unique video references across cover URL, gallery and media-gallery aliases. Repeated aliases count once; each array also has a bounded length. Partial media changes are checked with saved fields; non-media edits bypass legacy media validation. Existing records are not rewritten. This is request-time validation, not a concurrency-safe storage quota or asset-ownership proof.

Media values now require bounded strings and HTTP(S) or root-relative URLs; credentials, protocol-relative URLs, unsupported schemes, whitespace/control characters, backslashes and malformed ports/hosts are rejected. This does not fetch remote URLs, establish MIME/content safety for external URLs, restrict remote hosts or verify their ownership. Known optional `label` and `thumbnail` metadata remain supported with bounds. Unsupported metadata/entry types and non-object listing JSON produce 400 instead of silent dropping or server errors. Empty primary URLs explicitly clear saved references. Media errors occur before mutation; owner authorization still precedes edit validation.

URLs are no longer HTML-escaped or truncated before storage: query strings containing `&` survive exactly. Existing historically escaped URLs are not repaired automatically. Historical invalid media must be replaced when editing media, but does not block a price-only edit. Read-only imported `image_urls` is outside this writable media contract.

The editor now uses `src/lib/listingMediaPayload.ts` to send explicit empty cover/video URLs, fixing removed media reappearing after save. It retains ordering, deduplicates exact URLs and does not silently truncate over-limit submissions. The Next.js skill informed preserving the current Client Component and route boundary; no shell/style change was needed.

Validation: 51 journey/security + eight limiter + four import tests pass (63 backend); 83 frontend tests pass. Full ESLint, changed-file ESLint, TypeScript, Python compilation, dependency and whitespace checks pass. The restricted build failed only with `Failed to fetch Geist / Geist Mono from Google Fonts`; network-enabled retry passed with 24 generated pages. Existing Browserslist-age and Git line-ending warnings remain. Frontend/backend respond, six preview cars preserved. Browser discovery remains empty, so interactive QA is pending rather than passed.

Additional manual checks: save 12 images/two videos; remove all media and refresh; remove only the primary video while retaining the second; replace the cover; try an over-limit/invalid request and confirm the listing and draft are unchanged; edit a legacy listing's price without touching media. Confirm signed/query-string URLs render unchanged. Run these in English/Arabic and mobile/desktop. Concurrent independent edits require staging testing; request-time validation is not an atomic storage-budget reservation.

Follow-up files: new `backend/app/listing_media.py`, `backend/app/routes/cars.py`, `backend/test_public_journey.py`, `src/lib/listingMediaPayload.ts`, `src/components/listings/ListingEditorView.tsx`, `tests/listing-media-payload.test.mjs`, and the upload/readiness/roadmap documents. Roll back only the media-validator integration and payload-helper hunks with their helpers/tests; preserve prior route authentication, limiter and safe-error changes. No schema or data rollback required. Reverting the editor helper restores the removed-media persistence bug.

Next remaining deliverable: persistent asset identity/ownership and reservation contract for signed uploads. URL validation alone must never authorize asset deletion. Per-user bytes/quotas, environment folders, direct upload, validated completion, cleanup and real cloud acceptance remain unfinished.

## Original upload validation batch: behavior and references

- `backend/app/upload_validation.py:validate_upload` measures actual stream bytes before storage. Images are capped at 15 MiB, videos at 100 MiB. Pillow verifies PNG/JPEG/GIF/WebP content, extension and declared MIME, then decodes frames to reject damaged images. Empty/octet-stream MIME remains compatible with generic clients.
- Images are bounded to 10,000 pixels per dimension, 25 million pixels per frame, 100 frames and 50 million aggregate decoded pixels. Each decoded frame is checked as well as the initial canvas. Streams are rewound before the storage adapter receives them.
- Videos receive container-signature and declared MIME screening only: ftyp MP4/MOV, RIFF AVI, and EBML WebM/Matroska. This is not codec, playability, duration or malware validation. Legacy QuickTime without an ftyp box is not supported by this screening.
- `backend/app/routes/system.py:upload_image/upload_video` retains authentication, endpoint quotas and successful response shapes. Exactly one file is accepted per request. Invalid uploads return JSON 400 before any storage call. Missing/failing cloud upload returns safe JSON 503 when local fallback is disabled.
- `backend/app/__init__.py:create_app` sets local fallback only when `FLASK_ENV` is `development` (the existing unset default). Production/staging must declare their environment correctly; an unset variable still means development. No deployment setting was changed. Cloud initialization exceptions remain handled by the existing generic server-error boundary.
- Failed cloud attempts can consume a stream. Development fallback now rewinds before saving, preventing empty local files.
- The application-wide request-body limit is now 101 MiB, allowing 100 MiB video plus multipart overhead (previously 500 MiB). Larger requests receive Flask's existing 413 response, not the upload JSON 400 envelope. This limit affects other large request bodies too.
- `backend/requirements.txt` pins Pillow 12.3.0 for decoding. Existing image URLs, successful upload fields, local UUID filenames and existing media-serving routes are preserved.

## Validation

- 45 isolated journey/security tests, eight rate-limiter tests and four import tests pass: 57 total. `backend/test_public_journey.py` covers actual PNG success, corrupt/empty/renamed/MIME-mismatched images, image/video byte caps, excessive dimensions/animation, multiple files, cloud success, disabled local fallback and stream rewinding after cloud failure.
- Video test data is a synthetic container header, not a playable movie. Cloud operations are mocked. Tests use disposable data, not preview or production records.
- Python compilation and `pip check` pass. No frontend changes: lint, TypeScript, build and 80 frontend entries last passed in the preceding frontend/security batch; not rerun or claimed current here.
- Frontend `http://localhost:3000` returns 200; backend `http://localhost:5000/api/cars` returns the existing six cars. Both preview processes restarted. Browser discovery returns no connected browser; interactive acceptance remains pending.

## Manual QA pending

1. Sign in and upload a real JPEG/PNG/WebP/GIF; preview and saved listing must show the same image after refresh in English/Arabic, desktop/mobile.
2. Upload real supported video containers below 100 MiB; confirm playback and listing restoration. Check actual browser MIME variants. Do not infer this from header-only tests.
3. Submit empty, renamed, damaged, oversized and oversized-dimension files; show a recoverable error without adding media or losing the listing draft. Retry with a valid file successfully.
4. Submit duplicate file parts; expect 400 and no storage writes. Request bodies beyond 101 MiB must return 413 and a usable frontend error.
5. In isolated staging with non-development environment, test unavailable cloud storage; expect failure and no local persistence. With configured cloud storage, verify the asset remains available after restart/redeploy. Do not run destructive tests on production assets.
6. In development, simulate a consumed-stream cloud failure; fallback must save intact bytes (automated), and the browser preview must remain usable (pending).

## Remaining work

Signed direct uploads, validated/owned asset association, listing-level media count and per-user storage quotas, environment-specific folders, duration validation, deletion/orphan cleanup and moderation remain. Image parsing is not sandboxed/re-encoded and metadata is not stripped. The existing upload rate limits do not equal storage quotas. Real persistent cloud acceptance and browser checks are launch gates. No production fallback guarantee applies to a misconfigured development environment.

## Files and rollback

This batch: `backend/app/upload_validation.py`, `backend/app/__init__.py`, `backend/app/routes/system.py`, `backend/requirements.txt`, `backend/test_public_journey.py`, this document, `PUBLIC_RELEASE_READINESS.md`, `ROADMAP_CONTINUATION.md`.

Rollback only this batch's validation/configuration/storage-guard hunks and corresponding tests, removing the new helper and Pillow pin together. Preserve pre-existing auth, limiter, safe-error, frontend and database work; do not reset whole dirty files. Reverting these protections reopens unsafe uploads and ephemeral hosted persistence and is unsuitable for public deployment. No data rollback or schema change is required.
