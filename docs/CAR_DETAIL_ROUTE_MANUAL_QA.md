# Car Detail Route Manual QA

1. Open `/cars/<valid-id>` directly; expect one public header and the existing detail content.
2. Use desktop header links; expect Next.js navigation to home and listings.
3. Check a narrow viewport; expect header controls remain usable without a duplicate header.
4. Switch language; expect header labels change and the route wrapper changes to RTL for Arabic.
5. Switch theme; expect the shell and detail dark styling update.
6. Refresh after a theme change; expect the saved theme preference to be applied.
7. Switch currency; expect AuthContext currency behavior remains consistent with the existing application.
8. Open a car from `/listings`; expect return navigation to `/listings`.
9. Use browser Back and Forward; expect compatible route history.
10. Refresh the route; expect the same car to reload safely.
11. Open `/cars/invalid`; expect the existing safe invalid-ID error state.
12. Verify favorites, reviews, seller/dealer navigation, messaging, and callback actions still work.
13. Confirm the route does not import or mount `AppView`.
