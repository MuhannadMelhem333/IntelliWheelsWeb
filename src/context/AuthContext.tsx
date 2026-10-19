'use client';

import { createContext, useCallback, useContext, useEffect, useMemo, useRef, useState } from 'react';
import { STORAGE_KEYS, CurrencyCode, CURRENCY_RATES, COOKIE_AUTH_ENABLED, convertCurrency as convertCurrencyUtil, formatPrice as formatPriceUtil } from '@/lib/config';
import { getCookieSessionVersion, getCookieSessionRevision, setCookieSessionVersion, announceCookieSessionChange, cookieSessionChangeKey } from '@/lib/cookieSession';
import { getProfile, loginUser, logoutUser, signupUser, updateProfile, verifySession, googleAuth, forgotPassword, resetPassword } from '@/lib/api';
import { UserProfile } from '@/lib/types';
import { shouldInvalidateSession, subscribeToSessionRejection } from '@/lib/sessionEvents';
import { logoutSession } from '@/lib/logoutSession';

interface AuthContextValue {
  user: UserProfile | null;
  // In cookie mode this is a non-secret session version for legacy UI props.
  token: string | null;
  loading: boolean;
  sessionValidated: boolean;
  error: string | null;
  login: (username: string, password: string) => Promise<boolean>;
  signup: (username: string, email: string, password: string) => Promise<boolean>;
  loginWithGoogle: (credential: string) => Promise<boolean>;
  requestPasswordReset: (email: string) => Promise<{ success: boolean; message?: string }>;
  resetUserPassword: (token: string, password: string) => Promise<{ success: boolean; message?: string }>;
  logout: () => Promise<void>;
  refreshProfile: () => Promise<UserProfile | null>;
  updateMyProfile: (payload: Partial<UserProfile> & { password?: string; current_password?: string }) => Promise<boolean>;
  clearError: () => void;
  // Currency support
  currency: CurrencyCode;
  setCurrency: (currency: CurrencyCode) => void;
  formatPrice: (value: number | undefined | null, sourceCurrency?: CurrencyCode) => string;
  convertCurrency: (amount: number, from: CurrencyCode, to?: CurrencyCode) => number;
}

const AuthContext = createContext<AuthContextValue | undefined>(undefined);
const errorMessage = (error: unknown, fallback: string) => error instanceof Error ? error.message : fallback;

