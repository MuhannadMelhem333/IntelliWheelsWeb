import type { Metadata } from 'next';
import { MyListingsView } from '@/components/listings/MyListingsView';
import { AuthProvider } from '@/context/AuthContext';
import { PublicRouteShell } from '@/components/public/PublicRouteShell';
export const metadata: Metadata = { title: 'My Listings', robots: { index: false, follow: false } };
export default function MyListingsPage() { return <AuthProvider><PublicRouteShell><MyListingsView /></PublicRouteShell></AuthProvider>; }
