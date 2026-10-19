# Regression checks in CI — September 22, 2026

Latest September 23 update: added Ubuntu FFmpeg installation and `test_video_validation`, with `REQUIRE_VIDEO_TOOLS=1` so real-media tests cannot silently skip in CI. 109 backend tests pass locally with real tools; hosted runner execution remains pending. See `VIDEO_UPLOAD_VALIDATION.md` for runtime prerequisites and rollback.

September 23 update: added explicit `test_inspect_upload_provider` module to the backend gate. The combined backend suite is now 99 tests, all passing locally; the frontend remains 94. YAML/wiring revalidated. Hosted execution/enforcement is still pending.

The existing GitHub workflow now runs frontend Node tests after lint/typecheck and before build, and explicit backend unittest modules after dependency installation/syntax checks. Previously neither suite ran in CI.

Backend test dependencies now include `backend/requirements-test.txt` (fakeredis with Lua support); both requirement files participate in the pip cache key. Tests use disposable SQLite and mocked providers, never the preview/production database. Explicit modules and the backend working directory avoid Flask package discovery before fixture isolation. No hosted secrets are needed for these tests.

Local commands verified:

```powershell
npm.cmd test
cd backend
..\.venv\Scripts\python.exe -m unittest test_public_journey test_rate_limits test_import_local_cars test_inspect_uploads -v
```

94 frontend and 91 backend tests pass locally. The GitHub-hosted Linux workflow has **not** run yet; local Windows execution is not proof of hosted compatibility. No push, commit, deployment, branch protection, paid service or hosted configuration change was performed. Existing branch triggers and build settings are preserved.

This adds checks, not deployment enforcement. Vercel/Render auto-deployment may be independent of GitHub checks; required branch checks and staging/promotion configuration still require review. Do not call this a production release gate until hosted enforcement is verified.

Workflow YAML parsed and test-step wiring assertions passed with the existing `js-yaml` dependency. Python PyYAML was unavailable; no dependency was added for this check. Installed Python dependency consistency and changed Python compilation pass. Frontend application code did not change in this batch; lint/typecheck/build retain the preceding batch's passing results rather than being claimed as newly rerun. Both local previews respond, with six cars retained.

Files: `.github/workflows/ci.yml` and this document, with roadmap/readiness log updates. Rollback only the two regression-test steps, test dependency/cache additions; retain the previous lint/typecheck/build checks and all unrelated workflow edits.
