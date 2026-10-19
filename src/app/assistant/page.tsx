import type { Metadata } from 'next';
import { AssistantView } from '@/components/assistant/AssistantView';
import { AuthProvider } from '@/context/AuthContext';
import { PublicRouteShell } from '@/components/public/PublicRouteShell';
export const metadata: Metadata = { title: 'AI Assistant', robots: { index: false, follow: false } };
export default function AssistantPage() { return <AuthProvider><PublicRouteShell><AssistantView /></PublicRouteShell></AuthProvider>; }
