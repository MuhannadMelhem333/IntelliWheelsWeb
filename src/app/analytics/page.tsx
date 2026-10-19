import type { Metadata } from 'next';
import { AnalyticsView } from '@/components/analytics/AnalyticsView';
import { AuthProvider } from '@/context/AuthContext';
import { PublicRouteShell } from '@/components/public/PublicRouteShell';
export const metadata: Metadata = { title: 'Market Analytics', robots: { index: false, follow: false } };
export default function AnalyticsPage() { return <AuthProvider><PublicRouteShell><AnalyticsView /></PublicRouteShell></AuthProvider>; }
