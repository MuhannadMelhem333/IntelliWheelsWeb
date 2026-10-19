'use client';
import Link from 'next/link';
import Image from 'next/image';
import dynamic from 'next/dynamic';
import { useRouter } from 'next/navigation';
import { useEffect, useState } from 'react';
import { fetchDealers } from '@/lib/api';
import { DealerSummary } from '@/lib/types';
import { useAuth } from '@/context/AuthContext';
import { usePublicPreferences } from '@/components/public/PublicRouteShell';
import { RouteErrorState } from '@/components/RouteErrorState';

const DealerMap = dynamic(() => import('@/components/DealerMap').then(m => m.DealerMap), { ssr: false });
export function DealerListView() {
  const { token, formatPrice } = useAuth(); const router = useRouter(); const { theme } = usePublicPreferences(); const [dealers, setDealers] = useState<DealerSummary[]>([]); const [loading, setLoading] = useState(true); const [error, setError] = useState(''); const [retryKey, setRetryKey] = useState(0); const [view, setView] = useState<'grid' | 'map'>('grid'); const dark = theme === 'dark';
  useEffect(() => { let live = true; fetchDealers(token).then(r => { if (live) { setDealers(r.dealers || []); setError(''); } }).catch(e => live && setError(e instanceof Error ? e.message : 'Unable to load dealers')).finally(() => live && setLoading(false)); return () => { live = false; }; }, [token, retryKey]);
  if (loading) return <main className="p-8 text-center">Loading dealers…</main>; if (error) return <RouteErrorState message={error} onRetry={() => { setLoading(true); setError(''); setRetryKey((key) => key + 1); }} />;
  return <main className="mx-auto max-w-7xl p-4 md:p-8"><div className="flex items-center justify-between gap-3"><h1 className={`text-3xl font-bold ${dark ? 'text-white' : 'text-slate-900'}`}>Dealers</h1><div className="flex gap-2"><button type="button" onClick={() => setView('grid')}>Grid</button><button type="button" onClick={() => setView('map')}>Map</button></div></div>{view === 'map' ? <div className="mt-6"><DealerMap dealers={dealers} isDark={dark} onDealerClick={(id) => router.push(`/dealers/${id}`)} /></div> : <div className="mt-6 grid gap-4 md:grid-cols-2 xl:grid-cols-3">{dealers.map(d => <Link key={d.id} href={`/dealers/${d.id}`} className={`rounded-3xl border p-4 ${dark ? 'border-slate-700 bg-slate-800 text-white' : 'border-slate-200 bg-white'}`}><Image unoptimized src={d.hero_image || '/placeholder-car.svg'} alt={d.name} width={640} height={320} className="h-40 w-full rounded-2xl object-cover"/><h2 className="mt-4 text-lg font-semibold">{d.name}</h2><p className="text-sm">{d.total_listings} listings</p><p className="text-sm">{d.average_price ? formatPrice(d.average_price, 'JOD') : '—'}</p></Link>)}</div>}{!dealers.length && <p className="mt-6 text-slate-500">No dealers available.</p>}</main>;
}
