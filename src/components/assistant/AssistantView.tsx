'use client';

import Image from 'next/image';
import Link from 'next/link';
import { useRouter } from 'next/navigation';
import { useRef, useState } from 'react';
import { createListing, handleChatbotMessage, uploadListingImage } from '@/lib/api';
import { STORAGE_KEYS } from '@/lib/config';
import type { Car, ChatMessage, ChatSession, ListingDraft } from '@/lib/types';
import { useAuth } from '@/context/AuthContext';
import { usePublicPreferences } from '@/components/public/PublicRouteShell';

const HISTORY_LIMIT = 20;

function readSessions(userId: number): ChatSession[] {
  try {
    const raw = localStorage.getItem(`${STORAGE_KEYS.chatSessions}-${userId}`);
    const parsed: unknown = raw ? JSON.parse(raw) : [];
    return Array.isArray(parsed) ? parsed as ChatSession[] : [];
  } catch { return []; }
}

async function readAttachment(file: File): Promise<{ preview: string; base64: string; mime: string }> {
  const preview = await new Promise<string>((resolve, reject) => {
    const reader = new FileReader(); reader.onload = () => resolve(String(reader.result)); reader.onerror = () => reject(new Error('Unable to read image')); reader.readAsDataURL(file);
  });
  return { preview, base64: preview.split(',')[1] ?? '', mime: file.type };
}

