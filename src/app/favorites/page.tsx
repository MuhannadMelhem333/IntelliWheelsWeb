import type { Metadata } from 'next';
import { FavoritesView } from '@/components/favorites/FavoritesView';
import { AuthProvider } from '@/context/AuthContext';
import { PublicRouteShell } from '@/components/public/PublicRouteShell';

export const metadata: Metadata = { title: 'Favorites', robots: { index: false, follow: false } };
export default function FavoritesPage() { return <AuthProvider><PublicRouteShell><FavoritesView /></PublicRouteShell></AuthProvider>; }
