import assert from 'node:assert/strict';
import { readFile } from 'node:fs/promises';
import test from 'node:test';
import ts from 'typescript';

const source = await readFile(new URL('../src/lib/messageThread.ts', import.meta.url), 'utf8');
const { outputText } = ts.transpileModule(source, { compilerOptions: { module: ts.ModuleKind.ESNext, target: ts.ScriptTarget.ES2020 } });
const { messagesForConversation } = await import(`data:text/javascript;base64,${Buffer.from(outputText).toString('base64')}`);

test('initial and unselected conversations have no loaded thread', () => {
  assert.equal(messagesForConversation(null, 1), null);
  assert.equal(messagesForConversation({ conversationId: 1, messages: [] }, null), null);
});
test('previous recipient messages stay hidden after switching conversations', () => {
  const thread = { conversationId: 1, messages: [{ id: 9, content: 'Thread one' }] };
  assert.equal(messagesForConversation(thread, 2), null);
  assert.deepEqual(messagesForConversation(thread, 1), thread.messages);
});
test('loaded empty conversation differs from a still-loading conversation', () => {
  assert.deepEqual(messagesForConversation({ conversationId: 2, messages: [] }, 2), []);
  assert.equal(messagesForConversation({ conversationId: 1, messages: [] }, 2), null);
});
