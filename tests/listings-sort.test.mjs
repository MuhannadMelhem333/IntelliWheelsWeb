import assert from 'node:assert/strict';
import { readFile } from 'node:fs/promises';
import test from 'node:test';
import ts from 'typescript';

const source = await readFile(new URL('../src/lib/sortListings.ts', import.meta.url), 'utf8');
const { outputText } = ts.transpileModule(source, { compilerOptions: { module: ts.ModuleKind.ESNext, target: ts.ScriptTarget.ES2020 } });
const { sortListings } = await import(`data:text/javascript;base64,${Buffer.from(outputText).toString('base64')}`);
const cars = [{ id: 1, price: 30, rating: 3, year: 2020 }, { id: 2, price: 10, rating: 5, year: 2023 }, { id: 3, price: 20, rating: 4, year: 2021 }];
const ids = (rows) => rows.map((row) => row.id);
const price = (car) => car.price;

test('default keeps API ordering and never mutates input', () => {
  const copy = structuredClone(cars);
  assert.deepEqual(ids(sortListings(cars, 'default', price)), [1, 2, 3]);
  sortListings(cars, 'price-asc', price);
  assert.deepEqual(cars, copy);
});
test('all sort options order before page slicing', () => {
  for (const [sort, expected] of [['price-asc', [2, 3, 1]], ['price-desc', [1, 3, 2]], ['year-desc', [2, 3, 1]], ['rating-desc', [2, 3, 1]]]) {
    assert.deepEqual(ids(sortListings(cars, sort, price)), expected);
  }
  assert.deepEqual(ids(sortListings(cars, 'price-asc', price).slice(0, 2)), [2, 3]);
});
test('price comparison uses converted rather than nominal prices', () => {
  const mixed = [{ id: 1, price: 100, currency: 'JOD' }, { id: 2, price: 300, currency: 'AED' }];
  assert.deepEqual(ids(sortListings(mixed, 'price-asc', (car) => car.price * (car.currency === 'AED' ? 0.193 : 1))), [2, 1]);
});
test('missing prices sort last in either direction; ties stay stable', () => {
  const data = [{ id: 1 }, { id: 2, price: 10 }, { id: 3, price: 10 }];
  for (const sort of ['price-asc', 'price-desc']) assert.deepEqual(ids(sortListings(data, sort, price)), [2, 3, 1]);
});
