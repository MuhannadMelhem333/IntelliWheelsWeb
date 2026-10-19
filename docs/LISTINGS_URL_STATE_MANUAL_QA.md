# Listings URL State Manual QA

Run these checks locally against `/listings` after deployment/build access is available.

1. Open `/listings`; expect default filters and page one.
2. Change one filter; expect its supported value in the URL and matching results.
3. Change make, category, search, and sort; expect all non-default values serialized.
4. Change page; expect `page` to update while filters remain.
5. Change a filter from a later page; expect page one and no `page` parameter.
6. Refresh; expect filters and page restored from the URL.
7. Open a copied URL in a new tab; expect identical state.
8. Use Back; expect the preceding URL, filters, page, and results restored.
9. Use Forward; expect the following URL, filters, page, and results restored.
10. Use invalid `sort` or `page`; expect default sort and page one without a crash.
11. Watch network/navigation while changing state; expect one route update and no repeated listing requests.
12. Repeat in English and Arabic, RTL, desktop, and mobile; expect unchanged listing behavior and layout.
# Localization follow-up — manual checks pending

- Switch to Arabic: every filter label and option, sort option, empty state, pagination control and retry message is Arabic; make/model names remain source data.
- Change any translated dropdown: its URL value remains the existing English API enum (for example `fuelType=hybrid`), never the displayed Arabic text.
- Refresh or share the URL: selected values restore and use the persisted language.
- Simulate slow/failed route loading: loading/error boundaries restore theme and language, including RTL, without duplicating the public header.
- On mobile, open the navigation, tab to a link or setting and press Escape: menu closes and keyboard focus returns to the menu toggle.
- Switch English/Arabic while the menu is open: navigation and settings accessible names follow the selected language.
