import type { CarFilters, FuelType, SortOption, TransmissionType, VehicleCategory, VehicleCondition } from '@/lib/types';

export interface ListingsSearchState { filters: CarFilters; page: number; }
const SORTS = new Set<SortOption>(['default', 'price-asc', 'price-desc', 'rating-desc', 'year-desc']);
const CATEGORIES = new Set<VehicleCategory>(['all', 'car', 'suv', 'truck', 'bike', 'van', 'bus', 'other']);
const CONDITIONS = new Set<VehicleCondition>(['new', 'used', 'certified']);
const TRANSMISSIONS = new Set<TransmissionType>(['automatic', 'manual', 'cvt', 'other']);
const FUELS = new Set<FuelType>(['petrol', 'diesel', 'electric', 'hybrid', 'plugin_hybrid', 'lpg', 'other']);

export function readListingsSearchParams(params: URLSearchParams): ListingsSearchState {
  const sortValue = params.get('sort'); const categoryValue = params.get('category'); const conditionValue = params.get('condition');
  const transmissionValue = params.get('transmission'); const fuelValue = params.get('fuelType'); const parsedPage = Number(params.get('page'));
  return {
    filters: {
      make: params.get('make')?.trim() || 'all', search: params.get('search')?.trim() || '',
      sort: sortValue && SORTS.has(sortValue as SortOption) ? sortValue as SortOption : 'default',
      category: categoryValue && CATEGORIES.has(categoryValue as VehicleCategory) ? categoryValue as VehicleCategory : 'all',
      condition: conditionValue && CONDITIONS.has(conditionValue as VehicleCondition) ? conditionValue as VehicleCondition : undefined,
      transmission: transmissionValue && TRANSMISSIONS.has(transmissionValue as TransmissionType) ? transmissionValue as TransmissionType : undefined,
      fuelType: fuelValue && FUELS.has(fuelValue as FuelType) ? fuelValue as FuelType : undefined,
    },
    page: Number.isSafeInteger(parsedPage) && parsedPage > 0 ? parsedPage : 1,
  };
}

export function updateListingsSearchParams(current: URLSearchParams, patch: Partial<CarFilters> & { page?: number }, resetPage = false): string {
  const next = new URLSearchParams(current);
  const set = (key: string, value: string | number | undefined, defaultValue?: string | number) => {
    if (value === undefined || value === '' || value === defaultValue) next.delete(key); else next.set(key, String(value));
  };
  if ('make' in patch) set('make', patch.make, 'all');
  if ('search' in patch) set('search', patch.search?.trim());
  if ('sort' in patch) set('sort', patch.sort, 'default');
  if ('category' in patch) set('category', patch.category, 'all');
  if ('condition' in patch) set('condition', patch.condition);
  if ('transmission' in patch) set('transmission', patch.transmission);
  if ('fuelType' in patch) set('fuelType', patch.fuelType);
  if (resetPage) next.delete('page'); else if ('page' in patch) set('page', patch.page && Number.isSafeInteger(patch.page) && patch.page > 1 ? patch.page : undefined);
  next.sort();
  return next.toString();
}
