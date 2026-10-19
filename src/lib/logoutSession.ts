interface LogoutOptions {
  cookieMode: boolean;
  identity: string | null;
  revoke: (identity: string | null) => Promise<unknown>;
  isCurrent: () => boolean;
}

/** Decide UI disposition without letting a delayed logout replace newer auth. */
export async function logoutSession({ cookieMode, identity, revoke, isCurrent }: LogoutOptions): Promise<'clear' | 'failed' | 'stale'> {
  if (!isCurrent()) return 'stale';
  try {
    // An HttpOnly cookie may exist even when startup verification has not finished.
    if (cookieMode || identity) await revoke(identity);
  } catch {
    if (!isCurrent()) return 'stale';
    // Preserve legacy offline sign-out, but never claim cookie revocation succeeded.
    return cookieMode ? 'failed' : 'clear';
  }
  return isCurrent() ? 'clear' : 'stale';
}
