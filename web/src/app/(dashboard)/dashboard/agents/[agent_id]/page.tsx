"use client";

import { useQuery } from "@tanstack/react-query";
import { useParams } from "next/navigation";
import Link from "next/link";
import { useState, useCallback, useRef, useEffect } from "react";
import { useMutation, useQueryClient } from "@tanstack/react-query";
import { getAgent, listHeartbeatRuns, listTickets, triggerHeartbeat, updateAgent, delegateTicket } from "@/lib/api";
import { roleColors, statusColors, statusDot, executorBadge, ticketStatusColors, transcriptTypeBadge, transcriptTypeBorder, triggerBadgeColors } from "@/lib/colors";
import { cn } from "@/lib/utils";
import { Tabs, TabsList, TabsTrigger, TabsContent } from "@/components/ui/tabs";
import type { HeartbeatRun, TicketInfo, TranscriptEntry } from "@/lib/types";

function timeAgo(ts: string | undefined): string {
  if (!ts) return "";
  const diff = Date.now() - new Date(ts).getTime();
  const secs = Math.floor(diff / 1000);
  if (secs < 60) return `${secs}s ago`;
  const mins = Math.floor(secs / 60);
  if (mins < 60) return `${mins}m ago`;
  const hrs = Math.floor(mins / 60);
  if (hrs < 24) return `${hrs}h ago`;
  return `${Math.floor(hrs / 24)}d ago`;
}

function formatDuration(startedAt: string, completedAt: string | null): string {
  if (!completedAt) return "running...";
  const ms = new Date(completedAt).getTime() - new Date(startedAt).getTime();
  const secs = Math.round(ms / 1000);
  if (secs < 60) return `${secs}s`;
  return `${Math.floor(secs / 60)}m ${secs % 60}s`;
}

function formatTokens(n: number): string {
  if (n >= 1000000) return `${(n / 1000000).toFixed(1)}M`;
  if (n >= 1000) return `${(n / 1000).toFixed(1)}k`;
  return String(n);
}

function formatTimestamp(ts: string): string {
  try {
    const d = new Date(ts);
    return d.toLocaleTimeString("en-US", { hour12: false, hour: "2-digit", minute: "2-digit", second: "2-digit" });
  } catch {
    return ts;
  }
}

function isJsonLike(s: string): boolean {
  const trimmed = s.trim();
  return (trimmed.startsWith("{") && trimmed.endsWith("}")) ||
         (trimmed.startsWith("[") && trimmed.endsWith("]"));
}

function tryFormatJson(s: string): string {
  try {
    return JSON.stringify(JSON.parse(s), null, 2);
  } catch {
    return s;
  }
}

