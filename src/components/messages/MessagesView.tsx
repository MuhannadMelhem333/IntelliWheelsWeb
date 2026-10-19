'use client';

import Link from 'next/link';
import { useEffect, useState, type FormEvent } from 'react';
import { fetchConversations, fetchMessages, sendMessage, type Conversation } from '@/lib/api';
import { messagesForConversation, type MessageThread } from '@/lib/messageThread';
import { useAuth } from '@/context/AuthContext';
import { usePublicPreferences } from '@/components/public/PublicRouteShell';
import { RouteErrorState } from '@/components/RouteErrorState';

export function MessagesView() {
  const { token, loading: authLoading, sessionValidated } = useAuth();
  const { theme, language } = usePublicPreferences();
  const [conversations, setConversations] = useState<Conversation[]>([]);
  const [activeId, setActiveId] = useState<number | null>(null);
  const [thread, setThread] = useState<MessageThread | null>(null);
  const [loading, setLoading] = useState(true);
  const [sending, setSending] = useState(false);
  const [error, setError] = useState('');
  const [retryKey, setRetryKey] = useState(0);
  const dark = theme === 'dark';
  const active = conversations.find((conversation) => conversation.id === activeId) ?? null;
  const messages = messagesForConversation(thread, activeId);

  useEffect(() => {
    if (authLoading || !sessionValidated || !token) return;
    let live = true;
    fetchConversations(token).then((response) => {
      if (!live) return;
      setConversations(response.conversations || []);
      setActiveId((current) => current ?? response.conversations?.[0]?.id ?? null);
      setError('');
    }).catch((loadError: unknown) => {
      if (live) setError(loadError instanceof Error ? loadError.message : 'Unable to load conversations');
    }).finally(() => { if (live) setLoading(false); });
    return () => { live = false; };
  }, [authLoading, retryKey, sessionValidated, token]);

  useEffect(() => {
    if (!activeId || !token || !sessionValidated) return;
    let live = true;
    fetchMessages(activeId, token).then((response) => {
      if (live) { setThread({ conversationId: activeId, messages: response.messages || [] }); setError(''); }
    }).catch((loadError: unknown) => {
      if (live) setError(loadError instanceof Error ? loadError.message : 'Unable to load messages');
    });
    return () => { live = false; };
  }, [activeId, retryKey, sessionValidated, token]);

  if (authLoading) return <main className="p-8 text-center text-slate-500" aria-live="polite">{language === 'ar' ? 'جارٍ تحميل الرسائل…' : 'Loading messages…'}</main>;
  if (!token || !sessionValidated) return <main className="p-8 text-center"><p className={dark ? 'text-slate-300' : 'text-slate-600'}>{language === 'ar' ? 'سجّل الدخول للوصول إلى رسائلك.' : 'Sign in to access your messages.'}</p><Link href="/account" className="mt-4 inline-block rounded-xl bg-indigo-600 px-4 py-2 font-semibold text-white">{language === 'ar' ? 'تسجيل الدخول' : 'Sign In'}</Link></main>;
  if (loading) return <main className="p-8 text-center text-slate-500" aria-live="polite">{language === 'ar' ? 'جارٍ تحميل الرسائل…' : 'Loading messages…'}</main>;
  if (error) return <RouteErrorState message={error} retryLabel={language === 'ar' ? 'حاول مجدداً' : 'Try again'} onRetry={() => { setLoading(true); setError(''); setRetryKey((key) => key + 1); }} />;

  const handleSubmit = async (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    if (!active || !token || sending || messages === null) return;
    const form = event.currentTarget;
    const data = new FormData(form);
    const content = String(data.get('message') || '').trim();
    if (!content) return;
    setSending(true);
    try {
      await sendMessage(active.other_user_id, content, active.listing_id, token);
      const response = await fetchMessages(active.id, token);
      setThread({ conversationId: active.id, messages: response.messages || [] });
      form.reset();
    } catch (sendError: unknown) {
      setError(sendError instanceof Error ? sendError.message : 'Unable to send message');
    } finally {
      setSending(false);
    }
  };

  return (
    <main className="mx-auto max-w-7xl p-4 md:p-8">
      <h1 className={`mb-4 text-3xl font-bold ${dark ? 'text-white' : 'text-slate-900'}`}>{language === 'ar' ? 'الرسائل' : 'Messages'}</h1>
      <div className="flex min-h-[600px] flex-col gap-4 md:flex-row">
        <section className={`w-full overflow-hidden rounded-2xl border md:w-1/3 ${dark ? 'border-slate-700 bg-slate-800' : 'border-slate-200 bg-white'}`} aria-label={language === 'ar' ? 'المحادثات' : 'Conversations'}>
          <h2 className={`border-b p-4 text-lg font-bold ${dark ? 'border-slate-700 text-white' : 'border-slate-200 text-slate-900'}`}>{language === 'ar' ? 'المحادثات' : 'Conversations'}</h2>
          {conversations.length ? conversations.map((conversation) => <button type="button" key={conversation.id} disabled={sending} onClick={() => setActiveId(conversation.id)} className={`block w-full border-b p-4 text-start ${activeId === conversation.id ? 'bg-indigo-600 text-white' : dark ? 'border-slate-700 text-slate-200' : 'border-slate-100 text-slate-800'}`}><span className="block font-semibold">{conversation.other_username}</span><span className="block truncate text-sm opacity-75">{conversation.listing_title || conversation.last_message || 'Conversation'}</span>{conversation.unread_count > 0 ? <span className="mt-1 inline-block rounded-full bg-rose-500 px-2 py-0.5 text-xs text-white">{conversation.unread_count}</span> : null}</button>) : <p className="p-4 text-center text-slate-500">{language === 'ar' ? 'لا توجد محادثات بعد.' : 'No conversations yet.'}</p>}
        </section>
        <section className={`flex min-h-[420px] flex-1 flex-col overflow-hidden rounded-2xl border ${dark ? 'border-slate-700 bg-slate-800' : 'border-slate-200 bg-white'}`} aria-label={language === 'ar' ? 'المحادثة الحالية' : 'Active conversation'}>
          {active ? <><header className={`border-b p-4 ${dark ? 'border-slate-700 text-white' : 'border-slate-200 text-slate-900'}`}><h2 className="font-bold">{active.other_username}</h2>{active.listing_title ? <p className="text-sm opacity-70">{active.listing_title}</p> : null}</header><div className="flex-1 space-y-3 overflow-y-auto p-4" aria-live="polite">{messages === null ? <p role="status">{language === 'ar' ? 'جارٍ تحميل المحادثة…' : 'Loading conversation…'}</p> : messages.map((message) => <div key={message.id} className={`max-w-[80%] rounded-2xl px-4 py-2 ${message.is_mine ? 'ms-auto bg-indigo-600 text-white' : dark ? 'bg-slate-700 text-slate-100' : 'bg-slate-100 text-slate-900'}`}><p>{message.content}</p><time className="text-xs opacity-70">{new Date(message.created_at).toLocaleString()}</time></div>)}</div><form key={active.id} className={`flex gap-2 border-t p-4 ${dark ? 'border-slate-700' : 'border-slate-200'}`} onSubmit={handleSubmit}><label className="sr-only" htmlFor="message-content">{language === 'ar' ? 'الرسالة' : 'Message'}</label><input id="message-content" name="message" className={`min-w-0 flex-1 rounded-xl border px-3 py-2 ${dark ? 'border-slate-600 bg-slate-700 text-white' : 'border-slate-200'}`} autoComplete="off" required /><button type="submit" disabled={sending || messages === null} className="rounded-xl bg-indigo-600 px-4 py-2 font-semibold text-white disabled:opacity-50">{sending ? (language === 'ar' ? 'جارٍ الإرسال…' : 'Sending…') : language === 'ar' ? 'إرسال' : 'Send'}</button></form></> : <p className="m-auto text-slate-500">{language === 'ar' ? 'اختر محادثة.' : 'Select a conversation.'}</p>}
        </section>
      </div>
    </main>
  );
}
