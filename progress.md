# Project Progress

**Project:** সোনার দাম — Gold Investment Insight App for Bangladesh
**Started:** 2026-04-02
**Last updated:** 2026-04-02

---

## What We're Building

A web app for Bangladeshi users to:
1. See live daily gold prices (sourced from bajus.org / BAJUS)
2. Track historical price trends via interactive chart
3. Calculate ROI on past gold purchases
4. Manage a personal gold portfolio (multi-purchase tracking)

**Target users:** General public, existing gold owners, potential investors in Bangladesh
**UI language:** Bangla primary, English secondary
**Gold units:** Bhari, Ana, Roti, Gram, Tola, Ounce
**Gold karats:** 22k, 21k, 18k, 24k (pure), Sanatan

---

## Accomplished

### Phase 1 — Design (2026-04-02) ✅
- Completed full product design via 14-question grill-me session
- All decisions documented with rationale in `memory/decisions.md`

### Phase 2 — Initial Build (2026-04-02) ✅

#### Backend (Python)
- [x] `backend/shared/models.py` — GoldPrice dataclass, karat definitions
- [x] `backend/shared/dynamo.py` — DynamoDB CRUD helpers (put, get, range scan, latest)
- [x] `backend/shared/units.py` — Full unit conversion (all 6 units, Decimal precision)
- [x] `backend/lambdas/scraper/handler.py` — Daily scraper Lambda (bajus.org → DynamoDB)
- [x] `backend/lambdas/api/handler.py` — API Lambda with 3 routes:
  - `GET /prices/latest` — today's prices
  - `GET /prices?start=&end=` — historical range
  - `GET /prices/roi?buy_date=&amount=&unit=&karat=` — ROI calculation

#### Infrastructure
- [x] `infrastructure/setup_localstack.py` — Creates all AWS resources locally:
  - DynamoDB table (`gold-prices`, partition key: `date`)
  - Lambda functions (scraper + api)
  - API Gateway (REST, `/prices` routes)
  - EventBridge rule (daily cron at 6AM UTC = 12PM BST)
  - S3 bucket with static website hosting

#### Frontend (React + Vite)
- [x] Dark theme CSS with Hind Siliguri Bangla font, gold color palette
- [x] 3-tab navigation: ড্যাশবোর্ড / ROI ক্যালকুলেটর / পোর্টফোলিও
- [x] `PriceCard` — today's prices for all 5 karats in a grid
- [x] `PriceChart` — interactive line chart with karat selector + date range filter (recharts)
- [x] `RoiCalculator` — single-purchase ROI form (date, amount, unit, karat) with profit/loss result
- [x] `Portfolio` — multi-purchase tracker with localStorage persistence + live ROI per entry + summary totals
- [x] API client (`utils/api.js`)
- [x] localStorage portfolio helpers (`utils/portfolio.js`)

#### Dev Tooling
- [x] `scripts/run_scraper_local.py` — test scraper without Lambda deploy
- [x] `requirements.txt`, `frontend/package.json`
- [x] `SETUP.md` — step-by-step local dev guide
- [x] `docker-compose.yml` — LocalStack + Mailhog (pre-existing)

---

## Current State

**LocalStack is running and all three API routes are confirmed working end-to-end.**

The system is fully operational locally. All bugs found during first deployment have been fixed. Frontend needs `npm install && npm run dev` to start.

### Confirmed facts about bajus.org (discovered 2026-04-02)
- Prices are **per gram** (BDT/GRAM) — scraper converts to per bhari on store (× 11.664)
- Table has 3 columns: Product | Description | Price — price is in column index 2
- Karat labels: "22 KARAT Gold", "21 KARAT Gold", "18 KARAT Gold", "TRADITIONAL Gold" (= Sanatan)
- **No 24k gold listed** on bajus.org — removed from expected fields
- bajus.org returns 403 to plain httpx — Playwright (headless browser) required
- Scraper successfully ran on 2026-04-02, stored 4 karat prices in DynamoDB

### Historical data seeded (2026-04-02)
- `backend/prices.csv` — 707 rows, 2007-03-07 to 2025-09-11, per gram
- Seeded via `scripts/seed_historical.py` — batch writes, converts per-gram to per-bhari (× 11.664)
- Gap of ~7 months (Sep 2025 → Apr 2026) — chart connects dots silently (`connectNulls=true`)
- DynamoDB now has 708 total records (707 CSV + 1 live scraper)

