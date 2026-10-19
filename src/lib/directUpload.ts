export type UploadResult = { success: boolean; url: string; assetId?: string; path?: string; filename?: string };
export type UploadPreparation = { mode: 'proxy' } | { mode: 'complete'; intentId: string } | {
  mode: 'direct'; intentId: string; uploadUrl: string; parameters: Record<string, string | number>;
};

const attempts = new WeakMap<File, { scope: string; key: string; intentId?: string }>();

/** Only an explicit proxy response permits sending bytes through the backend. */
export async function tryDirectUpload(
  file: File, kind: 'image' | 'video', scope: string,
  prepare: (requestKey: string) => Promise<UploadPreparation>,
  complete: (intentId: string) => Promise<UploadResult>,
  send: typeof fetch = fetch,
): Promise<UploadResult | null> {
  let attempt = attempts.get(file);
  if (!attempt || attempt.scope !== scope) {
    attempt = { scope, key: crypto.randomUUID() };
    attempts.set(file, attempt);
  }
  // An ambiguous provider response must be reconciled, never uploaded again.
  if (attempt.intentId) return complete(attempt.intentId);
  const preparation = await prepare(attempt.key);
  if (preparation.mode === 'proxy') return null;
  if (preparation.mode === 'complete') return complete(preparation.intentId);
  const url = new URL(preparation.uploadUrl);
  if (url.protocol !== 'https:' || url.hostname !== 'api.cloudinary.com' || url.port ||
      url.username || url.password || url.search || url.hash ||
      !new RegExp(`^/v1_1/[A-Za-z0-9_-]+/${kind}/upload$`).test(url.pathname)) {
    throw new Error('Unexpected upload destination');
  }
  const body = new FormData();
  for (const [key, value] of Object.entries(preparation.parameters)) body.append(key, String(value));
  body.append('file', file);
  attempt.intentId = preparation.intentId;
  try {
    // No application token, cookies, or browser-reported metadata crosses this boundary.
    await send(url.href, { method: 'POST', body, credentials: 'omit', redirect: 'error', signal: AbortSignal.timeout(120000) });
  } catch {
    // The provider may have stored the object despite a lost response.
  }
  return complete(preparation.intentId);
}
