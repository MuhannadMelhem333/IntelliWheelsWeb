'use client';

import Image from 'next/image';
import Link from 'next/link';
import { useEffect, useState } from 'react';
import { fetchFavorites, removeFavorite } from '@/lib/api';
import type { Car } from '@/lib/types';
import { useAuth } from '@/context/AuthContext';
import { usePublicPreferences } from '@/components/public/PublicRouteShell';
import { RouteErrorState } from '@/components/RouteErrorState';

export function FavoritesView() {
  const { token, loading: authLoading, sessionValidated, formatPrice } = useAuth();
  const { theme, language } = usePublicPreferences();
  const [cars, setCars] = useState<Car[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [retryKey, setRetryKey] = useState(0);
  const dark = theme === 'dark';

  useEffect(() => {
    if (authLoading) return;
    if (!token || !sessionValidated) return;
    let live = true;
    fetchFavorites(token).then((response) => {
      if (live) { setCars(response.cars || []); setError(''); }
    }).catch((loadError: unknown) => {
      if (live) setError(loadError instanceof Error ? loadError.message : 'Unable to load favorites');
    }).finally(() => { if (live) setLoading(false); });
    return () => { live = false; };
  }, [authLoading, retryKey, sessionValidated, token]);

  if (authLoading) return <main className="p-8 text-center text-slate-500" aria-live="polite">{language === 'ar' ? 'جارٍ تحميل المفضلة…' : 'Loading favorites…'}</main>;
  if (!token || !sessionValidated) return <main className="p-8 text-center"><p className={dark ? 'text-slate-300' : 'text-slate-600'}>{language === 'ar' ? 'سجّل الدخول لعرض المفضلة.' : 'Sign in to view your favorites.'}</p><Link className="mt-4 inline-block rounded-xl bg-indigo-600 px-4 py-2 font-semibold text-white" href="/account">{language === 'ar' ? 'تسجيل الدخول' : 'Sign In'}</Link></main>;
  if (loading) return <main className="p-8 text-center text-slate-500" aria-live="polite">{language === 'ar' ? 'جارٍ تحميل المفضلة…' : 'Loading favorites…'}</main>;
  if (error) return <RouteErrorState message={error} retryLabel={language === 'ar' ? 'حاول مجدداً' : 'Try again'} onRetry={() => { setLoading(true); setError(''); setRetryKey((key) => key + 1); }} />;

  return (
    <main className="mx-auto max-w-7xl p-4 md:p-8">
      <h1 className={`text-3xl font-bold ${dark ? 'text-white' : 'text-slate-900'}`}>{language === 'ar' ? 'السيارات المفضلة' : 'Favorite Cars'}</h1>
      {cars.length ? <div className="mt-6 grid gap-4 md:grid-cols-2 xl:grid-cols-3">{cars.map((car) => <article key={car.id} className={`rounded-3xl border p-4 ${dark ? 'border-slate-700 bg-slate-800 text-white' : 'border-slate-200 bg-white'}`}><Link href={`/cars/${car.id}?from=favorites`}><Image unoptimized src={car.imageUrls?.[0] || car.galleryImages?.[0] || car.image || '/placeholder-car.svg'} alt={`${car.make} ${car.model}`} width={640} height={320} className="h-40 w-full rounded-2xl object-cover"/><h2 className="mt-4 text-lg font-semibold">{car.make} {car.model}</h2><p>{formatPrice(car.price, car.currency)}</p></Link><button type="button" className="mt-4 rounded-xl border border-rose-300 px-3 py-2 text-sm font-semibold text-rose-600" onClick={async () => { try { await removeFavorite(car.id, token); setCars((current) => current.filter((item) => item.id !== car.id)); } catch (removeError: unknown) { setError(removeError instanceof Error ? removeError.message : 'Unable to update favorites'); } }}>{language === 'ar' ? 'إزالة من المفضلة' : 'Remove favorite'}</button></article>)}</div> : <p className={`mt-6 ${dark ? 'text-slate-400' : 'text-slate-500'}`}>{language === 'ar' ? 'لا توجد سيارات مفضلة بعد.' : 'No favorite cars yet.'}</p>}
    </main>
  );
}
