import assert from 'node:assert/strict';
import { readFile } from 'node:fs/promises';
import test from 'node:test';
import ts from 'typescript';

const source = await readFile(new URL('../src/lib/sessionEvents.ts', import.meta.url), 'utf8');
const { outputText } = ts.transpileModule(source, { compilerOptions: { module: ts.ModuleKind.ESNext, target: ts.ScriptTarget.ES2020 } });
const { shouldInvalidateSession, notifySessionRejected, subscribeToSessionRejection } = await import(`data:text/javascript;base64,${Buffer.from(outputText).toString('base64')}`);

test('only a rejection of the current nonempty session invalidates it', () => {
  assert.equal(shouldInvalidateSession('fixture-current', 'fixture-current'), true);
  assert.equal(shouldInvalidateSession('fixture-new', 'fixture-old'), false);
  assert.equal(shouldInvalidateSession(null, 'fixture-old'), false);
  assert.equal(shouldInvalidateSession('fixture-current', null), false);
  assert.equal(shouldInvalidateSession('', ''), false);
});

test('server notification is a safe no-op', () => {
  assert.doesNotThrow(() => notifySessionRejected('fixture-server'));
});

test('browser rejection notification delivers once and unsubscribes cleanly', () => {
  const previous = globalThis.window;
  globalThis.window = new EventTarget();
  try {
    const received = [];
    const unsubscribe = subscribeToSessionRejection((token) => received.push(token));
    notifySessionRejected(null);
    notifySessionRejected('fixture-session');
    assert.deepEqual(received, ['fixture-session']);
    unsubscribe();
    notifySessionRejected('fixture-session');
    assert.equal(received.length, 1);
  } finally {
    if (previous === undefined) delete globalThis.window;
    else globalThis.window = previous;
  }
});
