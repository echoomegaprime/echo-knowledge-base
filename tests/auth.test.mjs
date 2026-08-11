import { test } from 'node:test';
import assert from 'node:assert/strict';
import worker from '../src/index.ts';

function makeD1(overrides = {}) {
  const stmt = {
    bind(...args) { stmt._lastBindArgs = args; return stmt; },
    async run() { return { success: true }; },
    async all() { return { results: [] }; },
    async first() { return overrides.first ? overrides.first(stmt._lastBindArgs) : null; },
  };
  return { prepare(sql) { stmt._lastSql = sql; return stmt; } };
}

function makeEnv(overrides = {}) {
  return {
    DB: makeD1(),
    CACHE: { get: async () => null, put: async () => {} },
    ENGINE_RUNTIME: { fetch: async () => new Response(JSON.stringify({ response: 'ok' })) },
    ECHO_API_KEY: 'test-echo-knowledge-base-key-3f8a',
    ...overrides,
  };
}

test('GET / and /health need no auth (unchanged public contract)', async () => {
  const env = makeEnv();
  for (const p of ['/', '/health', '/status']) {
    const res = await worker.fetch(new Request('https://x' + p), env);
    assert.notEqual(res.status, 401);
  }
});

test('GET /articles is public (unchanged -- this is a knowledge-base wiki, public reads are the product)', async () => {
  const env = makeEnv();
  const res = await worker.fetch(new Request('https://x/articles?tenant_id=t1'), env);
  assert.notEqual(res.status, 401);
});

test('a write (POST /articles) with NO key is rejected', async () => {
  const env = makeEnv();
  const res = await worker.fetch(new Request('https://x/articles', {
    method: 'POST',
    body: JSON.stringify({ title: 'x' }),
    headers: { 'Content-Type': 'application/json' },
  }), env);
  assert.equal(res.status, 401);
});

test('a write (POST /articles) with the WRONG key is rejected', async () => {
  const env = makeEnv();
  const res = await worker.fetch(new Request('https://x/articles', {
    method: 'POST',
    body: JSON.stringify({ title: 'x' }),
    headers: { 'Content-Type': 'application/json', 'X-Echo-API-Key': 'wrong-key' },
  }), env);
  assert.equal(res.status, 401);
});

test('POST /articles/:id/feedback stays public (unchanged -- visitor feedback needs no credential)', async () => {
  const env = makeEnv();
  const res = await worker.fetch(new Request('https://x/articles/a1/feedback', {
    method: 'POST',
    body: JSON.stringify({ is_helpful: true }),
    headers: { 'Content-Type': 'application/json' },
  }), env);
  assert.notEqual(res.status, 401);
});

test('key-length side-channel: a same-length wrong key and a different-length wrong key both fail identically', async () => {
  const env = makeEnv();
  for (const key of ['test-echo-knowledge-base-key-XXXX', 'x']) {
    const res = await worker.fetch(new Request('https://x/articles', {
      method: 'POST',
      body: '{}',
      headers: { 'Content-Type': 'application/json', 'X-Echo-API-Key': key },
    }), env);
    assert.equal(res.status, 401);
  }
});

test('GET /articles/:id no longer leaks author_email -- it did via a bare SELECT * while /articles (the list) deliberately excluded it', async () => {
  // SQL-aware mock: the full row (including author_email, a real column)
  // exists at the "table" level, but first() only returns the columns
  // actually named in the SELECT clause -- exactly what real D1 does. This
  // makes the test discriminating against the SQL text itself, not just the
  // application layer (which does no additional filtering -- it returns
  // whatever the query gives it).
  const FULL_ROW = {
    id: 'a1', tenant_id: 't1', title: 'Test', slug: 'test',
    author_name: 'Jane', author_email: 'jane@example.com',
    content: 'body', status: 'published',
  };
  const env = makeEnv({
    DB: {
      prepare(sql) {
        return {
          bind() { return this; },
          async first() {
            if (/SELECT\s+\*/i.test(sql)) return { ...FULL_ROW };
            const fieldsMatch = sql.match(/SELECT\s+([^\n]+?)\s+FROM/i);
            if (!fieldsMatch) return { ...FULL_ROW };
            const fields = fieldsMatch[1].split(',').map(f => f.trim());
            const projected = {};
            for (const f of fields) if (f in FULL_ROW) projected[f] = FULL_ROW[f];
            return projected;
          },
          async run() { return { success: true }; },
        };
      },
    },
  });
  const res = await worker.fetch(new Request('https://x/articles/a1'), env);
  const body = await res.json();
  assert.equal(body.author_email, undefined, 'author_email must not appear in the public article-detail response');
  assert.equal(body.author_name, 'Jane', 'author_name (not sensitive) should still be present');
});
