'use client';

import Image from 'next/image';
import Link from 'next/link';
import { usePathname, useRouter, useSearchParams } from 'next/navigation';
import { useEffect, useMemo, useState } from 'react';
import { fetchCars, fetchMakes } from '@/lib/api';
import type { Car, CarFilters, FuelType, TransmissionType, VehicleCategory, VehicleCondition } from '@/lib/types';
import { readListingsSearchParams, updateListingsSearchParams } from '@/lib/listingsSearchParams';
import { listingsCopy } from '@/lib/listingsCopy';
import { sortListings } from '@/lib/sortListings';
import { useAuth } from '@/context/AuthContext';
import { usePublicPreferences } from '@/components/public/PublicRouteShell';
import { RouteErrorState } from '@/components/RouteErrorState';

const PAGE_SIZE = 10;

export function PublicListingsView() {
  const searchParams = useSearchParams(); const pathname = usePathname(); const router = useRouter(); const query = searchParams.toString();
  const { token, formatPrice, convertCurrency } = useAuth(); const { theme, language } = usePublicPreferences();
  const copy = listingsCopy[language];
  const [cars, setCars] = useState<Car[]>([]); const [makes, setMakes] = useState<string[]>([]); const [loading, setLoading] = useState(true);
  const [error, setError] = useState(''); const [retryKey, setRetryKey] = useState(0); const dark = theme === 'dark';
  const filterQuery = useMemo(() => updateListingsSearchParams(new URLSearchParams(), readListingsSearchParams(new URLSearchParams(query)).filters), [query]);
  const filters = useMemo(() => readListingsSearchParams(new URLSearchParams(filterQuery)).filters, [filterQuery]);
  const page = useMemo(() => readListingsSearchParams(new URLSearchParams(query)).page, [query]);

  useEffect(() => {
    let live = true;
    const controller = new AbortController();
    fetchCars(filters, controller.signal, token).then((carsResponse) => {
      if (live) { setCars(carsResponse.cars ?? []); setError(''); }
    }).catch((loadError: unknown) => { if (live) setError(loadError instanceof Error ? loadError.message : 'Unable to load listings'); })
      .finally(() => { if (live) setLoading(false); });
    return () => { live = false; controller.abort(); };
  }, [filters, retryKey, token]);

  useEffect(() => {
    let live = true;
    fetchMakes(token).then((response) => { if (live) setMakes(response.makes ?? []); })
      .catch(() => { if (live) setMakes([]); });
    return () => { live = false; };
  }, [retryKey, token]);

  // Reference-data failure must not hide otherwise valid inventory. Retain the
  // current URL selection and makes visible in the returned records as options.
  const availableMakes = useMemo(() => Array.from(new Set([
    ...makes, ...cars.map((car) => car.make), ...(filters.make !== 'all' ? [filters.make] : []),
  ])).sort(), [cars, filters.make, makes]);

  const totalPages = Math.max(1, Math.ceil(cars.length / PAGE_SIZE)); const safePage = Math.min(page, totalPages);
  const sortedCars = useMemo(() => sortListings(cars, filters.sort, (car) => typeof car.price === 'number' ? convertCurrency(car.price, car.currency ?? 'JOD', 'JOD') : NaN), [cars, filters.sort, convertCurrency]);
  const visibleCars = sortedCars.slice((safePage - 1) * PAGE_SIZE, safePage * PAGE_SIZE);
  const navigate = (patch: Partial<CarFilters> & { page?: number }, resetPage = false) => {
    const next = updateListingsSearchParams(new URLSearchParams(query), patch, resetPage); const href = next ? `${pathname}?${next}` : pathname;
    if (href !== `${pathname}${query ? `?${query}` : ''}`) router.push(href, { scroll: false });
  };
  const field = `rounded-xl border p-3 text-sm ${dark ? 'border-slate-700 bg-slate-900 text-white' : 'border-slate-200 bg-white text-slate-900'}`;

  if (loading) return <main className="p-8 text-center" aria-live="polite">{copy["Loading listings…"]}</main>;
  if (error) return <RouteErrorState message={copy['Unable to load listings']} retryLabel={copy['Try again']} onRetry={() => { setLoading(true); setError(''); setRetryKey((key) => key + 1); }}/>;
  return <main className="mx-auto max-w-7xl p-4 md:p-8"><div className="flex flex-wrap items-end justify-between gap-3"><div><h1 className={`text-3xl font-bold ${dark ? 'text-white' : 'text-slate-900'}`}>{copy.Listings}</h1><p className={dark ? 'text-slate-400' : 'text-slate-500'}>{cars.length} {copy.results}</p></div><Link href="/my-listings/new" className="rounded-xl bg-emerald-600 px-4 py-3 text-sm font-semibold text-white">{copy['Sell a Vehicle']}</Link></div>
    <section className="mt-6 grid gap-3 sm:grid-cols-2 lg:grid-cols-4" aria-label={copy["Listing filters"]}><label className="sr-only" htmlFor="listing-search">{copy["Search"]}</label><input id="listing-search" value={filters.search} onChange={(event) => navigate({ search: event.target.value }, true)} placeholder={copy['Search…']} className={field}/><label className="sr-only" htmlFor="listing-make">{copy["Make"]}</label><select id="listing-make" value={filters.make} onChange={(event) => navigate({ make: event.target.value }, true)} className={field}><option value="all">{copy["All makes"]}</option>{availableMakes.map((make) => <option key={make}>{make}</option>)}</select><label className="sr-only" htmlFor="listing-category">{copy["Category"]}</label><select id="listing-category" value={filters.category ?? 'all'} onChange={(event) => navigate({ category: event.target.value as VehicleCategory }, true)} className={field}><option value="all">{copy["All categories"]}</option><option value="car">{copy["Cars"]}</option><option value="suv">{copy["SUVs"]}</option><option value="truck">{copy["Trucks"]}</option><option value="bike">{copy["Motorcycles"]}</option><option value="van">{copy["Vans"]}</option><option value="bus">{copy["Buses"]}</option><option value="other">{copy["Other"]}</option></select><label className="sr-only" htmlFor="listing-condition">{copy["Condition"]}</label><select id="listing-condition" value={filters.condition ?? ''} onChange={(event) => navigate({ condition: (event.target.value || undefined) as VehicleCondition | undefined }, true)} className={field}><option value="">{copy["Any condition"]}</option><option value="new">{copy["New"]}</option><option value="used">{copy["Used"]}</option><option value="certified">{copy["Certified"]}</option></select><label className="sr-only" htmlFor="listing-transmission">{copy["Transmission"]}</label><select id="listing-transmission" value={filters.transmission ?? ''} onChange={(event) => navigate({ transmission: (event.target.value || undefined) as TransmissionType | undefined }, true)} className={field}><option value="">{copy["Any transmission"]}</option><option value="automatic">{copy["Automatic"]}</option><option value="manual">{copy["Manual"]}</option><option value="cvt">{copy["CVT"]}</option><option value="other">{copy["Other"]}</option></select><label className="sr-only" htmlFor="listing-fuel">{copy["Fuel type"]}</label><select id="listing-fuel" value={filters.fuelType ?? ''} onChange={(event) => navigate({ fuelType: (event.target.value || undefined) as FuelType | undefined }, true)} className={field}><option value="">{copy["Any fuel"]}</option><option value="petrol">{copy["Petrol"]}</option><option value="diesel">{copy["Diesel"]}</option><option value="electric">{copy["Electric"]}</option><option value="hybrid">{copy["Hybrid"]}</option><option value="plugin_hybrid">{copy["Plug-in hybrid"]}</option><option value="lpg">{copy["LPG"]}</option><option value="other">{copy["Other"]}</option></select><label className="sr-only" htmlFor="listing-sort">{copy["Sort"]}</label><select id="listing-sort" value={filters.sort} onChange={(event) => navigate({ sort: event.target.value as CarFilters['sort'] }, true)} className={field}><option value="default">{copy["Recommended"]}</option><option value="price-asc">{copy["Price: low to high"]}</option><option value="price-desc">{copy["Price: high to low"]}</option><option value="rating-desc">{copy["Highest rated"]}</option><option value="year-desc">{copy["Newest year"]}</option></select><button type="button" onClick={() => router.push(pathname, { scroll: false })} className="rounded-xl border border-slate-300 px-4 py-3 text-sm font-semibold text-slate-500">{copy["Clear filters"]}</button></section>
    <div className="mt-6 grid gap-4 md:grid-cols-2 xl:grid-cols-3">{visibleCars.map((car) => <Link href={`/cars/${car.id}?from=listings`} key={car.id} className={`rounded-3xl border p-4 ${dark ? 'border-slate-700 bg-slate-800 text-white' : 'border-slate-200 bg-white'}`}><Image unoptimized src={car.imageUrls?.[0] || car.galleryImages?.[0] || car.image || '/placeholder-car.svg'} alt={`${car.make} ${car.model}`} width={640} height={320} className="h-40 w-full rounded-2xl object-cover"/><h2 className="mt-4 text-lg font-semibold">{car.make} {car.model}</h2><p>{car.year}</p><p className="font-semibold text-emerald-600">{formatPrice(car.price, car.currency)}</p></Link>)}</div>{!visibleCars.length ? <p className="mt-6 text-slate-500">{copy["No listings match your filters."]}</p> : null}
    {totalPages > 1 ? <nav className="mt-8 flex items-center justify-center gap-3" aria-label={copy["Listings pagination"]}><button disabled={safePage <= 1} onClick={() => navigate({ page: safePage - 1 })} className="rounded-xl border px-4 py-2 disabled:opacity-40">{copy["Previous"]}</button><span className={dark ? 'text-slate-300' : 'text-slate-600'}>{copy.Page} {safePage} {copy.of} {totalPages}</span><button disabled={safePage >= totalPages} onClick={() => navigate({ page: safePage + 1 })} className="rounded-xl border px-4 py-2 disabled:opacity-40">{copy["Next"]}</button></nav> : null}
  </main>;
}
