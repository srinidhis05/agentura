"use client";

import { useQuery, useQueryClient } from "@tanstack/react-query";
import Link from "next/link";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { listExecutions, approveExecution } from "@/lib/api";
import { formatOutput } from "@/lib/format-output";
import { useState } from "react";

const outcomeStyles: Record<string, string> = {
  accepted: "bg-emerald-50 text-emerald-700 border-emerald-200",
  corrected: "bg-amber-50 text-amber-700 border-amber-200",
  pending_review: "bg-blue-50 text-blue-700 border-blue-200",
  pending_approval: "bg-orange-50 text-orange-700 border-orange-200",
  approved: "bg-emerald-50 text-emerald-700 border-emerald-200",
  rejected: "bg-red-50 text-red-700 border-red-200",
};

type FilterTab = "all" | "pending_approval" | "accepted" | "corrected";

const filterTabs: { key: FilterTab; label: string }[] = [
  { key: "all", label: "All" },
  { key: "pending_approval", label: "Pending Approval" },
  { key: "accepted", label: "Accepted" },
  { key: "corrected", label: "Corrected" },
];

function StatusDot({ outcome }: { outcome: string }) {
  const color =
    outcome === "accepted" ? "bg-emerald-500" :
    outcome === "corrected" ? "bg-amber-500" :
    outcome === "pending_approval" ? "bg-orange-500" :
    outcome === "rejected" ? "bg-red-500" : "bg-blue-500";
  return <span className={`inline-block h-2 w-2 rounded-full ${color}`} />;
}