function AssistantSessionView({ userId, token }: { userId: number; token: string }) {
  const router = useRouter();
  const { theme, language } = usePublicPreferences();
  const [sessions, setSessions] = useState<ChatSession[]>(() => readSessions(userId));
  const [activeId, setActiveId] = useState<string | null>(() => readSessions(userId)[0]?.id ?? null);
  const [input, setInput] = useState('');
  const [attachment, setAttachment] = useState<{ preview: string; base64: string; mime: string } | null>(null);
  const [busy, setBusy] = useState(false); const [publishingId, setPublishingId] = useState<string | null>(null); const [error, setError] = useState(''); const abortRef = useRef<AbortController | null>(null);
  const dark = theme === 'dark'; const active = sessions.find((session) => session.id === activeId) ?? null; const messages = active?.messages ?? [];

  const commit = (next: ChatSession[], nextActive = activeId) => {
    setSessions(next); setActiveId(nextActive); localStorage.setItem(`${STORAGE_KEYS.chatSessions}-${userId}`, JSON.stringify(next));
  };
  const newChat = () => {
    const id = crypto.randomUUID(); const session: ChatSession = { id, title: language === 'ar' ? 'محادثة جديدة' : 'New chat', messages: [], updatedAt: new Date().toISOString() };
    commit([session, ...sessions], id);
  };
  const deleteChat = (id: string) => {
    const next = sessions.filter((session) => session.id !== id); commit(next, id === activeId ? next[0]?.id ?? null : activeId);
  };
  const send = async () => {
    const text = input.trim(); if ((!text && !attachment) || busy) return;
    const sessionId = activeId ?? crypto.randomUUID(); const now = new Date().toISOString();
    const userMessage: ChatMessage = { id: crypto.randomUUID(), role: 'user', text: text || 'Please analyze this image.', timestamp: now, attachmentUrl: attachment?.preview };
    const prior = sessions.find((session) => session.id === sessionId)?.messages ?? [];
    const pendingMessages = [...prior, userMessage].slice(-HISTORY_LIMIT); const title = prior.length ? active?.title ?? 'Chat' : (text || 'Image analysis').slice(0, 42);
    const pendingSession: ChatSession = { id: sessionId, title, messages: pendingMessages, updatedAt: now };
    commit([pendingSession, ...sessions.filter((session) => session.id !== sessionId)], sessionId);
    const sentAttachment = attachment; setInput(''); setAttachment(null); setBusy(true); setError('');
    const controller = new AbortController(); abortRef.current = controller;
    try {
      const response = await handleChatbotMessage({ query: text, history: pendingMessages.map((message) => ({ role: message.role === 'user' ? 'user' : 'bot', text: message.text })), imageBase64: sentAttachment?.base64, imageMimeType: sentAttachment?.mime }, token, controller.signal);
      const assistant: ChatMessage = { id: crypto.randomUUID(), role: 'assistant', text: response.response, timestamp: new Date().toISOString(), relevantCarIds: response.relevant_car_ids, listingData: response.listing_data, actionType: response.action_type };
      setSessions((current) => {
        const currentSession = current.find((session) => session.id === sessionId) ?? pendingSession;
        const updated = { ...currentSession, messages: [...currentSession.messages, assistant].slice(-HISTORY_LIMIT), updatedAt: assistant.timestamp };
        const next = [updated, ...current.filter((session) => session.id !== sessionId)]; localStorage.setItem(`${STORAGE_KEYS.chatSessions}-${userId}`, JSON.stringify(next)); return next;
      });
    } catch (sendError: unknown) {
      if (!(sendError instanceof DOMException && sendError.name === 'AbortError')) setError(sendError instanceof Error ? sendError.message : 'The assistant could not respond');
    } finally { setBusy(false); abortRef.current = null; }
  };
  const publishDraft = async (draft: ListingDraft, messageId: string, messageIndex: number) => {
    setPublishingId(messageId); setError('');
    try {
      let image = draft.image ?? draft.image_url ?? '';
      const sourceMessage = messages.slice(0, messageIndex).toReversed().find((message) => message.role === 'user' && message.attachmentUrl);
      if (!image && sourceMessage?.attachmentUrl) {
        const blob = await fetch(sourceMessage.attachmentUrl).then((response) => response.blob());
        const upload = await uploadListingImage(new File([blob], 'listing-image.jpg', { type: blob.type }), token); image = upload.url;
      }
      const currentYear = new Date().getFullYear(); const proposedYear = Number(draft.year); const proposedPrice = Number(draft.price);
      const payload: Partial<Car> = {
        make: draft.make || 'Unknown', model: draft.model || 'Unknown', year: proposedYear >= 1900 && proposedYear <= currentYear + 2 ? proposedYear : currentYear,
        price: Number.isFinite(proposedPrice) && proposedPrice >= 0 ? proposedPrice : 0, currency: draft.currency ?? 'JOD', description: draft.description ?? '',
        image, galleryImages: image ? [image] : [], specs: { bodyStyle: draft.bodyStyle, horsepower: draft.horsepower, engine: draft.engine, fuelEconomy: draft.fuelEconomy },
        odometerKm: draft.odometerKm,
      };
      await createListing(payload, token); router.push('/my-listings'); router.refresh();
    } catch (publishError: unknown) { setError(publishError instanceof Error ? publishError.message : 'Unable to create the listing'); }
    finally { setPublishingId(null); }
  };

  return <main className="mx-auto flex min-h-[calc(100vh-72px)] max-w-7xl gap-4 p-4 md:p-8">
    <aside className={`hidden w-72 shrink-0 rounded-2xl border p-3 lg:block ${dark ? 'border-slate-700 bg-slate-900 text-white' : 'border-slate-200 bg-white'}`}><button onClick={newChat} className="w-full rounded-xl bg-indigo-600 px-4 py-3 font-semibold text-white">+ {language === 'ar' ? 'محادثة جديدة' : 'New chat'}</button><div className="mt-3 space-y-1">{sessions.map((session) => <div key={session.id} className="flex items-center gap-1"><button onClick={() => setActiveId(session.id)} className={`min-w-0 flex-1 truncate rounded-lg px-3 py-2 text-start text-sm ${session.id === activeId ? 'bg-indigo-50 text-indigo-700' : ''}`}>{session.title}</button><button aria-label="Delete chat" onClick={() => deleteChat(session.id)} className="rounded p-2 text-rose-500">×</button></div>)}</div></aside>
    <section className={`flex min-w-0 flex-1 flex-col rounded-2xl border ${dark ? 'border-slate-700 bg-slate-900 text-white' : 'border-slate-200 bg-white'}`}>
      <header className="flex flex-wrap items-center justify-between gap-3 border-b border-current/10 p-4"><div><h1 className="text-xl font-bold">{language === 'ar' ? 'مساعد IntelliWheels' : 'IntelliWheels Assistant'}</h1><p className="text-sm opacity-60">{language === 'ar' ? 'اسأل عن السيارات والسوق' : 'Ask about vehicles and the market'}</p></div><div className="flex gap-2 lg:hidden"><select aria-label="Chat history" value={activeId ?? ''} onChange={(event) => setActiveId(event.target.value)} className="max-w-40 rounded-lg border bg-transparent p-2"><option value="">Chat history</option>{sessions.map((session) => <option key={session.id} value={session.id}>{session.title}</option>)}</select><button onClick={newChat} className="rounded-lg bg-indigo-600 px-3 py-2 text-white">+</button></div></header>
      <div className="min-h-96 flex-1 space-y-4 overflow-y-auto p-4 md:p-6">{messages.length ? messages.map((message, messageIndex) => <article key={message.id} className={`flex ${message.role === 'user' ? 'justify-end' : 'justify-start'}`}><div className={`max-w-[85%] rounded-2xl p-4 ${message.role === 'user' ? 'bg-indigo-600 text-white' : dark ? 'bg-slate-800' : 'bg-slate-100'}`}>{message.attachmentUrl ? <Image unoptimized src={message.attachmentUrl} alt="Attached vehicle" width={420} height={240} className="mb-3 max-h-60 rounded-xl object-cover"/> : null}<p className="whitespace-pre-wrap text-sm leading-relaxed">{message.text}</p>{message.relevantCarIds?.length ? <div className="mt-3 flex flex-wrap gap-2">{message.relevantCarIds.map((id) => <Link key={id} href={`/cars/${id}`} className="rounded-lg bg-white/20 px-3 py-1 text-xs font-semibold">View car {id}</Link>)}</div> : null}{message.listingData ? <button type="button" disabled={publishingId === message.id} onClick={() => void publishDraft(message.listingData as ListingDraft, message.id, messageIndex)} className="mt-3 w-full rounded-lg bg-emerald-600 px-3 py-2 text-xs font-semibold text-white disabled:opacity-50">{publishingId === message.id ? 'Creating listing…' : 'Create Listing Now'}</button> : null}</div></article>) : <div className="flex min-h-80 items-center justify-center text-center opacity-60"><p>{language === 'ar' ? 'ابدأ محادثة جديدة واسأل عن أي سيارة.' : 'Start a new chat and ask about any vehicle.'}</p></div>}{busy ? <p aria-live="polite" className="text-sm text-indigo-500">Thinking…</p> : null}{error ? <p role="alert" className="rounded-xl bg-rose-50 p-3 text-sm text-rose-700">{error}</p> : null}</div>
      <footer className="border-t border-current/10 p-4">{attachment ? <div className="mb-3 flex items-center gap-3"><Image unoptimized src={attachment.preview} alt="Selected attachment" width={64} height={64} className="h-16 w-16 rounded-lg object-cover"/><button onClick={() => setAttachment(null)} className="text-sm text-rose-500">Remove</button></div> : null}<div className="flex items-end gap-2"><label className="cursor-pointer rounded-xl border border-current/20 p-3" aria-label="Attach image">📷<input type="file" accept="image/*" className="hidden" onChange={async (event) => { const file = event.target.files?.[0]; if (file) setAttachment(await readAttachment(file)); }}/></label><textarea aria-label="Message" rows={2} value={input} onChange={(event) => setInput(event.target.value)} onKeyDown={(event) => { if (event.key === 'Enter' && !event.shiftKey) { event.preventDefault(); void send(); } }} className={`min-h-12 flex-1 resize-none rounded-xl border p-3 ${dark ? 'border-slate-600 bg-slate-800' : 'border-slate-200 bg-slate-50'}`} placeholder={language === 'ar' ? 'اكتب رسالتك…' : 'Type your message…'}/>{busy ? <button onClick={() => abortRef.current?.abort()} className="rounded-xl bg-rose-600 px-4 py-3 text-white">Stop</button> : <button onClick={() => void send()} disabled={!input.trim() && !attachment} className="rounded-xl bg-indigo-600 px-4 py-3 text-white disabled:opacity-50">Send</button>}</div></footer>
    </section>
  </main>;
}

export function AssistantView() {
  const { user, token, loading, sessionValidated } = useAuth(); const { theme, language } = usePublicPreferences();
  if (loading) return <main className="p-8 text-center text-slate-500">Loading assistant…</main>;
  if (!user || !token || !sessionValidated) return <main className="p-8 text-center"><p className={theme === 'dark' ? 'text-slate-300' : 'text-slate-600'}>{language === 'ar' ? 'سجّل الدخول لاستخدام المساعد.' : 'Sign in to use the assistant.'}</p><Link href="/account" className="mt-4 inline-block rounded-xl bg-indigo-600 px-4 py-2 text-white">Sign In</Link></main>;
  return <AssistantSessionView key={user.id} userId={user.id} token={token}/>;
}
