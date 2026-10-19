import type { Metadata } from 'next';
import { ListingEditorView } from '@/components/listings/ListingEditorView';
import { AuthProvider } from '@/context/AuthContext';
import { PublicRouteShell } from '@/components/public/PublicRouteShell';

export const metadata: Metadata = { title: 'Create Listing', robots: { index: false, follow: false } };
export default function CreateListingPage() { return <AuthProvider><PublicRouteShell><ListingEditorView /></PublicRouteShell></AuthProvider>; }
