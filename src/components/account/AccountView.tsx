'use client';

import { useCallback, useEffect, useState, type FormEvent } from 'react';
import { useRouter, useSearchParams } from 'next/navigation';
import { useAuth } from '@/context/AuthContext';
import { getOAuthConfig } from '@/lib/api';
import { usePublicPreferences } from '@/components/public/PublicRouteShell';

type AuthMode = 'login' | 'signup' | 'forgot';

export function AccountView() {
  const router = useRouter();
  const searchParams = useSearchParams();
  const resetToken = searchParams.get('reset_token');
  const { theme, language } = usePublicPreferences();
  const { user, loading, error, login, signup, loginWithGoogle, requestPasswordReset, resetUserPassword, logout, refreshProfile, updateMyProfile, clearError } = useAuth();
  // Reset mode belongs to the URL, not remembered local state. Removing the
  // token (including with Back/Forward) must reveal the normal account form.
  const [mode, setMode] = useState<AuthMode>('login');
  const [googleClientId, setGoogleClientId] = useState<string | null>(null);
  const [notice, setNotice] = useState<string | null>(null);
  const dark = theme === 'dark';
  const fieldClass = `w-full rounded-2xl border p-3 ${dark ? 'border-slate-600 bg-slate-700 text-white' : 'border-slate-200 bg-slate-50 text-slate-900'}`;
  const copy = language === 'ar' ? {
    title: 'الحساب', signIn: 'تسجيل الدخول', signUp: 'إنشاء حساب', username: 'اسم المستخدم', email: 'البريد الإلكتروني', password: 'كلمة المرور', forgot: 'نسيت كلمة المرور؟', sendReset: 'إرسال رابط الاستعادة', back: 'العودة لتسجيل الدخول', reset: 'إعادة تعيين كلمة المرور', confirm: 'تأكيد كلمة المرور', profile: 'الملف الشخصي', update: 'تحديث الملف الشخصي', refresh: 'تحديث البيانات', signOut: 'تسجيل الخروج', phone: 'رقم الهاتف', currentPassword: 'كلمة المرور الحالية', newPassword: 'كلمة المرور الجديدة', google: 'المتابعة باستخدام Google',
  } : {
    title: 'Account', signIn: 'Sign In', signUp: 'Create Account', username: 'Username', email: 'Email', password: 'Password', forgot: 'Forgot password?', sendReset: 'Send Reset Link', back: 'Back to Sign In', reset: 'Reset Password', confirm: 'Confirm Password', profile: 'Profile', update: 'Update Profile', refresh: 'Refresh Profile', signOut: 'Sign Out', phone: 'Phone', currentPassword: 'Current Password', newPassword: 'New Password', google: 'Continue with Google',
  };

  useEffect(() => {
    getOAuthConfig().then((config) => {
      if (config.google.enabled && config.google.client_id) setGoogleClientId(config.google.client_id);
    }).catch(() => setGoogleClientId(null));
  }, []);

  const showNotice = useCallback((message: string) => {
    setNotice(message);
    window.setTimeout(() => setNotice(null), 4000);
  }, []);

  const handleGoogleSignIn = useCallback(async () => {
    if (!googleClientId) return;
    if (!window.google?.accounts?.id) {
      await new Promise<void>((resolve, reject) => {
        const script = document.createElement('script');
        script.src = 'https://accounts.google.com/gsi/client';
        script.async = true;
        script.defer = true;
        script.onload = () => resolve();
        script.onerror = () => reject(new Error('Failed to load Google Sign-In'));
        document.head.appendChild(script);
      }).catch((loadError: unknown) => showNotice(loadError instanceof Error ? loadError.message : 'Failed to load Google Sign-In'));
    }
    if (!window.google?.accounts?.id) return;
    window.google.accounts.id.initialize({
      client_id: googleClientId,
      callback: async ({ credential }: { credential: string }) => {
        if (await loginWithGoogle(credential)) showNotice('Signed in with Google.');
      },
    });
    window.google.accounts.id.prompt();
  }, [googleClientId, loginWithGoogle, showNotice]);

  if (loading) return <main className="p-8 text-center text-slate-500" aria-live="polite">{language === 'ar' ? 'جارٍ تحميل الحساب…' : 'Loading account…'}</main>;

  const panelClass = `rounded-3xl border p-6 shadow-sm ${dark ? 'border-slate-700 bg-slate-800 text-white' : 'border-slate-100 bg-white text-slate-900'}`;
  const activeMode = resetToken ? 'reset' : mode;

  if (user) {
    return (
      <main className="mx-auto grid max-w-5xl gap-6 p-4 md:grid-cols-2 md:p-8">
        {error ? <p className="rounded-2xl bg-rose-50 p-3 text-rose-700 md:col-span-2" role="alert">{error}</p> : null}
        <section className={panelClass}>
          <h1 className="text-xl font-semibold">{copy.profile}</h1>
          <dl className="mt-4 space-y-2 text-sm">
            <div><dt className="font-medium">{copy.username}</dt><dd>{user.username}</dd></div>
            <div><dt className="font-medium">{copy.email}</dt><dd>{user.email}</dd></div>
            {user.phone ? <div><dt className="font-medium">{copy.phone}</dt><dd>{user.phone}</dd></div> : null}
          </dl>
          <button type="button" className="mt-4 rounded-xl border px-4 py-2" onClick={() => void refreshProfile()}>{copy.refresh}</button>
        </section>
        <section className={panelClass}>
          <h2 className="text-xl font-semibold">{copy.update}</h2>
          <form className="mt-4 space-y-3" onSubmit={async (event: FormEvent<HTMLFormElement>) => {
            event.preventDefault();
            const data = new FormData(event.currentTarget);
            const success = await updateMyProfile({ username: data.get('username')?.toString(), email: data.get('email')?.toString(), phone: data.get('phone')?.toString(), current_password: data.get('current-password')?.toString(), password: data.get('new-password')?.toString() });
            if (success) showNotice('Profile updated successfully.');
          }}>
            <label className="block text-sm">{copy.username}<input className={`${fieldClass} mt-1`} name="username" defaultValue={user.username} /></label>
            <label className="block text-sm">{copy.email}<input className={`${fieldClass} mt-1`} name="email" type="email" defaultValue={user.email} /></label>
            <label className="block text-sm">{copy.phone}<input className={`${fieldClass} mt-1`} name="phone" type="tel" defaultValue={user.phone || ''} /></label>
            <label className="block text-sm">{copy.currentPassword}<input className={`${fieldClass} mt-1`} name="current-password" type="password" /></label>
            <label className="block text-sm">{copy.newPassword}<input className={`${fieldClass} mt-1`} name="new-password" type="password" /></label>
            <button type="submit" className="w-full rounded-2xl bg-emerald-500 py-3 font-semibold text-white">{copy.update}</button>
          </form>
          <button type="button" className="mt-4 w-full rounded-2xl border py-2 font-semibold" onClick={() => void logout()}>{copy.signOut}</button>
        </section>
        {notice ? <p className="md:col-span-2" role="status">{notice}</p> : null}
      </main>
    );
  }

  const submitLogin = async (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault(); clearError(); const data = new FormData(event.currentTarget);
    if (await login(String(data.get('username')), String(data.get('password')))) showNotice('Signed in successfully.');
  };
  const submitSignup = async (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault(); clearError(); const data = new FormData(event.currentTarget);
    if (await signup(String(data.get('username')), String(data.get('email')), String(data.get('password')))) showNotice('Account created successfully.');
  };

  return (
    <main className="mx-auto max-w-5xl p-4 md:p-8">
      <h1 className={`mb-6 text-3xl font-bold ${dark ? 'text-white' : 'text-slate-900'}`}>{copy.title}</h1>
      {error ? <p className="mb-4 rounded-2xl bg-rose-50 p-3 text-rose-700" role="alert">{error}</p> : null}
      {notice ? <p className="mb-4 rounded-2xl bg-emerald-50 p-3 text-emerald-700" role="status">{notice}</p> : null}
      {activeMode === 'forgot' ? <section className={`mx-auto max-w-md ${panelClass}`}><h2 className="text-xl font-semibold">{copy.forgot}</h2><form className="mt-4 space-y-4" onSubmit={async (event) => { event.preventDefault(); const data = new FormData(event.currentTarget); const result = await requestPasswordReset(String(data.get('email'))); showNotice(result.message || 'If an account exists, a reset link has been sent.'); if (result.success) setMode('login'); }}><label className="block text-sm">{copy.email}<input className={`${fieldClass} mt-1`} name="email" type="email" required /></label><button className="w-full rounded-2xl bg-sky-600 py-3 font-semibold text-white" type="submit">{copy.sendReset}</button></form><button type="button" className="mt-4 text-sky-600" onClick={() => setMode('login')}>{copy.back}</button></section> : null}
      {activeMode === 'reset' && resetToken ? <section className={`mx-auto max-w-md ${panelClass}`}><h2 className="text-xl font-semibold">{copy.reset}</h2><form className="mt-4 space-y-4" onSubmit={async (event) => { event.preventDefault(); const data = new FormData(event.currentTarget); const password = String(data.get('password')); if (password !== String(data.get('confirm-password'))) { showNotice('Passwords do not match.'); return; } const result = await resetUserPassword(resetToken, password); showNotice(result.message || (result.success ? 'Password reset successfully.' : 'Password reset failed.')); if (result.success) { setMode('login'); router.replace('/account'); } }}><label className="block text-sm">{copy.newPassword}<input className={`${fieldClass} mt-1`} name="password" type="password" minLength={8} required /></label><label className="block text-sm">{copy.confirm}<input className={`${fieldClass} mt-1`} name="confirm-password" type="password" minLength={8} required /></label><button className="w-full rounded-2xl bg-sky-600 py-3 font-semibold text-white" type="submit">{copy.reset}</button></form></section> : null}
      {activeMode === 'login' || activeMode === 'signup' ? <div className="grid gap-6 md:grid-cols-2"><section className={panelClass}><h2 className="text-xl font-semibold">{copy.signIn}</h2><form className="mt-4 space-y-4" onSubmit={submitLogin}><label className="block text-sm">{copy.username}<input className={`${fieldClass} mt-1`} name="username" autoComplete="username" required /></label><label className="block text-sm">{copy.password}<input className={`${fieldClass} mt-1`} name="password" type="password" autoComplete="current-password" required /></label><button type="submit" className="w-full rounded-2xl bg-sky-600 py-3 font-semibold text-white">{copy.signIn}</button></form><button type="button" className="mt-3 text-sky-600" onClick={() => setMode('forgot')}>{copy.forgot}</button>{googleClientId ? <button type="button" className="mt-4 w-full rounded-2xl border py-3" onClick={() => void handleGoogleSignIn()}>{copy.google}</button> : null}</section><section className={panelClass}><h2 className="text-xl font-semibold">{copy.signUp}</h2><form className="mt-4 space-y-4" onSubmit={submitSignup}><label className="block text-sm">{copy.username}<input className={`${fieldClass} mt-1`} name="username" autoComplete="username" required /></label><label className="block text-sm">{copy.email}<input className={`${fieldClass} mt-1`} name="email" type="email" autoComplete="email" required /></label><label className="block text-sm">{copy.password}<input className={`${fieldClass} mt-1`} name="password" type="password" autoComplete="new-password" minLength={8} required /></label><button type="submit" className="w-full rounded-2xl bg-emerald-500 py-3 font-semibold text-white">{copy.signUp}</button></form></section></div> : null}
    </main>
  );
}
