# CareerTwin AI

An academic prototype for exploring career options and their possible futures. Salary figures and career trajectories will be illustrative estimates, not guaranteed predictions. The first version is designed to use a local career dataset and deterministic, explainable scoring; no external AI API is required.

## Project structure

- `src/` — React + TypeScript + Vite frontend
- `backend/` — FastAPI, SQLAlchemy, SQLite, local career catalog, profile API, and CareerTwin generation

## Application structure

After sign in and profile setup, the frontend opens a focused CareerTwin workspace. `CareerTwinDashboard` owns the shared dashboard shell, sidebar navigation, current journey context, account controls, and Overview page. Feature modules render only for the active page; the larger simulators remain lazy-loaded.

Client-side routes use React Router. The dashboard shell stays mounted while its route element changes, and only the selected feature page renders. Routes are `/career-twin` (Overview), `/career-twin/career-fit`, `/career-twin/comparison`, `/career-twin/what-if`, `/career-twin/simulation`, `/career-twin/salary`, `/career-twin/skills`, `/career-twin/development-plan`, `/career-twin/switching`, `/career-twin/ai-risk`, `/career-twin/market`, `/career-twin/trade-offs`, and `/career-twin/education-roi`. Login, sign up, and profile setup use `/login`, `/signup`, and `/profile`. Browser Back/Forward and direct route refresh are supported; production hosting must serve the SPA entry point for these paths.

Profile and account identity continue to come from the authenticated session and backend profile API. Market, What-If, comparison selection, simulation selections, development target, career-switch inputs, decision settings, and education assumptions use the existing journey-session helper. The comparison page adds only its own persisted set of career IDs; its displayed fit and market fields are existing CareerTwin values, not a new scoring model. Start Over resets journey assumptions and opens profile setup while keeping the account and persisted profile intact.

## Requirements

- Node.js 20.19+ or 22.12+ and npm
- Python 3.10+

## Run locally

In one terminal, start the API:

```bash
cd backend
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
cp .env.example .env
set -a
source .env
set +a
uvicorn app.main:app --reload
```

The API is available at `http://localhost:8000`; its health check is `http://localhost:8000/api/health`, and interactive API docs are at `http://localhost:8000/docs`. The career catalog is seeded into SQLite on startup, and profiles and their latest generated CareerTwin are saved locally. `GET /api/simulations?market=IN` returns India trajectories in INR lakh/year, and `market=US` returns US trajectories in USD/year. Set `CAREERTWIN_DATABASE_URL` to use a different SQLAlchemy database URL.

In another terminal, install and start the frontend from the project root:

```bash
cp .env.example .env
npm install
npm run dev
```

Open the URL printed by Vite (usually `http://localhost:5173`). The first version includes profile creation/editing, the local career catalog, and a personalized CareerTwin dashboard. Career fit is an explainable 0–100 profile-alignment estimate: interests contribute up to 40 points, skills 30, work preferences 15, and career priorities 15. Each factor divides its weight evenly across the student's selected options; aligned options earn their share and unmatched options earn no points. Empty optional skills do not create a penalty. Each career card reports the matched and unmatched selections, factor points, and calculation explanation. The dashboard also compares illustrative 10-year annual salary ranges and possible role/skill milestones for India (INR lakh) or the United States (USD). The sample ranges are not predictions or guarantees, use nominal local currency, and are interpolated between illustrative stage estimates.

The 10-year simulation returns one point for each year (0–10), plus six market snapshots at years 0, 1, 3, 5, 7, and 10 with role, required skills, demand, AI exposure, salary range, possible promotion, and transition context. Salary figures are labelled **illustrative scenario-based estimates**. Values are sample prototype estimates in nominal local currency, interpolated linearly between career-stage milestones; they exclude bonus, tax, inflation, location-level differences, and individual outcomes. They are not guarantees or predictions.

Career fit now combines **85% profile alignment** (existing factor weights remain 40/30/15/15) and **15% market alignment**. Market alignment is separately and deterministically scored from job demand, demand trend, salary growth, hiring trend, AI resilience, and fit to emerging skills; each card exposes the factor calculations and skill gaps. Changing the selected market calls `POST /api/profiles/{profile_id}/careertwin?market=IN` or `market=US` and recalculates the career scores and ranking from that market's current local signals.

The Labor Market Intelligence dashboard is driven by a normalized per-career/per-market table in SQLite and a replaceable `MarketDataProvider` interface. The provider exposes market/career retrieval, last-update and provenance metadata, record updates, and market refresh/upsert operations. `GET /api/markets` lists market metadata and availability; `GET /api/market-intelligence?market=IN` (or `US`) returns all career signals, currency, source, confidence, and update time. India (INR) is selected by default. The United States (USD) is also enabled; UK (GBP), Canada (CAD), Australia (AUD), and Germany (EUR) are listed but disabled until local market and salary datasets are configured. This avoids implying comparable salary data where none has been added.

**Market-data status: Prototype / Illustrative.** The seeded signals are synthetic demonstration values (confidence 25%), last dated October 1, 2026; they are not sourced from observed vacancies, official statistics, or salary datasets. No automatic or real-time feed is connected. The provider interface is the future integration point for reviewed labor-market APIs, job-posting data, salary datasets, and government/open data. The product concept is to use updated signals and scenario modeling to explore possible trajectories—not to claim an exact 10-year prediction.

The dashboard's **Run demo market update** action applies a deterministic local scenario to the selected market's Product Analyst record (demand index to 50, declining demand and hiring trends), persists the updated record and timestamp, regenerates the CareerTwin scores/ranking, and refreshes the market, What-If, and simulation views from the stored data. A separate **Reset demo data** action restores that career-market record's seeded illustrative values. The before/after panel explains which inputs changed. These are demonstration updates—not live refreshes. The API route is `POST /api/profiles/{profile_id}/market-intelligence/{market}/demo-update?career_id=product-analyst&action=apply|reset`.

