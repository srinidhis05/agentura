"use client";

import { useParams } from "next/navigation";
import { useQuery, useQueryClient } from "@tanstack/react-query";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Separator } from "@/components/ui/separator";
import { getExecution, approveExecution } from "@/lib/api";
import { TraceTimeline } from "@/components/trace/trace-timeline";
import { useState } from "react";

const outcomeStyles: Record<string, string> = {
  accepted: "bg-emerald-500/10 text-emerald-400 border-emerald-500/20",
  corrected: "bg-amber-500/10 text-amber-400 border-amber-500/20",
  pending_review: "bg-blue-500/10 text-blue-400 border-blue-500/20",
  pending_approval: "bg-orange-500/10 text-orange-400 border-orange-500/20",
  approved: "bg-emerald-500/10 text-emerald-400 border-emerald-500/20",
  rejected: "bg-red-500/10 text-red-400 border-red-500/20",
};

export default function ExecutionDetailPage() {
  const params = useParams<{ id: string }>();
  const queryClient = useQueryClient();
  const [approving, setApproving] = useState(false);
  const [approvalNotes, setApprovalNotes] = useState("");

  const { data, isLoading } = useQuery({
    queryKey: ["execution", params.id],
    queryFn: () => getExecution(params.id),
  });

  async function handleApproval(approved: boolean) {
    setApproving(true);
    try {
      await approveExecution(params.id, approved, approvalNotes);
      queryClient.invalidateQueries({ queryKey: ["execution", params.id] });
      setApprovalNotes("");
    } finally {
      setApproving(false);
    }
  }

  if (isLoading) {
    return (
      <div className="flex items-center justify-center py-20">
        <div className="h-8 w-8 animate-spin rounded-full border-4 border-primary border-t-transparent" />
      </div>
    );
  }

  if (!data) {
    return <p className="text-sm text-muted-foreground">Execution not found.</p>;
  }

  const { execution: exec, corrections, reflexions } = data;
  const hasChain = corrections.length > 0 || reflexions.length > 0;

  return (
    <div className="space-y-6">
      {/* Header */}
      <div>
        <div className="flex items-center gap-3">
          <h2 className="font-mono text-lg font-bold">{exec.execution_id}</h2>
          <Badge variant="outline" className={outcomeStyles[exec.outcome] ?? ""}>
            {exec.outcome}
          </Badge>
        </div>
        <p className="mt-1 text-sm text-muted-foreground">
          {exec.skill} &middot; {exec.timestamp ? new Date(exec.timestamp).toLocaleString() : ""}
        </p>
      </div>

      {/* Inline approval form for pending executions */}
      {exec.outcome === "pending_approval" && (
        <Card className="border-orange-500/20 bg-orange-500/5">
          <CardContent className="py-4">
            <div className="space-y-3">
              <p className="text-xs font-medium text-orange-400">This execution requires approval</p>
              <textarea
                value={approvalNotes}
                onChange={(e) => setApprovalNotes(e.target.value)}
                placeholder="Reviewer notes (optional)..."
                className="w-full rounded-md border border-border bg-background px-3 py-2 text-xs placeholder:text-muted-foreground focus:outline-none focus:ring-1 focus:ring-ring"
                rows={2}
              />
              <div className="flex items-center gap-2">
                <Button
                  size="sm"
                  className="h-7 bg-emerald-600 px-4 text-xs text-white hover:bg-emerald-700"
                  disabled={approving}
                  onClick={() => handleApproval(true)}
                >
                  {approving ? "..." : "Approve"}
                </Button>
                <Button
                  size="sm"
                  variant="outline"
                  className="h-7 border-red-500/30 px-4 text-xs text-red-400 hover:bg-red-500/10"
                  disabled={approving}
                  onClick={() => handleApproval(false)}
                >
                  Reject
                </Button>
              </div>
            </div>
          </CardContent>
        </Card>
      )}

      {/* Execution trace timeline */}
      <TraceTimeline execution={exec} />

      <div className={`grid gap-6 ${hasChain ? "md:grid-cols-2" : ""}`}>
        {/* Left: Execution data */}
        <div className="space-y-4">
          <Card>
            <CardHeader className="pb-2">
              <CardTitle className="text-sm">Input</CardTitle>
            </CardHeader>
            <CardContent>
              <pre className="max-h-48 overflow-auto rounded-md bg-accent/50 p-3 text-xs">
                {typeof exec.input_summary === "string"
                  ? exec.input_summary
                  : JSON.stringify(exec.input_summary, null, 2)}
              </pre>
            </CardContent>
          </Card>

          <Card>
            <CardHeader className="pb-2">
              <CardTitle className="text-sm">Output</CardTitle>
            </CardHeader>
            <CardContent>
              <pre className="max-h-60 overflow-auto rounded-md bg-accent/50 p-3 text-xs">
                {typeof exec.output_summary === "string"
                  ? exec.output_summary
                  : JSON.stringify(exec.output_summary, null, 2)}
              </pre>
            </CardContent>
          </Card>

          {exec.reflexion_applied && (
            <Card className="border-violet-500/20">
              <CardHeader className="pb-2">
                <CardTitle className="flex items-center gap-2 text-sm">
                  <span className="h-2 w-2 rounded-full bg-violet-400" />
                  Reflexion Applied
                </CardTitle>
              </CardHeader>
              <CardContent>
                <p className="text-sm text-muted-foreground">{exec.reflexion_applied}</p>
              </CardContent>
            </Card>
          )}

          {/* Timing bar */}
          <Card>
            <CardContent className="py-4">
              <div className="space-y-2">
                <div className="flex items-center justify-between text-xs">
                  <span className="text-muted-foreground">Latency</span>
                  <span className="font-mono">{(exec.latency_ms / 1000).toFixed(1)}s</span>
                </div>
                <div className="h-2 rounded-full bg-accent">
                  <div
                    className="h-2 rounded-full bg-blue-500"
                    style={{ width: `${Math.min((exec.latency_ms / 10000) * 100, 100)}%` }}
                  />
                </div>
                <div className="flex items-center justify-between text-xs text-muted-foreground">
                  <span>Cost: ${exec.cost_usd.toFixed(4)}</span>
                  <span>Model: {exec.model_used?.split("/").pop()}</span>
                </div>
              </div>
            </CardContent>
          </Card>
        </div>

        {/* Right: Correction chain (only if corrections exist) */}
        {hasChain && (
          <div className="space-y-4">
            <h3 className="text-sm font-semibold uppercase tracking-wider text-muted-foreground">
              Correction Chain
            </h3>

            {/* Chain visualization */}
            <div className="flex items-center gap-2 text-xs">
              <span className="rounded bg-blue-500/10 px-2 py-1 font-mono text-blue-400">
                EXEC
              </span>
              {corrections.map((c) => (
                <span key={c.correction_id} className="flex items-center gap-2">
                  <svg className="h-3 w-3 text-muted-foreground" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 5l7 7-7 7" />
                  </svg>
                  <span className="rounded bg-amber-500/10 px-2 py-1 font-mono text-amber-400">
                    {c.correction_id}
                  </span>
                </span>
              ))}
              {reflexions.map((r) => (
                <span key={r.reflexion_id} className="flex items-center gap-2">
                  <svg className="h-3 w-3 text-muted-foreground" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 5l7 7-7 7" />
                  </svg>
                  <span className="rounded bg-violet-500/10 px-2 py-1 font-mono text-violet-400">
                    {r.reflexion_id}
                  </span>
                </span>
              ))}
            </div>

            <Separator />

            {/* Corrections */}
            {corrections.map((c) => (
              <Card key={c.correction_id} className="border-amber-500/20">
                <CardHeader className="pb-2">
                  <CardTitle className="flex items-center gap-2 text-sm">
                    <span className="h-2 w-2 rounded-full bg-amber-400" />
                    Correction {c.correction_id}
                  </CardTitle>
                </CardHeader>
                <CardContent className="space-y-3">
                  <p className="text-sm text-muted-foreground">{c.user_correction}</p>
                  <div className="text-[10px] text-muted-foreground">
                    {c.timestamp ? new Date(c.timestamp).toLocaleString() : ""}
                  </div>
                </CardContent>
              </Card>
            ))}

            {/* Reflexions */}
            {reflexions.map((r) => (
              <Card key={r.reflexion_id} className="border-violet-500/20">
                <CardHeader className="pb-2">
                  <CardTitle className="flex items-center gap-2 text-sm">
                    <span className="h-2 w-2 rounded-full bg-violet-400" />
                    Reflexion {r.reflexion_id}
                    <Badge variant="outline" className="ml-auto text-[10px]">
                      confidence: {r.confidence}
                    </Badge>
                  </CardTitle>
                </CardHeader>
                <CardContent className="space-y-2">
                  <p className="text-sm font-medium">{r.rule}</p>
                  {r.applies_when && (
                    <p className="text-xs text-muted-foreground italic">
                      Applies when: {r.applies_when}
                    </p>
                  )}
                  <div className="flex items-center gap-2">
                    <Badge
                      variant={r.validated_by_test ? "default" : "secondary"}
                      className="text-[10px]"
                    >
                      {r.validated_by_test ? "Validated by test" : "Not yet validated"}
                    </Badge>
                  </div>
                </CardContent>
              </Card>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}
