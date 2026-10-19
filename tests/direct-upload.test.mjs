import assert from 'node:assert/strict';
import { readFile } from 'node:fs/promises';
import test from 'node:test';
import ts from 'typescript';

const source = await readFile(new URL('../src/lib/directUpload.ts', import.meta.url), 'utf8');
const code = ts.transpileModule(source, { compilerOptions: { module: ts.ModuleKind.ESNext, target: ts.ScriptTarget.ES2020 } }).outputText;
const { tryDirectUpload } = await import(`data:text/javascript;base64,${Buffer.from(code).toString('base64')}`);
const file = () => new File(['bytes'], 'car.png', { type: 'image/png' });
const prepared = { mode: 'direct', intentId: 'fixture', uploadUrl: 'https://api.cloudinary.com/v1_1/fixture/image/upload', parameters: { timestamp: 1, signature: 'fixture' } };
const result = { success: true, url: 'https://res.cloudinary.com/fixture/verified.png', assetId: 'fixture' };
const unexpected = () => { throw new Error('Unexpected call'); };

test('explicit proxy choice preserves the existing upload path', async () => {
  assert.equal(await tryDirectUpload(file(), 'image', 'owner', async () => ({ mode: 'proxy' }), unexpected, unexpected), null);
});
test('prepare failure never silently downgrades to proxy', async () => {
  await assert.rejects(tryDirectUpload(file(), 'image', 'owner', async () => { throw new Error('quota'); }, unexpected, unexpected), /quota/);
});
test('direct bytes omit credentials; only server completion metadata is returned', async () => {
  const response = await tryDirectUpload(file(), 'image', 'owner', async () => prepared, async (id) => {
    assert.equal(id, 'fixture'); return result;
  }, async (url, options) => {
    assert.equal(url, prepared.uploadUrl);
    assert.equal(options.credentials, 'omit');
    assert.equal(options.redirect, 'error');
    assert.equal(options.headers, undefined);
    assert.equal(options.body.get('signature'), 'fixture');
    assert.ok(options.body.get('file') instanceof File);
    return new Response('untrusted provider response');
  });
  assert.deepEqual(response, result);
});
test('ambiguous provider failure retries completion without re-upload or new reservation', async () => {
  const input = file(); let sends = 0; let completions = 0;
  const complete = async () => { if (++completions === 1) throw new Error('pending'); return result; };
  await assert.rejects(tryDirectUpload(input, 'image', 'owner', async () => prepared, complete, async () => { sends++; throw new Error('lost response'); }), /pending/);
  assert.deepEqual(await tryDirectUpload(input, 'image', 'owner', unexpected, complete, unexpected), result);
  assert.equal(sends, 1);
});
test('stable prepare key is scoped to the current session', async () => {
  const input = file(); const keys = [];
  const prepare = async (key) => { keys.push(key); return { mode: 'proxy' }; };
  for (const scope of ['one', 'one', 'two']) await tryDirectUpload(input, 'image', scope, prepare, unexpected, unexpected);
  assert.equal(keys[0], keys[1]); assert.notEqual(keys[1], keys[2]);
});
test('invalid provider destinations cannot receive signed parameters or bytes', async () => {
  for (const uploadUrl of ['https://evil.test/upload', 'https://api.cloudinary.com/v1_1/fixture/raw/upload', prepared.uploadUrl + '?leak=true']) {
    await assert.rejects(tryDirectUpload(file(), 'image', 'owner', async () => ({ ...prepared, uploadUrl }), unexpected, unexpected), /Unexpected upload destination/);
  }
});
test('already completed preparation skips provider upload', async () => {
  assert.deepEqual(await tryDirectUpload(file(), 'image', 'owner', async () => ({ mode: 'complete', intentId: 'fixture' }), async () => result, unexpected), result);
});
