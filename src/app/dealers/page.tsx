import type { Metadata } from 'next';
import { AuthProvider } from '@/context/AuthContext';
import { PublicRouteShell } from '@/components/public/PublicRouteShell';
import { DealerListView } from '@/components/dealers/DealerListView';

export const metadata: Metadata = {
  title: 'Verified Dealers',
  description: 'Browse public dealer profiles and available inventory on IntelliWheels.',
  alternates: { canonical: '/dealers' },
};
export default function DealersPage(){return <AuthProvider><PublicRouteShell><DealerListView/></PublicRouteShell></AuthProvider>}
