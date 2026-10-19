# Phase 1F Frontend Quality

## Implemented

- Language preference now persists under a shared storage key in both the legacy SPA and public App Router shell.
- English/Arabic changes update the root document `lang` and `dir` attributes.
- The public shell has labeled language, theme, and currency controls and exposes every configured currency.
- Public navigation has a keyboard-operable mobile menu with `aria-expanded`, `aria-controls`, and close-on-navigation behavior.
- Root and public-route error states provide an accessible retry action.
- Public listing and dealer cards use `next/image`; arbitrary backend media remains `unoptimized` for compatibility with environment-specific hosts.
- Public routes have route-specific canonical metadata instead of inheriting the home-page canonical.
- The sitemap includes all stable public routes.

## Manual QA

1. Select Arabic, refresh, and confirm Arabic remains selected and the document uses RTL.
2. Return to English and confirm document direction returns to LTR.
3. Open and operate the public mobile menu using keyboard controls.
4. Confirm all configured currencies are available and selection remains consistent after refresh.
5. Confirm light/dark theme controls remain usable on desktop and mobile.
6. Inspect listings and dealer cards for correct aspect ratio, fallback images, and layout at common breakpoints.
7. Confirm public route canonicals and `/sitemap.xml` contain the expected URLs.
8. Trigger a public loading failure and confirm **Try again** starts a new request.

## Remaining frontend-wide quality debt

The SPA-owned private, AI, messaging, listing-management, and admin interfaces still contain pre-existing accessibility and image warnings inside `AppView`. They require focused page extraction and QA rather than a broad mechanical rewrite.
