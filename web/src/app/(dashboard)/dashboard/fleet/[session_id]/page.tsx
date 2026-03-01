"use client";

import { useQuery } from "@tanstack/react-query";
import { useParams } from "next/navigation";
import Link from "next/link";
import { getFleetSession, cancelFleetSession } from "@/lib/api";
import type { FleetAgent } from "@/lib/api";
import { useFleetStream } from "@/hooks/use-fleet-stream";
import { useState } from "react";

const STATUS_BADGE: Record<string, { bg: string; text: string }> = {
  pending: { bg: "bg-gray-500/15", text: "text-gray-400" },
  running: { bg: "bg-blue-500/15", text: "text-blue-400" },
  completed: { bg: "bg-emerald-500/15", text: "text-emerald-400" },
  failed: { bg: "bg-red-500/15", text: "text-red-400" },
  cancelled: { bg: "bg-amber-500/15", text: "text-amber-400" },
};

export default function FleetSessionDetailPage() {
  const { session_id } = useParams<{ session_id: string }>();
  const [cancelling, setCancelling] = useState(false);

  const { data: session, refetch } = useQuery({
    queryKey: ["fleet-session", session_id],
    queryFn: () => getFleetSession(session_id),
    refetchInterval: 5_000,
  });

  const isLive = session?.status === "running" || session?.status === "pending";
  const { agents: liveAgents } = useFleetStream(isLive ? session_id : null);

  const handleCancel = async () => {
    setCancelling(true);
    try {
      await cancelFleetSession(session_id);
      refetch();
    } finally {
      setCancelling(false);
    }
  };

  if (!session) {
    return <div className="py-20 text-center text-sm text-muted-foreground">Loading...</div>;
  }

  const agents = session.agents ?? [];

  // Merge live SSE updates with DB agents
  const mergedAgents = agents.map((agent) => {
    const live = liveAgents[agent.agent_id];
    if (live) {
      return { ...agent, status: live.status as FleetAgent["status"], success: live.success, cost_usd: live.cost_usd, latency_ms: live.latency_ms };
    }
    return agent;
  });

  const badge = STATUS_BADGE[session.status] ?? STATUS_BADGE.pending;

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-start justify-between">
        <div>
          <div className="flex items-center gap-3">
            <Link href="/dashboard/fleet" className="text-sm text-muted-foreground hover:text-foreground">
              Fleet
            </Link>
            <span className="text-muted-foreground">/</span>
            <h1 className="font-mono text-lg font-bold">{session.session_id}</h1>
          </div>
          <div className="mt-2 flex items-center gap-3 text-sm">
            <span className={`inline-flex items-center gap-1.5 rounded-full px-2.5 py-0.5 text-xs font-medium ${badge.bg} ${badge.text}`}>
              {session.status}
            </span>
            {session.repo && <span className="text-muted-foreground">{session.repo}</span>}
            {session.pr_number > 0 && (
              <a
                href={session.pr_url}
                target="_blank"
                rel="noopener noreferrer"
                className="text-blue-400 hover:underline"
              >
                PR #{session.pr_number}
              </a>
            )}
          </div>
        </div>
        {isLive && (
          <button
            onClick={handleCancel}
            disabled={cancelling}
            className="rounded-lg border border-red-500/30 bg-red-500/10 px-4 py-2 text-xs font-medium text-red-400 hover:bg-red-500/20 disabled:opacity-50"
          >
            {cancelling ? "Cancelling..." : "Cancel Session"}
          </button>
        )}
      </div>

      {/* Stats row */}
      <div className="grid grid-cols-4 gap-4">
        <StatCard label="Total Agents" value={String(session.total_agents)} />
        <StatCard label="Completed" value={String(session.completed_agents)} color="emerald" />
        <StatCard label="Failed" value={String(session.failed_agents)} color="red" />
        <StatCard label="Total Cost" value={`$${(session.total_cost_usd ?? 0).toFixed(3)}`} />
      </div>

      {/* Agent grid */}
      <div>
        <h2 className="text-lg font-semibold">Agents</h2>
        <div className="mt-4 grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
          {mergedAgents.map((agent) => (
            <AgentCard key={agent.agent_id} agent={agent} />
          ))}
        </div>
      </div>

      {/* Timeline */}
      {mergedAgents.length > 0 && (
        <div>
          <h2 className="text-lg font-semibold">Execution Timeline</h2>
          <div className="mt-4 rounded-xl border border-border bg-card p-4">
            <Timeline agents={mergedAgents} sessionCreated={session.created_at} />
          </div>
        </div>
      )}
    </div>
  );
}

