# Phase 1C Application Shell Extraction

## Architecture change

Before this phase, the root route mounted `AppView`, which owned shared chrome and every page workflow in one 5,369-line Client Component.

After route extraction, each active route composes `AuthProvider`, `PublicRouteShell`, and a focused page component. `PublicRouteShell` owns the active public header, desktop/mobile navigation, language and document RTL, light/dark theme persistence, currency, service-mode persistence/navigation, authenticated actions, and unread-message indicator. Page components own only route-specific interactions.

The typed `src/components/layout/` primitives remain available, but no active route depends on the deleted SPA. `src/lib/publicRoutes.ts` is the only temporary compatibility layer and converts historical page keys to current paths; it does not emulate the SPA.

## State flow

- Language, theme and service mode use `useStoredPreference`: stable server defaults and browser-storage restoration through `useSyncExternalStore`, avoiding mismatched hydration markup. Changes persist and notify same-tab and cross-tab consumers.
- Language updates `<html lang>`, `<html dir>`, and the shell `dir` attribute.
- Currency remains owned by `AuthContext` and uses existing conversion/formatting behavior.
- Service mode initializes from its storage key and navigates to `/`, `/dealers`, or `/assistant`.
- Unread messages are fetched only for a verified authenticated session.
- Authenticated route actions remain gated by `token` plus `sessionValidated`.

## Coupling result

`rg AppView src` returns no import or render site. `rg "?view=" src` returns no legacy navigation URL. The former component was removed as unreachable after route migration.

## Manual verification

The active shell now composes `PublicHeader` and the reused `AppFooter`. Header presentation is separate from preferences/auth/unread state. See [UI_PREVIEW_REPAIR.md](UI_PREVIEW_REPAIR.md) for the September 7 regression repairs and remaining browser QA. The prior lazy initialization implementation was replaced, not retained.

See [FRONTEND_PHASE_1_MANUAL_QA.md](FRONTEND_PHASE_1_MANUAL_QA.md). Browser QA is pending because the browser CLI is unavailable in this environment.
