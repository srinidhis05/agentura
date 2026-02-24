"use client";

import { useQuery } from "@tanstack/react-query";
import Link from "next/link";
import { listSkills, listExecutions, listReflexions, listEvents } from "@/lib/api";
import type { SkillInfo, PlatformEvent } from "@/lib/types";
import { useEffect, useState } from "react";

const domainColors: Record<string, string> = {
  ecm: "#10b981",
  wealth: "#3b82f6",
  frm: "#f59e0b",
  fincrime: "#ef4444",
  hr: "#ec4899",
  platform: "#6b7280",
};

export default function DashboardPage() {
  const { data: skills } = useQuery({
    queryKey: ["skills"],
    queryFn: listSkills,
  });

  const { data: executions } = useQuery({
    queryKey: ["executions"],
    queryFn: () => listExecutions(),
    refetchInterval: 10_000,
  });

  const { data: reflexions } = useQuery({
    queryKey: ["reflexions"],
    queryFn: () => listReflexions(),
  });

  const { data: events } = useQuery({
    queryKey: ["events-recent"],
    queryFn: () => listEvents({ limit: 10 }),
    refetchInterval: 8_000,
  });

  const allSkills = (skills ?? []).filter((s) => s.domain !== "platform");
  const allExecs = executions ?? [];
  const allEvents = events ?? [];

  // Reflexion counts per skill
  const reflexionsBySkill: Record<string, number> = {};
  for (const r of reflexions ?? []) {
    reflexionsBySkill[r.skill] = (reflexionsBySkill[r.skill] ?? 0) + 1;
  }

  const runningCount = allSkills.filter(
    (s) => s.health === "healthy" || s.deploy_status === "active"
  ).length;

  return (
    <div className="space-y-8">
      {/* Header */}
      <div className="flex items-start justify-between">
        <div>
          <h1 className="text-2xl font-bold tracking-tight">Agent Network</h1>
          <p className="mt-1 text-sm text-muted-foreground">
            Live visualization of agent connections and data flows
          </p>
        </div>
        <span className="flex items-center gap-1.5 rounded-full border border-emerald-200 bg-emerald-50 px-3 py-1 text-xs font-medium text-emerald-700">
          <span className="h-2 w-2 rounded-full bg-emerald-500" />
          {runningCount} agents active
        </span>
      </div>

      {/* Agent Topology Graph */}
      <div className="rounded-xl border border-border bg-card p-6">
        <div className="mb-1 text-sm font-semibold">Agent Topology</div>
        <p className="mb-3 text-xs text-muted-foreground">Real-time agent network visualization</p>
        <div className="mb-4 flex flex-wrap items-center gap-5 text-xs">
          <span className="flex items-center gap-1.5">
            <span className="h-2.5 w-2.5 rounded-full bg-emerald-500" /> active
          </span>
          <span className="flex items-center gap-1.5">
            <span className="h-2.5 w-2.5 rounded-full bg-amber-500" /> processing
          </span>
          <span className="flex items-center gap-1.5">
            <span className="h-2.5 w-2.5 rounded-full bg-gray-400" /> idle
          </span>
          <span className="mx-2 h-3 w-px bg-border" />
          <span className="flex items-center gap-1.5">
            <span className="h-2 w-4 rounded-full" style={{ background: "#E01E5A", opacity: 0.5 }} /> Slack
          </span>
          <span className="flex items-center gap-1.5">
            <span className="h-2 w-4 rounded-full" style={{ background: "#8B5CF6", opacity: 0.5 }} /> Cron
          </span>
          <span className="flex items-center gap-1.5">
            <span className="h-2 w-4 rounded-full" style={{ background: "#0EA5E9", opacity: 0.5 }} /> API
          </span>
        </div>
        <TopologyGraph skills={allSkills} executions={allExecs} />
      </div>

      {/* Live Activity */}
      <div>
        <h2 className="text-lg font-semibold">Live Activity</h2>
        <p className="mt-0.5 text-xs text-muted-foreground">Real-time stream of agent activities</p>
        <div className="mt-4">
          <LiveActivityFeed events={allEvents} executions={allExecs} />
        </div>
      </div>
    </div>
  );
}

/* ── Topology Graph (SVG DAG) — Gateway → Domain Managers → Agents ── */

interface GraphNode {
  id: string;
  name: string;
  domain: string;
  role: string;
  x: number;
  y: number;
  status: "active" | "processing" | "idle";
  isGateway?: boolean;
  isChannel?: boolean;
  channelType?: "slack" | "cron" | "api" | "manual";
}