export default function AgentDetailPage() {
  const params = useParams();
  const agentId = params.agent_id as string;
  const queryClient = useQueryClient();
  const [showAssignModal, setShowAssignModal] = useState(false);

  const { data: agent, isLoading } = useQuery({
    queryKey: ["agent", agentId],
    queryFn: () => getAgent(agentId),
  });

  const { data: heartbeats = [] } = useQuery({
    queryKey: ["heartbeats", agentId],
    queryFn: () => listHeartbeatRuns({ agent_id: agentId, limit: 20 }),
    enabled: !!agent,
    refetchInterval: 8000,
  });

  const { data: tickets = [] } = useQuery({
    queryKey: ["tickets", agentId],
    queryFn: () => listTickets({ assigned_to: agentId, limit: 20 }),
    enabled: !!agent,
    refetchInterval: 10000,
  });

  const isPaused = agent?.status === "paused";

  const invokeMutation = useMutation({
    mutationFn: () => triggerHeartbeat(agentId),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["heartbeats", agentId] });
      queryClient.invalidateQueries({ queryKey: ["agent", agentId] });
    },
  });

  const togglePauseMutation = useMutation({
    mutationFn: () => updateAgent(agentId, { status: isPaused ? "idle" : "paused" } as any),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["agent", agentId] });
    },
  });

  if (isLoading) {
    return (
      <div className="space-y-4">
        <div className="h-6 w-48 rounded bg-muted dark:bg-card/50 animate-pulse" />
        <div className="h-48 rounded-lg bg-muted dark:bg-card/50 animate-pulse border border-border" />
      </div>
    );
  }

  if (!agent) {
    return <div className="text-muted-foreground">Agent not found</div>;
  }

  const budget = (agent.config as Record<string, unknown>)?.budget as Record<string, unknown> | undefined;
  const delegation = (agent.config as Record<string, unknown>)?.delegation as Record<string, unknown> | undefined;
  const liveHeartbeats = heartbeats.filter((h) => h.status === "running");

  return (
    <div className="space-y-5">
      {/* Breadcrumb */}
      <div className="flex items-center gap-2 text-sm text-muted-foreground">
        <Link href="/dashboard/agents" className="hover:text-foreground transition-colors">Agents</Link>
        <span>/</span>
        <span className="text-foreground">{agent.display_name || agent.name}</span>
      </div>

      {/* Header */}
      <div className="flex items-start gap-4">
        <div className="flex h-12 w-12 items-center justify-center rounded-lg bg-muted dark:bg-card/80 text-xl font-bold text-foreground">
          {(agent.display_name || agent.name).charAt(0).toUpperCase()}
        </div>
        <div className="flex-1 min-w-0">
          <div className="flex items-center gap-3">
            <h1 className="text-xl font-bold text-foreground">{agent.display_name || agent.name}</h1>
            <div className={`h-2.5 w-2.5 rounded-full ${statusDot[agent.status] || statusDot.idle}`} />
            {liveHeartbeats.length > 0 && (
              <span className="flex items-center gap-1.5">
                <span className="relative flex h-2 w-2">
                  <span className="animate-ping absolute h-full w-full rounded-full bg-blue-400 opacity-75" />
                  <span className="relative inline-flex rounded-full h-2 w-2 bg-blue-500" />
                </span>
                <span className="text-[11px] font-medium text-blue-600 dark:text-blue-400">
                  {liveHeartbeats.length} live
                </span>
              </span>
            )}
          </div>
          <p className="text-xs text-muted-foreground font-mono mt-0.5">{agent.name}</p>
          <div className="mt-2 flex flex-wrap gap-1.5">
            <span className={`rounded-md px-2 py-0.5 text-[11px] font-medium ${roleColors[agent.role] || roleColors.agent}`}>
              {agent.role}
            </span>
            <span className={`rounded-md px-2 py-0.5 text-[11px] font-medium ${statusColors[agent.status] || statusColors.idle}`}>
              {agent.status}
            </span>
            {agent.executor && (
              <span className={`rounded-md px-2 py-0.5 text-[11px] font-medium ${executorBadge[agent.executor] || "bg-gray-100 text-gray-600 dark:bg-indigo-500/20 dark:text-indigo-400"}`}>
                {agent.executor}
              </span>
            )}
            <span className="rounded-md bg-muted dark:bg-card px-2 py-0.5 text-[11px] text-muted-foreground">
              {agent.domain}
            </span>
          </div>
        </div>

        {/* Action buttons */}
        <div className="flex items-center gap-2 shrink-0">
          <button
            onClick={() => setShowAssignModal(true)}
            className="inline-flex items-center gap-1.5 rounded-lg border border-border bg-card px-3 py-1.5 text-xs font-medium text-foreground hover:bg-accent transition-colors"
          >
            <svg className="h-3.5 w-3.5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M12 4v16m8-8H4" />
            </svg>
            Assign Task
          </button>
          <button
            onClick={() => invokeMutation.mutate()}
            disabled={invokeMutation.isPending || isPaused}
            className={cn(
              "inline-flex items-center gap-1.5 rounded-lg px-3 py-1.5 text-xs font-medium transition-colors",
              isPaused
                ? "border border-border bg-muted text-muted-foreground cursor-not-allowed"
                : "bg-blue-600 text-white hover:bg-blue-700 dark:bg-blue-500 dark:hover:bg-blue-600"
            )}
          >
            {invokeMutation.isPending ? (
              <svg className="h-3.5 w-3.5 animate-spin" fill="none" viewBox="0 0 24 24">
                <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
                <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z" />
              </svg>
            ) : (
              <svg className="h-3.5 w-3.5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M14.752 11.168l-3.197-2.132A1 1 0 0010 9.87v4.263a1 1 0 001.555.832l3.197-2.132a1 1 0 000-1.664z" />
              </svg>
            )}
            Invoke
          </button>
          <button
            onClick={() => togglePauseMutation.mutate()}
            disabled={togglePauseMutation.isPending}
            className={cn(
              "inline-flex items-center gap-1.5 rounded-lg border px-3 py-1.5 text-xs font-medium transition-colors",
              isPaused
                ? "border-emerald-300 dark:border-emerald-600 text-emerald-700 dark:text-emerald-400 hover:bg-emerald-50 dark:hover:bg-emerald-500/10"
                : "border-border text-muted-foreground hover:bg-accent"
            )}
          >
            {isPaused ? (
              <>
                <svg className="h-3.5 w-3.5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M14.752 11.168l-3.197-2.132A1 1 0 0010 9.87v4.263a1 1 0 001.555.832l3.197-2.132a1 1 0 000-1.664z" />
                </svg>
                Resume
              </>
            ) : (
              <>
                <svg className="h-3.5 w-3.5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M10 9v6m4-6v6" />
                </svg>
                Pause
              </>
            )}
          </button>
        </div>
      </div>

      {/* Assign Task Modal */}
      {showAssignModal && (
        <AssignTaskModal agentId={agentId} agentName={agent.display_name || agent.name} onClose={() => setShowAssignModal(false)} />
      )}

      {/* Tabs */}
      <Tabs defaultValue="overview">
        <TabsList variant="line">
          <TabsTrigger value="overview">Overview</TabsTrigger>
          <TabsTrigger value="runs">
            Runs
            {heartbeats.length > 0 && (
              <span className="ml-1.5 text-[10px] text-muted-foreground tabular-nums">
                ({heartbeats.length})
              </span>
            )}
          </TabsTrigger>
          <TabsTrigger value="tickets">
            Tickets
            {tickets.length > 0 && (
              <span className="ml-1.5 text-[10px] text-muted-foreground tabular-nums">
                ({tickets.length})
              </span>
            )}
          </TabsTrigger>
        </TabsList>

        {/* Overview Tab */}
        <TabsContent value="overview">
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-4 mt-1">
            {/* Soul */}
            {agent.soul && (
              <div className="rounded-lg border border-border bg-card p-4 lg:col-span-2">
                <h2 className="text-xs font-medium text-muted-foreground uppercase tracking-widest mb-2">Soul</h2>
                <div className="prose dark:prose-invert prose-sm max-w-none text-muted-foreground whitespace-pre-wrap text-[13px]">
                  {agent.soul}
                </div>
              </div>
            )}

            {/* Skills */}
            <div className="rounded-lg border border-border bg-card p-4">
              <h2 className="text-xs font-medium text-muted-foreground uppercase tracking-widest mb-2">Skills</h2>
              {agent.skills?.length > 0 ? (
                <div className="space-y-1">
                  {agent.skills.map((skill: string) => (
                    <div key={skill} className="flex items-center gap-2 rounded-md bg-muted dark:bg-card/80 px-3 py-1.5">
                      <svg className="h-3.5 w-3.5 text-muted-foreground shrink-0" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M14.752 11.168l-3.197-2.132A1 1 0 0010 9.87v4.263a1 1 0 001.555.832l3.197-2.132a1 1 0 000-1.664z" />
                      </svg>
                      <span className="text-[13px] font-mono text-foreground">{skill}</span>
                    </div>
                  ))}
                </div>
              ) : (
                <p className="text-sm text-muted-foreground">No skills configured</p>
              )}
            </div>

            {/* Configuration */}
            <div className="rounded-lg border border-border bg-card p-4">
              <h2 className="text-xs font-medium text-muted-foreground uppercase tracking-widest mb-2">Configuration</h2>
              <div className="space-y-3 text-sm">
                {budget && (
                  <div>
                    <h3 className="text-xs text-muted-foreground mb-1">Budget</h3>
                    <div className="grid grid-cols-2 gap-2">
                      <div className="rounded-md bg-muted dark:bg-card/80 px-3 py-2">
                        <div className="text-xs text-muted-foreground">Monthly</div>
                        <div className="text-sm font-semibold font-mono text-foreground">${String(budget.monthly_limit_usd || 0)}</div>
                      </div>
                      <div className="rounded-md bg-muted dark:bg-card/80 px-3 py-2">
                        <div className="text-xs text-muted-foreground">Per exec</div>
                        <div className="text-sm font-semibold font-mono text-foreground">${String(budget.per_execution_limit || 0)}</div>
                      </div>
                    </div>
                  </div>
                )}
                {delegation && (
                  <div>
                    <h3 className="text-xs text-muted-foreground mb-1">Delegation</h3>
                    <div className="rounded-md bg-muted dark:bg-card/80 px-3 py-2 space-y-1 text-xs">
                      <div className="flex justify-between">
                        <span className="text-muted-foreground">Autonomy</span>
                        <span className="text-foreground">{String(delegation.autonomy_level || "—")}</span>
                      </div>
                      <div className="flex justify-between">
                        <span className="text-muted-foreground">Max concurrent</span>
                        <span className="text-foreground">{String(delegation.max_concurrent_tickets || "—")}</span>
                      </div>
                      {Array.isArray(delegation.can_assign_to) && delegation.can_assign_to.length > 0 && (
                        <div>
                          <span className="text-muted-foreground">Assigns to: </span>
                          <span className="text-foreground">{delegation.can_assign_to.join(", ")}</span>
                        </div>
                      )}
                    </div>
                  </div>
                )}
                {agent.model && (
                  <div>
                    <h3 className="text-xs text-muted-foreground mb-1">Model</h3>
                    <div className="rounded-md bg-muted dark:bg-card/80 px-3 py-1.5 font-mono text-xs text-foreground">
                      {agent.model}
                    </div>
                  </div>
                )}
                {agent.heartbeat_schedule && (
                  <div>
                    <h3 className="text-xs text-muted-foreground mb-1">Heartbeat</h3>
                    <div className="rounded-md bg-muted dark:bg-card/80 px-3 py-1.5 font-mono text-xs text-foreground">
                      {agent.heartbeat_schedule}
                    </div>
                  </div>
                )}
              </div>
            </div>
          </div>
        </TabsContent>

        {/* Runs Tab — Paperclip-style split view */}
        <TabsContent value="runs">
          <RunsTab heartbeats={heartbeats} agentId={agentId} />
        </TabsContent>

        {/* Tickets Tab */}
        <TabsContent value="tickets">
          <TicketsTab tickets={tickets} />
        </TabsContent>
      </Tabs>
    </div>
  );
}

