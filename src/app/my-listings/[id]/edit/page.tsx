import type { Metadata } from 'next';
import { ListingEditorView } from '@/components/listings/ListingEditorView';
import { AuthProvider } from '@/context/AuthContext';
import { PublicRouteShell } from '@/components/public/PublicRouteShell';

interface EditListingPageProps { params: Promise<{ id: string }>; }
export const metadata: Metadata = { title: 'Edit Listing', robots: { index: false, follow: false } };
export default async function EditListingPage({ params }: EditListingPageProps) {
  const { id } = await params;
  return <AuthProvider><PublicRouteShell><ListingEditorView listingId={id} /></PublicRouteShell></AuthProvider>;
}
