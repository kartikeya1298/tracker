# DataScience Career Tracker AI

Monitors career pages at 62 companies (the original 50 plus 12 analytics-consulting/
India-product-company additions — see the registry section below) every 15 minutes,
filters for fresher / 0–2 yr
Data Science roles (Data Analyst, Data Scientist, ML Engineer, AI Engineer, and 16 more
close variants), deduplicates against previously-seen postings, enriches new matches
with Claude (summary, skill extraction, resume match score, learning recommendations),
emails you instantly, and surfaces everything in a Next.js dashboard with bookmarks,
an application tracker, and CSV/Excel export.

## Architecture

```
backend/          FastAPI + SQLAlchemy + APScheduler + Playwright/httpx scrapers
  app/scrapers/    One adapter per ATS: Greenhouse, Lever, Workday, and a config-driven
                   generic Playwright adapter for SuccessFactors/Taleo/Oracle/custom sites
  app/core/        Role matching, experience/location/internship filters, dedup, ranking
  app/ai/          Claude-powered enrichment (summary/skills/resume match) + client
  app/routers/     REST API (jobs, companies, stats, bookmarks, applications, export)
  app/pipeline.py  Orchestrates one full monitoring cycle
  app/scheduler.py Runs the pipeline every SCRAPE_INTERVAL_MINUTES (default 15)

frontend/          Next.js 15 (App Router) + TypeScript + Tailwind dashboard
docker-compose.yml Postgres + Redis + backend + frontend
```

## Quickstart (Docker Compose)

```bash
cp .env.example .env
# edit .env: at minimum set ANTHROPIC_API_KEY for AI features and SMTP_* for email alerts
mkdir -p data && cp data/resume.example.txt data/resume.txt   # then edit with your real resume

docker compose up --build
```

- Dashboard: http://localhost:3000
- API: http://localhost:8000 (docs at http://localhost:8000/docs)

On first boot the backend seeds the 50-company registry and starts the 15-minute
scheduler automatically. Trigger an out-of-band scan any time with:

```bash
curl -X POST http://localhost:8000/api/jobs/scrape-now
```

## Manual/dev setup (no Docker)

```bash
# Backend
cd backend
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
playwright install --with-deps chromium
export DATABASE_URL="postgresql+psycopg://tracker:tracker@localhost:5432/career_tracker"
uvicorn app.main:app --reload

# Frontend (separate shell)
cd frontend
npm install
NEXT_PUBLIC_API_URL=http://localhost:8000 npm run dev
```

Run the backend test suite:

```bash
cd backend && pytest
```

## Company registry — what's verified vs. what needs setup

`backend/app/scrapers/registry.py` seeds 63 rows: the original 50 user-specified
companies (51 rows — Adobe has a second early-careers Workday site) plus 12
user-approved additions — pure-play analytics/decision-science consulting firms
(Mu Sigma, Fractal Analytics, ZS Associates, Tiger Analytics, LatentView Analytics)
and India-based product companies/GCCs with large data science hiring (Flipkart,
Swiggy, Target India, American Express, Optum, EXL Service, WNS Global Services) —
that are often more fresher-friendly for DS specifically than several companies on
the original list. Two tiers:

- **Verified (30 rows, work immediately):** API-backed rows (Greenhouse, Lever,
  Workday's CxS API — Databricks, Airbnb, 11 Workday companies including the new
  Fractal Analytics, confirmed via live job-posting URLs/the real API) plus
  CSS-selector rows with real selectors extracted from live rendered HTML via
  `tools/inspect_career_sites.py` (SAP, Siemens, Amazon, Microsoft, IBM, Apple,
  Snowflake, Goldman Sachs, Deloitte, Accenture, Infosys, LTIMindtree, EY, PwC,
  Ericsson, Zoho, HCLTech). Several needed more than a selector fix — their query
  strings don't actually trigger a search on page load, only a real keystroke+submit
  against the search box, so `GenericPlaywrightScraper`
  (`app/scrapers/generic.py`) supports an optional `search_input_selector`/
  `search_submit_selector`/`search_text` config for that. CSS-selector rows are
  inherently more fragile than API-backed ones since a site redesign can silently
  break a selector, so still worth a periodic spot-check.
