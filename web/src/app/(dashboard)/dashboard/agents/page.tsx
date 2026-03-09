"use client";

import { useQuery } from "@tanstack/react-query";
import Link from "next/link";
import { listAgents, listHeartbeatRuns } from "@/lib/api";
import type { AgentInfo } from "@/lib/types";
import {
  domainLabelsLong,
  domainColors,
  domainFallback,
  roleColors,
  statusDot,
  executorBadge,
} from "@/lib/colors";

function groupByDomain(agents: AgentInfo[]): Record<string, AgentInfo[]> {
  const groups: Record<string, AgentInfo[]> = {};
  for (const agent of agents) {
    const domain = agent.domain || "other";
    if (!groups[domain]) groups[domain] = [];
    groups[domain].push(agent);
  }
  return groups;
}

export default function AgentsPage() {
  const { data: agents = [], isLoading } = useQuery({
    queryKey: ["agents"],
    queryFn: () => listAgents(),
    refetchInterval: 10000,
  });

  const { data: heartbeats = [] } = useQuery({
    queryKey: ["heartbeats-recent"],
    queryFn: () => listHeartbeatRuns({ limit: 50 }),
    refetchInterval: 10000,
  });

  const grouped = groupByDomain(agents);
  const activeCount = agents.filter((a) => a.status === "working").length;
  const idleCount = agents.filter((a) => a.status === "idle").length;
  const runningHeartbeats = heartbeats.filter((h) => h.status === "running");

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-foreground">Agents</h1>
          <p className="text-sm text-muted-foreground mt-1">
            {agents.length} agents across {Object.keys(grouped).length} domains
          </p>
        </div>
        {activeCount > 0 && (
          <span className="flex items-center gap-2 text-xs font-medium text-blue-600 dark:text-blue-400">
            <span className="relative flex h-2 w-2">
              <span className="animate-ping absolute h-full w-full rounded-full bg-blue-400 opacity-75" />
              <span className="relative inline-flex rounded-full h-2 w-2 bg-blue-500" />
            </span>
            {activeCount} active
          </span>
        )}
      </div>

      {/* Summary metrics */}
      <div className="grid grid-cols-2 xl:grid-cols-4 gap-2">
        <MetricCard label="Total Agents" value={agents.length} />
        <MetricCard label="Active" value={activeCount} accent="text-blue-600 dark:text-blue-400" />
        <MetricCard label="Idle" value={idleCount} />
        <MetricCard
          label="Live Heartbeats"
          value={runningHeartbeats.length}
          accent={runningHeartbeats.length > 0 ? "text-amber-600 dark:text-amber-400" : undefined}
        />
      </div>

      {/* Agent cards by domain */}
      {isLoading ? (
        <div className="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-3 gap-3">
          {[...Array(6)].map((_, i) => (
            <div key={i} className="h-28 rounded-lg bg-muted dark:bg-card/50 animate-pulse border border-border" />
          ))}
        </div>
      ) : (
        Object.entries(grouped).map(([domain, domainAgents]) => {
          const colors = domainColors[domain] || domainFallback;
          return (
            <div key={domain} className="space-y-2">
              <h2 className="text-xs font-medium text-muted-foreground uppercase tracking-widest">
                {domainLabelsLong[domain] || domain}
                <span className="ml-1.5 text-muted-foreground/60">
                  ({domainAgents.length})
                </span>
              </h2>
              <div className="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-3 gap-2">
                {domainAgents.map((agent) => {
                  const agentHeartbeats = heartbeats.filter((h) => h.agent_id === agent.id);
                  const liveCount = agentHeartbeats.filter((h) => h.status === "running").length;
                  return (
                    <Link
                      key={agent.id}
                      href={`/dashboard/agents/${agent.id}`}
                      className="group flex items-center gap-3 rounded-lg border border-border bg-card px-3 py-3 transition-colors hover:bg-accent/50"
                    >
                      {/* Avatar */}
                      <div className={`flex h-9 w-9 shrink-0 items-center justify-center rounded-lg text-sm font-bold ${colors.bg} ${colors.text}`}>
                        {(agent.display_name || agent.name).charAt(0).toUpperCase()}
                      </div>

                      {/* Info */}
                      <div className="flex-1 min-w-0">
                        <div className="flex items-center gap-2">
                          <span className="text-[13px] font-medium text-foreground truncate">
                            {agent.display_name || agent.name}
                          </span>
                          <div className={`h-2 w-2 rounded-full shrink-0 ${statusDot[agent.status] || statusDot.idle}`} />
                        </div>
                        <div className="flex items-center gap-1.5 mt-0.5">
                          <span className={`inline-flex items-center rounded px-1.5 py-0 text-[10px] font-medium ${roleColors[agent.role] || roleColors.agent}`}>
                            {agent.role}
                          </span>
                          {agent.executor && (
                            <span className={`inline-flex items-center rounded px-1.5 py-0 text-[10px] font-medium ${executorBadge[agent.executor] || "bg-gray-100 text-gray-600 dark:bg-gray-500/20 dark:text-gray-400"}`}>
                              {agent.executor}
                            </span>
                          )}
                        </div>
                      </div>

                      {/* Live indicator */}
                      {liveCount > 0 && (
                        <span className="flex items-center gap-1.5 shrink-0">
                          <span className="relative flex h-2 w-2">
                            <span className="animate-ping absolute h-full w-full rounded-full bg-blue-400 opacity-75" />
                            <span className="relative inline-flex rounded-full h-2 w-2 bg-blue-500" />
                          </span>
                          <span className="text-[11px] font-medium text-blue-600 dark:text-blue-400">
                            {liveCount} live
                          </span>
                        </span>
                      )}
                    </Link>
                  );
                })}
              </div>
            </div>
          );
        })
      )}
    </div>
  );
}

function MetricCard({
  label,
  value,
  accent,
}: {
  label: string;
  value: number;
  accent?: string;
}) {
  return (
    <div className="rounded-lg border border-border bg-card px-4 py-3">
      <p className={`text-2xl font-semibold tracking-tight tabular-nums ${accent || "text-foreground"}`}>
        {value}
      </p>
      <p className="text-xs text-muted-foreground mt-0.5">{label}</p>
    </div>
  );
}
