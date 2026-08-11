# Changelog

## Unreleased -- consolidation pass (2026-08-11)

### Fixed
- `GET /articles/:id` leaked `author_email` via `SELECT *` -- the sibling list endpoint
  already excluded it deliberately. Replaced with the same safe field list.
- Constant-time `timingSafeEqual` for the `X-Echo-API-Key` comparison (was raw `!==`).

### Added
- `tests/auth.test.mjs` -- 7 tests, including an SQL-aware D1 mock that proves the
  `author_email` fix at the query level (not just an application-layer assumption), the
  write-auth gate, the intentionally-public read/feedback routes, and a same-length-vs-
  different-length wrong-key timing-shape check.
- Full governance set (README, SECURITY, CONTRIBUTING, CODE_OF_CONDUCT, LICENSE, CI).

### Documented, not changed
- Every GET route is intentionally unauthenticated -- correct for a public help-center wiki,
  not a bug. `npm audit`'s 8 findings are all `wrangler`/`miniflare` dev-tooling transitives,
  never shipped in the deployed bundle. See SECURITY.md.

## 2.0.0 -- original release

Multi-tenant knowledge-base wiki: categories, articles with versioning and full-text search,
visitor feedback, per-tenant analytics, AI-assisted article generation/improvement, Stripe
subscription billing.
