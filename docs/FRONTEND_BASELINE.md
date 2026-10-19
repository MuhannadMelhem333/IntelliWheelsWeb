# IntelliWheels Frontend Baseline (Phase 1A)

Assessment date: 2026-07-20  
Scope: characterization only. No frontend, backend, API, or deployment behavior was changed.

> Implementation status (2026-07-20): the Phase 1B static-information-page migration has been completed. The pages are now available at `/about`, `/how-it-works`, `/pricing`, `/faq`, `/contact`, `/cookie-policy`, and `/disclaimer`; this baseline otherwise describes the pre-migration frontend state.

## Confirmed platform baseline

- Next.js `^16.0.7`, React `19.2.0`, TypeScript, Tailwind CSS 3, and ESLint 9 are declared in `package.json:5-30`.
- The app uses the Next.js App Router under `src/app`.
- React Compiler is enabled in `next.config.ts:4-6`.
- The root page is a Client Component which mounts `AuthProvider` and the entire `AppView` shell (`src/app/page.tsx:1-12`).

## Current routes and URL behavior

| Current URL | Route implementation | Current content boundary |
| --- | --- | --- |
| `/` | `src/app/page.tsx` | Client-rendered `AppView` SPA shell |
| `/cars/[id]` | `src/app/cars/[id]/page.tsx:1-16` | `CarDetailView`, wrapped in `AuthProvider` |
| `/dealers/[id]` | `src/app/dealers/[id]/page.tsx:1-15` | `DealerDetailView`, wrapped in `AuthProvider` |
| `/robots.txt` | `src/app/robots.ts` | Generated robots metadata |
| `/sitemap.xml` | `src/app/sitemap.ts` | Generated sitemap containing only `/` |
| `/manifest.webmanifest` | `src/app/manifest.ts` | Generated web-app manifest |

All remaining major screens are not App Router routes. They are selected by client state in `AppView` and persist to `sessionStorage` (`src/components/AppView.tsx:767-786`). Car and dealer detail navigation does use `router.push` to their dynamic URLs (`src/components/AppView.tsx:1000-1013`).

## SPA page-key inventory

`NAV_CONFIG` defines these main page keys (`src/components/AppView.tsx:73-85`):

- `home`, `listings`, `favorites`, `messages`, `dealers`, `myListings`, `addListing`, `profile`, `chatbot`, `analytics`, `admin`

Additional static/information keys (`src/components/AppView.tsx:87-88`):

- `about`, `howItWorks`, `pricing`, `faq`, `contact`, `cookiePolicy`, `disclaimer`

`renderContent` branches on those keys (`src/components/AppView.tsx:3359-3361`, `3583-4919`). Service modes (`marketplace`, `dealer`, `insights`) restrict the current navigation set and persist in browser storage (`src/components/AppView.tsx:90-102`, `1144-1160`).

## Client/server component boundaries

Explicit Client Components are:

- `src/app/page.tsx`
- `src/components/AppView.tsx`
- `src/components/CarDetailView.tsx`
- `src/components/DealerDetailView.tsx`
- `src/components/DealerMap.tsx`
- `src/components/InfoPages.tsx`
- `src/context/AuthContext.tsx`

The dynamic page files themselves are server components, but each mounts an `AuthProvider` around a client detail view. No route-level `loading.tsx`, `error.tsx`, or `not-found.tsx` files were found.

## State, authentication, and persistence baseline

- `AuthContext` owns user, token, loading, session-validation, currency, profile, and authentication operations (`src/context/AuthContext.tsx:8-28`, `32-38`).
- Auth token and user profile persist in `localStorage`; theme, service mode, currency, and chat sessions also use browser storage (`src/context/AuthContext.tsx:76-97`, `169-181`; `src/lib/config.ts:18-25`; `src/components/AppView.tsx:1139-1147`).
- Current behavior treats a stored user as authenticated before background session validation completes (`src/context/AuthContext.tsx:121-159`). This is a documented future Phase 1E behavior concern, not changed here.
- `AppView` holds listings, filters, favorites, dealer data, messages, admin data, chatbot state, forms, UI menus, language, theme, and service-mode state in one component (`src/components/AppView.tsx:767-900`).