export const AuthProvider = ({ children }: { children: React.ReactNode }) => {
  const [user, setUser] = useState<UserProfile | null>(null);
  const [token, setToken] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);
  const [sessionValidated, setSessionValidated] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [currency, setCurrencyState] = useState<CurrencyCode>('JOD');

  // Load persisted currency preference
  useEffect(() => {
    const storedCurrency = typeof window !== 'undefined' ? localStorage.getItem(STORAGE_KEYS.currency) : null;
    if (storedCurrency && Object.keys(CURRENCY_RATES).includes(storedCurrency)) {
      setCurrencyState(storedCurrency as CurrencyCode);
    }
  }, []);

  const setCurrency = useCallback((newCurrency: CurrencyCode) => {
    setCurrencyState(newCurrency);
    if (typeof window !== 'undefined') {
      localStorage.setItem(STORAGE_KEYS.currency, newCurrency);
    }
  }, []);

  const formatPrice = useCallback(
    (value: number | undefined | null, sourceCurrency: CurrencyCode = 'JOD') => {
      return formatPriceUtil(value, sourceCurrency, currency);
    },
    [currency]
  );

  const convertCurrency = useCallback(
    (amount: number, from: CurrencyCode, to?: CurrencyCode) => {
      return convertCurrencyUtil(amount, from, to ?? currency);
    },
    [currency]
  );

  // Track if we've done the initial localStorage check
  const [initialCheckDone, setInitialCheckDone] = useState(false);
  const [verificationRevision, setVerificationRevision] = useState(0);
  
  // Use a ref to track "skip validation" - this prevents stale closure issues
  // When we just logged in, we don't need to re-validate the fresh token
  const skipNextValidation = useRef(false);

  const clearLocalAuth = useCallback(() => {
    if (COOKIE_AUTH_ENABLED) setCookieSessionVersion(null);
    skipNextValidation.current = false;
    setToken(null);
    setUser(null);
    setSessionValidated(false);
    localStorage.removeItem(STORAGE_KEYS.token);
    localStorage.removeItem(STORAGE_KEYS.user);
  }, []);

  useEffect(() => {
    if (!COOKIE_AUTH_ENABLED) return;
    const recheck = () => {
      clearLocalAuth();
      setLoading(true);
      setVerificationRevision(value => value + 1);
    };
    const onStorage = (event: StorageEvent) => {
      if (event.key === cookieSessionChangeKey) recheck();
    };
    window.addEventListener('focus', recheck);
    window.addEventListener('storage', onStorage);
    return () => {
      window.removeEventListener('focus', recheck);
      window.removeEventListener('storage', onStorage);
    };
  }, [clearLocalAuth]);

  useEffect(() => subscribeToSessionRejection((rejectedToken) => {
    // Check persisted identity too: login may have stored a replacement token
    // before React commits its new state and updates this subscription.
    if (shouldInvalidateSession(token, rejectedToken) &&
        shouldInvalidateSession(COOKIE_AUTH_ENABLED ? getCookieSessionVersion() : localStorage.getItem(STORAGE_KEYS.token), rejectedToken)) {
      clearLocalAuth();
      setLoading(false);
    }
  }), [token, clearLocalAuth]);

  useEffect(() => {
    if (COOKIE_AUTH_ENABLED) {
      for (const key of [STORAGE_KEYS.token, STORAGE_KEYS.user, 'token', 'authToken']) localStorage.removeItem(key);
    }
    const storedToken = !COOKIE_AUTH_ENABLED && typeof window !== 'undefined' ? localStorage.getItem(STORAGE_KEYS.token) : null;

    if (storedToken) {
      setToken(storedToken);
      // A cached profile is not proof of an active server session. Keep it in
      // storage until verification succeeds so private UI is never enabled by
      // a stale profile while the API is unavailable.
    } else {
      // No stored token - we're done loading
      if (!COOKIE_AUTH_ENABLED) setLoading(false);
    }
    setInitialCheckDone(true);
  }, []);

  useEffect(() => {
    // Don't run until initial localStorage check is complete
    if (!initialCheckDone) {
      return;
    }
    // Skip validation if we just authenticated (ref avoids stale closure issues)
    if (skipNextValidation.current) {
      skipNextValidation.current = false;
      setSessionValidated(true);
      setLoading(false);
      return;
    }
    let live = true;
    const controller = new AbortController();
    const startedAt = getCookieSessionRevision();
    const isCurrentRequest = () => live && (COOKIE_AUTH_ENABLED
      ? startedAt === getCookieSessionRevision()
      : localStorage.getItem(STORAGE_KEYS.token) === token);
    async function validateSession() {
      if (!token && !COOKIE_AUTH_ENABLED) {
        // No token after initial check means guest user
        setSessionValidated(false);
        setLoading(false);
        return;
      }

      const timeoutId = setTimeout(() => controller.abort(), 15000);
      try {
        // A timeout leaves the session unverified and returns the app to guest state.
        const response = await verifySession(token, controller.signal);
        if (!isCurrentRequest()) return;
        if (response.success && response.authenticated && (!COOKIE_AUTH_ENABLED || response.sessionVersion)) {
          if (response.user) {
            setUser(response.user);
            if (!COOKIE_AUTH_ENABLED) localStorage.setItem(STORAGE_KEYS.user, JSON.stringify(response.user));
          }
          if (COOKIE_AUTH_ENABLED && response.sessionVersion) {
            setCookieSessionVersion(response.sessionVersion);
            skipNextValidation.current = true;
            setToken(response.sessionVersion);
          }
          setSessionValidated(true);
        } else {
          // Token is invalid/expired - silently logout
          setSessionValidated(false);
          clearLocalAuth();
        }
      } catch (err) {
        if (!isCurrentRequest()) return;
        console.error('[Auth] Validation error:', err);
        setSessionValidated(false);
        clearLocalAuth();
      } finally {
        clearTimeout(timeoutId);
        if (live) setLoading(false);
      }
    }
    validateSession();
    return () => { live = false; controller.abort(); };
  }, [token, initialCheckDone, clearLocalAuth, verificationRevision]);

  const persistAuth = useCallback((authToken: string, profile: UserProfile) => {
    // Mark to skip the next validation - we know the token is valid (just received from server)
    skipNextValidation.current = true;
    setSessionValidated(true);
    setToken(authToken);
    setUser(profile);
    if (COOKIE_AUTH_ENABLED) {
      setCookieSessionVersion(authToken);
      announceCookieSessionChange();
    } else {
      localStorage.setItem(STORAGE_KEYS.token, authToken);
      localStorage.setItem(STORAGE_KEYS.user, JSON.stringify(profile));
    }
  }, []);

  const fetchProfileForToken = useCallback(async (authToken: string, fallback?: UserProfile | null) => {
    if (fallback) return fallback;
    try {
      const result = await getProfile(authToken);
      if (result.success) {
        return result.user;
      }
    } catch (err) {
      console.warn('Unable to load profile after auth', err);
    }
    return null;
  }, []);

  const handleLogin = useCallback(async (username: string, password: string) => {
    try {
      setLoading(true);
      setError(null);
      const response = await loginUser(username, password);
      const identity = COOKIE_AUTH_ENABLED ? response.sessionVersion : response.token;
      if (response.success && identity) {
        const profile = await fetchProfileForToken(identity, response.user);
        if (!profile) {
          setError('Unable to load profile details');
          return false;
        }
        persistAuth(identity, profile);
        return true;
      }
      setError(response.error || 'Unable to login');
      return false;
    } catch (err: unknown) {
      console.error('[Auth] Login error:', err);
      setError(errorMessage(err, 'Unable to login'));
      return false;
    } finally {
      setLoading(false);
    }
  }, [persistAuth, fetchProfileForToken]);

  const handleSignup = useCallback(async (username: string, email: string, password: string) => {
    try {
      setLoading(true);
      setError(null);
      const response = await signupUser(username, email, password);
      const identity = COOKIE_AUTH_ENABLED ? response.sessionVersion : response.token;
      if (response.success && identity) {
        const profile = await fetchProfileForToken(identity, response.user);
        if (!profile) {
          setError('Unable to load profile details');
          return false;
        }
        persistAuth(identity, profile);
        return true;
      }
      setError(response.error || 'Unable to sign up');
      return false;
    } catch (err: unknown) {
      setError(errorMessage(err, 'Unable to sign up'));
      return false;
    } finally {
      setLoading(false);
    }
  }, [persistAuth, fetchProfileForToken]);

  const handleGoogleLogin = useCallback(async (credential: string) => {
    try {
      setLoading(true);
      setError(null);
      const response = await googleAuth(credential);
      const identity = COOKIE_AUTH_ENABLED ? response.sessionVersion : response.token;
      if (response.success && identity) {
        const profile = await fetchProfileForToken(identity, response.user);
        if (!profile) {
          setError('Unable to load profile details');
          return false;
        }
        persistAuth(identity, profile);
        return true;
      }
      setError(response.error || 'Google sign-in failed');
      return false;
    } catch (err: unknown) {
      setError(errorMessage(err, 'Google sign-in failed'));
      return false;
    } finally {
      setLoading(false);
    }
  }, [persistAuth, fetchProfileForToken]);

  const handleForgotPassword = useCallback(async (email: string) => {
    try {
      setLoading(true);
      setError(null);
      const response = await forgotPassword(email);
      return { success: response.success, message: response.message };
    } catch (err: unknown) {
      const message = errorMessage(err, 'Failed to send reset email');
      setError(message);
      return { success: false, message };
    } finally {
      setLoading(false);
    }
  }, []);

  const handleResetPassword = useCallback(async (resetToken: string, newPassword: string) => {
    try {
      setLoading(true);
      setError(null);
      const response = await resetPassword(resetToken, newPassword);
      if (COOKIE_AUTH_ENABLED && response.success) {
        clearLocalAuth();
        announceCookieSessionChange();
      }
      return { success: response.success, message: response.message };
    } catch (err: unknown) {
      const message = errorMessage(err, 'Failed to reset password');
      setError(message);
      return { success: false, message };
    } finally {
      setLoading(false);
    }
  }, [clearLocalAuth]);

  const handleLogout = useCallback(async () => {
    const startedAt = getCookieSessionRevision();
    const isCurrent = () => COOKIE_AUTH_ENABLED
      ? startedAt === getCookieSessionRevision() && token === getCookieSessionVersion()
      : token === localStorage.getItem(STORAGE_KEYS.token);
    const outcome = await logoutSession({
      cookieMode: COOKIE_AUTH_ENABLED,
      identity: token,
      revoke: logoutUser,
      isCurrent,
    });
    if (!isCurrent()) return;
    if (outcome === 'clear') {
      clearLocalAuth();
      if (COOKIE_AUTH_ENABLED) announceCookieSessionChange();
    } else if (outcome === 'failed') {
      setError('Sign out failed. Please try again.');
    }
  }, [token, clearLocalAuth]);

  const refreshProfile = useCallback(async () => {
    if (!token) return null;
    try {
      const response = await getProfile(token);
      if (COOKIE_AUTH_ENABLED && getCookieSessionVersion() !== token) return null;
      if (response.success) {
        setUser(response.user);
        if (!COOKIE_AUTH_ENABLED) localStorage.setItem(STORAGE_KEYS.user, JSON.stringify(response.user));
        return response.user;
      }
    } catch (err) {
      console.error('Failed to refresh profile', err);
    }
    return null;
  }, [token]);

  const updateMyProfile = useCallback(
    async (payload: Partial<UserProfile> & { password?: string; current_password?: string }) => {
      if (!token) return false;
      try {
        const response = await updateProfile(payload, token);
        if (COOKIE_AUTH_ENABLED && getCookieSessionVersion() !== token) return false;
        if (response.success) {
          if (COOKIE_AUTH_ENABLED && response.sessionVersion && response.user) {
            persistAuth(response.sessionVersion, response.user);
          } else {
            await refreshProfile();
          }
          return true;
        }
        setError(response.error || 'Unable to update profile');
        return false;
      } catch (err: unknown) {
        setError(errorMessage(err, 'Unable to update profile'));
        return false;
      }
    },
    [token, refreshProfile, persistAuth]
  );

  const value = useMemo<AuthContextValue>(() => ({
    user,
    token,
    loading,
    sessionValidated,
    error,
    login: handleLogin,
    signup: handleSignup,
    loginWithGoogle: handleGoogleLogin,
    requestPasswordReset: handleForgotPassword,
    resetUserPassword: handleResetPassword,
    logout: handleLogout,
    refreshProfile,
    updateMyProfile,
    clearError: () => setError(null),
    // Currency support
    currency,
    setCurrency,
    formatPrice,
    convertCurrency,
  }), [user, token, loading, sessionValidated, error, handleLogin, handleSignup, handleGoogleLogin, handleForgotPassword, handleResetPassword, handleLogout, refreshProfile, updateMyProfile, currency, setCurrency, formatPrice, convertCurrency]);

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
};

export const useAuth = () => {
  const context = useContext(AuthContext);
  if (!context) {
    throw new Error('useAuth must be used within an AuthProvider');
  }
  return context;
};
