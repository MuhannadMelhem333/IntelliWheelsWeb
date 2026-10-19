import { API_BASE_URL } from './config';

// Only a non-authenticating server identifier is held in memory, never a token.
let sessionVersion: string | null = null;
let revision = 0;
let csrfRequest: Promise<string> | null = null;

export const getCookieSessionVersion = () => sessionVersion;
export const getCookieSessionRevision = () => revision;
export function setCookieSessionVersion(value: string | null) {
  sessionVersion = value;
  revision += 1;
}

export const cookieSessionChangeKey = 'intelliwheels-session-change';
export function announceCookieSessionChange() {
  try {
    localStorage.setItem(cookieSessionChangeKey, crypto.randomUUID());
  } catch {
    // Storage may be disabled; focus-based verification still resynchronizes.
  }
}

async function fetchCsrf(): Promise<string> {
  const response = await fetch(`${API_BASE_URL}/auth/csrf`, {
    credentials: 'include', cache: 'no-store', signal: AbortSignal.timeout(15000),
  });
  if (!response.ok) throw new Error('Unable to prepare secure request');
  const data: unknown = await response.json();
  if (!data || typeof data !== 'object' || !('csrfToken' in data) ||
      typeof data.csrfToken !== 'string' || !data.csrfToken) {
    throw new Error('Invalid security response');
  }
  return data.csrfToken;
}

export async function prepareCookieHeaders(headers: Headers, method: string, expectedVersion: string | null, signal?: AbortSignal) {
  signal?.throwIfAborted();
  const startedAt = revision;
  headers.delete('Authorization');
  if (expectedVersion) headers.set('X-Session-Version', expectedVersion);
  if (method !== 'GET') {
    // Coalesce simultaneous bootstrap requests so guest seed cookies cannot race.
    csrfRequest ??= fetchCsrf().finally(() => { csrfRequest = null; });
    const csrf = await csrfRequest;
    signal?.throwIfAborted();
    if (startedAt !== revision || (expectedVersion && expectedVersion !== sessionVersion)) {
      throw new Error('Session changed. Please try again.');
    }
    headers.set('X-CSRF-Token', csrf);
  }
}
