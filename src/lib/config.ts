const rawApiBase =
  process.env.NEXT_PUBLIC_API_BASE_URL ||
  process.env.NEXT_PUBLIC_API_URL ||
  process.env.NEXT_PUBLIC_API_BASE ||
  process.env.NEXT_PUBLIC_BACKEND_URL ||
  process.env.API_BASE_URL ||
  process.env.API_BASE ||
  process.env.BACKEND_URL;

function normalizeApiBase(base: string | undefined) {
  if (!base) return 'http://localhost:5000/api';
  const trimmed = base.replace(/\/+$/, '');
  return trimmed.endsWith('/api') ? trimmed : `${trimmed}/api`;
}

export const API_BASE_URL = normalizeApiBase(rawApiBase);
// Coordinated rollout gate: keep aligned with the backend after acceptance.
export const COOKIE_AUTH_ENABLED: boolean = false;
// export const DEFAULT_GEMINI_API_KEY = process.env.NEXT_PUBLIC_GEMINI_API_KEY ?? '';

export const STORAGE_KEYS = {
  token: 'intelliwheels-token',
  user: 'intelliwheels-user',
  chatSessions: 'intelliwheels-chat-sessions',
  theme: 'intelliwheels-theme',
  language: 'intelliwheels-language',
  serviceMode: 'intelliwheels-service-mode',
  currency: 'intelliwheels-currency',
};

// Re-export CurrencyCode from types for convenience
export type { CurrencyCode } from './types';
import type { CurrencyCode } from './types';

// Conversion rates: 1 unit of [currency] = N JOD
// Example: 1 AED = 0.19 JOD, 1 USD = 0.71 JOD
export const CURRENCY_RATES: Record<CurrencyCode, number> = {
  JOD: 1,
  AED: 0.19,     // 1 AED ≈ 0.19 JOD
  USD: 0.71,     // 1 USD ≈ 0.71 JOD
  EUR: 0.65,     // 1 EUR ≈ 0.65 JOD (approx, as EUR is stronger)
  GBP: 0.56,     // 1 GBP ≈ 0.56 JOD (approx)
  SAR: 0.19,     // 1 SAR ≈ 0.19 JOD
  QAR: 0.19,     // 1 QAR ≈ 0.19 JOD
  BHD: 1.88,     // 1 BHD ≈ 1.88 JOD
  KWD: 2.31,     // 1 KWD ≈ 2.31 JOD
  OMR: 1.84,     // 1 OMR ≈ 1.84 JOD
};

export const CURRENCY_SYMBOLS: Record<CurrencyCode, string> = {
  JOD: 'JD',
  AED: 'AED',
  USD: '$',
  EUR: '€',
  GBP: '£',
  SAR: 'SAR',
  QAR: 'QAR',
  BHD: 'BHD',
  KWD: 'KWD',
  OMR: 'OMR',
};

/**
 * Convert a price from source currency to target currency
 * Rates are defined as: 1 unit of [currency] = N JOD
 * So to convert FROM X to JOD: amount * rate
 * To convert FROM JOD to X: amount / rate
 */
export function convertCurrency(amount: number, from: CurrencyCode, to: CurrencyCode): number {
  if (from === to) return amount;
  // First convert source to JOD (multiply by source rate)
  const inJOD = amount * CURRENCY_RATES[from];
  // Then convert JOD to target (divide by target rate)
  return inJOD / CURRENCY_RATES[to];
}

/**
 * Format a number as currency
 */
export function formatCurrency(value: number | undefined | null, currency: CurrencyCode): string {
  if (value === undefined || value === null) return 'TBD';
  try {
    return new Intl.NumberFormat('en-US', {
      style: 'currency',
      currency,
      maximumFractionDigits: 0,
    }).format(value);
  } catch {
    return `${value.toLocaleString()} ${currency}`;
  }
}

/**
 * Format price with conversion from source currency to display currency
 */
export function formatPrice(value: number | undefined | null, sourceCurrency: CurrencyCode, displayCurrency: CurrencyCode): string {
  if (value === undefined || value === null) return 'TBD';
  const converted = convertCurrency(value, sourceCurrency, displayCurrency);
  return formatCurrency(converted, displayCurrency);
}

export const CHAT_HISTORY_LIMIT = 40;
