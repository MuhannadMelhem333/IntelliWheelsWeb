# Phase 1E Session and Route Error Handling

## Session verification

`AuthContext` no longer trusts `localStorage` user data as an authenticated session. On startup, a stored token must receive a successful `/auth/verify` response before `sessionValidated` becomes true and the user profile is restored into state.

- A timeout or other verification failure clears local credentials immediately without waiting for another network request.
- An explicit unsuccessful verification response follows the same local cleanup path.
- Fresh login, signup, and Google login retain their existing skip-once validation behavior because the server has just issued the token.
- Private fetch effects already gate on `loading`, `sessionValidated`, and `token` in `AppView`.

## Route boundaries

The application now has a root `loading.tsx` and retryable `error.tsx`. Public listings, cars, dealer list, and dealer detail retain their route-specific boundaries and reuse a shared accessible retry component. Client-side listings and dealer fetch failures also expose retry actions because errors caught inside effects do not propagate to App Router error boundaries.

SPA-only authenticated screens remain inside `AppView`; their loading state is supplied by `AuthProvider`, and private fetch effects remain gated by verified-session state. Migrating those screens into independent routes is a later route-architecture task rather than part of this error-handling patch.

## Manual QA

1. With a valid stored session, refresh and confirm private controls appear only after verification completes.
2. Simulate a network timeout with a stored token and confirm the app returns to a guest state without private listings, messages, favorites, or profile actions becoming available.
3. Simulate a 401 verification response and confirm the same credential cleanup occurs.
4. Confirm a fresh login, signup, and Google login still enter the authenticated experience.
5. Visit public listings, car, dealer list, and dealer-detail routes during loading and after an API error; confirm a useful failure state appears.
6. Select **Try again** for listings, dealer list, and a route-rendering error; confirm a new load is attempted.
