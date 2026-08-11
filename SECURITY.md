# Security policy

Echo Knowledge Base is a multi-tenant Cloudflare Worker (Hono, D1 + KV) serving a public
help-center wiki plus a tenant-authenticated management API and Stripe billing.

## Fixed in this consolidation pass

1. **`GET /articles/:id` leaked `author_email` via an unfiltered `SELECT *`.** The sibling
   `GET /articles` (list) endpoint already deliberately hand-picks a safe field list that
   excludes `author_email` -- an internal contact address column with no reason to be public.
   The single-article endpoint used `SELECT * FROM articles WHERE id=?` instead, returning
   every column. Because every GET route on this Worker is intentionally unauthenticated (see
   below), this meant `author_email` was world-readable for any published article. Replaced
   with the same safe field list the list endpoint already uses, plus the full body fields
   (`content`, `meta_title`, `meta_description`) a detail view legitimately needs. The
   inconsistency between the two endpoints -- one careful, one not -- is what made this
   identifiable as a real oversight rather than an intentional design choice.
2. **Timing side-channel in the credential check.** The API key comparison used a raw `!==`.
   Replaced with a constant-time `timingSafeEqual`. (The existing Stripe webhook signature
   check, `verifyStripeSignature`, was already constant-time and left unchanged.)

## Known design choice, not changed in this pass

**Every GET route is intentionally unauthenticated.** Unlike the `author_email` leak above,
this is not a bug: a knowledge-base/help-center wiki's entire purpose is public article reads
-- that is the product. `/articles`, `/categories`, `/search`, and (after the fix above)
`/articles/:id` returning only non-sensitive fields is the expected, intended behavior for
this kind of service, not scope creep. `/analytics/overview` and `/analytics/popular` expose
only aggregate view/helpfulness counts, not customer data.

## Known, not fixed: npm audit findings are all dev-tooling transitives

`npm audit` reports 8 vulnerabilities (undici, ws) via `wrangler`/`miniflare`'s dependency
tree -- local dev-server/build tooling, never shipped in the deployed Worker bundle. Same
disposition as the identical finding on `echo-compliance-auditor`, `echo-lms`, and
`echo-document-manager` earlier in this consolidation campaign.

## Supported version

Security fixes target the current `main` branch. Historical commits are retained for evidence
and are not patched in place.

## Report a vulnerability

Do not open a public issue for a suspected vulnerability. Send a private report to
`security@echo-op.com` with:

- affected endpoint and exact revision;
- reproduction steps and expected impact;
- safe contact details for follow-up.

Never include a live `ECHO_API_KEY`, `STRIPE_SECRET_KEY`, or `STRIPE_WEBHOOK_SECRET` in a
report.
