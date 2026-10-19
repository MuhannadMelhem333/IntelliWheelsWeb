'use client';

import { RouteErrorState } from '@/components/RouteErrorState';

export default function Error({ reset }: { reset: () => void }) {
  return <RouteErrorState message="Unable to load this vehicle." onRetry={reset} />;
}
