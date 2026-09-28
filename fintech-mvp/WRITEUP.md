# AI Personal Finance Platform v1 — Final Write-up

**Author:** Fagite Sheriff Ayomide · Computer Science, Elizade University
**Status as of 28 Sep 2026:** deployed and working; evaluation partly complete (see §4 — what is measured and what is not).
**Live:** frontend `ayo-fintech-mvp-frontend.onrender.com` · API `ayo-fintech-mvp-backend.onrender.com`
**Code:** `github.com/fagitesheriff123-droid/fintech-mvp`

> **How to read the numbers in this document.** Every figure is either (a) counted from the code, (b) measured on a
> named dataset with the sample size stated, or (c) marked **NOT MEASURED** with what is needed to measure it.
> Nothing is estimated or rounded in the system's favour. The evaluation data so far is small (one real-format bank
> statement), and that is stated wherever it matters.

---

## 1. What was built

A spending-analytics web app: a user uploads a bank statement (CSV or PDF) and gets categorised transactions, a
next-month spending forecast per category, flagged unusual transactions, a 0–100 financial health score, a
"what if I saved more?" simulator, savings-goal tracking, and a debt-payoff planner (avalanche / snowball).
Every analytic output ships with a plain-language reason — that is the design principle the project is built around.
An opt-in experimental track (sandbox account link, a labelled synthetic market signal, a spending-only Q&A) is
switched on by an environment flag and is clearly labelled as not real.

| Item | Measured value | How measured |
|---|---|---|
| API operations | **20** (auth 3, transactions 3, analytics 3, planning 7, experimental 3, health 1) | FastAPI OpenAPI spec |
| Database tables | **4** (users, transactions, goals, debts) | `models.py` |
| Backend code | **≈1,100 lines** Python across 19 files | `wc -l` |
| Frontend code | **≈680 lines** React across 5 pages + shared UI | `wc -l` |
| Stack | FastAPI 0.115, SQLAlchemy 2, PostgreSQL 16, pandas 2.2, scikit-learn 1.5, pdfplumber 0.11 · React 18, Vite 5, Tailwind 3, Recharts 2 | `requirements.txt`, `package.json` |
| Hosting | Render free tier: Docker web service + static site + Postgres | Render service config |
| Redeploy time (5 deploys measured) | backend 44 s, 75 s, 50 s · frontend 16 s, 17 s | Render deploy timestamps |

**Ingestion.** CSV (`date, description, amount`) and PDF. The PDF parser tries ruled tables first, then a text-line
parser that infers debit vs credit from the running-balance column, then a plain "date description amount" fallback.
It detects day-first vs month-first dates from the whole document, reads cheque tables, and ignores summary boxes and
secondary accounts.

**Analytics** (`services/analytics.py`, `simulator.py`):
- *Forecast* — per category, a straight-line fit through monthly spend totals, extrapolated one month.
- *Anomalies* — scikit-learn `IsolationForest(contamination=0.15)` fitted per category (categories with ≥4 transactions).
- *Health score* — `savings_rate × 100`, minus 5 if more than 6 spend categories, clipped to 0–100.
- *Simulator, goals, debt order* — arithmetic on the user's own average monthly income and spend.

**Offline / low-data mode.** Every successful GET is cached locally and served when the network fails; "Lite mode"
reuses cache for 10 minutes and hides charts; the app shell is a service-worker-cached, installable PWA.

**Security and privacy controls (from code).** JWT auth; bcrypt password hashing; passwords ≥8 characters; signup
rate-limited to 5 per 60 s; 5 MB upload cap; CORS allow-list in production; `GET /transactions/export` and
`DELETE /auth/me` for data portability and deletion (NDPR). See `SECURITY.md` and `NDPR_DATA_HANDLING.md`.

## 2. What is deliberately not built

Live bank / stock / crypto linking, real market prediction, an unscoped LLM advisor, and any buy / sell / allocate
language. These were held back on purpose: personalised investment recommendations are regulated activity (SEC / CBN
territory in Nigeria), and a short-horizon price predictor that backtests well is not evidence it works live. They
remain on the gated Phase 5 track and the app never depends on them.

## 3. Method

