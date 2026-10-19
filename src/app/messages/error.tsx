'use client';
import { RouteErrorState } from '@/components/RouteErrorState';
export default function Error({ reset }: { reset: () => void }) { return <RouteErrorState message="Unable to load messages." onRetry={reset} />; }
