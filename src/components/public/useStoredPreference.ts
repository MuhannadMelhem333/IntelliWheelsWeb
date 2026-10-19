'use client';

import { useCallback, useState, useSyncExternalStore } from 'react';

const preferenceEvent = 'intelliwheels-preference-change';
function subscribe(notify: () => void) {
  window.addEventListener('storage', notify);
  window.addEventListener(preferenceEvent, notify);
  return () => {
    window.removeEventListener('storage', notify);
    window.removeEventListener(preferenceEvent, notify);
  };
}

/** Stable SSR defaults; restore browser preferences after hydration, not during it. */
export function useStoredPreference<T extends string>(key: string, allowed: readonly T[], defaultValue: T) {
  const [fallback, setFallback] = useState(defaultValue);
  const getSnapshot = useCallback(() => {
    try {
      const value = localStorage.getItem(key);
      return allowed.includes(value as T) ? value as T : fallback;
    } catch { return fallback; }
  }, [allowed, fallback, key]);
  const value = useSyncExternalStore(subscribe, getSnapshot, () => defaultValue);
  const setValue = useCallback((next: T) => {
    setFallback(next);
    try { localStorage.setItem(key, next); } catch { /* Preferences still work without storage. */ }
    window.dispatchEvent(new Event(preferenceEvent));
  }, [key]);
  return [value, setValue] as const;
}
