# Echo Knowledge Base

Multi-tenant knowledge-base / help-center wiki on Cloudflare Workers (Hono, D1 + KV). Categories,
articles with versioning and full-text search, visitor feedback, per-tenant analytics,
AI-assisted article generation/improvement, and Stripe subscription billing across four
tiers.

Not to be confused with the fleet's docs-first **Knowledge Forge** (`echo.knowledge.*` SDK
namespace, `echo-knowledge-forge`/`-scout`/`-tools` services on FORGE) -- that is the internal
doctrine/grounding RAG system CLAUDE.md itself references. This repo is a separate,
customer-facing product; see `.echo/sdk.json` for the full disambiguation.

## Endpoints

Public by design (this is a help-center wiki -- public article reads are the product):
`/`, `/health`, `/status`, every `GET` route (`/articles`, `/articles/:id`, `/categories`,
`/search`, `/analytics/*`), `POST /articles/:id/feedback` (visitor feedback needs no
credential), `/webhooks/stripe` (own signature check), `/plans`.

Authenticated (writes): create/update/delete tenants, categories, articles; publish/unpublish;
AI generation; Stripe checkout.

## Authentication

Every write requires `X-Echo-API-Key`, compared to `env.ECHO_API_KEY` in constant time. See
[SECURITY.md](SECURITY.md) for what changed in this consolidation pass, including a real fix:
`GET /articles/:id` previously leaked `author_email` via an unfiltered `SELECT *`.

## Verify

```powershell
npm install
npm test
```

## Security

See [SECURITY.md](SECURITY.md) to report a vulnerability -- never as a public issue.

## License

See [LICENSE](LICENSE). Contributions: see [CONTRIBUTING.md](CONTRIBUTING.md).
