r"""Critical journey for the ECHO Certification Forge.

The Forge runs this argv (declared as a top-level `journey` field in the
POST /v1/certifications request body -- NOT read from .echo/certification.json;
see [[reference-certification-forge-submit-recipe-20260810]] gotcha #8) inside
its isolated `python:3.12-alpine` sandbox, against the exact acquired commit,
with no network and no Node -- so the Worker itself cannot actually run, and
there is no `git` binary either (gotcha #9 of the same recipe). The full
behavioural suite (`npm test` -- typecheck plus the real auth/leak test
suite, run against the actual `src/index.ts` via Node's native TypeScript
support) runs in CI on this same commit; this journey proves the artifact
the Forge actually acquired is the intact, complete Worker source -- not
that it currently boots.

This repository is TypeScript-only (a single Cloudflare Worker, Hono + D1 +
KV, no other framework); this journey therefore checks structural and
textual invariants rather than parsing Python.

Checks:
  1. The critical surfaces exist -- the Worker entrypoint, its test file, and
     the pinned Node dependency manifest.
  2. `src/index.ts` has not been truncated -- a cheap, tokenizer-free line
     and byte-size floor.
  3. No install-lifecycle scripts have crept into `package.json`.
  4. No hardcoded secret-shaped literals in the acquired source.
  5. The auth check still calls the constant-time `timingSafeEqual` rather
     than a raw `!==` -- functional tests can't distinguish a timing-safe
     comparison from a raw one (both return the same true/false), so this
     text-pattern check is the ONLY regression guard for that fix.
  6. `GET /articles/:id` still uses the explicit `ARTICLE_DETAIL_FIELDS`
     column list rather than `SELECT *` -- the repo as found leaked
     `author_email` (an internal contact address) on every public article
     read via an unfiltered `SELECT *`, while the sibling list endpoint
     deliberately excluded it.
"""

from __future__ import annotations

import json
import pathlib
import re
import sys
from typing import NoReturn

CRITICAL_SURFACES = (
    "src/index.ts",
    "tests/auth.test.mjs",
    "package.json",
    "tsconfig.json",
)

INSTALL_LIFECYCLE_HOOKS = ("preinstall", "install", "postinstall", "prepare")

SECRET_LITERAL_PATTERN = re.compile(
    r'(?:api_key|secret|password|token)\s*=\s*["\'][a-zA-Z0-9_\-]{16,}["\']',
    re.IGNORECASE,
)

MIN_INDEX_TS_LINES = 400
MIN_INDEX_TS_BYTES = 14_000


def _fail(message: str) -> NoReturn:
    print(f"ECHO_KNOWLEDGE_BASE_CRITICAL_JOURNEY_FAILED: {message}", file=sys.stderr)
    raise SystemExit(1)


def check_critical_surfaces() -> None:
    for surface in CRITICAL_SURFACES:
        if not pathlib.Path(surface).exists():
            _fail(f"missing critical surface: {surface}")


def _source_text() -> str:
    return pathlib.Path("src/index.ts").read_text(encoding="utf-8")


def check_index_ts_not_truncated() -> None:
    text = _source_text()
    line_count = text.count("\n") + 1
    byte_size = len(text.encode("utf-8"))
    if line_count < MIN_INDEX_TS_LINES:
        _fail(f"src/index.ts has only {line_count} lines (expected >= {MIN_INDEX_TS_LINES}) -- possible truncation")
    if byte_size < MIN_INDEX_TS_BYTES:
        _fail(f"src/index.ts is only {byte_size} bytes (expected >= {MIN_INDEX_TS_BYTES}) -- possible truncation")
    if "export default" not in text:
        _fail("src/index.ts is missing its 'export default' Worker entrypoint")


def check_no_install_hooks() -> None:
    manifest = pathlib.Path("package.json")
    try:
        scripts = json.loads(manifest.read_text(encoding="utf-8")).get("scripts", {})
    except (json.JSONDecodeError, UnicodeDecodeError) as exc:
        _fail(f"package.json is not valid JSON: {exc}")
    present = sorted(hook for hook in INSTALL_LIFECYCLE_HOOKS if hook in scripts)
    if present:
        _fail(f"package.json reintroduced install-lifecycle script(s): {', '.join(present)}")


def check_no_hardcoded_secrets() -> None:
    match = SECRET_LITERAL_PATTERN.search(_source_text())
    if match:
        _fail(f"src/index.ts contains a hardcoded secret-shaped literal: {match.group(0)[:40]}...")


def check_constant_time_auth() -> None:
    text = _source_text()
    if "timingSafeEqual(key, c.env.ECHO_API_KEY)" not in text:
        _fail("the auth check no longer calls timingSafeEqual on the API key comparison")
    if re.search(r"key\s*!==\s*c\.env\.ECHO_API_KEY", text):
        _fail("the auth check regressed to a raw !== comparison")


def check_article_detail_no_select_star() -> None:
    text = _source_text()
    if "const ARTICLE_DETAIL_FIELDS" not in text:
        _fail("ARTICLE_DETAIL_FIELDS is missing entirely")
    if "author_email" in text.split("const ARTICLE_DETAIL_FIELDS", 1)[1].split(";", 1)[0]:
        _fail("ARTICLE_DETAIL_FIELDS reintroduced author_email")
    # The two GET /articles/:id queries (by-id, by-slug) must both use the
    # explicit field list, not SELECT * -- that's exactly how the leak
    # happened originally.
    detail_section = text.split("app.get('/articles/:id'", 1)
    if len(detail_section) != 2:
        _fail("GET /articles/:id route is missing")
    body = detail_section[1].split("app.post('/articles'", 1)[0]
    if re.search(r"SELECT\s+\*\s+FROM\s+articles", body, re.IGNORECASE):
        _fail(
            "GET /articles/:id uses SELECT * again -- this reintroduces the original "
            "author_email leak (the sibling list endpoint deliberately excludes it)"
        )
    if body.count("ARTICLE_DETAIL_FIELDS") < 2:
        _fail("GET /articles/:id no longer uses ARTICLE_DETAIL_FIELDS for both the id and slug lookups")


def main() -> None:
    check_critical_surfaces()
    check_index_ts_not_truncated()
    check_no_install_hooks()
    check_no_hardcoded_secrets()
    check_constant_time_auth()
    check_article_detail_no_select_star()
    print(
        "ECHO_KNOWLEDGE_BASE_CRITICAL_JOURNEY_OK "
        "critical_surfaces=4 install_hooks=0 hardcoded_secrets=0 "
        "constant_time_auth=1 article_detail_field_list_intact=1"
    )


if __name__ == "__main__":
    main()
