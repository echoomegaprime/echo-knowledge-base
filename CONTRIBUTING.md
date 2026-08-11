# Contributing

Thank you for improving Echo Knowledge Base. This is a public, proprietary infrastructure
project: contributions are welcome for review, but repository visibility does not grant a
general use or redistribution license.

## Development path

1. Open an issue describing the behavior being changed.
2. Create a focused branch from current `main`.
3. Add a failing test before changing `timingSafeEqual`, the auth exemption list, or the
   `ARTICLE_DETAIL_FIELDS` column list -- see SECURITY.md for exactly what's public by design
   (article reads) versus what was a real leak (`author_email`).
4. Validate before opening a pull request:

   ```powershell
   npm install
   npm test
   ```

5. Open a pull request using the repository template and include exact test output.

## Pull-request requirements

- No secrets (`ECHO_API_KEY`, `STRIPE_SECRET_KEY`, `STRIPE_WEBHOOK_SECRET`) are included.
- No stubs, placeholders, or self-asserted readiness.
- **Any change to `ARTICLE_DETAIL_FIELDS` (or a reversion to `SELECT *` anywhere in the public
  read path) must be called out explicitly in the pull request description** -- this is
  exactly the class of change that introduced the `author_email` leak fixed in this
  consolidation pass.
