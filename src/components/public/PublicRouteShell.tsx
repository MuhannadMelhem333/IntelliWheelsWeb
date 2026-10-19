'use client';

import { usePathname, useRouter } from 'next/navigation';
import { createContext, useContext, useEffect, useState } from 'react';
import { CURRENCY_RATES, STORAGE_KEYS, type CurrencyCode } from '@/lib/config';
import { useAuth } from '@/context/AuthContext';
import { fetchUnreadCount } from '@/lib/api';
import { useStoredPreference } from './useStoredPreference';
import { AppFooter } from '@/components/layout/AppFooter';
import { PublicHeader } from './PublicHeader';

type ServiceMode = 'marketplace' | 'dealer' | 'insights';
type PublicPreferences = { theme: 'light' | 'dark'; language: 'en' | 'ar'; serviceMode: ServiceMode };
const themes = ['light', 'dark'] as const;
const languages = ['en', 'ar'] as const;
const serviceModes = ['marketplace', 'dealer', 'insights'] as const;

const PublicPreferencesContext = createContext<PublicPreferences>({ theme: 'light', language: 'en', serviceMode: 'marketplace' });
export const usePublicPreferences = () => useContext(PublicPreferencesContext);

export function PublicRouteShell({ children }: { children: React.ReactNode }) {
  const router = useRouter();
  const pathname = usePathname();
  const { currency, setCurrency, user, token, sessionValidated } = useAuth();
  const [theme, setTheme] = useStoredPreference(STORAGE_KEYS.theme, themes, 'light');
  const [language, setLanguage] = useStoredPreference(STORAGE_KEYS.language, languages, 'en');
  const [serviceMode, setServiceMode] = useStoredPreference(STORAGE_KEYS.serviceMode, serviceModes, 'marketplace');
  const [unreadCount, setUnreadCount] = useState(0);
  const [mobileOpen, setMobileOpen] = useState(false);

  useEffect(() => {
    document.documentElement.lang = language;
    document.documentElement.dir = language === 'ar' ? 'rtl' : 'ltr';
  }, [language]);

  useEffect(() => {
    document.documentElement.dataset.theme = theme;
    document.documentElement.style.colorScheme = theme;
  }, [theme]);

  useEffect(() => {
    if (!user || !token || !sessionValidated) return;
    let live = true;
    fetchUnreadCount(token).then((response) => { if (live) setUnreadCount(response.unread_count ?? 0); }).catch(() => undefined);
    return () => { live = false; };
  }, [sessionValidated, token, user]);

  const updateTheme = (next: 'light' | 'dark') => {
    setTheme(next);
  };
  const updateServiceMode = (next: ServiceMode) => {
    setServiceMode(next);
    router.push(next === 'dealer' ? '/dealers' : next === 'insights' ? '/assistant' : '/');
    setMobileOpen(false);
  };

  const links = [
    { href: '/', label: language === 'ar' ? 'الرئيسية' : 'Home' },
    { href: '/listings', label: language === 'ar' ? 'السيارات' : 'Listings' },
    { href: '/dealers', label: language === 'ar' ? 'الوكلاء' : 'Dealers' },
    ...(user ? [{ href: '/favorites', label: language === 'ar' ? 'المفضلة' : 'Favorites' }] : []),
    ...(user ? [{ href: '/messages', label: `${language === 'ar' ? 'الرسائل' : 'Messages'}${unreadCount ? ` (${unreadCount})` : ''}` }] : []),
    ...(user ? [{ href: '/my-listings', label: language === 'ar' ? 'إعلاناتي' : 'My Listings' }] : []),
    ...(user ? [{ href: '/assistant', label: language === 'ar' ? 'المساعد' : 'Assistant' }] : []),
    ...(user ? [{ href: '/analytics', label: language === 'ar' ? 'التحليلات' : 'Analytics' }] : []),
    ...(user?.is_admin ? [{ href: '/admin', label: language === 'ar' ? 'الإدارة' : 'Admin' }] : []),
    { href: '/account', label: user ? (language === 'ar' ? 'حسابي' : 'Account') : (language === 'ar' ? 'تسجيل الدخول' : 'Sign In') },
  ];

  const preferenceControls = (
    <div className="iw-preferences">
      <button type="button" onClick={() => setLanguage(language === 'en' ? 'ar' : 'en')} aria-label={language === 'en' ? 'Switch to Arabic' : 'التبديل إلى الإنجليزية'}>
        {language === 'en' ? 'العربية' : 'English'}
      </button>
      <button type="button" onClick={() => updateTheme(theme === 'dark' ? 'light' : 'dark')} aria-label={language === 'ar' ? (theme === 'dark' ? 'استخدام المظهر الفاتح' : 'استخدام المظهر الداكن') : (theme === 'dark' ? 'Use light theme' : 'Use dark theme')}>
        {theme === 'dark' ? '☀' : '☾'}
      </button>
      <select value={currency} onChange={(event) => setCurrency(event.target.value as CurrencyCode)} aria-label={language === 'ar' ? 'العملة' : 'Currency'}>
        {(Object.keys(CURRENCY_RATES) as CurrencyCode[]).map((code) => <option key={code} value={code}>{code}</option>)}
      </select>
      <select value={serviceMode} onChange={(event) => updateServiceMode(event.target.value as ServiceMode)} aria-label={language === 'ar' ? 'وضع الخدمة' : 'Service mode'}>
        <option value="marketplace">{language === 'ar' ? 'السوق' : 'Marketplace'}</option>
        <option value="dealer">{language === 'ar' ? 'الوكلاء' : 'Dealers'}</option>
        <option value="insights">{language === 'ar' ? 'الرؤى' : 'Insights'}</option>
      </select>
    </div>
  );

  return (
    <PublicPreferencesContext.Provider value={{ theme, language, serviceMode }}>
      <div data-theme={theme} dir={language === 'ar' ? 'rtl' : 'ltr'} className="iw-app">
        <a className="iw-skip" href="#public-content">{language === 'ar' ? 'انتقل إلى المحتوى' : 'Skip to content'}</a>
        <PublicHeader theme={theme} language={language} pathname={pathname} links={links} preferences={preferenceControls} mobileOpen={mobileOpen} onToggleMenu={() => setMobileOpen((open) => !open)} onNavigate={() => setMobileOpen(false)} />
        <div id="public-content" tabIndex={-1}>{children}</div>
        <AppFooter theme={theme} language={language} year={new Date().getFullYear()} />
      </div>
    </PublicPreferencesContext.Provider>
  );
}
