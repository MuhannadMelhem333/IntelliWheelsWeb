import type { Metadata } from 'next';
import { CarDetailView } from '@/components/CarDetailView';
import { AuthProvider } from '@/context/AuthContext';
import { PublicRouteShell } from '@/components/public/PublicRouteShell';

interface CarDetailPageProps {
  params: Promise<{ id: string }>;
}

export async function generateMetadata({ params }: CarDetailPageProps): Promise<Metadata> {
  const { id } = await params;
  return { title: 'Vehicle Details', alternates: { canonical: `/cars/${encodeURIComponent(id)}` } };
}

export default async function CarDetailPage({ params }: CarDetailPageProps) {
  const { id } = await params;

  return (
    <AuthProvider>
      <PublicRouteShell><CarDetailView carId={id} /></PublicRouteShell>
    </AuthProvider>
  );
}