### Verified API routes (2026-04-02) ✅
| Route | Result |
|-------|--------|
| `GET /prices/latest` | Returns today's 4-karat prices (live bajus.org data) |
| `GET /prices?start=&end=` | Returns 60 records for Jan–Mar 2025 range test |
| `GET /prices/roi?buy_date=2025-01-15&amount=1&unit=bhari&karat=karat_22` | Returns full ROI breakdown (77.83% gain) |

### API endpoint (LocalStack)
```
http://localhost:4566/restapis/2mdvlqjnsz/prod/_user_request_
```
`frontend/.env` already contains this URL. API ID `2mdvlqjnsz` is stable (reused across re-runs).

### Bugs fixed during first deployment (2026-04-02)
See `LOCALSTACK_COMMANDS.md` for full debug session log.

1. **`No module named 'backend'`** — `zip_lambda()` packs shared code as `shared/` at zip root, but handler imports said `from backend.shared.X`. Fixed: changed both handlers to `from shared.X import ...` and removed broken `sys.path.insert`.
2. **`/prices/latest` → "Missing Authentication Token"** — API Gateway only had `/prices` resource; sub-paths were never registered. Fixed: `setup_localstack.py` now creates `/prices/latest` and `/prices/roi` resources.
3. **`EndpointConnectionError: localhost:4566`** — Lambda runs inside a Docker container; `localhost` inside the container is not the host. LocalStack Pro sets `LOCALSTACK_HOSTNAME` inside Lambda containers. Fixed: `dynamo.py` now reads `LOCALSTACK_HOSTNAME` first, falls back to `LOCALSTACK_ENDPOINT` for local scripts.

---

## Next Steps

### Immediate — Start the UI
- [ ] `cd frontend && npm install && npm run dev`
- [ ] Open browser to `http://localhost:5173`
- [ ] Verify dashboard loads with live prices
- [ ] Test ROI calculator with a real date (e.g. 2025-01-15)
- [ ] Test portfolio add/remove/persist in localStorage

### Short-term — Polish & verify
- [ ] Mobile responsiveness check
- [ ] Verify chart renders full historical range (2007–2026) with gap visible
- [ ] Test karat selector and date range filter in chart
- [ ] Confirm `connectNulls=true` bridges the Sep 2025 → Apr 2026 gap gracefully

### Medium-term — Production readiness
- [ ] CloudFront distribution for the S3 frontend bucket
- [ ] Deploy Lambdas to real AWS (not just LocalStack)
- [ ] Set up real EventBridge daily trigger on AWS
- [ ] Error handling if bajus.org is unreachable (store last known price, surface stale warning in UI)
- [ ] CloudWatch alarms for scraper failures

### Medium-term — Production readiness
- [ ] CloudFront distribution for the S3 frontend bucket
- [ ] Deploy Lambdas to real AWS (not just LocalStack)
- [ ] Set up real EventBridge daily trigger on AWS
- [ ] Error handling if bajus.org is unreachable (store last known price, surface stale warning in UI)
- [ ] CloudWatch alarms for scraper failures

### Future (v2)
- [ ] Price change visual indicators (% up/down vs yesterday)
- [ ] Share portfolio as a link (encode in URL params)
- [ ] Compare gold returns vs FDR / savings rates

---

## Tech Stack Summary

| Layer | Technology |
|-------|-----------|
| Frontend | React 18 + Vite → S3 + CloudFront |
| API | Python Lambda + API Gateway (REST) |
| Scraper | Python Lambda + EventBridge (daily cron) |
| Database | DynamoDB (`gold-prices` table, PK: `date`) |
| Local dev | LocalStack free tier (docker-compose) |
| Scraping libs | httpx + BeautifulSoup4 |
| Chart | Recharts |
| Font | Hind Siliguri (Google Fonts) |

---

## Key Decisions (summary)

| Decision | Choice | Rejected |
|----------|--------|---------|
| Accounts | None — localStorage only | OAuth, phone OTP |
| Price source | Scheduled Lambda scraper → DynamoDB | Direct client scrape, manual entry |
| History limit | Forever — accumulate from day 1 | Fixed window (30/90/365 days) |
| Frontend | React + Vite SPA | Next.js SSR |
| Backend | Python Lambda | Node.js Lambda |
| Alerts | None for MVP | Push notifications, visual badges |
| Language | Bangla primary | English only, full i18n toggle |

Full rationale for every decision: `memory/decisions.md`