function StatCard({ label, value, color }: { label: string; value: string; color?: string }) {
  const textColor = color === "emerald" ? "text-emerald-400" : color === "red" ? "text-red-400" : "text-foreground";
  return (
    <div className="rounded-xl border border-border bg-card p-4">
      <p className="text-xs text-muted-foreground">{label}</p>
      <p className={`mt-1 text-2xl font-bold ${textColor}`}>{value}</p>
    </div>
  );
}

function AgentCard({ agent }: { agent: FleetAgent }) {
  const badge = STATUS_BADGE[agent.status] ?? STATUS_BADGE.pending;
  const skillName = agent.skill_path.split("/").pop() ?? agent.agent_id;

  return (
    <div className="rounded-xl border border-border bg-card p-4 space-y-3">
      <div className="flex items-center justify-between">
        <span className="text-sm font-semibold">{agent.agent_id}</span>
        <span className={`rounded-full px-2 py-0.5 text-[10px] font-medium ${badge.bg} ${badge.text}`}>
          {agent.status}
        </span>
      </div>
      <p className="text-xs text-muted-foreground">{agent.skill_path}</p>
      <div className="grid grid-cols-2 gap-2 text-xs">
        <div>
          <span className="text-muted-foreground">Cost: </span>
          <span className="font-mono">${(agent.cost_usd ?? 0).toFixed(3)}</span>
        </div>
        <div>
          <span className="text-muted-foreground">Latency: </span>
          <span className="font-mono">{(agent.latency_ms ?? 0).toFixed(0)}ms</span>
        </div>
      </div>
      {agent.error_message && (
        <div className="rounded-lg bg-red-500/10 p-2 text-xs text-red-400">
          {agent.error_message}
        </div>
      )}
      {agent.execution_id && agent.execution_id !== "" && (
        <Link
          href={`/dashboard/executions/${agent.execution_id}`}
          className="block text-[10px] text-blue-400 hover:underline"
        >
          View execution {agent.execution_id}
        </Link>
      )}
    </div>
  );
}

function Timeline({ agents, sessionCreated }: { agents: FleetAgent[]; sessionCreated: string }) {
  const baseTime = new Date(sessionCreated).getTime();
  const maxLatency = Math.max(...agents.map((a) => a.latency_ms || 0), 1);

  return (
    <div className="space-y-2">
      {agents.map((agent) => {
        const width = maxLatency > 0 ? ((agent.latency_ms || 0) / maxLatency) * 100 : 0;
        const color = agent.success ? "bg-emerald-500" : agent.status === "running" ? "bg-blue-500" : agent.status === "failed" ? "bg-red-500" : "bg-gray-600";
        return (
          <div key={agent.agent_id} className="flex items-center gap-3">
            <span className="w-16 text-right text-[10px] text-muted-foreground">{agent.agent_id}</span>
            <div className="flex-1">
              <div className="h-5 rounded bg-gray-800">
                <div
                  className={`h-5 rounded ${color} flex items-center px-2 transition-all`}
                  style={{ width: `${Math.max(width, 2)}%` }}
                >
                  {agent.latency_ms > 0 && (
                    <span className="text-[9px] font-medium text-white">
                      {(agent.latency_ms / 1000).toFixed(1)}s
                    </span>
                  )}
                </div>
              </div>
            </div>
          </div>
        );
      })}
    </div>
  );
}
