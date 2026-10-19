'use client';

export interface RouteErrorStateProps {
  message: string;
  onRetry: () => void;
  retryLabel?: string;
}

export function RouteErrorState({ message, onRetry, retryLabel = 'Try again' }: RouteErrorStateProps) {
  return (
    <main className="mx-auto flex min-h-[40vh] max-w-xl flex-col items-center justify-center gap-4 p-8 text-center" role="alert">
      <p className="text-slate-600 dark:text-slate-300">{message}</p>
      <button
        type="button"
        onClick={onRetry}
        className="rounded-xl bg-indigo-600 px-4 py-2 font-semibold text-white transition hover:bg-indigo-700 focus:outline-none focus:ring-2 focus:ring-indigo-500 focus:ring-offset-2"
      >
        {retryLabel}
      </button>
    </main>
  );
}
