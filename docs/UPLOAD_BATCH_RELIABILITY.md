# Partial upload reliability — September 23, 2026

Confirmed defect: listing editor image/video handlers used `Promise.all`. Any rejected upload discarded all sibling results from the draft, even when files were already stored and registered. Successful files could become invisible to the user while still consuming quota.

## Implemented

- `uploadListingBatch` uses all-settled results, preserves successful response order/IDs and counts rejected, false-success and malformed responses. It waits for all selected work and never automatically retries.
- The editor shares one image/video batch handler, merges successful media with functional updates, and displays a safe English/Arabic partial-failure message. Over-limit selections are not sent and receive an explanatory notice.
- A shared synchronous lock prevents overlapping image/video batches; both file inputs are disabled while uploading/submitting. Saving and recovery addition retain their existing busy guards.
- The media merge helper now supports normal legacy upload responses without IDs while still requiring IDs for recovered media. Deduplication preserves existing IDs. The primary image counts toward the 12-image cap; videos remain capped at two.
- Token/validation/listing lifecycle changes invalidate pending batch results, and cookie-session revision changes also discard stale results. This does not cancel provider work already in flight or erase an existing draft on account changes.

Next.js/React guidance kept this inside the existing client editor, with no new route/provider, functional merges and event-driven requests. No backend, schema, styling, auth architecture or provider configuration change.

## Validation

106 frontend tests PASS, including five new batch/merge cases: partial failures, delayed sibling completion, malformed/false responses and synchronous exceptions, legacy compatibility, and primary-image capacity. TypeScript/project ESLint/whitespace PASS. Production build PASS with existing Google Fonts network access; old Browserslist warning remains. Final input-disabled attributes were subsequently typechecked/linted. Backend unchanged; previous 102 backend tests remain the latest result, not rerun in this frontend-only batch.

Browser acceptance remains pending. Test healthy plus rejected uploads together; successful previews must remain, IDs must persist after save/reload, and only failed files should be retried. Repeat for video, full gallery, rapid repeated selection, navigation/signout during upload, English/Arabic and mobile/light/dark. Network ambiguity can still leave provider objects requiring reconciliation; this patch does not release quota or delete them.

## Files and rollback

`src/components/listings/ListingEditorView.tsx`, `src/lib/listingUploadBatch.ts`, `src/lib/recoveredListingMedia.ts`, `tests/listing-upload-batch.test.mjs`, this document, `ROADMAP_CONTINUATION.md`, and `PUBLIC_RELEASE_READINESS.md`.

Rollback only the new batch handler/helper/tests and optional-ID media helper extension together. Preserve earlier recovery integration, ID payload behavior, security/ledger/quota work and all unrelated edits. No database rollback needed. No commit/deployment performed.

## Remaining priority

Signed upload settlement/cleanup cannot safely be enabled without provider enforcement/replay acceptance; no automatic refunds were added. The currently enabled proxy-video flow still screens only container headers, not playable media/duration. Address that active-path validation gap next while maintaining a safe local preview. Overall readiness remains 59/100; this defect fix is not a substitute for staged release acceptance.
