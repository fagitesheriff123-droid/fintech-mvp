# Security pass — Phase 6

Findings from reviewing the Phase 1–5 scaffold, and what was actually
fixed vs. what's flagged for before this touches real user data.

## Fixed in this pass
| Issue | Fix |
|---|---|
| `SECRET_KEY` silently defaulted to a hardcoded string in any environment | Now required via env var outside `ENV=development`; the app refuses to start without it in prod |
| CORS allowed every origin (`*`) unconditionally | Now reads `ALLOWED_ORIGINS` (comma-separated) in non-dev; wildcard only in local dev |
| No rate limiting on `/auth/login` or `/auth/signup` | Added a minimal in-memory limiter (`app/rate_limit.py`) — 10 login attempts / 5 signups per minute per IP |
| No password strength check | Minimum 8 characters enforced on signup |
| No upload size limit | CSV uploads capped at 5MB |
| No account deletion path | `DELETE /auth/me` removes the user and all their transactions/goals/debts (NDPR right to erasure) |
| No data export path | `GET /transactions/export` returns everything the account holds as JSON (NDPR data portability) |

## Known limitations — flag before real users touch this
- **JWTs aren't revocable.** A stolen token is valid until it expires (24h).
  Fine for a demo; a real deployment needs a token blocklist or short-lived
  access tokens + refresh tokens.
- **Rate limiter is in-memory, per-process.** Works for one worker. Move to
  Redis-backed limiting (Redis is already in docker-compose) before running
  more than one backend instance, or the limit resets per process.
- **No encryption-at-rest configuration shown here.** That's a database/infra
  setting (e.g. Postgres with encrypted storage), not application code —
  needs to be set up wherever this actually gets deployed.
- **No audit log.** There's no record of who accessed what when. Not needed
  for a portfolio piece; needed before "paid product" per the roadmap's
  Section 6 decision.
- **CORS `ALLOWED_ORIGINS` and `SECRET_KEY` still need to actually be set**
  in whatever hosting environment is used — this pass makes the app refuse
  to run insecurely by accident, it doesn't configure production for you.
- **File type check is by extension only** (`.csv`). Not a real content-type
  or malware scan. Low risk for a CSV-only upload, but worth knowing.

## Deliberately out of scope for a solo/portfolio project
- Penetration testing, dependency vulnerability scanning (could add
  `pip-audit` / `npm audit` to CI cheaply if this becomes more than a
  scaffold)
- Multi-factor auth
- Formal threat model
