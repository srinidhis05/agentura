"use client";

import { useState } from "react";
import { Badge } from "@/components/ui/badge";
import type { SkillResult } from "@/lib/types";

export function SkillResultCard({ result }: { result: SkillResult }) {
  const [showTrace, setShowTrace] = useState(false);

  return (
    <div className="mt-2 rounded-lg border border-border bg-card overflow-hidden">
      {/* Header */}
      <div className="flex items-center justify-between px-3 py-2 border-b border-border/50">
        <div className="flex items-center gap-2">
          <span className="text-sm font-medium">{result.skill_name}</span>
          <Badge variant={result.success ? "default" : "destructive"} className="text-[10px] px-1.5 py-0">
            {result.success ? "Success" : "Error"}
          </Badge>
        </div>
        {result.approval_required && (
          <Badge variant="secondary" className="text-[10px]">Approval Required</Badge>
        )}
      </div>

      {/* Stats */}
      <div className="flex items-center gap-3 px-3 py-1.5 text-xs text-muted-foreground border-b border-border/50">
        <span className="font-mono">{(result.model_used || "").split("/").pop()}</span>
        <span>${result.cost_usd.toFixed(4)}</span>
        <span>{(result.latency_ms / 1000).toFixed(1)}s</span>
        {result.route_to && <span>→ {result.route_to}</span>}
      </div>

      {/* Output */}
      <div className="px-3 py-2">
        <pre className="max-h-60 overflow-auto rounded-md bg-muted/50 p-2 text-xs font-mono whitespace-pre-wrap">
          {JSON.stringify(result.output, null, 2)}
        </pre>
      </div>

      {/* Reasoning trace toggle */}
      {result.reasoning_trace.length > 0 && (
        <div className="border-t border-border/50">
          <button
            onClick={() => setShowTrace(!showTrace)}
            className="flex items-center gap-1 px-3 py-2 text-xs text-muted-foreground hover:text-foreground transition-colors w-full text-left"
          >
            <svg
              className={`h-3 w-3 transition-transform ${showTrace ? "rotate-90" : ""}`}
              fill="none"
              stroke="currentColor"
              viewBox="0 0 24 24"
            >
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 5l7 7-7 7" />
            </svg>
            {showTrace ? "Hide" : "Show"} reasoning trace ({result.reasoning_trace.length} steps)
          </button>
          {showTrace && (
            <ol className="list-inside list-decimal space-y-1 px-3 pb-2 text-xs text-muted-foreground">
              {result.reasoning_trace.map((step, i) => (
                <li key={i}>{step}</li>
              ))}
            </ol>
          )}
        </div>
      )}
    </div>
  );
}
