'use client';

import Link from 'next/link';
import { useEffect, useState } from 'react';
import { approveDealerApplication, fetchDealerApplications, rejectDealerApplication } from '@/lib/api';
import type { DealerApplication } from '@/lib/types';
import { useAuth } from '@/context/AuthContext';
import { usePublicPreferences } from '@/components/public/PublicRouteShell';
import { RouteErrorState } from '@/components/RouteErrorState';

type ApplicationFilter = 'all' | 'pending' | 'approved' | 'rejected';
type PendingAction = { type: 'approve' | 'reject'; application: DealerApplication };

export function AdminDealerApplicationsView() {
  const { user, token, loading: authLoading, sessionValidated } = useAuth(); const { theme, language } = usePublicPreferences();
  const [filter, setFilter] = useState<ApplicationFilter>('pending'); const [applications, setApplications] = useState<DealerApplication[]>([]);
  const [loading, setLoading] = useState(true); const [error, setError] = useState(''); const [retryKey, setRetryKey] = useState(0);
  const [action, setAction] = useState<PendingAction | null>(null); const [reason, setReason] = useState(''); const [notes, setNotes] = useState(''); const [saving, setSaving] = useState(false);
  const dark = theme === 'dark';

  useEffect(() => {
    if (authLoading || !sessionValidated || !token || !user?.is_admin) return;
    let live = true;
    fetchDealerApplications(token, filter === 'all' ? undefined : filter).then((response) => { if (live) { setApplications(response.applications ?? []); setError(''); } })
      .catch((loadError: unknown) => { if (live) setError(loadError instanceof Error ? loadError.message : 'Unable to load dealer applications'); })
      .finally(() => { if (live) setLoading(false); });
    return () => { live = false; };
  }, [authLoading, filter, retryKey, sessionValidated, token, user?.is_admin]);

  const submitAction = async () => {
    if (!action || !token) return; if (action.type === 'reject' && !reason.trim()) { setError('A rejection reason is required.'); return; }
    setSaving(true); setError('');
    try {
      const response = action.type === 'approve' ? await approveDealerApplication(action.application.id, notes, token) : await rejectDealerApplication(action.application.id, reason, notes, token);
      if (!response.success) throw new Error(response.error || 'Unable to update the application');
      setAction(null); setReason(''); setNotes(''); setLoading(true); setRetryKey((key) => key + 1);
    } catch (actionError: unknown) { setError(actionError instanceof Error ? actionError.message : 'Unable to update the application'); }
    finally { setSaving(false); }
  };

  if (authLoading) return <main className="p-8 text-center text-slate-500">Loading admin panel…</main>;
  if (!token || !sessionValidated) return <main className="p-8 text-center"><p className={dark ? 'text-slate-300' : 'text-slate-600'}>Sign in with an administrator account.</p><Link href="/account" className="mt-4 inline-block rounded-xl bg-indigo-600 px-4 py-2 text-white">Sign In</Link></main>;
  if (!user?.is_admin) return <main className="p-8 text-center"><h1 className={`text-2xl font-bold ${dark ? 'text-white' : 'text-slate-900'}`}>Access Denied</h1><p className={dark ? 'text-slate-400' : 'text-slate-500'}>Your verified account does not have administrator privileges.</p></main>;
  if (loading) return <main className="p-8 text-center text-slate-500" aria-live="polite">Loading dealer applications…</main>;
  if (error && !action) return <RouteErrorState message={error} onRetry={() => { setLoading(true); setError(''); setRetryKey((key) => key + 1); }}/>;

  return <main className="mx-auto max-w-7xl space-y-6 p-4 md:p-8">
    <header className="flex flex-wrap items-end justify-between gap-4"><div><h1 className={`text-3xl font-bold ${dark ? 'text-white' : 'text-slate-900'}`}>{language === 'ar' ? 'لوحة الإدارة' : 'Admin Panel'}</h1><p className={dark ? 'text-slate-400' : 'text-slate-500'}>{language === 'ar' ? 'إدارة طلبات الوكلاء' : 'Manage dealer applications'}</p></div><div className="flex flex-wrap gap-2">{(['all', 'pending', 'approved', 'rejected'] as const).map((value) => <button key={value} onClick={() => { if (value !== filter) { setLoading(true); setFilter(value); } }} className={`rounded-xl px-4 py-2 text-sm font-semibold ${filter === value ? 'bg-indigo-600 text-white' : dark ? 'bg-slate-800 text-slate-200' : 'bg-slate-100 text-slate-600'}`}>{value[0].toUpperCase() + value.slice(1)}</button>)}</div></header>
    {applications.length ? <section className="grid gap-4 md:grid-cols-2 lg:grid-cols-3" aria-label="Dealer applications">{applications.map((application) => <article key={application.id} className={`rounded-2xl border p-5 ${dark ? 'border-slate-700 bg-slate-900 text-white' : 'border-slate-200 bg-white text-slate-900'}`}><div className="flex items-start justify-between gap-3"><div><h2 className="text-lg font-semibold">{application.name}</h2><p className="text-sm opacity-60">{application.city}</p></div><span className={`rounded-full px-3 py-1 text-xs font-semibold ${application.status === 'approved' ? 'bg-emerald-100 text-emerald-700' : application.status === 'rejected' ? 'bg-rose-100 text-rose-700' : 'bg-amber-100 text-amber-700'}`}>{application.status}</span></div><dl className="mt-4 space-y-2 text-sm"><div><dt className="sr-only">Email</dt><dd><a href={`mailto:${application.email}`} className="text-indigo-500">{application.email}</a></dd></div><div><dt className="sr-only">Phone</dt><dd><a href={`tel:${application.phone}`} className="text-indigo-500">{application.phone}</a></dd></div>{application.website ? <div><dt className="sr-only">Website</dt><dd><a href={application.website} target="_blank" rel="noopener noreferrer" className="text-indigo-500">{application.website}</a></dd></div> : null}</dl>{application.description ? <p className="mt-3 text-sm opacity-70">{application.description}</p> : null}<p className="mt-4 border-t border-current/10 pt-3 text-xs opacity-50">Submitted {new Date(application.created_at).toLocaleDateString()}</p>{application.status === 'pending' ? <div className="mt-4 flex gap-2"><button onClick={() => setAction({ type: 'approve', application })} className="flex-1 rounded-xl bg-emerald-600 py-2 text-sm font-semibold text-white">Approve</button><button onClick={() => setAction({ type: 'reject', application })} className="flex-1 rounded-xl bg-rose-600 py-2 text-sm font-semibold text-white">Reject</button></div> : null}</article>)}</section> : <section className={`rounded-3xl border p-8 text-center ${dark ? 'border-slate-700 bg-slate-900 text-slate-300' : 'border-slate-200 bg-white text-slate-600'}`}>No {filter === 'all' ? '' : `${filter} `}applications found.</section>}
    {action ? <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/60 p-4" role="dialog" aria-modal="true" aria-labelledby="admin-action-title"><div className={`w-full max-w-md rounded-3xl p-6 ${dark ? 'bg-slate-900 text-white' : 'bg-white text-slate-900'}`}><h2 id="admin-action-title" className="text-xl font-bold">{action.type === 'approve' ? 'Approve' : 'Reject'} {action.application.name}</h2>{error ? <p role="alert" className="mt-3 rounded-xl bg-rose-50 p-3 text-sm text-rose-700">{error}</p> : null}{action.type === 'reject' ? <label className="mt-4 block text-sm">Reason *<input value={reason} onChange={(event) => setReason(event.target.value)} className={`mt-1 w-full rounded-xl border p-3 ${dark ? 'border-slate-600 bg-slate-800' : 'border-slate-200'}`}/></label> : null}<label className="mt-4 block text-sm">Admin notes<textarea rows={3} value={notes} onChange={(event) => setNotes(event.target.value)} className={`mt-1 w-full rounded-xl border p-3 ${dark ? 'border-slate-600 bg-slate-800' : 'border-slate-200'}`}/></label><div className="mt-6 flex gap-3"><button disabled={saving} onClick={() => { setAction(null); setError(''); }} className="flex-1 rounded-xl border py-3">Cancel</button><button disabled={saving} onClick={() => void submitAction()} className={`flex-1 rounded-xl py-3 font-semibold text-white ${action.type === 'approve' ? 'bg-emerald-600' : 'bg-rose-600'}`}>{saving ? 'Saving…' : 'Confirm'}</button></div></div></div> : null}
  </main>;
}