## Data fetching and frontend environment baseline

- All frontend API calls go through `apiRequest` in `src/lib/api.ts:29-133`.
- It attaches a bearer token from its caller or browser storage (`src/lib/api.ts:44-78`) and sets `cache: 'no-store'` on every request (`84-99`).
- `src/lib/api.ts:135-577` exposes calls for listings, auth, profile, dealers, AI, uploads, reviews, applications, platform stats, and messaging.
- `API_BASE_URL` accepts `NEXT_PUBLIC_API_BASE_URL`, `NEXT_PUBLIC_API_BASE`, `NEXT_PUBLIC_BACKEND_URL`, `API_BASE_URL`, `API_BASE`, or `BACKEND_URL`; it otherwise defaults to `http://localhost:5000/api` (`src/lib/config.ts:1-15`).
- CI supplies `NEXT_PUBLIC_API_URL`, which is not among the recognized names (`.github/workflows/ci.yml:33-36`). This configuration mismatch remains unmodified and should be separately authorized before correction.

## SEO, accessibility, and bundle observations

- Root metadata, JSON-LD, GA4, manifest, robots, and sitemap support exist in `src/app/layout.tsx:23-204`, `src/app/manifest.ts`, `src/app/robots.ts`, and `src/app/sitemap.ts`.
- The root document is fixed as `<html lang="en">` (`src/app/layout.tsx:180`); Arabic/RTL behavior is managed in the client shell and needs browser characterization before any route migration.
- The sitemap contains only the homepage (`src/app/sitemap.ts:5-14`).
- No automated bundle analysis was generated. `next.config.ts:46-49` has an `ANALYZE=true` conditional but does not configure a bundle-analyzer package.
- Lint reports several image-optimization warnings (`@next/next/no-img-element`) and accessibility/keyboard behavior still requires manual browser validation.

## Characterization smoke checklist for later route work

Before migrating any route group, manually verify the existing behavior for:

1. English/Arabic content and RTL layout.
2. Light, dark, and system theme selection.
3. Service-mode navigation restrictions.
4. Currency selection and display.
5. Listing search/filter/pagination and car-detail return navigation.
6. Dealer list/detail navigation.
7. Login, signup, logout, reset password, and protected-page behavior.
8. Favorites, messages, listing management, uploads, chatbot, analytics, and admin access.
9. Desktop and mobile navigation plus keyboard focus behavior.

## Validation

| Command | Result | Notes |
| --- | --- | --- |
| `npm.cmd ci` | PASS | Installed lockfile dependencies. npm reported a deprecated transitive `glob` package. |
| `npm.cmd run lint` | FAIL | 47 errors and 48 warnings. Representative errors: explicit `any` in `DealerMap.tsx`, `AuthContext.tsx`, and `api.ts`; `prefer-const` errors in `api.ts`. No lint source was changed in this phase. |
| `npx.cmd tsc --noEmit` | PASS | Completed without TypeScript errors. |
| `npm.cmd run build` | FAIL (environment) | Next/Turbopack could not fetch Geist and Geist Mono from Google Fonts, imported by `src/app/layout.tsx`. This environment has restricted outbound font access; no application build error was established beyond those failed network fetches. |

## Recommended next atomic issue

**Phase 1B only — migrate the static information pages** (`about`, `howItWorks`, `pricing`, `faq`, `contact`, `cookiePolicy`, `disclaimer`) from the `AppView` page-key switch into real App Router routes.

Preserve translations, theme behavior, navigation, styling, and mobile behavior. Do not migrate listings, authentication, messages, AI, admin, backend, or database behavior in that issue.

**STOP: Awaiting explicit authorization.**
