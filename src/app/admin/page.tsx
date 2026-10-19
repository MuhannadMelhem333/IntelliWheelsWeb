import type { Metadata } from 'next';
import { AdminDealerApplicationsView } from '@/components/admin/AdminDealerApplicationsView';
import { AuthProvider } from '@/context/AuthContext';
import { PublicRouteShell } from '@/components/public/PublicRouteShell';
export const metadata: Metadata = { title: 'Admin', robots: { index: false, follow: false } };
export default function AdminPage() { return <AuthProvider><PublicRouteShell><AdminDealerApplicationsView /></PublicRouteShell></AuthProvider>; }
