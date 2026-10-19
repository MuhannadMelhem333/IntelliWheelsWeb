# Account, Favorites, and Messages Manual QA

## Account

1. Load `/account` directly as a guest; sign-in, signup, forgot-password, and Google controls should remain available.
2. Open `/account?reset_token=VALID_TOKEN`; the reset form should appear, validate matching passwords, and return to `/account` after success.
3. Sign in and refresh; private profile content must appear only after session verification.
4. Update username, email, phone, and password fields; existing profile API behavior should be preserved.
5. Switch English/Arabic, RTL/LTR, theme, currency, desktop/mobile layouts, then sign out.

## Favorites

1. Load `/favorites` signed out; a sign-in link should appear without a private API request.
2. Load with a verified session; favorite cars, prices, images, and detail links should render.
3. Remove a favorite and confirm it disappears without affecting other cards.
4. Trigger a fetch failure and confirm **Try again** issues a new request.
5. Verify Arabic/RTL, dark/light themes, currency formatting, desktop, and mobile layouts.

## Messages

1. Load `/messages` signed out; a sign-in link should appear.
2. With a verified session, conversations and unread counts should render.
3. Select conversations and confirm only their messages appear.
4. Send a message and confirm the conversation refreshes after success.
5. Confirm send failures expose a retryable error without losing authentication state.
6. Verify English/Arabic, RTL/LTR, dark/light themes, keyboard operation, desktop two-column layout, and mobile stacked layout.
7. Use browser Back, Forward, and direct refresh on all three routes.
# Follow-up regression checks — pending browser execution

- Open an account reset-token URL, then navigate Back/Forward to `/account` without the token: normal login/signup forms must reappear. Do not use or record a real reset token in test logs.
- Trigger a profile-update validation failure: the signed-in profile view must display the API error in an alert.
- Load conversation A, then switch to B with a slow network: A's messages must not appear beneath B's recipient header. A loading status appears until B's response arrives.
- Fail the active-thread request once, then select Try again: the active thread must actually refetch.
- Type a draft in A, then switch to B: A's text must not remain in B's composer. Draft retention across conversations is not implemented.
- Send a message on a slow network: recipient switching and duplicate sends remain disabled until completion; confirm it appears only in the selected thread.
- Favorites with only `galleryImages` or `image` populated must display that supplied image, not a placeholder.
- In Arabic, check account/favorites/messages loading text, retry buttons and the message input/sending labels.
