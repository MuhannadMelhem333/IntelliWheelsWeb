'use client';

import { RouteErrorState } from '@/components/RouteErrorState';
import { useStoredPreference } from '@/components/public/useStoredPreference';
import { STORAGE_KEYS } from '@/lib/config';
import { listingsCopy } from '@/lib/listingsCopy';

const languages = ['en', 'ar'] as const;
const themes = ['light', 'dark'] as const;

/** Route boundaries render outside the page's provider; reuse its storage hook. */
export function ListingsRouteFeedback({ onRetry }: { onRetry?: () => void }) {
  const [language] = useStoredPreference(STORAGE_KEYS.language, languages, 'en');
  const [theme] = useStoredPreference(STORAGE_KEYS.theme, themes, 'light');
  const copy = listingsCopy[language];
  return <div className="iw-app" data-theme={theme} lang={language} dir={language === 'ar' ? 'rtl' : 'ltr'}>
    {onRetry ? <RouteErrorState message={copy['Unable to load listings']} retryLabel={copy['Try again']} onRetry={onRetry}/> : <main className="p-8 text-center" role="status">{copy['Loading listings…']}</main>}
  </div>;
}
