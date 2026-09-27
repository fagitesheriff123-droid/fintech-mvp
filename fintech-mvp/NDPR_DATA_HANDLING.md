# Data handling notes — NDPR-aware, even at CSV-upload scale

This isn't a compliance certification — it's the honest documentation
the roadmap's Phase 6 calls for: what data this app touches, why, and
what rights a user actually has over it right now.

## What's collected
- **Account:** email, hashed password (bcrypt — the plaintext password
  is never stored)
- **Financial data:** whatever's in an uploaded CSV — date, description,
  amount, and a derived category. No account numbers, no card numbers,
  no BVN/NIN — the app never asks for these and has nowhere to put them
  if it received them
- **Planning data:** goal names/amounts/dates and debt names/balances/rates
  that the user types in directly

## Why each piece is collected
Every field above exists because a specific feature needs it (auth needs
email+password; forecasting needs date/amount/category; the debt helper
needs balance/rate). Nothing is collected "in case it's useful later."

## User rights implemented in this scaffold
- **Right to erasure:** `DELETE /auth/me` — deletes the account and every
  transaction, goal, and debt tied to it. Not a soft-delete; the rows are gone.
- **Right to data portability:** `GET /transactions/export` — returns
  everything the account holds as JSON.
- **Right to access:** the dashboard itself is the access mechanism — a
  user can already see everything stored about them.

## What's not yet handled (be honest about this before real users)
- **Retention policy.** There's currently no automatic deletion of stale
  data — an uploaded statement sits in Postgres indefinitely until the
  user deletes their account. A real policy needs a stated retention
  period, not just "user deletes it manually."
- **Consent language.** There's no explicit consent screen on signup
  explaining what's collected and why. Needed before this has real users,
  not needed for a portfolio demo.
- **Data processing agreement / sub-processor list.** If this ever moves
  to a paid product on managed infra (Render, a managed Postgres, etc.),
  those providers are sub-processors and belong in a privacy policy.
- **Breach notification process.** None exists. Not needed until there's
  real user data to breach, but worth having a plan before that's true.

## Encryption
- Passwords: bcrypt-hashed, never stored or logged in plaintext.
- Data in transit: HTTPS is assumed at the hosting/reverse-proxy layer —
  not something the app code enforces itself.
- Data at rest: not configured in this scaffold — it's a database/infra
  setting, and needs to be turned on wherever this is actually deployed
  (e.g. Postgres with encrypted storage on the hosting provider).

## Bottom line
For a portfolio piece or a free tool with a few real users, this is a
reasonable starting posture: real deletion, real export, no data
collected beyond what features need. For a paid product handling real
Nigerian users' financial statements, the retention policy and consent
language above are not optional — they're the next thing to build,
per the roadmap's Section 6 decision point.
