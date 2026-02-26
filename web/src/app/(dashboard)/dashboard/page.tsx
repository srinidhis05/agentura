"use client";

import { useQuery } from "@tanstack/react-query";
import Link from "next/link";
import { listSkills, listExecutions, listReflexions, listEvents } from "@/lib/api";
import type { SkillInfo, PlatformEvent } from "@/lib/types";
import { useState } from "react";

const domainColors: Record<string, string> = {
  dev: "#3b82f6",
  finance: "#f59e0b",
  hr: "#ec4899",
  productivity: "#8b5cf6",
  platform: "#6366f1",
};

const domainEmojis: Record<string, string> = {
  dev: "\u{1F4BB}",
  finance: "\u{1F4B0}",
  hr: "\u{1F465}",
  productivity: "\u26A1",
  platform: "\u{1F310}",
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

  const allSkills = skills ?? [];
  const allExecs = executions ?? [];
  const allEvents = events ?? [];

  const runningCount = allSkills.filter(
    (s) => s.health === "healthy" || s.deploy_status === "active"
  ).length;

  // Group skills by domain
  const classifier = allSkills.find(
    (s) => s.domain === "platform" && s.name === "classifier"
  );
  const domainSkills = groupByDomain(
    allSkills.filter(
      (s) => s.domain !== "platform"
    )
  );

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

      {/* Dark Agent Network */}
      <div className="rounded-2xl bg-gray-950 p-6 md:p-8">
        {/* Legend */}
        <div className="mb-6 flex flex-wrap items-center gap-5 text-xs text-gray-400">
          <span className="flex items-center gap-1.5">
            <span className="h-2.5 w-2.5 rounded-full bg-emerald-500" /> active
          </span>
          <span className="flex items-center gap-1.5">
            <span className="h-2.5 w-2.5 rounded-full bg-amber-500" /> processing
          </span>
          <span className="flex items-center gap-1.5">
            <span className="h-2.5 w-2.5 rounded-full bg-gray-500" /> idle
          </span>
        </div>

        {/* Classifier — top center */}
        {classifier && (
          <div className="mb-8 flex justify-center">
            <ClassifierCard skill={classifier} executions={allExecs} />
          </div>
        )}

        {/* Connection line from classifier to domains */}
        <div className="mb-6 flex justify-center">
          <div className="h-8 w-px bg-gradient-to-b from-indigo-500/60 to-gray-700/30" />
        </div>

        {/* Horizontal distribution line */}
        <div className="mx-auto mb-6 hidden max-w-4xl md:block">
          <div className="h-px bg-gradient-to-r from-transparent via-gray-600/40 to-transparent" />
        </div>

        {/* Domain Department Cards */}
        <div className="grid gap-5 sm:grid-cols-2 xl:grid-cols-4">
          {Object.entries(domainSkills).map(([domain, skills]) => (
            <DomainCard
              key={domain}
              domain={domain}
              skills={skills}
              executions={allExecs}
            />
          ))}
        </div>
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

/* ── Helpers ── */

function groupByDomain(skills: SkillInfo[]): Record<string, SkillInfo[]> {
  const groups: Record<string, SkillInfo[]> = {};
  for (const s of skills) {
    (groups[s.domain] ??= []).push(s);
  }
  // Sort domains consistently
  const sorted: Record<string, SkillInfo[]> = {};
  for (const d of ["dev", "finance", "hr", "productivity"]) {
    if (groups[d]) sorted[d] = groups[d];
  }
  // Include any other domains not in the predefined list
  for (const d of Object.keys(groups)) {
    if (!sorted[d]) sorted[d] = groups[d];
  }
  return sorted;
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

/* ── Classifier Card ── */

function ClassifierCard({
  skill,
  executions,
}: {
  skill: SkillInfo;
  executions: { skill: string; outcome: string }[];
}) {
  const status = getStatus(`${skill.domain}/${skill.name}`, executions);
  const color = "#6366f1";
  const dotColor =
    status === "active" ? "#10b981" : status === "processing" ? "#f59e0b" : "#6b7280";

  return (
    <div
      className="relative w-full max-w-md rounded-xl border border-indigo-500/30 bg-gray-900/80 p-5"
      style={{ boxShadow: `0 0 30px ${color}20, 0 0 60px ${color}10` }}
    >
      <div className="flex items-center gap-4">
        <div
          className="flex h-12 w-12 shrink-0 items-center justify-center rounded-lg text-sm font-bold text-white"
          style={{ backgroundColor: color }}
        >
          {skill.display_avatar || "CL"}
        </div>
        <div className="min-w-0 flex-1">
          <div className="flex items-center gap-2">
            <span className="text-base font-semibold text-white">
              {skill.display_title || "Classifier"}
            </span>
            <span
              className="h-2.5 w-2.5 rounded-full"
              style={{ backgroundColor: dotColor }}
            />
          </div>
          <p className="text-sm text-gray-400">
            {skill.display_subtitle || "Platform Router"}
          </p>
        </div>
      </div>
      {skill.display_tags?.length > 0 && (
        <div className="mt-3 flex flex-wrap gap-1.5">
          {skill.display_tags.map((tag) => (
            <span
              key={tag}
              className="rounded-full px-2 py-0.5 text-[10px] font-medium"
              style={{
                backgroundColor: `${color}20`,
                color: `${color}`,
                border: `1px solid ${color}30`,
              }}
            >
              {tag}
            </span>
          ))}
        </div>
      )}
    </div>
  );
}

/* ── Domain Department Card ── */

function DomainCard({
  domain,
  skills,
  executions,
}: {
  domain: string;
  skills: SkillInfo[];
  executions: { skill: string; outcome: string }[];
}) {
  const color = domainColors[domain] ?? "#6b7280";
  const emoji = domainEmojis[domain] ?? "\u{1F4E6}";

  // Triage/manager becomes the domain header, others are agent cards
  const manager = skills.find((s) => s.role === "manager");
  const agents = skills.filter((s) => s.role !== "manager");

  return (
    <div
      className="rounded-xl border bg-gray-900/60"
      style={{ borderColor: `${color}30` }}
    >
      {/* Domain header */}
      <div
        className="flex items-center gap-2.5 rounded-t-xl px-4 py-3"
        style={{ backgroundColor: `${color}10` }}
      >
        <span className="text-lg">{emoji}</span>
        <div className="min-w-0 flex-1">
          <span className="text-sm font-semibold uppercase tracking-wide text-white">
            {domain}
          </span>
          {manager && (
            <p className="truncate text-[11px] text-gray-400">
              {manager.display_subtitle || manager.description || `${domain} triage`}
            </p>
          )}
        </div>
        <span className="text-[10px] text-gray-500">
          {agents.length} agent{agents.length !== 1 ? "s" : ""}
        </span>
      </div>

      {/* Agent cards */}
      <div className="space-y-2 p-3">
        {agents.length === 0 ? (
          <p className="py-4 text-center text-xs text-gray-600">No agents</p>
        ) : (
          agents.map((agent) => (
            <AgentCard
              key={`${agent.domain}/${agent.name}`}
              skill={agent}
              domainColor={color}
              executions={executions}
            />
          ))
        )}
      </div>
    </div>
  );
}

/* ── Individual Agent Card ── */

function AgentCard({
  skill,
  domainColor,
  executions,
}: {
  skill: SkillInfo;
  domainColor: string;
  executions: { skill: string; outcome: string }[];
}) {
  const skillId = `${skill.domain}/${skill.name}`;
  const status = getStatus(skillId, executions);
  const color = skill.display_color || domainColor;
  const dotColor =
    status === "active" ? "#10b981" : status === "processing" ? "#f59e0b" : "#6b7280";

  return (
    <Link href={`/dashboard/skills/${skill.domain}/${skill.name}`}>
      <div className="group rounded-lg border border-gray-800 bg-gray-900/80 p-3 transition-all hover:border-gray-600 hover:bg-gray-800/80">
        <div className="flex items-start gap-3">
          {/* Avatar */}
          <div
            className="flex h-9 w-9 shrink-0 items-center justify-center rounded-lg text-xs font-bold text-white"
            style={{ backgroundColor: color }}
          >
            {skill.display_avatar || skill.name.slice(0, 2).toUpperCase()}
          </div>

          {/* Info */}
          <div className="min-w-0 flex-1">
            <div className="flex items-center gap-1.5">
              <span className="text-sm font-medium text-gray-200 group-hover:text-white">
                {skill.display_title || skill.name.replace(/-/g, " ")}
              </span>
              <span
                className="h-2 w-2 shrink-0 rounded-full"
                style={{ backgroundColor: dotColor }}
              />
            </div>
            <p className="mt-0.5 truncate text-[11px] text-gray-500">
              {skill.display_subtitle || skill.role}
            </p>
          </div>
        </div>

        {/* Tags */}
        {skill.display_tags?.length > 0 && (
          <div className="mt-2 flex flex-wrap gap-1">
            {skill.display_tags.map((tag) => (
              <span
                key={tag}
                className="rounded-full px-1.5 py-0.5 text-[9px] font-medium"
                style={{
                  backgroundColor: `${color}15`,
                  color: `${color}cc`,
                }}
              >
                {tag}
              </span>
            ))}
          </div>
        )}
      </div>
    </Link>
  );
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

  for (const evt of events.slice(0, 5)) {
    const [domain, agent] = (evt.skill || evt.domain || "").split("/");
    items.push({
      type: eventTypeToFeedType(evt.event_type),
      message: evt.message || eventTypeToMessage(evt.event_type),
      domain: evt.domain || domain || "",
      agent: agent || evt.skill || "",
      timeAgo: timeAgo(evt.timestamp),
    });
  }

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

function eventTypeToMessage(type: string): string {
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
