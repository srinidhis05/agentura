"use client";

import { useQuery } from "@tanstack/react-query";
import Link from "next/link";
import { listAgents, getOrgChart, getTicketStats, listHeartbeatRuns, listEvents } from "@/lib/api";
import type { AgentInfo, OrgChartNode, PlatformEvent } from "@/lib/types";
import { useState } from "react";
import {
  domainColors,
  domainFallback,
  domainLabels,
  roleIcons,
  statusDot,
} from "@/lib/colors";

export default function DashboardPage() {
  const { data: agents = [] } = useQuery({
    queryKey: ["agents"],
    queryFn: () => listAgents(),
    refetchInterval: 15000,
  });

  const { data: orgChart = [] } = useQuery({
    queryKey: ["org-chart"],
    queryFn: getOrgChart,
    refetchInterval: 15000,
  });

  const { data: ticketStats } = useQuery({
    queryKey: ["ticket-stats"],
    queryFn: () => getTicketStats(),
    refetchInterval: 10000,
  });

  const { data: heartbeats = [] } = useQuery({
    queryKey: ["recent-heartbeats"],
    queryFn: () => listHeartbeatRuns({ limit: 5 }),
    refetchInterval: 10000,
  });

  const { data: events = [] } = useQuery({
    queryKey: ["events-recent"],
    queryFn: () => listEvents({ limit: 10 }),
    refetchInterval: 8000,
  });

  const totalAgents = agents.length;
  const domains = [...new Set(agents.map((a) => a.domain).filter(Boolean))];

  const tree = buildTree(orgChart);
  const domainGroups = groupByDomain(tree);

  return (
    <div className="space-y-8">
      {/* Header */}
      <div className="flex items-start justify-between">
        <div>
          <h1 className="text-2xl font-bold tracking-tight">Company OS</h1>
          <p className="mt-1 text-sm text-muted-foreground">
            Organization overview across {domains.length} domains
          </p>
        </div>
        <span className="flex items-center gap-1.5 rounded-full border border-emerald-300 dark:border-emerald-500/30 bg-emerald-50 dark:bg-emerald-500/10 px-3 py-1 text-xs font-medium text-emerald-700 dark:text-emerald-400">
          <span className="h-2 w-2 rounded-full bg-emerald-500" />
          {totalAgents} agents registered
        </span>
      </div>

      {/* Stats Row */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
        <StatCard label="Total Agents" value={totalAgents} href="/dashboard/agents" />
        <StatCard
          label="Open Tickets"
          value={ticketStats?.open ?? 0}
          href="/dashboard/tickets"
          accent={ticketStats?.open ? "text-amber-600 dark:text-amber-400" : undefined}
        />
        <StatCard
          label="Active Tickets"
          value={ticketStats?.in_progress ?? 0}
          href="/dashboard/tickets"
        />
        <StatCard
          label="Recent Heartbeats"
          value={heartbeats.length}
          href="/dashboard/heartbeats"
        />
      </div>

      {/* Org Chart */}
      <div className="rounded-2xl border border-border bg-card shadow-sm p-6">
        <div className="flex items-center justify-between mb-5">
          <h2 className="text-lg font-semibold">Organization</h2>
          <Link
            href="/dashboard/org-chart"
            className="text-xs text-muted-foreground hover:text-foreground transition-colors"
          >
            View full org chart
          </Link>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-3 gap-4">
          {Object.entries(domainGroups).map(([domain, roots]) => {
            const colors = domainColors[domain] || domainFallback;
            return (
              <div key={domain} className={`rounded-xl border ${colors.border} ${colors.bg} p-4`}>
                <h3 className={`text-sm font-semibold ${colors.text} mb-3`}>
                  {domainLabels[domain] || domain}
                </h3>
                <div className="space-y-1.5">
                  {roots.map((root) => (
                    <MiniTreeNode key={root.id} node={root} />
                  ))}
                </div>
              </div>
            );
          })}

          {Object.keys(domainGroups).length === 0 && (
            <div className="col-span-full text-center py-8 text-sm text-muted-foreground">
              No agents registered yet. Add agent definitions to agency/ directory.
            </div>
          )}
        </div>
      </div>

      {/* Bottom Row: Tickets + Heartbeats */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Ticket Summary */}
        <div className="rounded-xl border border-border bg-card shadow-sm p-5">
          <div className="flex items-center justify-between mb-4">
            <h2 className="text-base font-semibold">Tickets</h2>
            <Link
              href="/dashboard/tickets"
              className="text-xs text-muted-foreground hover:text-foreground transition-colors"
            >
              View all
            </Link>
          </div>
          {ticketStats ? (
            <div className="grid grid-cols-4 gap-2">
              <MiniStat label="Open" value={ticketStats.open} color="text-blue-600 dark:text-blue-400" />
              <MiniStat label="Active" value={ticketStats.in_progress} color="text-amber-600 dark:text-amber-400" />
              <MiniStat label="Resolved" value={ticketStats.resolved} color="text-emerald-600 dark:text-emerald-400" />
              <MiniStat label="Escalated" value={ticketStats.escalated} color="text-red-600 dark:text-red-400" />
            </div>
          ) : (
            <p className="text-sm text-muted-foreground">No ticket data</p>
          )}
          {ticketStats?.total_cost_usd != null && ticketStats.total_cost_usd > 0 && (
            <div className="mt-3 pt-3 border-t border-border text-xs text-muted-foreground">
              Total cost: ${ticketStats.total_cost_usd.toFixed(2)}
            </div>
          )}
        </div>

        {/* Recent Heartbeats */}
        <div className="rounded-xl border border-border bg-card shadow-sm p-5">
          <div className="flex items-center justify-between mb-4">
            <h2 className="text-base font-semibold">Recent Heartbeats</h2>
            <Link
              href="/dashboard/heartbeats"
              className="text-xs text-muted-foreground hover:text-foreground transition-colors"
            >
              View all
            </Link>
          </div>
          {heartbeats.length > 0 ? (
            <div className="space-y-2">
              {heartbeats.map((hb) => (
                <div key={hb.id} className="flex items-center justify-between rounded-lg bg-muted dark:bg-card/80 px-3 py-2">
                  <div className="flex items-center gap-2">
                    <div className={`h-2 w-2 rounded-full ${
                      hb.status === "completed" ? "bg-emerald-400" :
                      hb.status === "failed" ? "bg-red-400" : "bg-amber-400 animate-pulse"
                    }`} />
                    <span className="text-sm text-foreground">{hb.agent_name || hb.agent_id}</span>
                  </div>
                  <span className="text-xs text-muted-foreground">{hb.trigger}</span>
                </div>
              ))}
            </div>
          ) : (
            <p className="text-sm text-muted-foreground">No heartbeat runs yet</p>
          )}
        </div>
      </div>

      {/* Live Activity */}
      <div>
        <h2 className="text-lg font-semibold">Live Activity</h2>
        <p className="mt-0.5 text-xs text-muted-foreground">Real-time stream of agent activities</p>
        <div className="mt-4">
          <LiveActivityFeed events={events} />
        </div>
      </div>
    </div>
  );
}

/* ---- Helpers ---- */

function buildTree(flatNodes: OrgChartNode[]): OrgChartNode[] {
  const nodeMap = new Map<string, OrgChartNode>();
  const roots: OrgChartNode[] = [];
  for (const node of flatNodes) {
    nodeMap.set(node.id, { ...node, children: [] });
  }
  for (const node of flatNodes) {
    const current = nodeMap.get(node.id)!;
    if (node.reports_to && nodeMap.has(node.reports_to)) {
      nodeMap.get(node.reports_to)!.children!.push(current);
    } else {
      roots.push(current);
    }
  }
  return roots;
}

function groupByDomain(roots: OrgChartNode[]): Record<string, OrgChartNode[]> {
  const groups: Record<string, OrgChartNode[]> = {};
  for (const root of roots) {
    const d = root.domain || "other";
    if (!groups[d]) groups[d] = [];
    groups[d].push(root);
  }
  return groups;
}

/* ---- Components ---- */

function StatCard({
  label,
  value,
  href,
  accent,
}: {
  label: string;
  value: number;
  href: string;
  accent?: string;
}) {
  return (
    <Link
      href={href}
      className="rounded-xl border border-border bg-card shadow-sm p-4 hover:shadow-md transition-all"
    >
      <div className="text-xs text-muted-foreground">{label}</div>
      <div className={`text-2xl font-bold mt-1 ${accent || "text-foreground"}`}>
        {value}
      </div>
    </Link>
  );
}

function MiniStat({ label, value, color }: { label: string; value: number; color: string }) {
  return (
    <div className="text-center">
      <div className={`text-xl font-bold ${color}`}>{value}</div>
      <div className="text-[10px] text-muted-foreground">{label}</div>
    </div>
  );
}

function MiniTreeNode({ node, depth = 0 }: { node: OrgChartNode; depth?: number }) {
  return (
    <div>
      <Link
        href={`/dashboard/agents/${node.id}`}
        className="flex items-center gap-2 rounded-md px-2 py-1.5 hover:bg-muted dark:hover:bg-card/60 transition-colors"
        style={{ paddingLeft: `${depth * 16 + 8}px` }}
      >
        <div className="flex h-6 w-6 items-center justify-center rounded text-[10px] font-bold bg-muted dark:bg-card/80 text-foreground">
          {roleIcons[node.role] || "A"}
        </div>
        <span className="text-xs text-foreground truncate flex-1">
          {node.display_name || node.name}
        </span>
        <div className={`h-1.5 w-1.5 rounded-full flex-shrink-0 ${statusDot[node.status] || statusDot.idle}`} />
      </Link>
      {node.children?.map((child) => (
        <MiniTreeNode key={child.id} node={child} depth={depth + 1} />
      ))}
    </div>
  );
}

function LiveActivityFeed({ events }: { events: PlatformEvent[] }) {
  const [paused, setPaused] = useState(false);

  return (
    <div className="rounded-xl border border-border bg-card shadow-sm">
      <div className="flex items-center justify-between border-b border-border px-5 py-3">
        <div className="flex items-center gap-2">
          <svg className="h-4 w-4 text-violet-600 dark:text-violet-500" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 10V3L4 14h7v7l9-11h-7z" />
          </svg>
          <span className="text-sm font-semibold">Live Activity Feed</span>
          <span className="h-2 w-2 rounded-full bg-emerald-500 animate-pulse" />
        </div>
        <button
          onClick={() => setPaused(!paused)}
          className="text-xs text-muted-foreground hover:text-foreground"
        >
          {paused ? "resume" : "pause"}
        </button>
      </div>

      <div className="divide-y divide-border">
        {events.length === 0 ? (
          <p className="px-5 py-8 text-center text-sm text-muted-foreground">
            No recent activity
          </p>
        ) : (
          events.slice(0, 8).map((evt, i) => (
            <div
              key={evt.event_id || i}
              className={`flex items-center gap-4 px-5 py-3.5 ${i === 0 ? "bg-blue-50/50 dark:bg-blue-500/5" : ""}`}
            >
              <div className={`flex h-9 w-9 shrink-0 items-center justify-center rounded-lg ${
                evt.severity === "error"
                  ? "bg-red-100 text-red-600 dark:bg-red-500/15 dark:text-red-400"
                  : "bg-blue-100 text-blue-600 dark:bg-blue-500/15 dark:text-blue-400"
              }`}>
                <svg className="h-4 w-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 10V3L4 14h7v7l9-11h-7z" />
                </svg>
              </div>
              <div className="min-w-0 flex-1">
                <p className="text-sm font-medium">{evt.message}</p>
                <p className="mt-0.5 text-xs text-muted-foreground">
                  {evt.domain} &middot; {evt.skill} &middot; {timeAgo(evt.timestamp)}
                </p>
              </div>
            </div>
          ))
        )}
      </div>
    </div>
  );
}

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
