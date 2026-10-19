'use client';

import Image from 'next/image';
import { useEffect, useRef, useState } from 'react';
import { completeRecoveredUpload, fetchRecoverableUploads, type RecoverableUpload } from '@/lib/api';
import { getCookieSessionRevision } from '@/lib/cookieSession';

interface Props {
  token: string; language: string; dark: boolean; disabled: boolean;
  imageCount: number; videoCount: number;
  onAdd: (kind: 'image' | 'video', url: string, assetId: string) => void;
}

export function UploadRecovery({ token, language, dark, disabled, imageCount, videoCount, onAdd }: Props) {
  const [entries, setEntries] = useState<RecoverableUpload[]>([]);
  const [cursor, setCursor] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);
  const [message, setMessage] = useState('');
  const [preview, setPreview] = useState<{ kind: 'image' | 'video'; url: string; assetId: string; revision: number } | null>(null);
  const live = useRef(false);
  const inFlight = useRef(false);
  useEffect(() => { live.current = true; return () => { live.current = false; }; }, []);
  const ar = language === 'ar';
  const button = 'rounded-xl border border-slate-400 px-3 py-2 text-sm disabled:opacity-50';
  const run = async (operation: (current: () => boolean, revision: number) => Promise<void>) => {
    if (disabled || inFlight.current) return;
    inFlight.current = true; setBusy(true); setMessage('');
    const revision = getCookieSessionRevision();
    const current = () => live.current && revision === getCookieSessionRevision();
    try { await operation(current, revision); }
    catch { if (current()) setMessage(ar ? 'تعذر استعادة الرفع الآن. قد تكون الميزة غير مفعلة؛ يمكنك إعادة المحاولة.' : 'Recovery is unavailable or verification is pending. You can retry.'); }
    finally { inFlight.current = false; if (live.current) setBusy(false); }
  };
  const load = (after?: string) => run(async (current) => {
    const result = await fetchRecoverableUploads(token, after);
    if (!current()) return;
    setEntries(result.uploads); setCursor(result.nextCursor); setPreview(null);
    if (!result.uploads.length) setMessage(ar ? 'لا توجد ملفات قابلة للاستعادة.' : 'No recoverable uploads found.');
  });
  const verify = (entry: RecoverableUpload) => run(async (current, revision) => {
    setPreview(null);
    const result = await completeRecoveredUpload(entry.intentId, token);
    if (!current()) return;
    if (!result.success || !result.assetId || !result.url) throw new Error('Unverified upload');
    setPreview({ kind: entry.kind, url: result.url, assetId: result.assetId, revision });
  });
  const full = preview?.kind === 'image' ? imageCount >= 12 : videoCount >= 2;
  return <section className={`space-y-3 rounded-xl border p-3 ${dark ? 'border-slate-600 text-slate-100' : 'border-slate-300 text-slate-900'}`} dir={ar ? 'rtl' : 'ltr'}>
    <button type="button" className={button} disabled={busy || disabled} onClick={() => void load()}>{ar ? 'استعادة ملفات مرفوعة سابقاً' : 'Recover previous uploads'}</button>
    <p className="text-sm">{ar ? 'تحقق من الملف وعاينه قبل إضافته. لا تُضاف الملفات أو تُحذف تلقائياً.' : 'Verify and preview a file before adding it. Files are never added or deleted automatically.'}</p>
    {busy ? <p role="status">{ar ? 'جارٍ التحقق…' : 'Checking…'}</p> : null}
    {message ? <p role="status">{message}</p> : null}
    <ul className="space-y-2">{entries.map((entry, index) => <li key={entry.intentId} className="flex flex-wrap items-center gap-2">
      <span>{entry.kind === 'image' ? (ar ? 'صورة' : 'Image') : (ar ? 'فيديو' : 'Video')} {index + 1} — {entry.state === 'completed' ? (ar ? 'تم التحقق' : 'Verified') : (ar ? 'بانتظار التحقق' : 'Pending verification')}</span>
      <button type="button" className={button} disabled={busy || disabled} onClick={() => void verify(entry)}>{ar ? 'تحقق ومعاينة' : 'Verify and preview'}</button>
    </li>)}</ul>
    {cursor ? <button type="button" className={button} disabled={busy || disabled} onClick={() => void load(cursor)}>{ar ? 'التالي' : 'Next uploads'}</button> : null}
    {preview ? <div className="space-y-2">
      {preview.kind === 'image' ? <Image src={preview.url} alt={ar ? 'معاينة الملف المستعاد' : 'Recovered upload preview'} width={320} height={200} unoptimized className="h-48 w-full rounded-lg object-contain" /> : <video src={preview.url} controls preload="metadata" className="h-48 w-full rounded-lg" />}
      <button type="button" className={button} disabled={busy || disabled || full} onClick={() => {
        if (preview.revision !== getCookieSessionRevision()) { setPreview(null); return; }
        onAdd(preview.kind, preview.url, preview.assetId); setPreview(null);
        setMessage(ar ? 'أُضيف إلى المسودة. احفظ الإعلان للاحتفاظ بالتغييرات.' : 'Added to the draft. Save the listing to keep this change.');
      }}>{ar ? 'إضافة إلى الإعلان' : 'Add to listing'}</button>
      {full ? <p role="status">{ar ? 'وصلت إلى الحد الأقصى للملفات.' : 'Media limit reached. Remove an item before adding this file.'}</p> : null}
    </div> : null}
  </section>;
}
