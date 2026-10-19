import assert from 'node:assert/strict';
import { readFile } from 'node:fs/promises';
import test from 'node:test';
import ts from 'typescript';

// Use the existing TypeScript compiler; no new framework or generated files.
const source = await readFile(new URL('../src/lib/listingsSearchParams.ts', import.meta.url), 'utf8');
const { outputText } = ts.transpileModule(source, { compilerOptions: { module: ts.ModuleKind.ESNext, target: ts.ScriptTarget.ES2020 } });
const { readListingsSearchParams: read, updateListingsSearchParams: update } = await import(`data:text/javascript;base64,${Buffer.from(outputText).toString('base64')}`);
const params = (query = '') => new URLSearchParams(query);

test('empty URL restores defaults', () => {
  const state = read(params());
  assert.equal(state.page, 1);
  assert.equal(state.filters.make, 'all');
  assert.equal(state.filters.search, '');
  assert.equal(state.filters.sort, 'default');
  assert.equal(state.filters.category, 'all');
});

test('all supported filters and pagination restore', () => {
  const state = read(params('make=Toyota&search=Camry&sort=price-asc&category=car&condition=used&transmission=automatic&fuelType=hybrid&page=3'));
  assert.deepEqual(state, { page: 3, filters: { make: 'Toyota', search: 'Camry', sort: 'price-asc', category: 'car', condition: 'used', transmission: 'automatic', fuelType: 'hybrid' } });
});

test('unsupported enumerated filters fall back', () => {
  const { filters } = read(params('sort=bad&category=bad&condition=bad&transmission=bad&fuelType=bad'));
  assert.equal(filters.sort, 'default');
  assert.equal(filters.category, 'all');
  for (const key of ['condition', 'transmission', 'fuelType']) assert.equal(filters[key], undefined);
});

test('invalid pagination falls back to page one', () => {
  for (const page of ['0', '-2', '1.5', 'NaN', 'Infinity', 'abc', '9007199254740992']) {
    assert.equal(read(params(`page=${page}`)).page, 1, page);
  }
});

test('filter changes reset pagination and preserve other parameters', () => {
  const next = params(update(params('page=4&make=BMW&utm_source=share&from=home'), { make: 'Toyota' }, true));
  assert.equal(next.get('make'), 'Toyota');
  assert.equal(next.has('page'), false);
  assert.equal(next.get('utm_source'), 'share');
  assert.equal(next.get('from'), 'home');
});

test('page updates retain active filters', () => {
  assert.equal(update(params('make=BMW'), { page: 3 }), 'make=BMW&page=3');
});

test('invalid page updates cannot serialize unsafe values', () => {
  for (const page of [Infinity, NaN, -1, 1.5, Number.MAX_SAFE_INTEGER + 1]) {
    assert.equal(update(params('make=BMW&page=3'), { page }), 'make=BMW');
  }
});

test('default and empty parameters are removed', () => {
  const next = update(params('make=BMW&search=old&sort=price-asc&category=car&condition=used&page=2'), { make: 'all', search: '  ', sort: 'default', category: 'all', condition: undefined, page: 1 });
  assert.equal(next, '');
});

test('serialization round trips Arabic and reserved characters', () => {
  const search = 'سيارة & BMW + SUV';
  assert.equal(read(params(update(params(), { search }))).filters.search, search);
});

test('stable serialization makes repeated updates navigation no-ops', () => {
  const patch = { make: 'BMW', category: 'car', search: '320' };
  const first = update(params('from=home'), patch, true);
  assert.equal(update(params(first), patch, true), first);
  assert.equal(first, 'category=car&from=home&make=BMW&search=320');
});

test('independent history entries restore their respective states', () => {
  const first = update(params(), { make: 'BMW', page: 2 });
  const second = update(params(first), { make: 'Toyota' }, true);
  assert.equal(read(params(first)).page, 2);
  assert.equal(read(params(first)).filters.make, 'BMW');
  assert.equal(read(params(second)).page, 1);
  assert.equal(read(params(second)).filters.make, 'Toyota');
});

test('canonical filter request key ignores pagination and unrelated query changes', () => {
  const key = (query) => update(params(), read(params(query)).filters);
  assert.equal(key('make=BMW&page=2&from=home'), key('from=listings&page=3&make=BMW'));
  assert.notEqual(key('make=BMW'), key('make=Toyota'));
});
