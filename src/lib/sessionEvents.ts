const sessionRejectedEvent = 'intelliwheels-session-rejected';

/** A delayed 401 from an old request must not sign out a newer session. */
export function shouldInvalidateSession(currentToken: string | null, rejectedToken: string | null): boolean {
  return Boolean(currentToken && rejectedToken && currentToken === rejectedToken);
}

export function notifySessionRejected(token: string | null | undefined) {
  if (token && typeof window !== 'undefined') {
    window.dispatchEvent(new CustomEvent<string>(sessionRejectedEvent, { detail: token }));
  }
}

export function subscribeToSessionRejection(onRejected: (token: string) => void) {
  const listener = (event: Event) => {
    const token: unknown = (event as CustomEvent<unknown>).detail;
    if (typeof token === 'string') onRejected(token);
  };
  window.addEventListener(sessionRejectedEvent, listener);
  return () => window.removeEventListener(sessionRejectedEvent, listener);
}
