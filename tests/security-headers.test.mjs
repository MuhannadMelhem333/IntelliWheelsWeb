import assert from 'node:assert/strict';
import { readFile } from 'node:fs/promises';
import test from 'node:test';
import ts from 'typescript';

const source = await readFile(new URL('../next.config.ts', import.meta.url), 'utf8');
const passthrough = 'data:text/javascript,export const withSentryConfig = config => config;';
for (const environment of ['development', 'production']) {
  test(`Next.js ${environment} security headers preserve runtime compatibility`, async () => {
    const { outputText } = ts.transpileModule(source, {
      compilerOptions: { module: ts.ModuleKind.ESNext, target: ts.ScriptTarget.ES2020 },
    });
    const code = outputText.replaceAll("'@sentry/nextjs'", JSON.stringify(passthrough))
      .replaceAll('process.env.NODE_ENV', JSON.stringify(environment));
    const { default: config } = await import(`data:text/javascript;base64,${Buffer.from(code).toString('base64')}`);
    const rules = await config.headers();
    const headers = Object.fromEntries(rules.find(rule => rule.source === '/:path*').headers.map(({ key, value }) => [key, value]));
    assert.equal(headers['Content-Security-Policy'], "base-uri 'self'; object-src 'none'; frame-ancestors 'self'");
    assert.equal(headers['X-Frame-Options'], 'SAMEORIGIN');
    assert.equal(headers['X-Content-Type-Options'], 'nosniff');
    assert.equal(headers['Referrer-Policy'], 'strict-origin-when-cross-origin');
    assert.equal(headers['Permissions-Policy'], 'camera=(), microphone=(), geolocation=()');
    assert.equal(headers['Strict-Transport-Security'], environment === 'production' ? 'max-age=31536000' : undefined);
    assert.ok(rules.every(rule => rule.headers.every(header => header.key !== 'Cache-Control')));
  });
}
