# Frontend Phase 1 Manual QA

Run with the frontend and matching backend. Record desktop/mobile results in English and Arabic unless noted.

| Area | Check | Expected result |
| --- | --- | --- |
| Home | Open `/` directly and refresh | Header/home render once; live stats and featured vehicles load or show a non-blocking API error. |
| Shell | Desktop and mobile links | All links navigate to real paths; mobile menu closes after navigation. |
| Shell | Language and RTL | Arabic updates visible shell copy plus document/shell direction; English restores LTR. |
| Shell | Theme and currency | Values update, affect price/theme output, and persist after refresh. |
| Shell | Service mode | Marketplace routes to `/`, Dealers to `/dealers`, Insights to `/assistant`, and selection persists. |
| Shell | Messages/auth | Verified users see private links and unread count; guests see Sign In; admin appears only for `is_admin`. |
| Listings | Default URL | `/listings` shows default filters and page 1 without default parameters. |
| Listings | Filters | Each filter updates the URL; multiple filters coexist; invalid enums fall back safely. |
| Listings | Pagination | Page updates `page`; a filter change removes it; page-only changes do not refetch listings. |
| Listings | History/share | Refresh, copied URL, Back, and Forward restore controls, page, URL, and results. |
| Cars | `/cars/[id]` | Direct load, refresh, gallery/fullscreen, favorites, reviews, seller/dealer info, messaging, and callback work. |
| Cars | Invalid ID/history | Invalid ID fails safely; return, Back, and Forward use real routes. |
| Dealers | Directory/detail | Grid/map, dealer application, inventory, contact, return, invalid ID, refresh, and history work. |
| Account | `/account` | Login, signup, Google, forgot/reset password, profile update, and logout retain behavior. |
| Private | `/favorites` | Verified session loads favorites; view/remove/retry work; guest sees sign-in guidance. |
| Private | `/messages` | Conversation list, reading, sending, unread behavior, refresh, and mobile layout work. |
| Listings management | `/my-listings` | Analytics/inventory load; View/Edit/Delete and empty state work. |
| Create listing | `/my-listings/new` | Validation, all fields, lookups, 12-image/2-video limits, removal, AI vision, price estimate, and publish work. |
| Edit listing | `/my-listings/[id]/edit` | Existing values/media restore; invalid/non-owned IDs fail safely; save and return work. |
| Assistant | `/assistant` | Per-user history, new/delete/select, text/image, Stop, car links, draft publish, and persistence work. |
| Analytics | `/analytics` | All/My/Favorites fetch correct summary/top makes; retry and guest gating work. |
| Admin | `/admin` | Only verified admins load data; filters, approve/reject, required reason, notes, and retry work. |
| Information | Seven static routes | Direct load, localized content, CTA links, canonical metadata, and unknown-slug 404 work. |
| Regression | Console/network | No overlay, hydration error, render loop, duplicate navigation, or duplicate API request caused by shell/URL state. |
| Responsive | 375px, tablet, desktop | Navigation, forms, cards, maps, modals, and galleries remain usable without horizontal overflow. |

Status: MANUAL QA PENDING
