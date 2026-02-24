"use client";

interface TraceTimelineProps {
  execution: {
    execution_id: string;
    latency_ms: number;
    model_used?: string;
    reasoning_trace?: string[];
  };
}

export function TraceTimeline({ execution }: TraceTimelineProps) {
  const trace = execution.reasoning_trace;
  if (!trace || trace.length === 0) return null;

  return (
    <div className="space-y-2">
      <h3 className="text-xs font-medium uppercase tracking-wider text-muted-foreground">
        Reasoning Trace
      </h3>
      <div className="space-y-1">
        {trace.map((step, i) => (
          <div key={i} className="flex items-start gap-2 text-xs">
            <span className="mt-0.5 h-1.5 w-1.5 shrink-0 rounded-full bg-blue-400" />
            <span className="text-muted-foreground">{step}</span>
          </div>
        ))}
      </div>
    </div>
  );
}