interface GraphEdge {
  from: string;
  to: string;
  dashed?: boolean;
}

const channelMeta: Record<string, { color: string; label: string; sublabel: string }> = {
  slack: { color: "#E01E5A", label: "Slack", sublabel: "/agentura run" },
  cron: { color: "#8B5CF6", label: "Cron", sublabel: "scheduled" },
  api: { color: "#0EA5E9", label: "REST API", sublabel: "webhooks" },
};

function TopologyGraph({
  skills,
  executions,
}: {
  skills: SkillInfo[];
  executions: { skill: string; outcome: string }[];
}) {
  if (skills.length === 0) {
    return <p className="py-12 text-center text-sm text-muted-foreground">No agents deployed</p>;
  }

  const nw = 160; // node width
  const nh = 50;  // node height
  const colGap = 70;
  const rowGap = 16;
  const channelW = 110; // channel node width
  const channelH = 44;

  const nodes: GraphNode[] = [];
  const edges: GraphEdge[] = [];

  // ─── Column layout offsets (channels → gateway → managers → skills) ──
  const col0 = 20;                           // input channels
  const col1 = col0 + channelW + colGap;     // gateway
  const col2 = col1 + nw + colGap;           // domain managers
  const col3 = col2 + nw + colGap;           // specialist/field skills

  // ─── Compute domain layout first to know total height ───────────
  const domains = [...new Set(skills.map((s) => s.domain))];
  const domainSkillCounts = domains.map(
    (d) => skills.filter((s) => s.domain === d).length
  );
  const totalRows = domainSkillCounts.reduce((a, b) => a + b, 0) + (domains.length - 1);
  const gatewayY = ((totalRows - 1) * (nh + rowGap)) / 2;

  // ─── Column -1: Input Channels ──────────────────────────────────
  const channels = ["slack", "cron", "api"] as const;
  const channelSpacing = 60;
  const channelsBlockH = channels.length * channelH + (channels.length - 1) * (channelSpacing - channelH);
  const channelsStartY = gatewayY + nh / 2 - channelsBlockH / 2;

  for (let i = 0; i < channels.length; i++) {
    const ch = channels[i];
    nodes.push({
      id: `channel/${ch}`,
      name: channelMeta[ch].label,
      domain: "channel",
      role: "channel",
      x: col0,
      y: channelsStartY + i * channelSpacing,
      status: "active",
      isChannel: true,
      channelType: ch,
    });
    edges.push({ from: `channel/${ch}`, to: "platform/classifier", dashed: true });
  }

  // ─── Column 0: Gateway ────────────────────────────────────────
  nodes.push({
    id: "platform/classifier",
    name: "classifier",
    domain: "gateway",
    role: "gateway",
    x: col1,
    y: gatewayY,
    status: "active",
    isGateway: true,
  });

  // ─── Column 1+: Domain skills ─────────────────────────────────
  let currentRow = 0;

  for (const domain of domains) {
    const domainSkills = skills.filter((s) => s.domain === domain);

    const roleOrder: Record<string, number> = { manager: 0, specialist: 1, field: 2 };
    domainSkills.sort(
      (a, b) => (roleOrder[a.role] ?? 2) - (roleOrder[b.role] ?? 2)
    );

    const manager = domainSkills.find((s) => s.role === "manager");
    const others = domainSkills.filter((s) => s.role !== "manager");

    if (manager) {
      const managerId = `${manager.domain}/${manager.name}`;
      const managerY = currentRow * (nh + rowGap) + (others.length * (nh + rowGap)) / 2;

      nodes.push({
        id: managerId,
        name: manager.name,
        domain: manager.domain,
        role: manager.role,
        x: col2,
        y: managerY,
        status: getStatus(managerId, executions),
      });

      edges.push({ from: "platform/classifier", to: managerId });

      for (let i = 0; i < others.length; i++) {
        const skill = others[i];
        const id = `${skill.domain}/${skill.name}`;
        nodes.push({
          id,
          name: skill.name,
          domain: skill.domain,
          role: skill.role,
          x: col3,
          y: currentRow * (nh + rowGap),
          status: getStatus(id, executions),
        });
        edges.push({ from: managerId, to: id });
        currentRow++;
      }

      if (others.length === 0) currentRow++;
    } else {
      for (let i = 0; i < domainSkills.length; i++) {
        const skill = domainSkills[i];
        const id = `${skill.domain}/${skill.name}`;
        nodes.push({
          id,
          name: skill.name,
          domain: skill.domain,
          role: skill.role,
          x: col2,
          y: currentRow * (nh + rowGap),
          status: getStatus(id, executions),
        });
        edges.push({ from: "platform/classifier", to: id });
        currentRow++;
      }
    }

    currentRow++;
  }

  const svgWidth = Math.max(...nodes.map((n) => n.x + nw + 40), 800);
  const svgHeight = Math.max(...nodes.map((n) => n.y + nh + 30), 300);
  const nodeMap = Object.fromEntries(nodes.map((n) => [n.id, n]));

  return (
    <div className="overflow-x-auto">
      <svg
        viewBox={`0 0 ${svgWidth} ${svgHeight}`}
        className="w-full"
        style={{ minHeight: Math.min(svgHeight, 500), maxHeight: 650 }}
      >
        <defs>
          <marker id="arrow" markerWidth="8" markerHeight="6" refX="8" refY="3" orient="auto">
            <path d="M0,0 L8,3 L0,6" fill="oklch(0.65 0 0)" />
          </marker>
          <marker id="arrow-channel" markerWidth="8" markerHeight="6" refX="8" refY="3" orient="auto">
            <path d="M0,0 L8,3 L0,6" fill="oklch(0.7 0 0)" />
          </marker>
        </defs>

        {/* Edges */}
        {edges.map((edge, i) => {
          const from = nodeMap[edge.from];
          const to = nodeMap[edge.to];
          if (!from || !to) return null;

          const fromW = from.isChannel ? channelW : nw;
          const x1 = from.x + fromW;
          const y1 = from.y + (from.isChannel ? channelH / 2 : nh / 2);
          const x2 = to.x;
          const y2 = to.y + nh / 2;

          if (Math.abs(y1 - y2) < 5) {
            return (
              <line key={i} x1={x1} y1={y1} x2={x2 - 4} y2={y2}
                stroke={edge.dashed ? "oklch(0.78 0 0)" : "oklch(0.75 0 0)"}
                strokeWidth={edge.dashed ? 1.2 : 1.5}
                strokeDasharray={edge.dashed ? "6 4" : undefined}
                markerEnd={edge.dashed ? "url(#arrow-channel)" : "url(#arrow)"} />
            );
          }

          const mx = x1 + (x2 - x1) * 0.4;
          return (
            <path key={i}
              d={`M${x1},${y1} C${mx},${y1} ${mx},${y2} ${x2 - 4},${y2}`}
              fill="none"
              stroke={edge.dashed ? "oklch(0.78 0 0)" : "oklch(0.75 0 0)"}
              strokeWidth={edge.dashed ? 1.2 : 1.5}
              strokeDasharray={edge.dashed ? "6 4" : undefined}
              markerEnd={edge.dashed ? "url(#arrow-channel)" : "url(#arrow)"} />
          );
        })}

        {/* Channel Nodes */}
        {nodes.filter((n) => n.isChannel).map((node) => {
          const meta = channelMeta[node.channelType!];
          return (
            <g key={node.id}>
              <rect x={node.x} y={node.y} width={channelW} height={channelH} rx={22}
                fill="white" stroke={meta.color} strokeWidth={1.5} strokeOpacity={0.4} />
              <rect x={node.x} y={node.y} width={channelW} height={channelH} rx={22}
                fill={meta.color} fillOpacity={0.06} />
              {/* Channel icon */}
              <ChannelIcon type={node.channelType!} x={node.x + 14} y={node.y + channelH / 2} color={meta.color} />
              <text x={node.x + 32} y={node.y + channelH / 2 - 5} fontSize={11} fontWeight={600}
                fontFamily="var(--font-geist-sans)" fill="oklch(0.25 0 0)" dominantBaseline="central">
                {meta.label}
              </text>
              <text x={node.x + 32} y={node.y + channelH / 2 + 10} fontSize={9}
                fontFamily="var(--font-geist-sans)" fill="oklch(0.55 0 0)" dominantBaseline="central">
                {meta.sublabel}
              </text>
              {/* Pulsing dot */}
              <circle cx={node.x + channelW - 14} cy={node.y + channelH / 2} r={4}
                fill={meta.color} fillOpacity={0.6}>
                <animate attributeName="r" values="3;5;3" dur="2s" repeatCount="indefinite" />
                <animate attributeName="fill-opacity" values="0.6;0.2;0.6" dur="2s" repeatCount="indefinite" />
              </circle>
              {/* Connection point */}
              <circle cx={node.x + channelW} cy={node.y + channelH / 2} r={3} fill={meta.color} fillOpacity={0.4} />
            </g>
          );
        })}

        {/* Agent Nodes */}
        {nodes.filter((n) => !n.isChannel).map((node) => {
          const color = node.isGateway ? "#6366f1" : domainColors[node.domain] ?? "#6b7280";
          const dotColor =
            node.status === "active" ? "#10b981"
            : node.status === "processing" ? "#f59e0b"
            : "#9ca3af";
          const href = node.isGateway ? "#" : `/dashboard/skills/${node.domain}/${node.name}`;

          return (
            <Link key={node.id} href={href}>
              <g className="cursor-pointer">
                <rect x={node.x} y={node.y} width={nw} height={nh} rx={8}
                  fill="white" stroke={color} strokeWidth={1.5} strokeOpacity={0.5} />
                <rect x={node.x} y={node.y} width={nw} height={nh} rx={8}
                  fill={color} fillOpacity={0.05} />
                <circle cx={node.x + 16} cy={node.y + nh / 2 - 4} r={5} fill={dotColor} />
                <text x={node.x + 28} y={node.y + nh / 2 - 4} fontSize={12} fontWeight={600}
                  fontFamily="var(--font-geist-sans)" fill="oklch(0.2 0 0)" dominantBaseline="central">
                  {node.name}
                </text>
                <text x={node.x + 28} y={node.y + nh / 2 + 12} fontSize={10}
                  fontFamily="var(--font-geist-sans)" fill="oklch(0.55 0 0)" dominantBaseline="central">
                  {node.isGateway ? "gateway" : node.domain}
                </text>
                <circle cx={node.x} cy={node.y + nh / 2} r={3} fill={color} fillOpacity={0.4} />
                <circle cx={node.x + nw} cy={node.y + nh / 2} r={3} fill={color} fillOpacity={0.4} />
              </g>
            </Link>
          );
        })}
      </svg>
    </div>
  );
}

