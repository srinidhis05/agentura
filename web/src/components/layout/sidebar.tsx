"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { useQuery } from "@tanstack/react-query";
import { cn } from "@/lib/utils";
import { Switch } from "@/components/ui/switch";
import { useTheme } from "@/hooks/use-theme";
import { listAgents, listHeartbeatRuns } from "@/lib/api";
import { useState } from "react";
import { statusDot } from "@/lib/colors";

const navItems = [
  {
    href: "/chat",
    label: "Chat",
    icon: (
      <svg className="h-4 w-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M8 12h.01M12 12h.01M16 12h.01M21 12c0 4.418-4.03 8-9 8a9.863 9.863 0 01-4.255-.949L3 20l1.395-3.72C3.512 15.042 3 13.574 3 12c0-4.418 4.03-8 9-8s9 3.582 9 8z" />
      </svg>
    ),
  },
  {
    href: "/dashboard",
    label: "Dashboard",
    icon: (
      <svg className="h-4 w-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M4 6a2 2 0 012-2h2a2 2 0 012 2v2a2 2 0 01-2 2H6a2 2 0 01-2-2V6zm10 0a2 2 0 012-2h2a2 2 0 012 2v2a2 2 0 01-2 2h-2a2 2 0 01-2-2V6zM4 16a2 2 0 012-2h2a2 2 0 012 2v2a2 2 0 01-2 2H6a2 2 0 01-2-2v-2zm10 0a2 2 0 012-2h2a2 2 0 012 2v2a2 2 0 01-2 2h-2a2 2 0 01-2-2v-2z" />
      </svg>
    ),
  },
  {
    href: "/dashboard/executions",
    label: "Executions",
    icon: (
      <svg className="h-4 w-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M14.752 11.168l-3.197-2.132A1 1 0 0010 9.87v4.263a1 1 0 001.555.832l3.197-2.132a1 1 0 000-1.664z" />
        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
      </svg>
    ),
  },
  {
    href: "/dashboard/fleet",
    label: "Fleet",
    icon: (
      <svg className="h-4 w-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M19 11H5m14 0a2 2 0 012 2v6a2 2 0 01-2 2H5a2 2 0 01-2-2v-6a2 2 0 012-2m14 0V9a2 2 0 00-2-2M5 11V9a2 2 0 012-2m0 0V5a2 2 0 012-2h6a2 2 0 012 2v2M7 7h10" />
      </svg>
    ),
  },
  {
    href: "/dashboard/heartbeats",
    label: "Heartbeats",
    icon: (
      <svg className="h-4 w-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M3 12h3l3-9 3 18 3-9h3" />
      </svg>
    ),
  },
  {
    href: "/dashboard/org-chart",
    label: "Org Chart",
    icon: (
      <svg className="h-4 w-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M7.5 21L3 16.5m0 0L7.5 12M3 16.5h13.5m0-13.5L21 7.5m0 0L16.5 12M21 7.5H7.5" />
      </svg>
    ),
  },
  {
    href: "/dashboard/memory",
    label: "Memory",
    icon: (
      <svg className="h-4 w-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M9.663 17h4.673M12 3v1m6.364 1.636l-.707.707M21 12h-1M4 12H3m3.343-5.657l-.707-.707m2.828 9.9a5 5 0 117.072 0l-.548.547A3.374 3.374 0 0014 18.469V19a2 2 0 11-4 0v-.531c0-.895-.356-1.754-.988-2.386l-.548-.547z" />
      </svg>
    ),
  },
];

