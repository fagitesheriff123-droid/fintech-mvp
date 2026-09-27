# Final write-up — AI Personal Finance Platform v1

This is a template with the parts I can honestly fill in already done,
and the parts that need real usage data left as placeholders — filling
those in with invented numbers would defeat the point of Section 7's
"honest accuracy numbers" requirement.

## What was built
A CSV-upload spending analytics tool: auth, statement ingestion with
rule-based categorization, per-category forecasting (linear trend on
monthly totals), anomaly detection (IsolationForest per category), a
composite financial health score, a scenario simulator, goal-based
savings tracking, a debt payoff helper (avalanche/snowball), and an
opt-in experimental track (sandbox account linking, a labeled synthetic
market signal, a spending-scoped Q&A assistant) — all through Phases 1–5
of the reshaped roadmap.

## What's deliberately not built
Live bank/stock/crypto linking, real market prediction, an unscoped LLM
advisor, and any allocation/buy/sell language — all held back per the
roadmap's hard rule to stay out of regulated investment-advice territory,
and because Phase 5 gates them behind a real decision about whether this
is a portfolio piece, a free tool, or a paid product.

## Honest accuracy numbers — fill in after real runs
- **Forecast MAPE** (target <15% per roadmap Section 7):
  `___%` — run `/analytics/forecast` against a few months of real or
  realistic statement data and compare predicted vs. actual next-month
  spend per category to get this number. It won't be meaningful with
  under ~3 months of history — say so if that's the case.
- **Anomaly detection precision/recall:** `___` — needs a labeled set
  (transactions a human agrees are actually unusual) to score against.
  Without that, the honest statement is "flags transactions >~1.5
  standard deviations from category mean; not yet validated against
  human judgment."
- **Explanation quality:** `___` — this is qualitative. The honest way
  to answer it: show the forecast/anomaly/health-score reasons to a few
  real users and ask if they'd act on what the app told them.

## What worked
`[Fill in after actually running it — e.g. which module felt solid,
what was easy to demo, what users understood immediately]`

## What didn't / what surprised you
`[Fill in — e.g. where the linear-trend forecast broke down, whether
the rule-based categorizer missed obvious categories, whether the
health score felt meaningful with thin data]`

## What's next
Per the roadmap: the Phase 4 business-model decision (portfolio piece /
free tool / paid product) determines whether Phase 5's gated items are
worth pursuing for real, or whether this is a legitimate stopping point
as a documented, working v1.