/* SVG icons for input channels */
function ChannelIcon({ type, x, y, color }: { type: string; x: number; y: number; color: string }) {
  if (type === "slack") {
    return (
      <g transform={`translate(${x - 7}, ${y - 7})`}>
        <path d="M6 2a2 2 0 012 2v1h1a2 2 0 010 4H8v1a2 2 0 01-4 0V8H3a2 2 0 010-4h1V3a2 2 0 012-2z"
          fill={color} fillOpacity={0.8} transform="scale(1)" />
      </g>
    );
  }
  if (type === "cron") {
    return (
      <g transform={`translate(${x - 7}, ${y - 7})`}>
        <circle cx="7" cy="7" r="6" fill="none" stroke={color} strokeWidth={1.5} strokeOpacity={0.8} />
        <path d="M7 4v3.5l2.5 1.5" fill="none" stroke={color} strokeWidth={1.5} strokeLinecap="round" strokeOpacity={0.8} />
      </g>
    );
  }
  // api
  return (
    <g transform={`translate(${x - 7}, ${y - 7})`}>
      <path d="M3 7h8M7 3v8M4 4l6 6M10 4l-6 6" fill="none" stroke={color} strokeWidth={1.2} strokeLinecap="round" strokeOpacity={0.7} />
    </g>
  );
}

