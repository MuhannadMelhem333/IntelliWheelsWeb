import type { Metadata } from 'next';
import { notFound } from 'next/navigation';
import { InfoPageRoute } from '@/components/InfoPageRoute';
import { INFO_PAGE_SLUGS, type InfoPageSlug } from '@/lib/infoPages';
import { AuthProvider } from '@/context/AuthContext';
import { PublicRouteShell } from '@/components/public/PublicRouteShell';

interface StaticInfoPageProps {
  params: Promise<{ infoPage: string }>;
}

const INFO_TITLES: Record<InfoPageSlug, string> = {
  about: 'About',
  'how-it-works': 'How It Works',
  pricing: 'Pricing',
  faq: 'Frequently Asked Questions',
  contact: 'Contact',
  'cookie-policy': 'Cookie Policy',
  disclaimer: 'Disclaimer',
};

export async function generateMetadata({ params }: StaticInfoPageProps): Promise<Metadata> {
  const { infoPage } = await params;
  if (!INFO_PAGE_SLUGS.includes(infoPage as InfoPageSlug)) return {};
  return { title: INFO_TITLES[infoPage as InfoPageSlug], alternates: { canonical: `/${infoPage}` } };
}

export function generateStaticParams() {
  return INFO_PAGE_SLUGS.map((infoPage) => ({ infoPage }));
}

export default async function StaticInfoPage({ params }: StaticInfoPageProps) {
  const { infoPage } = await params;
  if (!INFO_PAGE_SLUGS.includes(infoPage as InfoPageSlug)) notFound();
  return <AuthProvider><PublicRouteShell><InfoPageRoute slug={infoPage as InfoPageSlug} /></PublicRouteShell></AuthProvider>;
}
