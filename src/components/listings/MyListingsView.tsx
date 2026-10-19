'use client';

import Image from 'next/image';
import Link from 'next/link';
import { useEffect, useState } from 'react';
import { deleteListing, fetchMyListings, fetchMyListingsAnalytics, type MyListingsAnalytics } from '@/lib/api';
import type { Car } from '@/lib/types';
import { useAuth } from '@/context/AuthContext';
import { usePublicPreferences } from '@/components/public/PublicRouteShell';
import { RouteErrorState } from '@/components/RouteErrorState';

export function MyListingsView() {
  const { token, loading: authLoading, sessionValidated, formatPrice } = useAuth();
  const { theme, language } = usePublicPreferences();
  const [cars, setCars] = useState<Car[]>([]);
  const [analytics, setAnalytics] = useState<MyListingsAnalytics | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [retryKey, setRetryKey] = useState(0);
  const dark = theme === 'dark';

  useEffect(() => {
    if (authLoading || !sessionValidated || !token) return;
    let live = true;
    Promise.all([fetchMyListings(token), fetchMyListingsAnalytics(token)]).then(([listingsResponse, analyticsResponse]) => {
      if (!live) return;
      setCars(listingsResponse.cars || []);
      setAnalytics(analyticsResponse.analytics || null);
      setError('');
    }).catch((loadError: unknown) => {
      if (live) setError(loadError instanceof Error ? loadError.message : 'Unable to load your listings');
    }).finally(() => { if (live) setLoading(false); });
    return () => { live = false; };
  }, [authLoading, retryKey, sessionValidated, token]);

  if (authLoading) return <main className="p-8 text-center text-slate-500" aria-live="polite">Loading your listings…</main>;
  if (!token || !sessionValidated) return <main className="p-8 text-center"><p className={dark ? 'text-slate-300' : 'text-slate-600'}>{language === 'ar' ? 'سجّل الدخول لإدارة إعلاناتك.' : 'Sign in to manage your listings.'}</p><Link href="/account" className="mt-4 inline-block rounded-xl bg-indigo-600 px-4 py-2 font-semibold text-white">{language === 'ar' ? 'تسجيل الدخول' : 'Sign In'}</Link></main>;
  if (loading) return <main className="p-8 text-center text-slate-500" aria-live="polite">Loading your listings…</main>;
  if (error) return <RouteErrorState message={error} onRetry={() => { setLoading(true); setError(''); setRetryKey((key) => key + 1); }} />;

  return (
    <main className="mx-auto max-w-7xl space-y-6 p-4 md:p-8">
      <div className="flex flex-wrap items-center justify-between gap-3"><h1 className={`text-3xl font-bold ${dark ? 'text-white' : 'text-slate-900'}`}>{language === 'ar' ? 'إعلاناتي' : 'My Listings'}</h1><Link href="/my-listings/new" className="rounded-2xl bg-emerald-600 px-4 py-2 font-semibold text-white">{language === 'ar' ? 'إضافة إعلان' : '+ Add New'}</Link></div>
      {analytics ? <section className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4" aria-label="Listing analytics"><div className="rounded-3xl bg-emerald-50 p-5 text-emerald-900"><p className="text-xs uppercase">Total Listings</p><p className="text-3xl font-bold">{analytics.total_listings}</p></div><div className="rounded-3xl bg-blue-50 p-5 text-blue-900"><p className="text-xs uppercase">Total Value</p><p className="text-2xl font-bold">{formatPrice(analytics.total_value, 'JOD')}</p></div><div className="rounded-3xl bg-amber-50 p-5 text-amber-900"><p className="text-xs uppercase">Average Price</p><p className="text-2xl font-bold">{formatPrice(analytics.average_price, 'JOD')}</p></div><div className="rounded-3xl bg-purple-50 p-5 text-purple-900"><p className="text-xs uppercase">Favorites</p><p className="text-3xl font-bold">{analytics.performance.total_favorites}</p></div></section> : null}
      {cars.length ? <section className="grid gap-4 md:grid-cols-2 lg:grid-cols-3" aria-label="Your listings">{cars.map((car) => <article key={car.id} className={`rounded-3xl border p-4 ${dark ? 'border-slate-700 bg-slate-800 text-white' : 'border-slate-200 bg-white'}`}><Image unoptimized src={car.imageUrls?.[0] || car.galleryImages?.[0] || car.image || '/placeholder-car.svg'} alt={`${car.make} ${car.model}`} width={640} height={320} className="h-40 w-full rounded-2xl object-cover"/><h2 className="mt-4 text-lg font-semibold">{car.make} {car.model}</h2><p>{car.year}</p><p className="font-bold text-emerald-600">{formatPrice(car.price, car.currency)}</p><div className="mt-4 grid grid-cols-3 gap-2"><Link className="rounded-xl border py-2 text-center text-sm font-semibold" href={`/cars/${car.id}?from=myListings`}>View</Link><Link className="rounded-xl border py-2 text-center text-sm font-semibold" href={`/my-listings/${car.id}/edit`}>Edit</Link><button type="button" className="rounded-xl bg-rose-600 py-2 text-sm font-semibold text-white" onClick={async () => { if (!window.confirm('Delete this listing?')) return; try { await deleteListing(car.id, token); setCars((current) => current.filter((item) => item.id !== car.id)); } catch (deleteError: unknown) { setError(deleteError instanceof Error ? deleteError.message : 'Unable to delete listing'); } }}>Delete</button></div></article>)}</section> : <section className={`rounded-3xl border border-dashed p-8 text-center ${dark ? 'border-slate-700 text-slate-400' : 'border-slate-200 text-slate-500'}`}><p>{language === 'ar' ? 'لا توجد إعلانات بعد.' : 'You have no listings yet.'}</p><Link href="/my-listings/new" className="mt-4 inline-block rounded-xl bg-emerald-600 px-4 py-2 font-semibold text-white">{language === 'ar' ? 'أنشئ إعلانك الأول' : 'Create your first listing'}</Link></section>}
    </main>
  );
}
