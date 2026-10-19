# Dealer Detail Route Manual QA

1. Open `/dealers/<valid-id>` and refresh; expect one public header and dealer data.
2. Verify desktop/mobile header navigation, language/RTL, theme persistence, and currency behavior.
3. Verify Back/Forward and return navigation to `/listings`.
4. Open an invalid ID; expect the existing safe error state.
5. Verify dealer information, inventory, reviews/contact/messaging/favorites where available, and responsive layout.
6. Confirm no `AppView` mount, duplicate header, or conflicting controls.