/* ---- Runs Tab with split view ---- */

function RunsTab({ heartbeats, agentId }: { heartbeats: HeartbeatRun[]; agentId: string }) {
  const [selectedRunId, setSelectedRunId] = useState<string | null>(null);
  const sorted = [...heartbeats].sort(
    (a, b) => new Date(b.started_at).getTime() - new Date(a.started_at).getTime()
  );
  const selectedRun = sorted.find((r) => r.id === selectedRunId) || null;

  if (sorted.length === 0) {
    return (
      <div className="mt-2 text-center py-12 text-sm text-muted-foreground border border-border rounded-lg">
        No heartbeat runs yet
      </div>
    );
  }

  return (
    <div className="flex gap-0 mt-1">
      {/* Left: Run list */}
      <div
        className={cn(
          "shrink-0 border border-border rounded-lg overflow-hidden",
          selectedRun ? "w-72" : "w-full"
        )}
      >
        <div className="sticky top-0 overflow-y-auto" style={{ maxHeight: "calc(100vh - 12rem)" }}>
          {sorted.map((run) => {
            const isActive = run.status === "running";
            const isSelected = run.id === selectedRunId;
            const totalTokens = (run.input_tokens || 0) + (run.output_tokens || 0);
            return (
              <button
                key={run.id}
                onClick={() => setSelectedRunId(run.id === selectedRunId ? null : run.id)}
                className={cn(
                  "flex items-start gap-2.5 w-full px-3 py-2.5 text-left border-b border-border last:border-b-0 transition-colors",
                  isSelected
                    ? "bg-accent text-foreground"
                    : "hover:bg-accent/50 text-foreground"
                )}
              >
                <div className={cn(
                  "h-2 w-2 rounded-full shrink-0 mt-1.5",
                  run.status === "completed" ? "bg-emerald-500" :
                  run.status === "failed" ? "bg-red-500" :
                  "bg-blue-500 animate-pulse"
                )} />
                <div className="flex-1 min-w-0">
                  <div className="flex items-center justify-between gap-2">
                    <span className="text-[11px] font-mono text-muted-foreground">
                      {run.id.slice(0, 11)}
                    </span>
                    {isActive && (
                      <span className="flex items-center gap-1">
                        <span className="relative flex h-1.5 w-1.5">
                          <span className="animate-ping absolute h-full w-full rounded-full bg-blue-400 opacity-75" />
                          <span className="relative inline-flex rounded-full h-1.5 w-1.5 bg-blue-500" />
                        </span>
                        <span className="text-[10px] font-medium text-blue-600 dark:text-blue-400">Live</span>
                      </span>
                    )}
                  </div>
                  <div className="flex items-center gap-1.5 mt-1">
                    <span className={cn(
                      "rounded px-1.5 py-0 text-[10px] font-medium",
                      triggerBadgeColors[run.trigger] || triggerBadgeColors.manual
                    )}>
                      {run.trigger || "manual"}
                    </span>
                    {totalTokens > 0 && (
                      <span className="text-[10px] text-muted-foreground tabular-nums">
                        {formatTokens(totalTokens)} tok
                      </span>
                    )}
                    {run.cost_usd > 0 && (
                      <span className="text-[10px] text-muted-foreground tabular-nums">
                        ${run.cost_usd.toFixed(3)}
                      </span>
                    )}
                  </div>
                  {run.summary && (
                    <div className="text-[11px] text-muted-foreground mt-0.5 truncate">
                      {run.summary.split("\n")[0].slice(0, 60)}
                    </div>
                  )}
                  <div className="text-[10px] text-muted-foreground/70 mt-0.5">
                    {timeAgo(run.started_at)}
                    {run.completed_at && ` · ${formatDuration(run.started_at, run.completed_at)}`}
                  </div>
                </div>
              </button>
            );
          })}
        </div>
      </div>

      {/* Right: Run detail */}
      {selectedRun && (
        <div className="flex-1 min-w-0 pl-3">
          <RunDetail run={selectedRun} />
        </div>
      )}
    </div>
  );
}

