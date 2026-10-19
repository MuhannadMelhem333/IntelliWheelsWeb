import type { Car, SortOption } from './types';

/** Sort a copy before pagination; priceValue uses the app's currency conversion. */
export function sortListings(cars: readonly Car[], sort: SortOption, priceValue: (car: Car) => number): Car[] {
  const result = [...cars];
  const value = (car: Car) => sort === 'rating-desc' ? car.rating : sort === 'year-desc' ? car.year : priceValue(car);
  if (sort === 'default') return result;
  return result.sort((a, b) => {
    const left = value(a);
    const right = value(b);
    const leftValid = typeof left === 'number' && Number.isFinite(left);
    const rightValid = typeof right === 'number' && Number.isFinite(right);
    if (!leftValid) return rightValid ? 1 : 0;
    if (!rightValid) return -1;
    return sort === 'price-asc' ? left - right : right - left;
  });
}
