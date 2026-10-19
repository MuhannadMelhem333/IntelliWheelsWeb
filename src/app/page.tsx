import { PublicHomeView } from '@/components/home/PublicHomeView';
import { AuthProvider } from '@/context/AuthContext';
import { PublicRouteShell } from '@/components/public/PublicRouteShell';

export default function Home() {
  return (
    <AuthProvider>
      <PublicRouteShell><PublicHomeView /></PublicRouteShell>
    </AuthProvider>
  );
}
