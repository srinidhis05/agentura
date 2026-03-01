"use client";

import { useQuery } from "@tanstack/react-query";
import Link from "next/link";
import { listFleetSessions } from "@/lib/api";
import type { FleetSession } from "@/lib/api";
import { useState } from "react";

const STATUS_COLORS: Record<string, string> = {
  pending: "bg-gray-500",
  running: "bg-blue-500 animate-pulse",
  completed: "bg-emerald-500",
  failed: "bg-red-500",
  cancelled: "bg-amber-500",
};

export default function FleetPage() {
  const [filter, setFilter] = useState<string>("all");

  const { data: sessions, isLoading } = useQuery({
    queryKey: ["fleet-sessions", filter],
    queryFn: () => listFleetSessions(filter === "all" ? undefined : filter),
    refetchInterval: 5_000,
  });

  const allSessions = sessions ?? [];

  return (
    <div className="space-y-6">
      <div className="flex items-start justify-between">
        <div>
          <h1 className="text-2xl font-bold tracking-tight">Fleet Sessions</h1>
          <p className="mt-1 text-sm text-muted-foreground">
            Parallel pipeline executions across agent fleets
          </p>
        </div>
        <div className="flex gap-1.5">
          {["all", "running", "completed", "failed"].map((s) => (
            <button
              key={s}
              onClick={() => setFilter(s)}
              className={`rounded-lg px-3 py-1.5 text-xs font-medium transition-colors ${
                filter === s
                  ? "bg-blue-500/20 text-blue-400"
                  : "text-muted-foreground hover:bg-gray-800"
              }`}
            >
              {s}
            </button>
          ))}
        </div>
      </div>

      {isLoading ? (
        <div className="py-20 text-center text-sm text-muted-foreground">Loading sessions...</div>
      ) : allSessions.length === 0 ? (
        <div className="rounded-xl border border-border bg-card py-20 text-center">
          <p className="text-sm text-muted-foreground">No fleet sessions yet.</p>
          <p className="mt-1 text-xs text-muted-foreground">
            Fleet sessions are created when a PR triggers the parallel review pipeline.
          </p>
        </div>
      ) : (
        <div className="rounded-xl border border-border bg-card">
          <table className="w-full text-sm">
            <thead>
              <tr className="border-b border-border text-left text-xs text-muted-foreground">
                <th className="px-4 py-3 font-medium">Session</th>
                <th className="px-4 py-3 font-medium">Repo</th>
                <th className="px-4 py-3 font-medium">PR</th>
                <th className="px-4 py-3 font-medium">Status</th>
                <th className="px-4 py-3 font-medium">Agents</th>
                <th className="px-4 py-3 font-medium">Cost</th>
                <th className="px-4 py-3 font-medium">Created</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-border">
              {allSessions.map((session) => (
                <SessionRow key={session.session_id} session={session} />
              ))}
            </tbody>
          </table>
        </div>
      )}
    </div>
  );
}

function SessionRow({ session }: { session: FleetSession }) {
  const completed = session.completed_agents ?? 0;
  const failed = session.failed_agents ?? 0;
  const total = session.total_agents ?? 0;
  const progress = total > 0 ? ((completed + failed) / total) * 100 : 0;

  return (
    <tr className="hover:bg-gray-900/50 transition-colors">
      <td className="px-4 py-3">
        <Link
          href={`/dashboard/fleet/${session.session_id}`}
          className="font-mono text-xs text-blue-400 hover:underline"
        >
          {session.session_id}
        </Link>
      </td>
      <td className="px-4 py-3 text-xs text-gray-300">{session.repo || "—"}</td>
      <td className="px-4 py-3 text-xs">
        {session.pr_number ? (
          <a
            href={session.pr_url}
            target="_blank"
            rel="noopener noreferrer"
            className="text-blue-400 hover:underline"
          >
            #{session.pr_number}
          </a>
        ) : (
          "—"
        )}
      </td>
      <td className="px-4 py-3">
        <span className="flex items-center gap-1.5">
          <span className={`h-2 w-2 rounded-full ${STATUS_COLORS[session.status] ?? "bg-gray-500"}`} />
          <span className="text-xs">{session.status}</span>
        </span>
      </td>
      <td className="px-4 py-3">
        <div className="flex items-center gap-2">
          <div className="h-1.5 w-16 rounded-full bg-gray-800">
            <div
              className="h-1.5 rounded-full bg-emerald-500 transition-all"
              style={{ width: `${progress}%` }}
            />
          </div>
          <span className="text-[10px] text-muted-foreground">
            {completed}/{total}
          </span>
        </div>
      </td>
      <td className="px-4 py-3 font-mono text-xs text-gray-400">
        ${(session.total_cost_usd ?? 0).toFixed(3)}
      </td>
      <td className="px-4 py-3 text-xs text-muted-foreground">
        {session.created_at ? timeAgo(session.created_at) : "—"}
      </td>
    </tr>
  );
}

function timeAgo(ts: string): string {
  const diff = Date.now() - new Date(ts).getTime();
  const secs = Math.floor(diff / 1000);
  if (secs < 60) return `${secs}s ago`;
  const mins = Math.floor(secs / 60);
  if (mins < 60) return `${mins}m ago`;
  const hrs = Math.floor(mins / 60);
  if (hrs < 24) return `${hrs}h ago`;
  return `${Math.floor(hrs / 24)}d ago`;
}
