'use client';

import Link from 'next/link';
import { useEffect, useState } from 'react';
import { getAnalytics } from '@/lib/api';
import type { AnalyticsInsights } from '@/lib/types';
import { useAuth } from '@/context/AuthContext';
import { usePublicPreferences } from '@/components/public/PublicRouteShell';
import { RouteErrorState } from '@/components/RouteErrorState';

type AnalyticsFilter = 'all' | 'my' | 'favorites';

export function AnalyticsView() {
  const { token, loading: authLoading, sessionValidated, formatPrice } = useAuth();
  const { theme, language } = usePublicPreferences();
  const [filter, setFilter] = useState<AnalyticsFilter>('all'); const [data, setData] = useState<AnalyticsInsights | null>(null);
  const [loading, setLoading] = useState(true); const [error, setError] = useState(''); const [retryKey, setRetryKey] = useState(0);
  const dark = theme === 'dark';

  useEffect(() => {
    if (authLoading || !sessionValidated || !token) return;
    let live = true;
    getAnalytics(filter, token).then((response) => { if (live) { setData(response.insights); setError(''); } })
      .catch((loadError: unknown) => { if (live) setError(loadError instanceof Error ? loadError.message : 'Unable to load analytics'); })
      .finally(() => { if (live) setLoading(false); });
    return () => { live = false; };
  }, [authLoading, filter, retryKey, sessionValidated, token]);

  if (authLoading) return <main className="p-8 text-center text-slate-500">Loading analytics…</main>;
  if (!token || !sessionValidated) return <main className="p-8 text-center"><p className={dark ? 'text-slate-300' : 'text-slate-600'}>{language === 'ar' ? 'سجّل الدخول لعرض التحليلات.' : 'Sign in to view analytics.'}</p><Link href="/account" className="mt-4 inline-block rounded-xl bg-indigo-600 px-4 py-2 text-white">Sign In</Link></main>;
  if (loading) return <main className="p-8 text-center text-slate-500" aria-live="polite">Loading analytics…</main>;
  if (error) return <RouteErrorState message={error} onRetry={() => { setLoading(true); setError(''); setRetryKey((key) => key + 1); }}/>;

  const summary = data?.summary;
  return <main className="mx-auto max-w-7xl space-y-6 p-4 md:p-8">
    <div><h1 className={`text-3xl font-bold ${dark ? 'text-white' : 'text-slate-900'}`}>{language === 'ar' ? 'تحليلات السوق' : 'Market Analytics'}</h1><p className={dark ? 'text-slate-400' : 'text-slate-500'}>{language === 'ar' ? 'رؤى حول الأسعار والإعلانات' : 'Pricing and listing insights'}</p></div>
    <div className="flex flex-wrap gap-3">{(['all', 'my', 'favorites'] as const).map((value) => <button key={value} onClick={() => { if (value !== filter) { setLoading(true); setFilter(value); } }} className={`rounded-2xl px-4 py-2 text-sm font-semibold ${filter === value ? 'bg-sky-600 text-white' : dark ? 'border border-slate-700 bg-slate-800 text-slate-200' : 'border border-slate-200 bg-white text-slate-600'}`}>{value === 'all' ? 'All Listings' : value === 'my' ? 'My Listings' : 'Favorites'}</button>)}</div>
    {summary ? <section className="grid gap-4 md:grid-cols-3" aria-label="Analytics summary">{[['Average price', summary.average_price], ['Lowest price', summary.min_price], ['Highest price', summary.max_price]].map(([label, value]) => <article key={String(label)} className={`rounded-3xl border p-5 shadow-sm ${dark ? 'border-slate-700 bg-slate-900 text-white' : 'border-slate-100 bg-white text-slate-900'}`}><p className="text-sm opacity-60">{label}</p><p className="mt-2 text-2xl font-bold">{formatPrice(typeof value === 'number' ? value : undefined, summary.currency)}</p></article>)}</section> : null}
    {data?.market_top_makes?.length ? <section className={`rounded-3xl border p-5 shadow-sm ${dark ? 'border-slate-700 bg-slate-900 text-white' : 'border-slate-100 bg-white text-slate-900'}`}><h2 className="text-lg font-semibold">Top Makes</h2><div className="mt-4 space-y-3">{data.market_top_makes.map((entry) => <div key={entry.make} className={`grid grid-cols-3 items-center gap-3 rounded-2xl px-4 py-3 text-sm ${dark ? 'bg-slate-800' : 'bg-slate-50'}`}><strong>{entry.make}</strong><span>{formatPrice(entry.avg_price, summary?.currency)}</span><span>{entry.listings} listings</span></div>)}</div></section> : null}
    {!data || (!summary && !data.market_top_makes?.length) ? <p className={dark ? 'text-slate-400' : 'text-slate-500'}>{language === 'ar' ? 'لا توجد بيانات تحليلية متاحة.' : 'No analytics data is available.'}</p> : null}
  </main>;
}