function RunDetail({ run }: { run: HeartbeatRun }) {
  const isActive = run.status === "running";
  const [sessionExpanded, setSessionExpanded] = useState(false);
  const transcriptEndRef = useRef<HTMLDivElement>(null);
  const transcript = run.transcript || [];

  // Auto-scroll transcript to bottom for running heartbeats
  useEffect(() => {
    if (isActive && transcriptEndRef.current) {
      transcriptEndRef.current.scrollIntoView({ behavior: "smooth" });
    }
  }, [isActive, transcript.length]);

  const totalTokens = (run.input_tokens || 0) + (run.output_tokens || 0) + (run.cached_tokens || 0);

  return (
    <div className="border border-border rounded-lg overflow-hidden">
      {/* Top bar: status + run ID */}
      <div className="flex items-center justify-between px-4 py-2.5 border-b border-border bg-muted/30 dark:bg-card/50">
        <div className="flex items-center gap-2.5">
          <span className={cn(
            "inline-flex items-center rounded-md px-2 py-0.5 text-xs font-medium",
            run.status === "completed" ? "bg-emerald-100 text-emerald-700 dark:bg-emerald-500/15 dark:text-emerald-400" :
            run.status === "failed" ? "bg-red-100 text-red-700 dark:bg-red-500/15 dark:text-red-400" :
            "bg-blue-100 text-blue-700 dark:bg-blue-500/15 dark:text-blue-400"
          )}>
            {run.status}
          </span>
          {isActive && (
            <span className="relative flex h-2 w-2">
              <span className="animate-ping absolute h-full w-full rounded-full bg-blue-400 opacity-75" />
              <span className="relative inline-flex rounded-full h-2 w-2 bg-blue-500" />
            </span>
          )}
          <span className="text-xs font-mono text-muted-foreground">{run.id}</span>
        </div>
        <div className="text-[11px] text-muted-foreground">
          {new Date(run.started_at).toLocaleString()}
          {run.completed_at && ` · ${formatDuration(run.started_at, run.completed_at)}`}
        </div>
      </div>

      {/* Metrics grid */}
      <div className="grid grid-cols-2 sm:grid-cols-4 gap-px bg-border">
        <MetricCell label="Input tokens" value={run.input_tokens ? formatTokens(run.input_tokens) : "—"} />
        <MetricCell label="Output tokens" value={run.output_tokens ? formatTokens(run.output_tokens) : "—"} />
        <MetricCell label="Cached tokens" value={run.cached_tokens ? formatTokens(run.cached_tokens) : "—"} />
        <MetricCell label="Cost" value={run.cost_usd > 0 ? `$${run.cost_usd.toFixed(4)}` : "—"} mono />
      </div>

      {/* Error banner */}
      {run.error_message && (
        <div className="px-4 py-2.5 bg-red-50 dark:bg-red-500/10 border-b border-red-200 dark:border-red-500/20">
          <div className="flex items-start gap-2">
            <svg className="h-3.5 w-3.5 text-red-500 mt-0.5 shrink-0" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 9v2m0 4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
            </svg>
            <span className="text-xs text-red-700 dark:text-red-400">{run.error_message}</span>
          </div>
        </div>
      )}

      {/* Transcript section */}
      {transcript.length > 0 ? (
        <div className="border-b border-border">
          <div className="px-4 py-2 bg-muted/20 dark:bg-card/30 border-b border-border">
            <span className="text-[11px] font-medium text-muted-foreground uppercase tracking-widest">
              Transcript ({transcript.length})
            </span>
          </div>
          <div className="overflow-y-auto" style={{ maxHeight: "calc(100vh - 24rem)" }}>
            <div className="divide-y divide-border/50">
              {transcript.map((entry, i) => (
                <TranscriptRow key={i} entry={entry} />
              ))}
            </div>
            <div ref={transcriptEndRef} />
          </div>
        </div>
      ) : (
        <div className="px-4 py-8 text-center border-b border-border">
          <span className="text-xs text-muted-foreground">No transcript data</span>
        </div>
      )}

      {/* Session/Invocation section (collapsible) */}
      <div>
        <button
          onClick={() => setSessionExpanded(!sessionExpanded)}
          className="flex items-center justify-between w-full px-4 py-2.5 text-left hover:bg-accent/30 transition-colors"
        >
          <span className="text-[11px] font-medium text-muted-foreground uppercase tracking-widest">
            Session Details
          </span>
          <svg
            className={cn("h-3.5 w-3.5 text-muted-foreground transition-transform", sessionExpanded && "rotate-180")}
            fill="none" stroke="currentColor" viewBox="0 0 24 24"
          >
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 9l-7 7-7-7" />
          </svg>
        </button>
        {sessionExpanded && (
          <div className="px-4 pb-4 space-y-2">
            <SessionField label="Model" value={run.model || "—"} mono />
            <SessionField label="Trigger" value={run.trigger || "—"} badge={triggerBadgeColors[run.trigger] || triggerBadgeColors.manual} />
            <SessionField label="Agent" value={run.agent_name || run.agent_id} />
            {run.ticket_id && (
              <div className="flex items-baseline gap-3">
                <span className="text-[11px] text-muted-foreground w-20 shrink-0">Ticket</span>
                <Link
                  href={`/dashboard/tickets/${run.ticket_id}`}
                  className="text-xs font-medium text-blue-600 dark:text-blue-400 hover:underline"
                >
                  {run.ticket_id.slice(0, 16)}
                </Link>
              </div>
            )}
            <SessionField label="Started" value={new Date(run.started_at).toLocaleString()} />
            {run.completed_at && (
              <SessionField label="Completed" value={new Date(run.completed_at).toLocaleString()} />
            )}
            {totalTokens > 0 && (
              <SessionField label="Total tokens" value={formatTokens(totalTokens)} mono />
            )}
          </div>
        )}
      </div>

      {/* Summary */}
      {run.summary && (
        <div className="border-t border-border p-4">
          <h3 className="text-[11px] font-medium text-muted-foreground uppercase tracking-widest mb-1.5">Summary</h3>
          <p className="text-sm text-foreground whitespace-pre-wrap">{run.summary}</p>
        </div>
      )}
    </div>
  );
}

