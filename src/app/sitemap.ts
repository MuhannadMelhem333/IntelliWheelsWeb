import type { MetadataRoute } from 'next';

const BASE_URL = 'https://intelliwheels.co';
const PUBLIC_PATHS = ['/', '/listings', '/dealers', '/about', '/how-it-works', '/pricing', '/faq', '/contact', '/cookie-policy', '/disclaimer'] as const;

export default function sitemap(): MetadataRoute.Sitemap {
  return PUBLIC_PATHS.map((path) => ({
    url: `${BASE_URL}${path === '/' ? '' : path}`,
    changeFrequency: path === '/' || path === '/listings' ? 'daily' : 'weekly',
    priority: path === '/' ? 1 : path === '/listings' ? 0.9 : 0.7,
  }));
}
