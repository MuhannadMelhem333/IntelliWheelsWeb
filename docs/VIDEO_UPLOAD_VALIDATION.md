# Enabled video upload validation — September 23, 2026

## Behavior

Authenticated proxy video uploads now pass bounded ffprobe metadata validation after existing size/MIME/container screening and **before** quota reservation or cloud/local storage. Images are unchanged. Direct uploads remain disabled.

Videos require a finite positive duration no greater than 120 seconds, at least one non-attached-picture video stream with a known codec, positive dimensions no greater than 10,000 per side / 25 million pixels, and no reported stream duration exceeding the limit. Audio-only content, oversized dimensions, missing duration and malformed metadata fail with HTTP 400. An unavailable/unlaunchable validator returns a generic HTTP 503; no storage or reservation occurs. The route does not disclose executable paths or process stderr.

Implementation: `video_validation.py:probe_video/validate_video`, called by `upload_validation.validate_upload`, handled in `routes/system.py:upload_video`. Temp input uses an application-generated name, never a supplied filename or URL, and is removed afterward. Original input stream is rewound. Process uses an argument list, no shell, no stdin, a 15-second timeout, restricted file protocol/demuxers, 10MB probing, 10-second analysis duration, 32 streams and 64MB per-allocation limit. Selected JSON output is capped at 64KB after return. These are not an OS-wide CPU/memory sandbox or an aggregate RAM/output cap during execution.

Important limitation: ffprobe metadata is not a full-frame decode, malware scanner, moderation system or browser codec-compatibility guarantee. Corruption late in a file, forged metadata and codec/device differences still need stronger decode/transcode validation and adversarial testing. This closes header-only acceptance, not every media risk. Reference: [official ffprobe documentation](https://ffmpeg.org/ffprobe.html).

## Runtime dependency and local change

FFmpeg/ffprobe 9.0.2 installed through the hash-verified WinGet `Gyan.FFmpeg` package for this Windows user. This modifies user PATH and adds ffmpeg/ffprobe/ffplay aliases; it is outside the repository. Existing shells may need restart. No Python dependency added.

Backend configuration `FFPROBE_PATH` defaults to `ffprobe`; use a trusted executable path when PATH lookup is unavailable. `VIDEO_UPLOAD_MAX_SECONDS` defaults to 120. Local preview was restarted with the installed ffprobe path, ledger/quota flags retained and signed mode OFF. Sandbox execution of the installed binary initially failed with Access Denied; tests and preview were rerun with approved execution access. No insecure fallback was introduced.

**Before any deployment**, provision a maintained ffprobe executable in the backend runtime and test its path, permissions and version. Otherwise video uploads return 503. No hosted environment, Render configuration, deployment image or production service was modified. Do not promote this change without runtime dependency acceptance.

## Validation

109 backend tests PASS with actual binaries, no skipped media acceptance tests. Real generated one-second MP4 accepted through the upload route; a 121-second MP4 rejected without storage. Header-only fake rejected by the actual probe. Unit cases cover missing binary, bounded subprocess arguments, timeout cleanup/rewind, dimensions, invalid/nonfinite duration, audio-only and attached pictures. Route tests prove rejection precedes reservation/storage and errors don't disclose private details.

Existing header-only storage fixtures explicitly mock the probe boundary; they are not presented as real-media acceptance. CI now installs Ubuntu FFmpeg and runs the new suite with `REQUIRE_VIDEO_TOOLS=1`, which fails if tools are absent rather than silently skipping. Hosted CI remains unrun. CI YAML/wiring validation, Python compilation and whitespace checks pass. Frontend unchanged; preceding 106 frontend tests and lint/typecheck/build remain the latest frontend results, not rerun for this backend-only patch.

## Files

`backend/app/video_validation.py`, `backend/app/upload_validation.py`, `backend/app/routes/system.py`, `backend/app/__init__.py`, `backend/test_video_validation.py`, `backend/test_public_journey.py`, `.gitignore`, `.github/workflows/ci.yml`, this document, CI/roadmap/readiness logs.

## Rollback and QA

Preserve stored media and quota data. Preferred response to validator problems is repairing the executable/runtime, not bypassing validation. Reverting this narrow validation hook/config/module and its route error handling/tests together restores weaker header-only checks and is unsafe for public deployment. Remove the added CI tool/test steps only with the related code. Local machine installation can independently be removed using Windows Installed Apps or `winget uninstall --id Gyan.FFmpeg`; doing so makes video verification unavailable until a replacement is provided.

Manual QA: upload a short video, preview/save/reload, reject audio-only/fake/overlong video, verify image uploads still work, test English/Arabic/mobile errors and validate all supported containers/codecs in staging. Browser unavailable; HTTP preview responds, backend healthy, six cars retained. No live test uploads or production changes.

Readiness estimate increases from 59 to 60/100 for active-path video validation with real-file API evidence only. Provider replay/settlement, cleanup/moderation, staging, production database and other release blockers remain. Next: media reference accounting for safe cleanup; no physical deletion before ownership/reference checks and recovery strategy are verified.