function getStatus(
  skillId: string,
  executions: { skill: string; outcome: string }[]
): "active" | "processing" | "idle" {
  const execs = executions.filter((e) => e.skill === skillId);
  if (execs.some((e) => e.outcome === "pending_review" || e.outcome === "pending_approval"))
    return "processing";
  return execs.length > 0 ? "active" : "idle";
}

/* ── Live Activity Feed ──────────────────────────────────────────── */

function LiveActivityFeed({
  events,
  executions,
}: {
  events: PlatformEvent[];
  executions: { skill: string; outcome: string; latency_ms: number; execution_id: string }[];
}) {
  const [paused, setPaused] = useState(false);

  // Build feed items from events + recent executions
  const feedItems = buildFeedItems(events, executions);

  return (
    <div className="rounded-xl border border-border bg-card">
      {/* Feed header */}
      <div className="flex items-center justify-between border-b border-border px-5 py-3">
        <div className="flex items-center gap-2">
          <svg className="h-4 w-4 text-violet-500" fill="none" stroke="currentColor" viewBox="0 0 24 24">
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

      {/* Feed items */}
      <div className="divide-y divide-border">
        {feedItems.length === 0 ? (
          <p className="px-5 py-8 text-center text-sm text-muted-foreground">
            No recent activity. Run a skill to see live events.
          </p>
        ) : (
          feedItems.map((item, i) => (
            <div
              key={i}
              className={`flex items-center gap-4 px-5 py-3.5 transition-colors ${
                i === 0 ? "bg-blue-50/50" : ""
              }`}
            >
              <FeedIcon type={item.type} />
              <div className="min-w-0 flex-1">
                <p className="text-sm font-medium">{item.message}</p>
                <p className="mt-0.5 text-xs text-muted-foreground">
                  {item.domain} &middot; {item.agent} &middot; {item.timeAgo}
                </p>
              </div>
              <FeedDot type={item.type} />
            </div>
          ))
        )}
      </div>
    </div>
  );
}

