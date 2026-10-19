# Upload accounting hold and recovery API — September 23, 2026

Status: implemented and tested behind the existing disabled direct-upload gate. Not a completed replay-proof architecture or public rollout.

## Editor integration — latest September 23 update

The earlier “no recovery UI” limitation below is now superseded. `UploadRecovery` is mounted inside the existing listing editor's client boundary, keyed by session token and listing. Typed API functions fetch private recovery pages and explicitly request completion. No request runs on mount: the user chooses **Recover previous uploads**, **Verify and preview**, then **Add to listing**. Adding changes only the draft; normal listing save persists the owned asset ID. Page navigation replaces the bounded recovery page, with the first-page button always available.

The new controls have English/Arabic copy, RTL and light/dark styles. Image/video previews use the verified completion URL. Buttons are non-submit controls, pending work is announced, and failures show a safe retry message. Disabled direct mode currently produces an unavailable message; normal proxy uploading remains unchanged. The recovery button does not activate direct mode.

`addRecoveredMedia` is pure, preserves other form fields, deduplicates URLs, records asset IDs and enforces 12 images/two videos using functional state updates. Primary images count toward the limit. The panel also disables adding when the relevant gallery is full. Concurrent requests are guarded; unmounting on session/listing change and cookie-session revision checks discard stale results. No tokens or recovery lists are persisted in browser storage.

Next.js/React skill review kept the server route unchanged, all handlers inside the existing client boundary, fetches event-driven, and gallery updates functional. No shared shell, auth architecture, schema or provider settings changed.

Validation: **101 frontend tests and 102 backend tests PASS**. New mounted tests cover explicit discovery/preview/add, pagination, limit-disabled controls, safe errors, stale session completion, and Arabic RTL; pure merge and actual API-client request tests cover asset IDs, deduplication, caps, no-store and authenticated completion. TypeScript, project ESLint and network-enabled production build PASS (24 generated pages; pre-existing old Browserslist warning). Browser discovery remains empty, so JSDOM tests are not claimed as visual/provider acceptance. Both previews respond; six cars retained. Backend restarted to load the current recovery endpoint, keeping signed mode OFF.

Files in this integration: `src/components/listings/UploadRecovery.tsx`, `src/components/listings/ListingEditorView.tsx`, `src/lib/recoveredListingMedia.ts`, `src/lib/api.ts`, `tests/upload-recovery.test.mjs`, `tests/api-session.test.mjs`, and recovery/roadmap/readiness documentation. Rollback only this editor integration, its API wrappers/helper/tests; retain backend ownership/holds and normal uploads. Nothing committed or deployed.

### Manual QA pending

1. Normal local image/video upload still previews and saves with recovery disabled; clicking recovery reports unavailable without switching transport.
2. In isolated approved direct-upload staging, refresh after interrupted upload; discovery finds the same owner intent, verification previews it, and nothing attaches before explicit Add.
3. Save/reload the listing: recovered media and asset IDs persist. Repeated selection does not duplicate gallery URLs.
4. At 12 images/two videos, adding is disabled; remove an item then recover. Primary image counts toward the cap.
5. Sign out/change account or navigate away during discovery/completion: no old data is added or displayed for the new session.
6. English/Arabic, RTL, desktop/mobile, light/dark, keyboard focus and preview sizing remain readable and usable.
7. Missing provider object/timeout/rejected metadata: safe retry, no automatic re-upload, deletion or allowance release.

Next remains audited quota settlement/replay accounting and real-provider acceptance. UI integration does not resolve these rollout blockers; readiness stays 59/100.

## Confirmed defect corrected

`signed_uploads.complete` previously removed the full-cap reservation as soon as the expected object was registered. Its signed upload capability could still be valid, allowing additional provider activity after quota was released. Completion now validates the exact owner/kind/full-cap reservation under the existing owner lock and leaves it intact while atomically recording the ledger and completion identity.

The account budget therefore counts both the actual registered bytes/asset and the full-cap reservation. This intentional conservative over-count blocks allowance recycling; it may reduce usable upload capacity until reconciliation exists. There is no automatic release at expiry and no release endpoint in this patch. Proxy uploads retain their previous settlement behavior. No schema migration is needed.

This does not solve the complete cross-resource replay problem: a signature may permit multiple objects and their storage may exceed the one-cap hold. Keep direct uploads disabled until provider enforcement or proven conservative multi-resource accounting is implemented and accepted. Do not describe this hold as a provider billing cap.

## Durable discovery contract

Authenticated `GET /api/uploads/recovery?after=<intent-id>` returns up to 20 owner-scoped entries, ordered by ID, and an optional `nextCursor`. IDs are opaque pagination markers, not chronological order. Entry fields:

- `intentId`, `kind`, `state` (`pending` or `completed`)
- `signatureExpired`, `quotaHeld`, `assetId` (nullable)

The endpoint is disabled with direct uploads, rejects malformed cursors, uses `Cache-Control: no-store`, and rate limits requests. It returns no signatures, provider IDs, URLs, credentials, original file names or other owners' records. It performs no provider I/O, upload, re-signing, refund, deletion or listing attachment. Existing completion can be called by the owner for a recovered ID even after signature expiry; completion still requires verified provider metadata.

No recovery UI or client API wrapper has been added yet. A refreshed editor does not automatically restore pending uploads. The endpoint is a durable backend building block, not a claim of completed user-facing recovery.

## Validation

102 backend tests PASS. Three new journey cases cover retained full-cap allowance after completion/expiry, inability to recycle that allowance into a new intent, private recovery discovery/pagination/cache behavior, and ledger rollback without a matching hold. Existing completion/association/idempotency tests still pass. Inventory now expects completed intents to retain their hold; older completed records without one are flagged inconsistent for review, not automatically repaired.

No live signed migration, provider mutation or production configuration change. Frontend unchanged: preceding 94 frontend tests and lint/typecheck/build remain the latest results, not rerun for this Python-only change.

## Files and rollback

`backend/app/signed_uploads.py`, `backend/inspect_uploads.py`, `backend/test_public_journey.py`, `backend/test_inspect_uploads.py`, this document, `SIGNED_UPLOADS.md`, `UPLOAD_RECONCILIATION.md`, `ROADMAP_CONTINUATION.md`, and `PUBLIC_RELEASE_READINESS.md`.

Rollback safest path: keep `SIGNED_UPLOADS_ENABLED=False`; preserve all reservations, intents and assets. Removing discovery is independent of upload writes, but must be coordinated with any future client consumer. Reverting the completion-hold change reintroduces premature quota release; do not do so for a public rollout. Never delete held reservations merely to recover capacity. Preserve all unrelated dirty-worktree changes.

## Next work

Integrate explicit editor recovery selection/preview with typed API calls and session-race protection, respecting the existing 12-image/two-video limits and never attaching automatically. Then implement audited reconciliation/settlement based on verified provider identity, signature expiry plus late-upload handling, all relevant resource types and listing references. Live provider acceptance, physical cleanup, moderation and target-database validation remain outstanding.
