export const INFO_PAGE_SLUGS = ['about', 'how-it-works', 'pricing', 'faq', 'contact', 'cookie-policy', 'disclaimer'] as const;
export type InfoPageSlug = (typeof INFO_PAGE_SLUGS)[number];