- **Best-effort (needs bespoke work, ~33 rows):** several inspection passes (see
  `tools/inspect_career_sites.py`'s git history for what each one found and fixed)
  got the count this far, including catching real bugs in my own guessed URLs along
  the way (wrong domains for Cisco/Cognizant/HCLTech/Zoho/Ericsson, a missing
  trailing slash for Google) once real ones were confirmed. What's left mostly
  didn't yield to a generic "type into a search box" heuristic — dropdown/
  autocomplete filter UIs instead of free text (confirmed for Bosch: a
  country-then-location autocomplete), multi-step flows, or persistent
  bot-detection/network failures (TCS). Several (Nokia, Oracle, JPMorgan Chase,
  Cisco, American Express, EXL Service) run Oracle Fusion Cloud Recruiting, whose
  two-field "Find"/"Near Location" search bar has a known interaction bug (Enter
  advances focus to the wrong field) — a deep-link URL with location params baked
  in bypasses it for some tenants but not all; still being worked through.

  Each entry has the correct `careers_url` and a *template* config for
  `GenericPlaywrightScraper`. Being honest about this bucket: it needs either
  per-company selector work like the successful rows above, or a further
  extension of the inspection tool to handle dropdown-based filter UIs — not more
  blind retries of the same search-box heuristic against sites that don't have one.

  **`tools/inspect_career_sites.py`** automates the discovery step from anywhere
  with normal internet access — a GitHub Actions runner (see
  `.github/workflows/inspect-career-sites.yml`, triggered via `workflow_dispatch`;
  results get committed straight back to the branch that ran it) or your own
  machine. It opens each unconfigured career site in a real Chromium (realistic
  desktop user-agent, `navigator.webdriver` masked, cookie-consent banners
  auto-dismissed) and, instead of dumping the full page HTML, scans for repeated
  "job card" DOM patterns — grouping elements by tag+class, first by
  career/job/listing-related class-name keywords, then (for sites using hashed
  CSS-in-JS classnames, where keyword matching finds nothing) by "repeated element
  wrapping a title-length link." It always also tries a search-box interaction
  (type "data scientist", submit, re-scan) regardless of whether the initial scan
  found something, since nav-menu/footer/testimonial content routinely clears the
  "≥3 repeated elements" bar without being real listings — both the `initial` and
  `after_search` candidate sets are kept in the output so a bad "which one's
  better" guess is easy to spot and override. It also checks Workday dc-subdomain
  ambiguity directly against the real CxS API rather than guessing, and retries
  hard navigation/network errors once before giving up.

  ```bash
  cd tools
  pip install -r requirements.txt
  playwright install chromium
  python inspect_career_sites.py                            # all unresolved sites
  python inspect_career_sites.py --only ericsson,cognizant   # just a few
  ```

  This writes `tools/site_inspections/<slug>.json` (`initial`/`after_search`
  candidate sets + HTML snippets + a screenshot) per company and a `summary.json`
  across all of them.

This mirrors how a real deployment is bootstrapped: platform + URL is known on day
one, selectors get filled in per-target during onboarding, and adapters degrade
gracefully (a misconfigured company just contributes 0 jobs that cycle, logged as an
error in `ScrapeRun.errors` — it never crashes the run for the other companies).

**Before enabling scraping against any site, check its Terms of Service and
`robots.txt`.** Several companies (Workday, SuccessFactors, Oracle Recruiting Cloud)
explicitly restrict automated access in their ToS. This project targets each
platform's documented public APIs where they exist (Greenhouse, Lever, Workday's CxS
API) precisely to stay off the "silently scraping the DOM" path, but you are
responsible for confirming acceptable use for each company you point it at.

## Target roles

