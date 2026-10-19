'use client';

import { ListingsRouteFeedback } from '@/components/listings/ListingsRouteFeedback';

export default function Error({ reset }: { reset: () => void }) {
  return <ListingsRouteFeedback onRetry={reset} />;
}