Development followed the reshaped six-phase roadmap. Testing was done in three layers: (1) local end-to-end runs of
every user flow against a scratch database; (2) tests on generated inputs (two synthetic PDF statements); (3) — added
late, and it mattered most — a real-format bank statement supplied from outside the project. The evaluation scripts
are in `backend/eval/` so the numbers below can be regenerated (§8).

## 4. Results — what was measured

### 4.1 Statement ingestion (PDF)

Dataset: **one** real-format 6-page US checking statement (Carson Bank sample, 33-day period; 47 listed transactions
plus 8 cheques = 55 rows) and **two** synthetic PDFs I generated. **n = 1 real statement.** No Nigerian bank statement
has been tested yet.

| Check | Result |
|---|---|
| Rows extracted from the real statement | **55** (47 listed transactions + 8 cheques) |
| Closing-balance reconciliation: opening 445.28 + parsed amounts (cheques excluded, as this statement's running-balance column excludes them) | **942.82 — equals the statement's 942.82 exactly** |
| Cheques found / total | **8 of 8, 1,783.32 — equals the printed total exactly** |
| Junk rows from summary boxes, loan section, interest table | **0** |
| Synthetic table-layout PDF | 8 of 8 rows, income and spend correct |
| Synthetic plain-text-layout PDF | 5 of 5 rows correct |

**Caveat:** reconciling to the closing balance shows the net of all rows is right; it does not by itself prove each
row's direction. It is strong evidence, not a per-row audit. Also, the statement's own summary box (10 deposits,
18,041.50) does not agree with its own transaction list (34 deposits, 7,612.77), so the running balance — which does
reconcile — was used as the reference instead.

**The first version failed, and this is the most useful number in the project.** The first PDF parser passed both
synthetic PDFs (13 of 13 rows). On the first real statement it returned **64 rows with 0 income recognised** (every
deposit read as spending), swapped day and month (07/01 read as 7 January), and included junk rows from the summary
boxes. It was rebuilt around the balance column. See §6.

### 4.2 Categoriser (rule-based keyword matching)

On the real statement: **23.6 % of all rows (13 of 55) and 61.9 % of spending rows (13 of 21) fell into "other".**
Eleven of the 13 are a single merchant string ("ACH DEBIT SETTLEMENT") the keyword rules do not know.
**Accuracy against human labels: NOT MEASURED** — this needs a hand-labelled set (target: 100+ transactions).

### 4.3 Anomaly detection

On the real statement: **9 of 55 transactions flagged (16.4 %)**, close to the 15 % `contamination` setting.
That is expected and it is the important point: **the flag rate is set by the parameter, not discovered from the data** —
the model will flag roughly 15 % of any category however normal it is. Also observed: **5 of the 9 flags were deposits**
(income), and the reason text is worded as "unusual … spend", which is wrong for income.
**Precision / recall: NOT MEASURED** — no labelled set of transactions a human considers unusual exists yet.

### 4.4 Forecast accuracy

**MAPE: NOT MEASURED.** The forecast needs history to be tested against, and the only real statement covers 1 month.
The backtest harness needs **≥ 4 months** of data (3 to fit, 1 to test). It was validated instead on known answers:
0.0 % error on a perfectly linear series, and exactly 50.0 % on a hand-computed step case
(history 100, 100, 100 → predicts 100; actual 200). The roadmap target is < 15 %. It reports MAPE, WAPE, and two naive
baselines (last month, historical mean) so any result can be judged against something to beat.

### 4.5 Health score

On the real statement the score was **0/100** (credits 7,612.77 vs debits 8,898.55 including cheques). This statement
looks like a retail-business account ("Deposit = 131" store deposits), not a personal one, so the score is not
meaningful here — a real limitation: the score assumes a personal account and treats **every** incoming amount as income.

### 4.6 Explanations

**6 of 6 core analytic outputs** (forecast, anomalies, health score, simulator, goal projection, debt order) return a
plain-language `reason`. That is coverage, verified in code — **it says nothing about whether the reasons are useful.**
Usefulness: **NOT MEASURED** — needs 3–5 real users shown the outputs and asked whether they would act on them.
`[TO FILL: number of testers, what they said]`

### 4.7 Reliability

One production incident was found from the live logs: two near-simultaneous signups for the same new email both passed
the "email exists?" check, and the second hit the database unique constraint and returned an unhandled HTTP 500
(seen twice, about 1 s apart, consistent with a double-click). Fixed by catching the constraint error and returning a
clean 400, and by disabling the button while a request is in flight. Verified locally with concurrent requests: one 200
and one 400. All other endpoints in the reviewed log window returned 200. Free-tier cold start after ~15 minutes idle is
roughly 30–60 s; the frontend now tells the user the server is waking up.

## 5. What worked

- **Explanation-first design.** Making every output carry a reason forced each module to be explainable rather than a
  black box, and it is uniform across the app.
- **Balance-based sign inference.** Deriving debit vs credit from the running balance is robust to column layout and
  self-checking (the balance must change by exactly the amount), and it reconciled a real statement to the cent.
- **Scope discipline.** Keeping investment advice, live linking and market prediction out of the core avoided the
  regulated area and kept the project finishable.
- **Push-to-deploy.** From `git push` to a live backend took 44–75 s, which made fix-and-verify cycles short.

## 6. What didn't work / what surprised me

1. **Synthetic tests validated my assumptions, not the world.** 13/13 on generated PDFs, then failure on the first real
   one (§4.1). Real data exposed direction, date-order and sectioning errors no self-made test would have.
2. **A one-line bug hidden by the data I had.** The categoriser matched "pos" inside "de*pos*it", so every deposit was
   tagged "transfer". Only visible on real descriptions. Fixed with word-boundary matching.
3. **Dependency drift broke sign-up on day one.** `email-validator` was missing, and `passlib 1.7.4` is incompatible with
   `bcrypt 5.x` (a false "password longer than 72 bytes" error). Both pinned.
4. **The frontend was broken in ways that looked like "plain".** No viewport tag (phones showed a shrunken desktop page)
   and browser-router links that 404 on a static host when refreshed. Switched to hash routing.
5. **The anomaly detector is less meaningful than it looks** (§4.3): its flag rate is a parameter, and it flags income.

**Forecast weaknesses found by reading the code (not yet measured):** the straight-line fit numbers months
0, 1, 2 … and ignores calendar gaps, so a category with spend in January and March is treated as consecutive months;
and a statement that ends mid-month makes its last month look artificially small. Both should lower accuracy; how
much is unknown until §4.4 is run.

## 7. Limitations and threats to validity

- **Sample size:** one real statement. Nothing here generalises to Nigerian banks yet (GTBank, Access, Zenith, UBA, etc.
  each format differently).
- **Author-written tests:** the two synthetic PDFs were produced by me, so they cannot show I am wrong about layouts.
- **Automated test coverage:** the repository contains only the harness self-test (3 checks). The API flow checks
  (sign-up → login → upload → analytics), the 7 offline-cache checks and the 14 page-render checks were run during
  development but are **not committed** as a test suite.
- **No user study:** nobody outside the project has yet judged whether the reasons or scores are useful or trusted.
- **Money is stored as a float** (`Float` columns); fine for analytics, not for a ledger.
- **Free-tier hosting:** cold starts, and no uptime guarantee.

## 8. Reproducing every number

```bash
cd backend
python -m eval.backtest --selftest                       # harness maths: 3/3 checks
python -m eval.statement_report statement.pdf \
       --opening 445.28 --closing 942.82                 # §4.1–4.3, 4.5 (use your statement's own balances)
python -m eval.backtest export.json                      # §4.4 — needs >=4 months; export.json from GET /transactions/export
```

## 9. What's next (in order of value for the evaluation)

1. **Collect ≥ 4 months of real statements** (your own, exported via `/transactions/export`) and run the backtest to
   fill in §4.4 — replaces the biggest unmeasured number.
2. **Get 3–5 Nigerian bank statement PDFs** and tune the parser per bank; report reconciliation for each.
3. **Hand-label ~100 transactions** to measure categoriser accuracy and anomaly precision/recall (§4.2, §4.3).
4. **Fix the known weaknesses:** align monthly series to the calendar (gaps), separate transfers from income, stop
   flagging income as "unusual spending", add a "Fees" category.
5. **Short user test (3–5 people)** on whether the reasons are understandable and actionable (§4.6).
6. **Commit the tests** that currently live only in development scratch space.
7. **Decide the Phase 4 business question** (portfolio piece / free tool / paid product) — it decides whether the gated
   Phase 5 items are worth pursuing or whether this is a legitimate stopping point as a documented, working v1.