Data Analyst · Business Analyst · Junior Data Analyst · Data Scientist · Junior Data
Scientist · Associate Data Scientist · Machine Learning Engineer · Junior Machine
Learning Engineer · AI Engineer · Applied Scientist · Research Scientist (AI/ML) ·
Data Engineer · Analytics Engineer · Business Intelligence Engineer · BI Analyst ·
Decision Scientist · AI/ML Engineer · Generative AI Engineer · Statistical Analyst ·
Quantitative Analyst (Entry Level)

Matching lives in `app/core/roles.py` (regex-based, most-specific-first so "Junior
Data Scientist" isn't collapsed into plain "Data Scientist") and excludes unrelated
software engineering roles and senior/lead/manager titles unless an entry-level
signal (junior/associate/graduate/fresher/campus/early career) is also present.

## Filtering

- **Location** (`app/core/filters.py`): India-based locations always pass; Remote and
  fully Global postings are opt-in via `INCLUDE_REMOTE` / `INCLUDE_GLOBAL`.
- **Experience**: parses ranges like "0-2 years", "3+ years", "minimum 1 year" from
  the job text; falls back to entry-level keyword detection (fresher/graduate/
  associate/junior/campus) when no explicit range is stated. Roles requiring more
  than `MAX_EXPERIENCE_YEARS` (default 2) are dropped.
- **Internships**: excluded by default; set `INCLUDE_INTERNSHIPS=true` to include them.

## Deduplication

Every job gets a stable `dedup_hash` (`app/core/dedup.py`): the ATS's own posting ID
when available (Greenhouse/Lever/Workday all provide one), else a normalized
title+location composite. A `UNIQUE` DB constraint on `dedup_hash` means a job is
inserted — and notified — exactly once, no matter how many times the 15-minute cycle
re-scrapes the same posting.

## AI features

Set `ANTHROPIC_API_KEY` to enable. Each newly-matched job gets one Claude call
(`app/ai/enrichment.py`) that returns a JSON summary, extracted skills, a resume
match score (0–100) against `data/resume.txt`, gap notes, and learning
recommendations. Skill extraction is also backed by a deterministic keyword list
(`app/ai/skills.py`) that's merged in regardless of AI availability, so skills still
populate with `AI_FEATURES_ENABLED=false`. Final ranking (`app/core/ranking.py`) is a
transparent weighted formula — role relevance (40%) + company reputation tier (25%,
`app/core/reputation.py`) + resume match (35%) — that degrades gracefully to a
50/50 role/company split when resume matching is off.

## Notifications

Email only, via SMTP (`app/notifications/email.py`). Set `SMTP_HOST` and
`NOTIFICATION_TO_EMAILS` in `.env`; leave `SMTP_HOST` blank to run without
notifications (jobs still populate the dashboard). Every send attempt is logged to
the `notification_logs` table.

## Dashboard

Next.js dashboard (`frontend/`) with: total jobs / jobs today / this week / companies
tracked stat tiles, company/role/location filters, full-text search, sort by best
match / newest / recently found, bookmarks, a status-based application tracker
(saved → applied → interviewing → offer/rejected), dark mode (persisted, respects
system preference), and CSV/Excel export.

## API reference

`GET /api/jobs`, `GET /api/jobs/{id}`, `POST /api/jobs/scrape-now`,
`GET /api/companies`, `GET /api/stats`,
`GET/POST/DELETE /api/bookmarks`, `GET/POST/PATCH/DELETE /api/applications`,
`GET /api/export/csv`, `GET /api/export/xlsx`. Full interactive docs at `/docs`
once the backend is running.

## Known limitations / next steps

- 30 of 63 companies are scrape-verified out of the box as of this writing; see
  "Company registry" above to activate the rest — this is expected onboarding work,
  not a bug.
- No auth on the dashboard/API — it's designed for single-user personal use behind
  your own network; add an auth layer before exposing it publicly.
- No Alembic migrations yet; schema is created via `Base.metadata.create_all()` on
  startup. Fine for a personal tracker; add Alembic if you need managed migrations.
- Salary is rarely provided by ATS listing APIs and is left blank unless the source
  explicitly includes it.
