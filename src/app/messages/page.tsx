import type { Metadata } from 'next';
import { MessagesView } from '@/components/messages/MessagesView';
import { AuthProvider } from '@/context/AuthContext';
import { PublicRouteShell } from '@/components/public/PublicRouteShell';
export const metadata: Metadata = { title: 'Messages', robots: { index: false, follow: false } };
export default function MessagesPage() { return <AuthProvider><PublicRouteShell><MessagesView /></PublicRouteShell></AuthProvider>; }
