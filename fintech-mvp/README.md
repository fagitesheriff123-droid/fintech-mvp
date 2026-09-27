# AI Personal Finance Platform — v1 (Phases 1–5 scaffold)

This is a working starting point for Phases 1–5 of the reshaped roadmap:
auth, CSV statement upload, a dashboard, predictive analytics, planning
tools, and now an **opt-in, off-by-default** experimental track —
sandbox account linking, a clearly-labeled synthetic market signal, and
a spending Q&A assistant scoped strictly to the user's own data.

## What's here
- **backend/** — FastAPI + PostgreSQL.
  - Signup/login (JWT)
  - CSV upload and parsing (`app/services/parser.py`)
  - Transaction listing
  - **Phase 3 analytics** (`app/services/analytics.py`, `app/routers/analytics.py`):
    - `/analytics/forecast` — per-category prediction for next month, using a
      linear trend on monthly totals (kept deliberately simple — honest given
      how little history a new user has)
    - `/analytics/anomalies` — IsolationForest per category, flags unusual
      transactions and explains why in plain language
    - `/analytics/health-score` — one 0–100 number from savings rate
  - **Phase 4 planning** (`app/services/simulator.py`, `app/routers/planning.py`):
    - `/planning/simulate?extra_savings=N` — "what if I saved ₦N more/mo",
      reusing the user's own avg income/spend, no market data involved
    - `/planning/goals` + `/planning/goals/{id}/projection` — set a target
      amount and date, get required monthly savings and whether you're on track
    - `/planning/debts` + `/planning/debts/payoff-order?strategy=avalanche|snowball` —
      enter debts directly, get a payoff order with the reasoning (highest
      interest first for avalanche, smallest balance first for snowball)
- **frontend/** — React + Tailwind + Recharts. Login, upload, dashboard
  (health score, forecast, flagged transactions), Planning (simulator,
  goals, debt payoff), and Experimental (off by default — see below).
- **docker-compose.yml** — Postgres + Redis + backend in one command.
- **SECURITY.md** — Phase 6 security pass: what was fixed (secret key
  handling, CORS, rate limiting, upload size cap, account deletion/export)
  and what's flagged for before real users touch this.
- **NDPR_DATA_HANDLING.md** — what's collected, why, and what's still
  missing (retention policy, consent language) before this is real.
- **WRITEUP.md** — final write-up template; the honest-accuracy-numbers
  section is left blank on purpose — fill it in after running this
  against real data rather than trusting invented numbers.

## Phase 5 — experimental track (off by default)
Set `ENABLE_EXPERIMENTAL=true` on the backend to turn it on. It's
deliberately isolated from every other router so leaving it off costs
nothing and changes nothing else:
- **Sandbox account link** — fabricated demo balances, shaped like a
  Mono/Okra response, so the frontend can be built against a stable
  shape before real credentials or NDPR-aware handling exist. No network
  call, no real bank, ever.
- **Market trend module** — runs on a synthetic random-walk price
  series (no live market API connected here), fits a naive moving-average
  signal, and labels itself `"experimental": true, "not_investment_advice": true`
  in every response. A good-looking backtest on fake data isn't evidence
  of anything — that's the point being demonstrated, not a real prediction.
- **Spending Q&A assistant** — rule-based pattern matching over the
  user's own uploaded transactions only (biggest category, total spend,
  spend in a named category). No external LLM call in this scaffold, no
  market or allocation opinions — it literally cannot answer anything
  outside the user's own CSV data.

## Running it

### Backend + database
```bash
docker compose up -d postgres redis
cd backend
pip install -r requirements.txt
export DATABASE_URL=postgresql://postgres:postgres@localhost:5432/fintech
uvicorn app.main:app --reload
```
API docs at http://localhost:8000/docs

### Frontend
```bash
cd frontend
npm install
npm run dev
```
Runs at http://localhost:5173

### Try it
1. Sign up / log in.
2. Upload a CSV with `date, description, amount` columns.
3. See it land on the dashboard, categorized automatically.

## What's deliberately NOT here
- Peer benchmarking — needs a real user base to mean anything, so it's
  held per the roadmap until there's one (Section 6's decision point)
- Real bank/stock/crypto linking — the sandbox stub shows the shape;
  actual Mono/Okra integration needs credentials and NDPR compliance
  work that's explicitly out of scope for a solo scaffold
- Any allocation/buy/sell language anywhere, including in Phase 5 —
  hard rule across every phase per the roadmap's risk section

The categorizer in `parser.py` is still keyword rules, not a trained model —
that upgrade path is open but wasn't the priority for Phase 3; the forecast,
anomaly, and score endpoints don't depend on it changing.

## Sample CSV for testing
```csv
date,description,amount
2026-09-01,Uber ride to office,-2500
2026-09-02,Salary credit alert,450000
2026-09-03,Netflix subscription,-4400
2026-09-05,Shoprite supermarket,-18500
```
