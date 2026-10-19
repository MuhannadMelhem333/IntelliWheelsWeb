/** Flask's local fallback returns root-relative API paths, not frontend paths. */
export function resolveUploadUrl(url: string, apiBaseUrl: string): string {
  if (!url.startsWith('/api/uploads/')) return url;
  return new URL(url, apiBaseUrl).href;
}
