import assert from 'node:assert/strict';
import { readFile } from 'node:fs/promises';
import test from 'node:test';
import ts from 'typescript';

const source = await readFile(new URL('../src/lib/logoutSession.ts', import.meta.url), 'utf8');
const { outputText } = ts.transpileModule(source, { compilerOptions: { module: ts.ModuleKind.ESNext, target: ts.ScriptTarget.ES2020 } });
const { logoutSession } = await import(`data:text/javascript;base64,${Buffer.from(outputText).toString('base64')}`);

test('cookie logout contacts server even before a JS identity is available', async () => {
  const calls = [];
  const outcome = await logoutSession({ cookieMode: true, identity: null,
    revoke: async identity => { calls.push(identity); }, isCurrent: () => true });
  assert.equal(outcome, 'clear');
  assert.deepEqual(calls, [null]);
});

test('cookie logout failure retains UI and offers retry', async () => {
  assert.equal(await logoutSession({ cookieMode: true, identity: 'fixture-version',
    revoke: async () => { throw new Error('Fixture offline'); }, isCurrent: () => true }), 'failed');
});

test('legacy logout still clears offline and skips requests for guests', async () => {
  assert.equal(await logoutSession({ cookieMode: false, identity: 'fixture-identity',
    revoke: async () => { throw new Error('Fixture offline'); }, isCurrent: () => true }), 'clear');
  assert.equal(await logoutSession({ cookieMode: false, identity: null,
    revoke: async () => { assert.fail('Guest should not revoke'); }, isCurrent: () => true }), 'clear');
});

test('stale logout handler cannot send a request for a newer session', async () => {
  assert.equal(await logoutSession({ cookieMode: true, identity: 'old-version',
    revoke: async () => { assert.fail('Stale handler should not revoke'); }, isCurrent: () => false }), 'stale');
});

for (const cookieMode of [false, true]) {
  for (const fails of [false, true]) {
    test(`${cookieMode ? 'cookie' : 'legacy'} delayed logout ${fails ? 'failure' : 'success'} cannot clear newer auth`, async () => {
      let current = true;
      let finish;
      const pending = logoutSession({ cookieMode, identity: 'old-version',
        revoke: () => new Promise((resolve, reject) => {
          finish = () => fails ? reject(new Error('Fixture failure')) : resolve();
        }), isCurrent: () => current });
      current = false;
      finish();
      assert.equal(await pending, 'stale');
    });
  }
}
