import type { Metadata } from 'next';
import { Suspense } from 'react';
import { AccountView } from '@/components/account/AccountView';
import { AuthProvider } from '@/context/AuthContext';
import { PublicRouteShell } from '@/components/public/PublicRouteShell';

export const metadata: Metadata = { title: 'Account', robots: { index: false, follow: false } };

export default function AccountPage() {
  return <AuthProvider><PublicRouteShell><Suspense fallback={<main className="p-8 text-center">Loading account…</main>}><AccountView /></Suspense></PublicRouteShell></AuthProvider>;
}