function MetricCell({ label, value, mono }: { label: string; value: string; mono?: boolean }) {
  return (
    <div className="bg-card px-4 py-3">
      <div className="text-[10px] text-muted-foreground uppercase tracking-wider">{label}</div>
      <div className={cn("text-sm font-semibold text-foreground mt-0.5", mono && "font-mono")}>{value}</div>
    </div>
  );
}

function SessionField({ label, value, mono, badge }: { label: string; value: string; mono?: boolean; badge?: string }) {
  return (
    <div className="flex items-baseline gap-3">
      <span className="text-[11px] text-muted-foreground w-20 shrink-0">{label}</span>
      {badge ? (
        <span className={cn("rounded px-1.5 py-0 text-[11px] font-medium", badge)}>{value}</span>
      ) : (
        <span className={cn("text-xs text-foreground", mono && "font-mono")}>{value}</span>
      )}
    </div>
  );
}

function TranscriptRow({ entry }: { entry: TranscriptEntry }) {
  const [expanded, setExpanded] = useState(false);
  const isCodeBlock = entry.type === "tool_call" || entry.type === "tool_result";
  const hasJsonContent = isCodeBlock && isJsonLike(entry.content);
  const displayContent = hasJsonContent && expanded ? tryFormatJson(entry.content) : entry.content;
  const isLong = entry.content.length > 200;

  return (
    <div className={cn(
      "flex gap-0 border-l-2",
      transcriptTypeBorder[entry.type] || "border-l-gray-300 dark:border-l-gray-500/40"
    )}>
      {/* Timestamp */}
      <div className="w-16 shrink-0 px-2 py-1.5 text-[10px] font-mono text-muted-foreground/70 tabular-nums">
        {formatTimestamp(entry.ts)}
      </div>

      {/* Type badge */}
      <div className="w-20 shrink-0 py-1.5">
        <span className={cn(
          "inline-flex rounded px-1.5 py-0 text-[10px] font-medium",
          transcriptTypeBadge[entry.type] || transcriptTypeBadge.system
        )}>
          {entry.type}
        </span>
      </div>

      {/* Content */}
      <div className="flex-1 min-w-0 py-1.5 pr-3">
        {isCodeBlock ? (
          <div>
            <pre className={cn(
              "text-[11px] font-mono text-foreground/90 bg-muted/50 dark:bg-card/80 rounded px-2 py-1.5 overflow-x-auto whitespace-pre-wrap break-all",
              !expanded && isLong && "max-h-20 overflow-hidden"
            )}>
              {displayContent}
            </pre>
            {(isLong || hasJsonContent) && (
              <button
                onClick={() => setExpanded(!expanded)}
                className="text-[10px] text-blue-600 dark:text-blue-400 hover:underline mt-0.5"
              >
                {expanded ? "Collapse" : hasJsonContent ? "Expand JSON" : "Show more"}
              </button>
            )}
          </div>
        ) : entry.type === "stderr" ? (
          <span className="text-[12px] text-red-600 dark:text-red-400 font-mono whitespace-pre-wrap break-all">
            {entry.content}
          </span>
        ) : (
          <div>
            <span className={cn(
              "text-[12px] text-foreground/90 whitespace-pre-wrap break-words",
              !expanded && isLong && "line-clamp-3"
            )}>
              {entry.content}
            </span>
            {isLong && (
              <button
                onClick={() => setExpanded(!expanded)}
                className="text-[10px] text-blue-600 dark:text-blue-400 hover:underline mt-0.5 block"
              >
                {expanded ? "Show less" : "Show more"}
              </button>
            )}
          </div>
        )}
        {entry.metadata && Object.keys(entry.metadata).length > 0 && (
          <div className="mt-1 text-[10px] text-muted-foreground/70 font-mono">
            {Object.entries(entry.metadata).map(([k, v]) => (
              <span key={k} className="mr-2">{k}={typeof v === "string" ? v : JSON.stringify(v)}</span>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}

/* ---- Tickets Tab ---- */

function TicketsTab({ tickets }: { tickets: TicketInfo[] }) {
  if (tickets.length === 0) {
    return (
      <div className="mt-2 text-center py-12 text-sm text-muted-foreground border border-border rounded-lg">
        No tickets assigned
      </div>
    );
  }

  return (
    <div className="mt-1 border border-border rounded-lg divide-y divide-border">
      {tickets.map((tkt) => (
        <Link
          key={tkt.id}
          href={`/dashboard/tickets/${tkt.id}`}
          className="flex items-center justify-between w-full px-3 py-2.5 text-sm hover:bg-accent/30 transition-colors"
        >
          <div className="flex items-center gap-2.5 min-w-0">
            <div className={cn(
              "h-2 w-2 rounded-full shrink-0",
              tkt.status === "resolved" ? "bg-emerald-500" :
              tkt.status === "in_progress" ? "bg-amber-500" :
              tkt.status === "escalated" ? "bg-red-500" : "bg-gray-400"
            )} />
            <span className="text-[13px] text-foreground truncate">{tkt.title}</span>
          </div>
          <div className="flex items-center gap-3 shrink-0 ml-2">
            <span className={cn(
              "rounded px-1.5 py-0 text-[10px] font-medium",
              ticketStatusColors[tkt.status] || "bg-gray-100 text-gray-600 dark:bg-gray-500/20 dark:text-gray-400"
            )}>
              {tkt.status}
            </span>
            <span className="text-xs text-muted-foreground tabular-nums">P{tkt.priority}</span>
          </div>
        </Link>
      ))}
    </div>
  );
}

/* ---- Assign Task Modal ---- */

function AssignTaskModal({ agentId, agentName, onClose }: { agentId: string; agentName: string; onClose: () => void }) {
  const [title, setTitle] = useState("");
  const [description, setDescription] = useState("");
  const [priority, setPriority] = useState(3);
  const queryClient = useQueryClient();

  const mutation = useMutation({
    mutationFn: () => delegateTicket(agentId, { title, description, priority }),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["tickets", agentId] });
      onClose();
    },
  });

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50" onClick={onClose}>
      <div
        className="w-full max-w-md rounded-xl border border-border bg-card p-5 shadow-xl"
        onClick={(e) => e.stopPropagation()}
      >
        <h2 className="text-base font-semibold text-foreground mb-4">
          Assign Task to {agentName}
        </h2>

        <div className="space-y-3">
          <div>
            <label className="text-xs font-medium text-muted-foreground mb-1 block">Title</label>
            <input
              type="text"
              value={title}
              onChange={(e) => setTitle(e.target.value)}
              placeholder="e.g. Triage stuck orders from last 7 days"
              className="w-full rounded-lg border border-border bg-background px-3 py-2 text-sm text-foreground placeholder:text-muted-foreground focus:outline-none focus:ring-1 focus:ring-blue-500"
              autoFocus
            />
          </div>

          <div>
            <label className="text-xs font-medium text-muted-foreground mb-1 block">Description</label>
            <textarea
              value={description}
              onChange={(e) => setDescription(e.target.value)}
              placeholder="Detailed instructions for the agent..."
              rows={3}
              className="w-full rounded-lg border border-border bg-background px-3 py-2 text-sm text-foreground placeholder:text-muted-foreground focus:outline-none focus:ring-1 focus:ring-blue-500 resize-none"
            />
          </div>

          <div>
            <label className="text-xs font-medium text-muted-foreground mb-1 block">Priority</label>
            <div className="flex gap-1.5">
              {[1, 2, 3, 4, 5].map((p) => (
                <button
                  key={p}
                  onClick={() => setPriority(p)}
                  className={cn(
                    "rounded-md px-3 py-1.5 text-xs font-medium transition-colors",
                    priority === p
                      ? p <= 2
                        ? "bg-red-100 text-red-700 dark:bg-red-500/20 dark:text-red-400"
                        : p === 3
                          ? "bg-amber-100 text-amber-700 dark:bg-amber-500/20 dark:text-amber-400"
                          : "bg-blue-100 text-blue-700 dark:bg-blue-500/20 dark:text-blue-400"
                      : "bg-muted text-muted-foreground hover:bg-accent"
                  )}
                >
                  P{p}
                </button>
              ))}
            </div>
          </div>
        </div>

        <div className="flex justify-end gap-2 mt-5">
          <button
            onClick={onClose}
            className="rounded-lg border border-border px-3 py-1.5 text-xs font-medium text-muted-foreground hover:bg-accent transition-colors"
          >
            Cancel
          </button>
          <button
            onClick={() => mutation.mutate()}
            disabled={!title.trim() || mutation.isPending}
            className={cn(
              "rounded-lg px-3 py-1.5 text-xs font-medium transition-colors",
              title.trim()
                ? "bg-blue-600 text-white hover:bg-blue-700 dark:bg-blue-500 dark:hover:bg-blue-600"
                : "bg-muted text-muted-foreground cursor-not-allowed"
            )}
          >
            {mutation.isPending ? "Assigning..." : "Assign"}
          </button>
        </div>

        {mutation.isError && (
          <p className="mt-2 text-xs text-red-600 dark:text-red-400">
            {(mutation.error as Error).message || "Failed to assign task"}
          </p>
        )}
      </div>
    </div>
  );
}
