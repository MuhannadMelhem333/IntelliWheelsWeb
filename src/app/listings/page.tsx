import type { Metadata } from 'next';
import { AuthProvider } from '@/context/AuthContext';
import { PublicRouteShell } from '@/components/public/PublicRouteShell';
import { PublicListingsView } from '@/components/listings/PublicListingsView';

export const metadata: Metadata = {
  title: 'Car Listings',
  description: 'Browse cars available through IntelliWheels in Jordan and the GCC.',
  alternates: { canonical: '/listings' },
};

export default function ListingsPage() {
  return <AuthProvider><PublicRouteShell><PublicListingsView /></PublicRouteShell></AuthProvider>;
}
