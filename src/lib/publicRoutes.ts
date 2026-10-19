const LEGACY_PAGE_PATHS: Record<string, string> = {
  home: '/', listings: '/listings', favorites: '/favorites', myListings: '/my-listings', addListing: '/my-listings/new',
  dealers: '/dealers', analytics: '/analytics', chatbot: '/assistant', messages: '/messages', profile: '/account', admin: '/admin',
  about: '/about', howItWorks: '/how-it-works', pricing: '/pricing', faq: '/faq', contact: '/contact', cookiePolicy: '/cookie-policy', disclaimer: '/disclaimer',
};

export function publicPathForPage(page: string | null, fallback = '/listings'): string {
  if (!page) return fallback;
  if (page.startsWith('dealer-')) {
    const dealerId = page.slice('dealer-'.length);
    return /^\d+$/.test(dealerId) ? `/dealers/${dealerId}` : fallback;
  }
  return LEGACY_PAGE_PATHS[page] ?? fallback;
}
