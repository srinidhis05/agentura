"use client";

import { useState } from "react";
import { Badge } from "@/components/ui/badge";
import type { SkillResult } from "@/lib/types";

/**
 * Unwrap LLM output: strip raw_output wrapper and markdown code fences.
 */
function unwrapOutput(output: Record<string, unknown>): Record<string, unknown> {
  if (typeof output?.raw_output === "string" && Object.keys(output).length === 1) {
    const raw = output.raw_output as string;
    const fenceMatch = raw.match(/```(?:json)?\s*\n?([\s\S]*?)```/);
    const jsonStr = fenceMatch ? fenceMatch[1].trim() : raw.trim();
    try {
      const parsed = JSON.parse(jsonStr);
      if (typeof parsed === "object" && parsed !== null) return parsed;
    } catch {
      // Return as plain text
      return { response: raw };
    }
  }
  return output;
}

/**
 * Render a value as readable content — handles strings, arrays, objects recursively.
 */
function RenderValue({ value, depth = 0 }: { value: unknown; depth?: number }) {
  if (value === null || value === undefined) return null;

  if (typeof value === "string") {
    return <span>{value}</span>;
  }

  if (typeof value === "number" || typeof value === "boolean") {
    return <span className="font-mono text-primary">{String(value)}</span>;
  }

  if (Array.isArray(value)) {
    // Array of strings → bullet list
    if (value.every((v) => typeof v === "string")) {
      return (
        <ul className="list-disc pl-4 space-y-0.5">
          {value.map((item, i) => (
            <li key={i} className="text-sm">{item}</li>
          ))}
        </ul>
      );
    }
    // Array of objects → render each
    return (
      <div className="space-y-3">
        {value.map((item, i) => (
          <div key={i} className="rounded-md border border-border/50 p-2">
            <RenderValue value={item} depth={depth + 1} />
          </div>
        ))}
      </div>
    );
  }

  if (typeof value === "object") {
    const obj = value as Record<string, unknown>;
    return (
      <div className={`space-y-1.5 ${depth > 0 ? "" : ""}`}>
        {Object.entries(obj).map(([key, val]) => {
          const label = key.replace(/_/g, " ").replace(/\b\w/g, (c) => c.toUpperCase());

          // Skip null/empty values
          if (val === null || val === undefined || val === "") return null;
          if (Array.isArray(val) && val.length === 0) return null;

          // Simple scalar → inline
          if (typeof val === "string" || typeof val === "number" || typeof val === "boolean") {
            return (
              <div key={key} className="flex gap-2 text-sm">
                <span className="font-medium text-muted-foreground min-w-[120px] shrink-0">{label}:</span>
                <RenderValue value={val} depth={depth + 1} />
              </div>
            );
          }

          // Complex → block
          return (
            <div key={key} className="text-sm">
              <div className="font-medium text-muted-foreground mb-1">{label}</div>
              <div className="pl-2 border-l-2 border-border/50">
                <RenderValue value={val} depth={depth + 1} />
              </div>
            </div>
          );
        })}
      </div>
    );
  }

  return <span className="font-mono text-xs">{String(value)}</span>;
}

export function SkillResultCard({ result }: { result: SkillResult }) {
  const [showTrace, setShowTrace] = useState(false);
  const [showRaw, setShowRaw] = useState(false);
  const output = unwrapOutput(result.output);

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

      {/* Formatted output */}
      <div className="px-3 py-3 max-h-[500px] overflow-auto">
        <RenderValue value={output} />
      </div>

      {/* Raw JSON toggle */}
      <div className="border-t border-border/50">
        <button
          onClick={() => setShowRaw(!showRaw)}
          className="flex items-center gap-1 px-3 py-2 text-xs text-muted-foreground hover:text-foreground transition-colors w-full text-left"
        >
          <svg
            className={`h-3 w-3 transition-transform ${showRaw ? "rotate-90" : ""}`}
            fill="none" stroke="currentColor" viewBox="0 0 24 24"
          >
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 5l7 7-7 7" />
          </svg>
          {showRaw ? "Hide" : "Show"} raw JSON
        </button>
        {showRaw && (
          <pre className="mx-3 mb-2 max-h-60 overflow-auto rounded-md bg-muted/50 p-2 text-xs font-mono whitespace-pre-wrap">
            {JSON.stringify(output, null, 2)}
          </pre>
        )}
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
              fill="none" stroke="currentColor" viewBox="0 0 24 24"
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