interface FeedItem {
  type: "execution" | "reflexion" | "optimization" | "processing" | "error";
  message: string;
  domain: string;
  agent: string;
  timeAgo: string;
}

function buildFeedItems(
  events: PlatformEvent[],
  executions: { skill: string; outcome: string; latency_ms: number; execution_id: string }[]
): FeedItem[] {
  const items: FeedItem[] = [];

  // From events
  for (const evt of events.slice(0, 5)) {
    const [domain, agent] = (evt.skill || evt.domain || "").split("/");
    items.push({
      type: eventTypeToFeedType(evt.event_type),
      message: evt.message || eventTypeToMessage(evt.event_type, evt.skill),
      domain: evt.domain || domain || "",
      agent: agent || evt.skill || "",
      timeAgo: timeAgo(evt.timestamp),
    });
  }

  // From recent executions (fill up to 8 items)
  for (const exec of executions.slice(0, 8 - items.length)) {
    const [domain, ...rest] = exec.skill.split("/");
    const agent = rest.join("/");
    items.push({
      type: exec.outcome === "rejected" ? "error" : "execution",
      message:
        exec.outcome === "accepted"
          ? `Completed execution in ${(exec.latency_ms / 1000).toFixed(1)}s`
          : exec.outcome === "corrected"
            ? "Execution corrected by user"
            : exec.outcome === "pending_approval"
              ? "Awaiting approval"
              : `Completed execution successfully`,
      domain,
      agent,
      timeAgo: "recent",
    });
  }

  return items.slice(0, 8);
}

function eventTypeToFeedType(type: string): FeedItem["type"] {
  if (type === "skill_executed") return "execution";
  if (type === "reflexion_generated") return "reflexion";
  if (type === "correction_submitted") return "optimization";
  if (type === "test_generated") return "processing";
  return "execution";
}

function eventTypeToMessage(type: string, skill?: string): string {
  switch (type) {
    case "skill_executed":
      return "Completed execution successfully";
    case "reflexion_generated":
      return "Optimized performance automatically";
    case "correction_submitted":
      return "Correction applied to agent";
    case "test_generated":
      return "Generated regression test";
    default:
      return type.replace(/_/g, " ");
  }
}

function FeedIcon({ type }: { type: FeedItem["type"] }) {
  const bg =
    type === "execution"
      ? "bg-blue-100 text-blue-600"
      : type === "reflexion"
        ? "bg-violet-100 text-violet-600"
        : type === "optimization"
          ? "bg-amber-100 text-amber-600"
          : type === "error"
            ? "bg-red-100 text-red-600"
            : "bg-gray-100 text-gray-600";

  return (
    <div className={`flex h-9 w-9 shrink-0 items-center justify-center rounded-lg ${bg}`}>
      {type === "execution" ? (
        <svg className="h-4 w-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 10V3L4 14h7v7l9-11h-7z" />
        </svg>
      ) : type === "reflexion" ? (
        <svg className="h-4 w-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15" />
        </svg>
      ) : type === "optimization" ? (
        <svg className="h-4 w-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-2.5L13.732 4c-.77-.833-1.964-.833-2.732 0L4.082 16.5c-.77.833.192 2.5 1.732 2.5z" />
        </svg>
      ) : (
        <svg className="h-4 w-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" />
        </svg>
      )}
    </div>
  );
}

function FeedDot({ type }: { type: FeedItem["type"] }) {
  const color =
    type === "execution"
      ? "bg-blue-500"
      : type === "reflexion"
        ? "bg-violet-500"
        : type === "optimization"
          ? "bg-amber-500"
          : type === "error"
            ? "bg-red-500"
            : "bg-gray-400";
  return <span className={`h-2.5 w-2.5 shrink-0 rounded-full ${color}`} />;
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