export function Sidebar() {
  const pathname = usePathname();
  const { isDark, toggle } = useTheme();
  const [agentsOpen, setAgentsOpen] = useState(true);

  const { data: agents = [] } = useQuery({
    queryKey: ["sidebar-agents"],
    queryFn: () => listAgents(),
    refetchInterval: 15000,
  });

  const { data: heartbeats = [] } = useQuery({
    queryKey: ["sidebar-heartbeats"],
    queryFn: () => listHeartbeatRuns({ status: "running", limit: 50 }),
    refetchInterval: 8000,
  });

  const liveByAgent = new Map<string, number>();
  for (const hb of heartbeats) {
    liveByAgent.set(hb.agent_id, (liveByAgent.get(hb.agent_id) || 0) + 1);
  }

  return (
    <aside className="flex h-screen w-52 flex-col border-r border-border bg-sidebar">
      {/* Brand */}
      <div className="px-5 pt-6 pb-5">
        <Link href="/" className="flex items-center gap-2.5">
          <div className="flex h-7 w-7 items-center justify-center rounded-lg bg-gradient-to-br from-blue-500 to-violet-600">
            <svg className="h-3.5 w-3.5 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2.5} d="M13 10V3L4 14h7v7l9-11h-7z" />
            </svg>
          </div>
          <span className="text-base font-bold tracking-tight text-foreground">Agentura</span>
        </Link>
      </div>

      {/* Navigation */}
      <nav className="flex-1 overflow-y-auto px-3 scrollbar-none">
        <div className="space-y-0.5">
          {navItems.map((item) => {
            const active =
              pathname === item.href || pathname.startsWith(item.href + "/");
            return (
              <Link
                key={item.href}
                href={item.href}
                className={cn(
                  "flex items-center gap-2.5 rounded-lg px-3 py-2 text-[13px] font-medium transition-colors",
                  active
                    ? "border-l-2 border-l-sidebar-primary bg-sidebar-accent text-sidebar-primary"
                    : "text-muted-foreground hover:bg-sidebar-accent/50 hover:text-foreground",
                )}
              >
                {item.icon}
                {item.label}
              </Link>
            );
          })}
        </div>

        {/* Collapsible Agents Section */}
        {agents.length > 0 && (
          <div className="mt-4">
            <button
              onClick={() => setAgentsOpen(!agentsOpen)}
              className="flex items-center gap-1 w-full px-3 py-1"
            >
              <svg
                className={cn(
                  "h-3 w-3 text-muted-foreground transition-transform",
                  agentsOpen && "rotate-90"
                )}
                fill="none"
                stroke="currentColor"
                viewBox="0 0 24 24"
              >
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 5l7 7-7 7" />
              </svg>
              <span className="text-[10px] font-medium text-muted-foreground uppercase tracking-widest">
                Agents
              </span>
              {heartbeats.length > 0 && (
                <span className="ml-auto flex items-center gap-1">
                  <span className="relative flex h-1.5 w-1.5">
                    <span className="animate-ping absolute h-full w-full rounded-full bg-blue-400 opacity-75" />
                    <span className="relative inline-flex rounded-full h-1.5 w-1.5 bg-blue-500" />
                  </span>
                  <span className="text-[10px] font-medium text-blue-600 dark:text-blue-400 tabular-nums">
                    {heartbeats.length}
                  </span>
                </span>
              )}
            </button>

            {agentsOpen && (
              <div className="mt-0.5 space-y-0">
                {agents.map((agent) => {
                  const isActive = pathname === `/dashboard/agents/${agent.id}`;
                  const liveCount = liveByAgent.get(agent.id) || 0;
                  return (
                    <Link
                      key={agent.id}
                      href={`/dashboard/agents/${agent.id}`}
                      className={cn(
                        "flex items-center gap-2 px-3 py-1.5 text-[13px] rounded-md transition-colors",
                        isActive
                          ? "bg-sidebar-accent text-foreground"
                          : "text-muted-foreground hover:bg-sidebar-accent/50 hover:text-foreground"
                      )}
                    >
                      <div className={`h-1.5 w-1.5 rounded-full shrink-0 ${statusDot[agent.status] || statusDot.idle}`} />
                      <span className="flex-1 truncate">
                        {agent.display_name || agent.name}
                      </span>
                      {liveCount > 0 && (
                        <span className="ml-auto flex items-center gap-1 shrink-0">
                          <span className="relative flex h-1.5 w-1.5">
                            <span className="animate-ping absolute h-full w-full rounded-full bg-blue-400 opacity-75" />
                            <span className="relative inline-flex rounded-full h-1.5 w-1.5 bg-blue-500" />
                          </span>
                          <span className="text-[10px] font-medium text-blue-600 dark:text-blue-400 tabular-nums">
                            {liveCount}
                          </span>
                        </span>
                      )}
                    </Link>
                  );
                })}
              </div>
            )}
          </div>
        )}
      </nav>

      {/* Footer */}
      <div className="border-t border-border px-5 py-4 space-y-3">
        <label className="flex items-center justify-between cursor-pointer">
          <div className="flex items-center gap-2 text-[13px] text-muted-foreground">
            {isDark ? (
              <svg className="h-4 w-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M20.354 15.354A9 9 0 018.646 3.646 9.003 9.003 0 0012 21a9.003 9.003 0 008.354-5.646z" />
              </svg>
            ) : (
              <svg className="h-4 w-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M12 3v1m0 16v1m9-9h-1M4 12H3m15.364 6.364l-.707-.707M6.343 6.343l-.707-.707m12.728 0l-.707.707M6.343 17.657l-.707.707M16 12a4 4 0 11-8 0 4 4 0 018 0z" />
              </svg>
            )}
            {isDark ? "Dark" : "Light"}
          </div>
          <Switch checked={isDark} onCheckedChange={toggle} />
        </label>
        <div className="flex items-center justify-between">
          <span className="text-[10px] text-muted-foreground">Version</span>
          <span className="font-mono text-[10px] text-muted-foreground">v1.2.4</span>
        </div>
      </div>
    </aside>
  );
}
