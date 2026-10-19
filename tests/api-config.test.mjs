import assert from 'node:assert/strict';
import { readFile } from 'node:fs/promises';
import test from 'node:test';
import ts from 'typescript';
const source = await readFile(new URL('../src/lib/config.ts', import.meta.url), 'utf8');
async function configured(env) {
  const code = ts.transpileModule(source, { compilerOptions: { module: ts.ModuleKind.ESNext, target: ts.ScriptTarget.ES2020 } }).outputText
    .replace(/process\.env\.([A-Z_]+)/g, (_, key) => JSON.stringify(env[key]) ?? 'undefined');
  return (await import(`data:text/javascript;base64,${Buffer.from(code).toString('base64')}`)).API_BASE_URL;
}
test('documented CI/public API variable works without falling back to localhost', async () => {
  assert.equal(await configured({ NEXT_PUBLIC_API_URL: 'https://api.example.com/' }), 'https://api.example.com/api');
});
test('existing primary variable retains priority and API suffix is not doubled', async () => {
  assert.equal(await configured({ NEXT_PUBLIC_API_BASE_URL: 'https://primary.example.com/api/', NEXT_PUBLIC_API_URL: 'https://secondary.example.com' }), 'https://primary.example.com/api');
});
test('legacy aliases and local default remain compatible', async () => {
  for (const key of ['NEXT_PUBLIC_API_BASE', 'NEXT_PUBLIC_BACKEND_URL', 'API_BASE_URL', 'API_BASE', 'BACKEND_URL']) {
    assert.equal(await configured({ [key]: 'https://api.example.com' }), 'https://api.example.com/api');
  }
  assert.equal(await configured({}), 'http://localhost:5000/api');
});
