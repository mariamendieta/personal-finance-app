"use client";

interface PipelineResult {
  script: string;
  success: boolean;
  output: string;
}

interface PipelineRunnerProps {
  results: PipelineResult[];
  savedCount: number;
  isRunning: boolean;
}

export default function PipelineRunner({ results, savedCount, isRunning }: PipelineRunnerProps) {
  if (isRunning) {
    return (
      <div className="flex items-center gap-3 py-4">
        <div className="h-5 w-5 border-2 border-azul border-t-transparent rounded-full animate-spin" />
        <span className="text-stone">Running pipeline...</span>
      </div>
    );
  }

  if (!results.length && savedCount === 0) return null;

  return (
    <div className="space-y-3 mt-4">
      {savedCount > 0 && (
        <div className="bg-verde-claro/10 border border-verde-claro rounded-lg px-4 py-2 text-sm text-verde-hoja">
          Saved {savedCount} file(s)
        </div>
      )}
      {results.map(r => (
        <div
          key={r.script}
          className={`rounded-lg px-4 py-2 text-sm border ${
            r.success
              ? "bg-verde-claro/10 border-verde-claro text-verde-hoja"
              : "bg-coral/10 border-coral text-coral"
          }`}
        >
          <p className="font-medium">{r.script} — {r.success ? "completed" : "failed"}</p>
          <details className="mt-1">
            <summary className="cursor-pointer text-xs opacity-70">Show output</summary>
            <pre className="mt-1 text-xs whitespace-pre-wrap opacity-80 max-h-40 overflow-y-auto">
              {r.output}
            </pre>
          </details>
        </div>
      ))}
    </div>
  );
}