export default function ExecutionsPage() {
  const queryClient = useQueryClient();
  const [activeFilter, setActiveFilter] = useState<FilterTab>("all");
  const [expandedId, setExpandedId] = useState<string | null>(null);
  const [approvalNotes, setApprovalNotes] = useState("");
  const [approvingId, setApprovingId] = useState<string | null>(null);

  const { data: executions, isLoading, error } = useQuery({
    queryKey: ["executions"],
    queryFn: () => listExecutions(),
    retry: 2,
    retryDelay: 1000,
  });

  async function handleApproval(executionId: string, approved: boolean) {
    setApprovingId(executionId);
    try {
      await approveExecution(executionId, approved, approvalNotes);
      queryClient.invalidateQueries({ queryKey: ["executions"] });
      setExpandedId(null);
      setApprovalNotes("");
    } finally {
      setApprovingId(null);
    }
  }

  if (isLoading) {
    return (
      <div className="flex items-center justify-center py-20">
        <div className="h-8 w-8 animate-spin rounded-full border-4 border-primary border-t-transparent" />
      </div>
    );
  }

  if (error) {
    return (
      <div className="py-12 text-center">
        <p className="text-sm text-red-400">Failed to load executions</p>
        <p className="mt-1 text-xs text-muted-foreground">{(error as Error).message}</p>
      </div>
    );
  }

  const allEntries = executions ?? [];
  const filtered = activeFilter === "all"
    ? allEntries
    : allEntries.filter((e) => e.outcome === activeFilter);
  const pendingCount = allEntries.filter((e) => e.outcome === "pending_approval").length;

  return (
    <div className="space-y-6">
      {/* Header */}
      <div>
        <h1 className="text-2xl font-bold tracking-tight">Executions</h1>
        <p className="mt-1 text-sm text-muted-foreground">
          Execution history and approval queue
        </p>
      </div>

      {/* Filter tabs */}
      <div className="flex items-center gap-1 rounded-xl border border-border bg-card p-1.5">
        {filterTabs.map((tab) => (
          <button
            key={tab.key}
            onClick={() => setActiveFilter(tab.key)}
            className={`rounded-lg px-4 py-1.5 text-xs transition-colors ${
              activeFilter === tab.key
                ? "bg-accent text-foreground font-medium"
                : "text-muted-foreground hover:text-foreground hover:bg-muted"
            }`}
          >
            {tab.label}
            {tab.key === "pending_approval" && pendingCount > 0 && (
              <span className="ml-1.5 inline-flex h-4 min-w-4 items-center justify-center rounded-full bg-orange-100 px-1 text-[10px] text-orange-600">
                {pendingCount}
              </span>
            )}
          </button>
        ))}
        <span className="ml-auto pr-2 text-xs text-muted-foreground">
          {filtered.length} {filtered.length === 1 ? "run" : "runs"}
        </span>
      </div>

      {/* Table */}
      {filtered.length === 0 ? (
        <p className="py-12 text-center text-sm text-muted-foreground">
          {activeFilter === "all"
            ? "No executions recorded yet."
            : `No ${activeFilter.replace("_", " ")} executions.`}
        </p>
      ) : (
        <div className="rounded-xl border border-border bg-card">
          {/* Table header */}
          <div className="flex items-center gap-3 border-b border-border px-4 py-2.5 text-[10px] font-semibold uppercase tracking-wider text-muted-foreground">
            <span className="w-4" />
            <span className="w-36">Execution ID</span>
            <span className="w-20">Domain</span>
            <span className="min-w-0 flex-1">Agent</span>
            <span className="w-16 text-right">Duration</span>
            <span className="w-14 text-right">Cost</span>
            <span className="w-24 text-right">Status</span>
            <span className="w-16" />
          </div>

          {/* Rows */}
          <div className="divide-y divide-border">
            {filtered.map((exec) => {
              const isPending = exec.outcome === "pending_approval";
              const isExpanded = expandedId === exec.execution_id;
              const [domain, ...rest] = exec.skill.split("/");
              const agent = rest.join("/") || exec.skill;

              return (
                <div key={exec.execution_id}>
                  <Link href={`/dashboard/executions/${exec.execution_id}`}>
                    <div className="flex items-center gap-3 px-4 py-3 transition-colors hover:bg-accent/20">
                      <StatusDot outcome={exec.outcome} />
                      <span className="w-36 truncate font-mono text-[11px] text-muted-foreground">
                        {exec.execution_id.slice(0, 22)}
                      </span>
                      <span className="w-20 text-[11px] text-muted-foreground">{domain}</span>
                      <span className="min-w-0 flex-1 truncate font-mono text-[11px]">{agent}</span>
                      <span className="w-16 text-right font-mono text-[11px] text-muted-foreground">
                        {((exec.latency_ms ?? 0) / 1000).toFixed(1)}s
                      </span>
                      <span className="w-14 text-right font-mono text-[11px] text-muted-foreground">
                        ${(exec.cost_usd ?? 0).toFixed(3)}
                      </span>
                      <span className="w-24 text-right">
                        <Badge variant="outline" className={`text-[9px] ${outcomeStyles[exec.outcome] ?? ""}`}>
                          {exec.outcome.replace("_", " ")}
                        </Badge>
                      </span>
                      {isPending ? (
                        <span
                          className="w-16 text-right"
                          onClick={(e) => {
                            e.preventDefault();
                            e.stopPropagation();
                            setExpandedId(isExpanded ? null : exec.execution_id);
                            setApprovalNotes("");
                          }}
                        >
                          <Button size="sm" variant="outline" className="h-6 px-2 text-[10px]">
                            {isExpanded ? "Close" : "Review"}
                          </Button>
                        </span>
                      ) : (
                        <span className="w-16" />
                      )}
                    </div>
                  </Link>

                  {/* Inline approval */}
                  {isPending && isExpanded && (
                    <div className="border-t border-orange-200 bg-orange-50/50 px-4 py-3">
                      {exec.output_summary != null && (
                        <div className="mb-3">
                          <p className="mb-1 text-[10px] font-medium text-muted-foreground">Output preview</p>
                          <pre className="max-h-24 overflow-auto whitespace-pre-wrap break-words rounded-lg bg-muted p-3 font-mono text-[11px] text-foreground">
                            {formatOutput(exec.output_summary)}
                          </pre>
                        </div>
                      )}
                      <textarea
                        value={approvalNotes}
                        onChange={(e) => setApprovalNotes(e.target.value)}
                        placeholder="Reviewer notes (optional)..."
                        className="mb-3 w-full rounded-lg border border-border bg-white px-3 py-2 font-mono text-xs placeholder:text-muted-foreground/50 focus:outline-none focus:ring-1 focus:ring-ring"
                        rows={2}
                        onClick={(e) => e.preventDefault()}
                      />
                      <div className="flex items-center gap-2" onClick={(e) => e.preventDefault()}>
                        <Button
                          size="sm"
                          className="h-7 bg-emerald-600 px-4 text-xs text-white hover:bg-emerald-700"
                          disabled={approvingId === exec.execution_id}
                          onClick={() => handleApproval(exec.execution_id, true)}
                        >
                          {approvingId === exec.execution_id ? "..." : "Approve"}
                        </Button>
                        <Button
                          size="sm"
                          variant="outline"
                          className="h-7 border-red-300 px-4 text-xs text-red-600 hover:bg-red-50"
                          disabled={approvingId === exec.execution_id}
                          onClick={() => handleApproval(exec.execution_id, false)}
                        >
                          Reject
                        </Button>
                      </div>
                    </div>
                  )}
                </div>
              );
            })}
          </div>
        </div>
      )}
    </div>
  );
}
