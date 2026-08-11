# ECHO Repository Health Receipt

Source repository: `echoomegaprime/echo-knowledge-base`

Source commit: `6eb535269dacfea1807c8706a5456e48f1451267`

Filed manually (2026-08-11): the same shared-framework App bug affecting other repos this
campaign (build #29466) also hit this repo's push webhook -- no check-run or PR appeared after
push (`gh api .../check-runs` returns 0). Cert Forge certification was obtained directly
against the live `cert-api.echosforge.com` API, run
`cert_00a3f8a282f8adfdbd54fa93647fdbd07649c3a4`, **PRODUCTION_READY on the first submission**,
confirmed via the signed ed25519 verdict payload (`reasons: ["all_mandatory_rules_verified"]`).
Submitted via a fallback path this run: `echo.shell.run` was unexpectedly absent from the
live SDK-gate namespace registry (confirmed via `echo_search_caps`, `echo_describe_cap`, and a
full `echo_list_namespaces` dump -- not the usual per-cap resolution flakiness tracked as
#29473) and `mcp__echo-cluster-ops__shell_run` still has its known unfixed HMAC/`fromhex` crash
-- both FORGE-shell paths were down simultaneously. Fell back to the documented direct
HAMMER-to-FORGE SSH bridge (`C:\Users\bobmc\forge_run.cmd`), transferring Python scripts via
base64 to avoid quote-nesting through cmd.exe -> ssh -> bash. Filed #29617 to track the
`echo.shell.run` regression. This receipt reproduces the identical showroom-floor audit the
App would post, verified by direct `git ls-tree` on the exact commit plus a secret-literal
scan of `src/`, `scripts/`, `tests/`.

## Showroom floor audit

- [x] `README.md`
- [x] `LICENSE`
- [x] `SECURITY.md`
- [x] `CONTRIBUTING.md`
- [x] `CODE_OF_CONDUCT.md`
- [x] `.gitignore`
- [x] `.github/workflows`

Result: **7/7 present**.

## Secret-literal scan

`grep -rniE "(api[_-]?key|secret|password|token)\s*[:=]\s*[\"'][a-zA-Z0-9_\-]{16,}[\"']"` across
`src/ scripts/ tests/`: one match, `tests/auth.test.mjs`'s
`ECHO_API_KEY: 'test-echo-knowledge-base-key-3f8a'` -- a test fixture placeholder, not a live
credential.
