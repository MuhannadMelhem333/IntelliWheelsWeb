'use client';

import { useRouter } from 'next/navigation';
import { usePublicPreferences } from './public/PublicRouteShell';
import { AboutPage, ContactPage, CookiePolicyPage, DisclaimerPage, FAQPage, HowItWorksPage, PricingPage } from './InfoPages';
import { publicPathForPage } from '@/lib/publicRoutes';

import type { InfoPageSlug } from '@/lib/infoPages';

export function InfoPageRoute({ slug }: { slug: InfoPageSlug }) {
  const router = useRouter();
  const { theme, language } = usePublicPreferences();

  const onNavigate = (page: string) => router.push(publicPathForPage(page, '/'));
  const props = { theme, language, onNavigate };

  switch (slug) {
    case 'about': return <AboutPage {...props} />;
    case 'how-it-works': return <HowItWorksPage {...props} />;
    case 'pricing': return <PricingPage {...props} />;
    case 'faq': return <FAQPage {...props} />;
    case 'contact': return <ContactPage {...props} />;
    case 'cookie-policy': return <CookiePolicyPage {...props} />;
    case 'disclaimer': return <DisclaimerPage {...props} />;
  }
}
