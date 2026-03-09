"use client";

export default function AgentDetailError({
  error,
  reset,
}: {
  error: Error & { digest?: string };
  reset: () => void;
}) {
  return (
    <div className="p-8 space-y-4">
      <h2 className="text-lg font-bold text-red-600">Agent Detail Error</h2>
      <pre className="text-xs bg-red-50 dark:bg-red-500/10 p-4 rounded-lg overflow-auto whitespace-pre-wrap text-red-800 dark:text-red-300">
        {error.message}
        {"\n\n"}
        {error.stack}
      </pre>
      <button
        onClick={reset}
        className="rounded-lg bg-blue-600 px-3 py-1.5 text-xs text-white hover:bg-blue-700"
      >
        Try again
      </button>
    </div>
  );
}
