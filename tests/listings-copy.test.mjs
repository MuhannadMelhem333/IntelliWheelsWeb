import assert from 'node:assert/strict';
import { readFile } from 'node:fs/promises';
import test from 'node:test';
import ts from 'typescript';

const source = await readFile(new URL('../src/lib/listingsCopy.ts', import.meta.url), 'utf8');
const { outputText } = ts.transpileModule(source, { compilerOptions: { module: ts.ModuleKind.ESNext, target: ts.ScriptTarget.ES2020 } });
const { listingsCopy } = await import(`data:text/javascript;base64,${Buffer.from(outputText).toString('base64')}`);

test('English and Arabic provide the same complete set of labels', () => {
  assert.deepEqual(Object.keys(listingsCopy.ar).sort(), Object.keys(listingsCopy.en).sort());
  for (const [key, value] of Object.entries(listingsCopy.ar)) {
    assert.match(value, /[\u0600-\u06ff]/u, key);
    assert.ok(listingsCopy.en[key].trim(), key);
  }
});

test('loading, error, retry, empty and pagination states are translated', () => {
  for (const key of ['Loading listings…', 'Unable to load listings', 'Try again', 'No listings match your filters.', 'Previous', 'Next', 'Page', 'of']) {
    assert.equal(typeof listingsCopy.en[key], 'string');
    assert.notEqual(listingsCopy.ar[key], listingsCopy.en[key]);
  }
});

test('localizing options preserves API and URL option values (static contract)', async () => {
  const view = await readFile(new URL('../src/components/listings/PublicListingsView.tsx', import.meta.url), 'utf8');
  const values = [...view.matchAll(/<option value="([^"]*)"/g)].map((match) => match[1]);
  assert.deepEqual(values, ['all', 'all', 'car', 'suv', 'truck', 'bike', 'van', 'bus', 'other', '', 'new', 'used', 'certified', '', 'automatic', 'manual', 'cvt', 'other', '', 'petrol', 'diesel', 'electric', 'hybrid', 'plugin_hybrid', 'lpg', 'other', 'default', 'price-asc', 'price-desc', 'rating-desc', 'year-desc']);
});