The dashboard's What-If Simulator compares the saved-profile baseline with all eight existing career conditions plus seven market conditions: demand up/down, AI adoption up/down, salary growth up/down, and emerging skills emphasized. `POST /api/profiles/{profile_id}/what-if?market=IN` (or `market=US`) accepts those as boolean JSON fields. It returns before/after fit scores, market indices, AI exposure, salary growth, skill gaps, explainable score effects, and salary/role scenarios. Opposing market controls cannot be enabled together. Salary growth assumptions compound the local illustrative salary path; demand, AI, and skill changes update market alignment and stage outlook without inventing promotion or salary causality. Faster growth and supported MBA routes keep their existing behavior. Scenario calculations do not modify the saved student profile.

The **Career Switching Simulator** is available from the dashboard navigation and uses `POST /api/career-switch`. Its request includes the saved `profile_id`, current/target career IDs, market, switch timing (0/1/2/3/5 years), education willingness, learned-skill assumptions, and supported existing What-If toggles. Transition edges and target-career skill requirements are explicitly configured in `backend/app/data/career_transitions.py`; unsupported routes are rejected. Product Manager was added as a selectable career with illustrative market and salary records, enabling Data Analyst → Product Analyst → Product Manager and a configured direct alternative. HR Analyst and Digital Marketing Manager have since been added using the same career catalog, with market and salary scenarios and configured switching requirements. Skill overlap is deterministic: 70% profile signals and explicit learning assumptions (direct matches count fully, related signals/interests partly) plus 30% current-role skill coverage. Assumed skills are shown separately from profile-evidenced skills; the profile stores skill tags, not proficiency ratings, so the UI does not invent skill levels. Stay/switch salary curves reuse `build_career_simulations`; all values remain illustrative. Market/AI/salary what-if assumptions are local scenario transforms and do not change the saved profile.

The **AI Risk Dashboard** is a separate career-risk configuration in `backend/app/data/ai_risk.py`, evaluated by `backend/app/services/ai_risk.py` and exposed through `GET /api/ai-risk?market=IN` and `POST /api/ai-risk/{career_id}/analysis`. It breaks each configured role into representative tasks, shows exposure/AI assistance/human-judgment signals and task categories, compares up to three careers, and returns opportunities, potential task changes, future skills, and market provenance. Current scores are deterministic prototype configuration values; resilience is calculated from weighted human judgment, communication, strategic importance, leadership, domain expertise, complexity, AI complementarity, and inverse automation exposure. The dashboard shares the same What-If scenario state with the Career Fit What-If panel: AI adoption changes recalculate risk and task exposure; learning technical skills creates separately labeled scenario assumptions for readiness; the existing What-If API provides the before/after career fit score and explanation. Market status, source, confidence, and last-updated time come from the selected `MarketDataProvider`; no live labor-market source is connected. Saved skills are boolean tags rather than proficiency levels, so personalized readiness is a weighted tag-to-future-skill match, not a validated capability assessment.

Run the backend behavior tests from the backend folder:

```bash
python -m unittest discover -s tests -v
```

Run the frontend production type-check/build from the project root with:

```bash
npm run build
```

## Production deployment (Render)

The repository includes a `render.yaml` Blueprint for a FastAPI web service, a static Vite frontend, PostgreSQL, the backend health check, and the React Router SPA fallback. It does not contain credentials. The frontend sends API calls to its own `/api` path; the Render static-site rewrite proxies those calls to the backend, keeping the browser requests same-origin so the existing HttpOnly `SameSite=Lax` session cookie works without third-party cookies. The API CORS allowlist is set from the deployed frontend origin.

Before deploying, push the repository to a Git provider supported by Render. In Render, create a Blueprint from that repository and review the resources and billing before applying it. The Blueprint names the API `careertwin-api`; verify that Render assigns it `https://careertwin-api.onrender.com`. If Render assigns a different hostname, update the `/api/*` rewrite destination in `render.yaml` to that API hostname and redeploy the static site. The Blueprint selects Render's smallest paid PostgreSQL compute plan so production data does not expire; its free PostgreSQL instances expire after 30 days and are intended for testing, not production ([Render free-instance limitations](https://render.com/docs/free)). Review or adjust service/database plans and region in Render before creating resources; no infrastructure has been created by this repository change.

The Render backend uses `DATABASE_URL` from the Blueprint database reference, `CORS_ORIGINS` from the frontend service URL, `CAREERTWIN_ENVIRONMENT=production`, and `CAREERTWIN_COOKIE_SECURE=true`. The backend starts with `uvicorn app.main:app --host 0.0.0.0 --port $PORT`; Render checks `GET /health` (the existing `GET /api/health` remains available too). The static site builds with `npm ci && npm run build`, publishes `dist/`, and rewrites feature routes to `index.html`.

For a non-Render frontend host such as Vercel, `vercel.json` supplies the SPA fallback. Set `VITE_API_BASE_URL` in Vercel's build environment to the backend **origin** (without `/api`); the API client appends `/api`. Set backend `CORS_ORIGINS` to the exact frontend origin. Because the current session cookie is `SameSite=Lax`, use frontend and API custom domains under the same registrable domain, or configure a same-origin API proxy as Render does. Do not rely on separate provider subdomains for cross-site cookies.

Database startup uses SQLAlchemy `create_all` plus idempotent additive checks for columns/indexes used by earlier schemas, and seeds only missing career/market rows. It does not drop or recreate existing tables. No migration framework is currently installed; use explicit migrations for future schema changes that cannot be represented by these additive checks.
