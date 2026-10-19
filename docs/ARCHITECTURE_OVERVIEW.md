# IntelliWheels — Architecture Overview

**AI-Powered Automotive Marketplace for Jordan & GCC**

- **Domain:** intelliwheels.co
- **Frontend:** Next.js 16 + React 19.2 + Tailwind CSS 3.4 (Vercel)
- **Backend:** Flask 3.0 + Gemini 2.5 AI (Render)
- **Database:** PostgreSQL/CockroachDB (prod), SQLite (dev)
- **AI:** Google Gemini 2.5 Flash (chat, vision, pricing, listing assistant)
- **Storage:** Cloudinary (preferred), local filesystem fallback (ephemeral)

---

## Table of Contents

1. [Monorepo Layout](#1-monorepo-layout)
2. [Architecture: Hybrid SPA + SSR](#2-architecture-hybrid-spa--ssr)
3. [Frontend Deep Dive](#3-frontend-deep-dive)
4. [Backend Deep Dive](#4-backend-deep-dive)
5. [Database Schema](#5-database-schema)
6. [Authentication & Security](#6-authentication--security)
7. [AI Features](#7-ai-features)
8. [File Upload System](#8-file-upload-system)
9. [API Reference](#9-api-reference)
10. [Development Workflow](#10-development-workflow)
11. [Deployment](#11-deployment)
12. [Common Pitfalls & Gotchas](#12-common-pitfalls--gotchas)

---

## 1. Monorepo Layout

```
/
├── src/                          # Next.js frontend
│   ├── app/
│   │   ├── layout.tsx            # Root layout (SEO, GA4, fonts, JSON-LD)
│   │   ├── page.tsx              # Entry: <AuthProvider><AppView /></AuthProvider>
│   │   ├── globals.css           # Tailwind directives, Leaflet z-index fixes
│   │   ├── icon.tsx              # Dynamic favicon generator
│   │   ├── cars/[id]/page.tsx    # SSR car detail page
│   │   └── dealers/[id]/page.tsx # SSR dealer detail page
│   ├── components/
│   │   ├── AppView.tsx           # ★ 5400-line SPA shell (all UI lives here)
│   │   ├── CarDetailView.tsx     # Car detail (1040 lines)
│   │   ├── DealerDetailView.tsx  # Dealer profile (190 lines)
│   │   ├── DealerMap.tsx         # Leaflet map (dynamic import, no SSR)
│   │   └── InfoPages.tsx         # About, FAQ, contact, legal (760 lines)
│   ├── context/
│   │   └── AuthContext.tsx        # Auth state, token mgmt, currency (380 lines)
│   └── lib/
│       ├── api.ts                # ★ 42 API functions, central request layer (580 lines)
│       ├── config.ts             # API_BASE_URL, currency rates, storage keys
│       ├── types.ts              # All TypeScript interfaces (250 lines)
│       └── vehicleDatabase.ts    # Make/model reference data
├── backend/
│   ├── app/
│   │   ├── __init__.py           # App factory: CORS, blueprints, Swagger
│   │   ├── db.py                 # Dual-engine DB (SQLite/PostgreSQL), schema (670 lines)
│   │   ├── security.py           # Auth decorators, rate limiting, validation (275 lines)
│   │   ├── routes/               # 9 blueprint modules
│   │   │   ├── ai.py             # Chatbot, price estimate, vision, semantic search
│   │   │   ├── auth.py           # Signup, login, OAuth, password reset (635 lines)
│   │   │   ├── cars.py           # Car CRUD + filters/pagination
│   │   │   ├── dealers.py        # Dealer directory + applications
│   │   │   ├── favorites.py      # User favorites CRUD
│   │   │   ├── listings.py       # Makes/models/engines, my-listings, analytics
│   │   │   ├── messages.py       # User-to-user messaging
│   │   │   ├── reviews.py        # Car reviews with aggregate ratings
│   │   │   └── system.py         # Health, uploads, stats, debug endpoints
│   │   └── services/
│   │       └── ai_service.py     # Gemini integration (770 lines)
│   ├── models/
│   │   └── fair_price_model.joblib  # ML model (unused — price est. is rule-based)
│   ├── data/                     # Sample CSV/XLSX data
│   ├── render-build.sh           # Render build script
│   ├── requirements.txt          # Python deps
│   └── run.py                    # Dev server entry (debug mode, loads .env)
├── docs/                         # Architecture, deployment, legal docs
├── public/                       # Static assets (logos, favicon, placeholders)
├── .github/
│   ├── workflows/ci.yml          # CI: lint → tsc → build on push/PR
│   └── copilot-instructions.md   # Deprecated — use AGENTS.md
├── render.yaml                   # ★ 3 Render services (dev/stg/prod)
├── next.config.ts                # React compiler, Sentry, security headers
├── eslint.config.mjs             # ESLint 9 flat config
├── tailwind.config.ts            # Tailwind config
├── tsconfig.json                 # Path alias @/* → ./src/*
├── sentry.client.config.ts       # Sentry DSN (hardcoded, prod only)
├── AGENTS.md                     # Agent instructions
└── package.json
```

---

## 2. Architecture: Hybrid SPA + SSR

This project uses a **hybrid architecture**:

| Route | Type | Purpose |
|-------|------|---------|
| `/` | Client SPA | `<AppView />` — all app UI inside one component |
| `/cars/[id]` | SSR page | `<CarDetailView />` — SEO-friendly car details |
| `/dealers/[id]` | SSR page | `<DealerDetailView />` — SEO-friendly dealer profile |

The SPA shell (`AppView.tsx`) manages 18 internal pages via `useState<PageKey>`:
`home`, `listings`, `favorites`, `messages`, `dealers`, `myListings`, `addListing`, `profile`, `chatbot`, `analytics`, `admin`, `about`, `howItWorks`, `pricing`, `faq`, `contact`, `cookiePolicy`, `disclaimer`

Navigation between SPA pages is instant (no page reload). Navigation to `/cars/[id]` and `/dealers/[id]` uses Next.js `router.push()` with a `?from=` param for back-navigation.

**Why hybrid?** The SPA gives instant UX for the marketplace UI; the SSR pages give SEO for individual car/dealer pages (indexable by Google).

---

## 3. Frontend Deep Dive

### 3.1 App Shell (`AppView.tsx` — 5400 lines)

This single file is the **entire application**. It contains:
- Header with nav, search, settings, messages badge
- 18 page views rendered via `renderContent()` switch statement
- All state (~100 `useState` hooks)
- Translation dictionary (400+ keys in English + Arabic)
- Theme, language, currency, and service mode management
- File upload handling (images, videos)
- Chat sessions management
- Admin panel

**Service modes** — three workspace modes filter which pages are visible:
- `marketplace` (default): full buyer/seller experience
- `dealer`: analytics + listing management focus
- `insights`: AI chat + analytics focus

**Persistence:**
| Storage | Key | Purpose |
|---------|-----|---------|
| `sessionStorage` | `intelliwheels-activePage` | Survives refresh |
| `localStorage` | `intelliwheels-token` | Auth token |
| `localStorage` | `intelliwheels-user` | User profile |
| `localStorage` | `intelliwheels-theme` | light/dark/system |
| `localStorage` | `intelliwheels-currency` | Display currency |
| `localStorage` | `intelliwheels-service-mode` | marketplace/dealer/insights |
| `localStorage` | `intelliwheels-chat-sessions-${userId}` | AI chat history |

### 3.2 AuthContext (`AuthContext.tsx`)

Manages: `user`, `token`, `loading`, `sessionValidated`, `currency`, auth methods.

**Boot sequence:**
1. On mount, read token+user from `localStorage`
2. Render immediately with stored user ("trust-then-verify" — avoids blocking on backend cold starts)
3. Background `verifySession(token)` call (15s timeout)
4. On success: refresh user data from server
5. On failure with stored user: log error, keep using stored user
6. On failure without stored user: silent logout

### 3.3 API Client (`api.ts` — 580 lines)

Central `apiRequest<T>()` function handles all HTTP:
- Auto-discovers token from `localStorage` (multiple key fallbacks)
- Auto-sets `Content-Type: application/json` (unless `isFormData: true`)
- `cache: 'no-store'` on all requests
- `fallback` option for graceful degradation if backend is unreachable
- 401 errors are logged with token details for debugging

**42 exported functions** covering: cars, auth, AI, dealers, favorites, reviews, messages, uploads, admin.

### 3.4 Theme & Styling

- Tailwind CSS 3.4 only (no CSS modules, no styled-components)
- Very rounded corners (`rounded-2xl`, `rounded-3xl`)
- Glass morphism (`backdrop-blur-md`, `bg-white/95`)
- Gradients heavily used (`from-indigo-500 to-purple-600`)
- Dark mode: `slate-800/900/950` palette
- Responsive: mobile-first with `sm:`, `md:`, `lg:`

### 3.5 Critical: `@/*` Import Alias

All imports use `@/` which maps to `./src/*`:
```typescript
import { AppView } from '@/components/AppView';
import { API_BASE_URL } from '@/lib/config';
```

---

## 4. Backend Deep Dive

### 4.1 App Factory (`__init__.py`)

`create_app()` function:
1. Validates `SECRET_KEY` (32+ chars in production, or crashes)
2. Configures CORS: restricted to `FRONTEND_ORIGIN` in prod, open in dev
3. Initializes database via `init_app()`
4. Registers 9 Flask blueprints
5. Mounts Swagger UI at `/api/docs`

Module-level `app = get_app()` creates the app instance for gunicorn.

### 4.2 Database Layer (`db.py` — 670 lines)

**Dual-engine** supporting both SQLite and PostgreSQL/CockroachDB:
- Auto-detects based on `DATABASE_URL` env var
- `PostgresCursorWrapper` converts SQLite-style `?` to `%s`, `json_extract` to `->>`, `CURRENT_TIMESTAMP` to `NOW()`, etc.
- Connection pooling for PostgreSQL (1-10 connections via `psycopg2.pool`)
- DATABASE_URL normalization: converts `postgres://` → `postgresql://`, `cockroachdb://` → `postgresql://`, adds `sslmode=require`

### 4.3 Security Module (`security.py`)

**Decorators:**
| Decorator | Purpose |
|-----------|---------|
| `@token_required` | Validates Bearer token, sets `g.current_user` |
| `@rate_limit(n, window)` | IP-based rate limiting |
| `@validate_json_request(required, optional)` | JSON body validation |

**Validation rules:**
| Field | Rule |
|-------|------|
| Username | `^[a-zA-Z0-9_-]{3,30}$` |
| Email | Standard regex, max 100 chars |
| Password | 8-128 chars, ≥1 letter + ≥1 number |
| Make/Model | Max 50/100 chars |
| Description | Max 5000 chars |
| Chat message | Max 4000 chars |
| Search query | Max 1000 chars (sanitized for SQL LIKE) |

**Sanitization:** `sanitize_string()` HTML-escapes all input. `sanitize_search_query()` additionally escapes SQL LIKE chars. Passwords are NOT sanitized (they get hashed).

**Security headers** (on every response):
- `X-Frame-Options: DENY`
- `X-Content-Type-Options: nosniff`
- `X-XSS-Protection: 1; mode=block`
- `Referrer-Policy: strict-origin-when-cross-origin`

### 4.4 Auth System

**Session-based tokens** (NOT JWT):
- Opaque bearer tokens: `secrets.token_urlsafe(32)` — crypto-random
- Stored in `user_sessions` table with 7-day expiry
- Sent as `Authorization: Bearer <token>`
- No refresh mechanism — user must re-login when token expires

**Password hashing:** `werkzeug.security.generate_password_hash` (pbkdf2:sha256:260000)

**Google OAuth:** Verifies ID tokens via `google.oauth2.id_token.verify_oauth2_token`. Creates user on first login, links google_id on subsequent logins.

**Password reset:** Email-based reset with 1-hour expiry tokens. Invalidates ALL sessions on reset. Email sending via `smtplib` (falls back to console logging).

### 4.5 Routes Architecture

Each blueprint registers with a prefix:

| Blueprint | Prefix | File | Endpoints |
|-----------|--------|------|-----------|
| `auth.bp` | `/api/auth` | `auth.py` | signup, login, logout, verify, profile, forgot-password, reset-password, google, oauth-config |
| `cars.bp` | `/api/cars` | `cars.py` | GET list (with filters), GET by id, POST create, PATCH update, DELETE |
| `ai.bp` | `/api` | `ai.py` | chatbot, price-estimate, semantic-search, vision-helper, listing-assistant, analytics/insights |
| `system.bp` | `/api` | `system.py` | health, stats, uploads (images/videos), swagger, debug endpoints |
| `dealers.bp` | `/api/dealers` | `dealers.py` | list, get by id, applications CRUD, approve/reject |
| `favorites.bp` | `/api/favorites` | `favorites.py` | list, add, remove |
| `listings.bp` | `/api` | `listings.py` | makes, models, engines, my-listings, my-listings/analytics, request-callback |
| `reviews.bp` | `/api/reviews` | `reviews.py` | list car reviews, add, delete, user's reviews |
| `messages.bp` | `/api/messages` | `messages.py` | conversations, conversation detail, send, unread-count |

### 4.6 Error Handling Patterns

- **Consistent JSON errors:** `{"success": false, "error": "message"}`
- **Generic error messages:** Login → "Invalid credentials" (prevents user enumeration). Password reset → always success.
- **DB rollback on errors:** Every modifying route wraps in try/except with explicit `db.rollback()`
- **Graceful degradation:** Reviews/favorites return empty results on DB errors instead of 500s
- **Migration tolerance:** ALTER TABLE migrations wrapped in try/except for idempotency

---

## 5. Database Schema

### Tables (9 total)

**`users`** — Core user accounts
| Column | Type | Notes |
|--------|------|-------|
| id | INT8/INTEGER | PK, auto-increment |
| username | TEXT | UNIQUE NOT NULL |
| email | TEXT | UNIQUE NOT NULL |
| password_hash | TEXT | Empty for OAuth-only users |
| role | TEXT | DEFAULT 'user' |
| is_admin | BOOLEAN | DEFAULT false |
| google_id | TEXT | nullable |
| avatar_url | TEXT | nullable |
| phone | TEXT | nullable |
| created_at | TIMESTAMP | |

**`user_sessions`** — Active auth sessions
| Column | Type | Notes |
|--------|------|-------|
| token | TEXT | PK, `secrets.token_urlsafe(32)` |
| user_id | INT8 | FK→users, ON DELETE CASCADE |
| expires_at | TIMESTAMP | 7-day TTL |

**`cars`** — Car listings (most columns)
| Column | Type | Notes |
|--------|------|-------|
| id | INT8 | PK |
| owner_id | INT8 | FK→users (optional) |
| make | TEXT | NOT NULL |
| model | TEXT | NOT NULL |
| year | INT | |
| price | REAL | |
| currency | TEXT | DEFAULT 'JOD' |
| odometer_km | INT | |
| image_url, image_urls, gallery_images, media_gallery, video_url | TEXT/JSON | Media fields |
| rating, reviews | REAL/INT | Aggregated from reviews |
| description | TEXT | |
| specs, engines, statistics, source_sheets | JSON | Flexible spec storage |
| category, condition, exterior_color, interior_color, transmission, fuel_type, regional_spec, payment_type, city, neighborhood, trim | TEXT | Filterable fields |
| created_at, updated_at | TIMESTAMP | |

**`dealers`** — Verified dealer profiles
| Column | Type |
|--------|------|
| id | PK |
| name | NOT NULL |
| location, rating, reviews_count, image_url, contact_email, contact_phone | |
| created_at | TIMESTAMP |

**`dealer_applications`** — Dealer onboarding queue
| Column | Type | Notes |
|--------|------|-------|
| id | PK | |
| name, email, phone, city, address, website, description | | Applicant info |
| status | TEXT | 'pending'/'approved'/'rejected' |
| admin_notes, reviewed_by, reviewed_at | | Admin review fields |
| created_at | TIMESTAMP | |

**`favorites`** — User saved listings
| Column | Notes |
|--------|-------|
| user_id + car_id | Composite PK, both FK→ ON DELETE CASCADE |
| created_at | TIMESTAMP |

**`reviews`** — Car reviews with ratings
| Column | Notes |
|--------|-------|
| car_id + user_id | UNIQUE constraint (one review per user per car) |
| rating | INT, 1-5, CHECK constraint |
| comment, created_at, updated_at | |

**`conversations`** — Message threads
| Column | PG name | SQLite name |
|--------|---------|-------------|
| Part A | buyer_id | user1_id |
| Part B | seller_id | user2_id |
| Car ref | car_id | listing_id |
| timestamps | created_at, updated_at | same |
| UNIQUE | (buyer_id, seller_id, car_id) | (user1_id, user2_id, listing_id) |

**`user_messages`** — Individual messages
| Column | Notes |
|--------|-------|
| id | PK |
| conversation_id | FK→conversations ON DELETE CASCADE |
| sender_id | FK→users |
| content | TEXT NOT NULL |
| is_read | BOOLEAN DEFAULT false |
| created_at | TIMESTAMP |

**`password_resets`** — Password reset tokens (1-hour TTL)
**`callbacks`** — Callback request form submissions

### Relationships

```
users ──1:N──> user_sessions
users ──1:N──> cars (owner_id)
users ──1:N──> favorites
users ──1:N──> reviews
users ──1:N──> conversations (as buyer/seller)
users ──1:N──> messages (sender)
users ──1:N──> password_resets
users ──1:N──> dealer_applications (reviewer)

cars ──1:N──> favorites
cars ──1:N──> reviews
cars ──1:N──> callbacks
cars ──1:N──> conversations

conversations ──1:N──> user_messages
```

---

## 6. Authentication & Security

### Auth Flow

```
Frontend                          Backend
─────────                         ───────
POST /api/auth/login ──────────>  validate credentials
                          <────── { token, user }
localStorage.set('token')
localStorage.set('user')

Every request:
Authorization: Bearer <token> ──>  verify in user_sessions table
                              <──── { success, data }
```

### Session Validation (Frontend Boot)

1. Read token+user from `localStorage`
2. **Optimistic render** — show UI immediately
3. `GET /api/auth/verify` in background (15s timeout)
4. On success → update user data
5. On failure + stored user → log error, continue
6. On failure + no stored user → clear auth, show login

This prevents blank-screen on Render cold starts (free tier spins down).

### Security Checklist

| Area | Implementation |
|------|---------------|
| Password storage | `pbkdf2:sha256:260000` (werkzeug) |
| Rate limiting | In-memory IP-based, per-endpoint limits |
| SQL injection | Parameterized queries only |
| XSS | `html.escape()` on all input |
| CORS | Restricted origins in production |
| Clickjacking | `X-Frame-Options: DENY` |
| MIME sniffing | `X-Content-Type-Options: nosniff` |
| CSRF | Not explicitly protected (CORS + SameSite=Lax mitigate) |
| Session expiry | 7-day TTL, deleted on logout/reset |
| Production SECRET_KEY | 32+ chars or app crashes on startup |

### Debug Endpoints (⚠️ marked for removal)

| Endpoint | Exposure | Risk |
|----------|----------|------|
| `/api/debug-verify/<token>` | Unauthenticated | Leaks session data |
| `/api/debug-tables` | Unauthenticated | Lists all tables + row counts |
| `/api/debug-sessions` | Unauthenticated | Leaks recent session tokens |
| `/api/admin-setup/*` | Weak secret (first 16 chars of SECRET_KEY) | Password reset, make admin |

---

## 7. AI Features

### Architecture

All AI features go through `AIService` singleton (`ai_service.py`):
- Initialized at module load time
- Reads `GEMINI_API_KEY` from env
- Tries models in priority: `gemini-2.5-flash` → `gemini-2.5-pro` → fallbacks

### Chatbot (`POST /api/chatbot`)

- Bilingual: auto-detects Arabic via Unicode character counting (>30% = Arabic)
- Last 5 messages sent as context
- Supports image attachments (base64 → multimodal prompt)
- Post-processes response for `json_listing` blocks (parses structured listing data)
- Rate limited only by Gemini quota (no app-level rate limit)

### Price Estimation (`POST /api/price-estimate`)

**Pure rule-based** (the `.joblib` model file is dead code):
- Categorizes make: luxury / premium / standard / budget
- Base prices: 45000 / 30000 / 18000 / 12000 JOD
- Depreciation: 8%/year (years 1-3), 5%/year (4-7), 3%/year (8+)
- Minimum: 30% of base
- Spec adjustments: horsepower, body type bonuses

### Semantic Search (`GET /api/semantic-search?q=...`)

**Keyword-based scoring** (NOT vector embeddings):
- Fetches ALL cars, scores each against query terms
- Matching: make (+50), model (+45), specs (+10), body type (+20), fuel type (+20)
- Price constraints parsed: "under 50k", "below 100000"
- Returns top results with normalized similarity score

### Vision Analysis (`POST /api/vision-helper`)

- Sends base64 image + detailed prompt to Gemini
- Returns: make, model, year, bodyStyle, estimatedPrice, conditionDescription
- Prompt includes Jordanian market price references

### Listing Assistant (`POST /api/listing-assistant`)

- Conversational listing creation (bilingual)
- AI builds structured `listing_data` JSON progressively
- Frontend auto-fills form when user clicks "Create Listing"

---

## 8. File Upload System

### Two-tier storage
1. **Cloudinary** (preferred) — requires `CLOUDINARY_CLOUD_NAME`, `CLOUDINARY_API_KEY`, `CLOUDINARY_API_SECRET`
2. **Local filesystem** — `backend/uploads/` (⚠️ ephemeral on Render — lost on redeploy)

### Endpoints
| Endpoint | Type | Max Size | Notes |
|----------|------|----------|-------|
| `POST /api/uploads/images` | Image | 500MB | png, jpg, jpeg, gif, webp |
| `POST /api/uploads/videos` | Video | 100MB (Cloudinary) / 500MB (local) | mp4, mov, avi, mkv, webm |

### Frontend upload flow
1. User selects file in `addListing` page
2. `uploadImageAsset(file)` → `uploadListingImage(file, token)` → FormData → `POST /api/uploads/images`
3. Returns `{ url }` → stored in `listingForm.image` or `listingForm.galleryImages[]`
4. `resolveImageUrl(src)`: if starts with `http` → use as-is (Cloudinary); if `data:` → base64; else → prepend `apiHost`

---

## 9. API Reference

### Public (no auth)

| Method | Path | Description |
|--------|------|-------------|
| GET | `/api/health` | Health check (DB, AI, Cloudinary status) |
| GET | `/api/stats` | Platform statistics |
| GET | `/api/cars` | List cars (filters: make, search, category, condition, transmission, fuelType, limit, offset) |
| GET | `/api/cars/<id>` | Get car by ID |
| GET | `/api/makes` | Distinct car makes |
| GET | `/api/models` | Models (filter by `?make=`) |
| GET | `/api/engines` | Engines (filter by `?make=&model=`) |
| GET | `/api/reviews/car/<id>` | Car reviews + stats |
| GET | `/api/dealers` | All dealers |
| GET | `/api/dealers/<id>` | Dealer detail |
| GET | `/api/semantic-search?q=` | Natural language search |
| POST | `/api/price-estimate` | Get price estimate |
| POST | `/api/auth/signup` | Register |
| POST | `/api/auth/login` | Login |
| POST | `/api/auth/forgot-password` | Request password reset |
| POST | `/api/auth/reset-password` | Execute password reset |
| POST | `/api/auth/google` | Google OAuth |
| GET | `/api/auth/oauth-config` | Google OAuth config |
| POST | `/api/uploads/images` | Upload image |
| POST | `/api/uploads/videos` | Upload video |
| POST | `/api/dealers/applications` | Submit dealer application |
| POST | `/api/request-callback` | Request callback |
| GET | `/api/swagger.json` | OpenAPI spec |
| GET | `/api/docs` | Swagger UI |

### Authenticated (Bearer token required)

| Method | Path | Description |
|--------|------|-------------|
| GET | `/api/auth/verify` | Verify session |
| PATCH | `/api/auth/profile` | Update profile |
| POST | `/api/auth/logout` | Logout |
| POST | `/api/cars` | Create listing |
| PATCH | `/api/cars/<id>` | Update listing (owner only) |
| DELETE | `/api/cars/<id>` | Delete listing (owner only) |
| GET | `/api/my-listings` | User's listings |
| GET | `/api/my-listings/analytics` | Listing analytics |
| GET | `/api/favorites` | User's favorites |
| POST | `/api/favorites` | Add favorite |
| DELETE | `/api/favorites/<car_id>` | Remove favorite |
| GET | `/api/messages/conversations` | Conversation list |
| GET | `/api/messages/conversations/<id>` | Conversation messages |
| POST | `/api/messages/send` | Send message |
| GET | `/api/messages/unread-count` | Unread count |
| POST | `/api/reviews/car/<id>` | Add/update review |
| DELETE | `/api/reviews/<id>` | Delete review (author only) |
| GET | `/api/reviews/user/me` | User's reviews |
| GET | `/api/analytics/insights` | Market analytics |
| POST | `/api/chatbot` | AI chat |
| POST | `/api/vision-helper` | Analyze car image |
| POST | `/api/listing-assistant` | AI listing helper |

### Admin (requires `is_admin` or specific role)

| Method | Path | Description |
|--------|------|-------------|
| GET | `/api/dealers/applications` | List all applications (?status=) |
| GET | `/api/dealers/applications/<id>` | Application detail |
| PUT | `/api/dealers/applications/<id>/approve` | Approve + create dealer |
| PUT | `/api/dealers/applications/<id>/reject` | Reject with reason |

---

## 10. Development Workflow

### Prerequisites
- Node.js 20+
- Python 3.11+
- Gemini API key (free from [aistudio.google.com](https://aistudio.google.com/apikey))

### Frontend

```bash
npm install
npm run dev              # localhost:3000
npm run lint             # ESLint
npx tsc --noEmit         # Typecheck
npm run build            # Production build
```

### Backend

```bash
cd backend
python -m venv .venv
.\.venv\Scripts\activate     # Windows
# source .venv/bin/activate   # Mac/Linux
pip install -r requirements.txt
# Create backend/.env:
#   GEMINI_API_KEY=your_key_here
#   FRONTEND_ORIGIN=http://localhost:3000
python run.py                # localhost:5000 (debug mode)
```

### CI Pipeline (`.github/workflows/ci.yml`)

Runs on push to `production`/`stg`/`dev`, and PRs to `production`/`stg`:

1. **Frontend:** `npm ci` → `npm run lint` → `npx tsc --noEmit` → `npm run build`
2. **Backend:** `pip install -r backend/requirements.txt` → `python -m py_compile` on 3 key files

**No test framework exists** — no Jest, pytest, or Vitest.

### Git Workflow

```
dev ──► stg ──► production
```

1. All changes go to `dev` first
2. Merge to `stg` for QA/testing
3. Merge to `production` for release

---

## 11. Deployment

### Frontend (Vercel)

- One Vercel project, 3 environments (production, preview-stg, preview-dev)
- Production branch: `production`
- `NEXT_PUBLIC_API_URL` per environment pointing to matching Render backend

### Backend (Render)

- 3 services defined in `render.yaml`:
  - `intelliwheels-backend-prod` ← `production` branch
  - `intelliwheels-backend-stg` ← `stg` branch
  - `intelliwheels-backend-dev` ← `dev` branch

Each service needs these env vars in the Render dashboard:

| Variable | Notes |
|----------|-------|
| `DATABASE_URL` | CockroachDB connection string (one per env) |
| `GEMINI_API_KEY` | Google Gemini API key |
| `SECRET_KEY` | Random 32+ char string |
| `FRONTEND_ORIGIN` | Comma-separated Vercel URLs |
| `BACKEND_URL` | Self-referencing Render URL |
| `CLOUDINARY_*` | Optional — 3 env vars for Cloudinary |

### Database (CockroachDB Serverless)

- Free 10 GiB tier
- One cluster per environment recommended
- Connection string goes in `DATABASE_URL`

---

## 12. Common Pitfalls & Gotchas

### Frontend

| Pitfall | Detail |
|---------|--------|
| **AppView.tsx is monolithic** | 5400 lines, one component. Any UI change touches this file. Consider refactoring into smaller components. |
| **No automated tests** | CI only checks syntax + build. Manual testing required. |
| **Session validation race** | Background validation may complete before or after user interacts. Allow for offline/partial states. |
| **Token auto-discovery** | `apiRequest()` searches multiple localStorage keys. Conflict if other apps use same keys. |
| **Language not persisted** | Language resets to English on page reload. Must re-toggle. |
| **Leaflet SSR crash** | `DealerMap` must be `dynamic(() => import(...), { ssr: false })`. Any import outside this pattern will crash build. |
| **Image URL resolution** | `resolveImageUrl()` has 3 cases. If Cloudinary URL format changes, images may not load. |
| **Optimistic favorites** | UI updates before API responds. On failure, must revert — but revert logic may not cover all edge cases. |

### Backend

| Pitfall | Detail |
|--------|--------|
| **Conversations table schema mismatch** | PostgreSQL uses `buyer_id/seller_id/car_id`, SQLite uses `user1_id/user2_id/listing_id`. Any query must check `is_postgres()`. |
| **Dual SQL everywhere** | Every query has `if is_postgres(): ... else: ...` branching. Easy to miss one branch. |
| **PostgreSQL transaction abortion** | Any error aborts the entire transaction. `db.rollback()` must be called before retrying. |
| **Lazy table creation** | Some routes call `CREATE TABLE IF NOT EXISTS` on every request. Works but is wasteful on SQLite. |
| **Debug endpoints exposed** | `/api/debug-verify/<token>` and `/api/debug-tables` have no auth. Marked for removal. |
| **Admin-setup endpoints** | Protected by first-16-chars of SECRET_KEY (which is known to any developer with access). |
| **Rate limiting is in-memory** | IP-based rate limiting resets on server restart. For horizontal scaling, needs Redis. |
| **SQLite vs PostgreSQL booleans** | Python `True`/`False` converted to 1/0 in SQLite, proper boolean in PG. |
| **Email not configured** | Password reset email falls back to `print()` in console if SMTP not set up. |
| **Price estimator ignores ML model** | `fair_price_model.joblib` is loaded but never used. Price estimation is rule-based. |
| **AIService is a global singleton** | Initialized at import time. If `GEMINI_API_KEY` changes at runtime, restart needed. |
| **CockroachDB SSL** | `sslmode=require` is auto-added, but some environments need `sslrootcert=system`. Check if connection fails. |

### Deployment

| Pitfall | Detail |
|---------|--------|
| **Uploads ephemeral on Render** | Without Cloudinary, all uploaded files are lost on every deployment. |
| **Render cold start** | Free tier spins down after inactivity. First request takes ~30s. Frontend handles this via optimistic auth. |
| **Vercel build needs API URL** | `npm run build` in CI needs `NEXT_PUBLIC_API_URL` set to a valid backend URL (for Sentry source maps). |
| **SECRET_KEY validation** | App crashes on startup in production if key is <32 chars or 'dev'. |
| **Branch mismatches** | CI, render.yaml, and Vercel all must agree on branch names. Currently: `production`, `stg`, `dev`. |

---
