# Phase 1D Frontend Data-Fetching and Cache Policy

## Scope

This phase replaces the frontend API client's blanket `no-store` setting with an explicit, conservative browser request policy. The Flask API remains unchanged.

## Policy

| Data type | Frontend request policy |
| --- | --- |
| Authenticated and mutation requests | `no-store` |
| Anonymous public listings, car details, dealers, reviews, and platform statistics | `default` (respect API HTTP cache headers) |
| Anonymous makes, models, and engines reference data | `force-cache` |

The API client resolves any token supplied by the legacy local-storage compatibility lookup before selecting the final policy. If a request is authenticated, it is always forced to `no-store`, even if its caller initially selected a public policy.

## Limitations

These route views are client components that fetch a separate Flask API. Consequently, this change does not create Next.js server `revalidate` entries or public CDN caching by itself. Effective public response lifetime remains controlled by the Flask API's HTTP response headers; introducing API cache headers belongs to a later backend-authorized workstream.

## Verification

- Private endpoints and all mutations retain `no-store`.
- Public cache policies are selected only when the final request has no authorization token.
- TypeScript and changed-file ESLint are run for the implementation.
