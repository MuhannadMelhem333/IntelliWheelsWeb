import type { Metadata } from 'next';
import { DealerDetailView } from '@/components/DealerDetailView';
import { AuthProvider } from '@/context/AuthContext';
import { PublicRouteShell } from '@/components/public/PublicRouteShell';

interface DealerPageProps {
  params: Promise<{ id: string }>;
}

export async function generateMetadata({ params }: DealerPageProps): Promise<Metadata> {
  const { id } = await params;
  return { title: 'Dealer Details', alternates: { canonical: `/dealers/${encodeURIComponent(id)}` } };
}

export default async function DealerPage({ params }: DealerPageProps) {
  const { id } = await params;
  return (
    <AuthProvider>
      <PublicRouteShell><DealerDetailView dealerId={id} /></PublicRouteShell>
    </AuthProvider>
  );
}
