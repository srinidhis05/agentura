"use client";

import { useQuery } from "@tanstack/react-query";
import Link from "next/link";
import { useState } from "react";
import { listTickets, getTicketStats, listAgents } from "@/lib/api";
import type { TicketInfo } from "@/lib/types";
import { ticketColumnColors, priorityColors } from "@/lib/colors";

const columns = [
  { key: "open", label: "Open" },
  { key: "in_progress", label: "In Progress" },
  { key: "resolved", label: "Resolved" },
  { key: "escalated", label: "Escalated" },
];

function timeAgo(dateStr: string): string {
  const diff = Date.now() - new Date(dateStr).getTime();
  const mins = Math.floor(diff / 60000);
  if (mins < 60) return `${mins}m ago`;
  const hrs = Math.floor(mins / 60);
  if (hrs < 24) return `${hrs}h ago`;
  return `${Math.floor(hrs / 24)}d ago`;
}

export default function TicketsPage() {
  const [domainFilter, setDomainFilter] = useState<string>("");
  const [priorityFilter, setPriorityFilter] = useState<string>("");

  const { data: tickets = [], isLoading } = useQuery({
    queryKey: ["tickets", domainFilter],
    queryFn: () => listTickets({ domain: domainFilter || undefined, limit: 100 }),
    refetchInterval: 8000,
  });

  const { data: stats } = useQuery({
    queryKey: ["ticket-stats", domainFilter],
    queryFn: () => getTicketStats(domainFilter || undefined),
    refetchInterval: 15000,
  });

  const { data: agents = [] } = useQuery({
    queryKey: ["agents"],
    queryFn: () => listAgents(),
  });

  const agentMap = new Map(agents.map((a) => [a.id, a.display_name || a.name]));

  const filteredTickets = priorityFilter
    ? tickets.filter((t) => t.priority === Number(priorityFilter))
    : tickets;

  const ticketsByStatus: Record<string, TicketInfo[]> = {};
  for (const col of columns) {
    ticketsByStatus[col.key] = filteredTickets.filter((t) => t.status === col.key);
  }

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-foreground">Tickets</h1>
          <p className="text-sm text-muted-foreground mt-1">
            {stats?.total || 0} total tickets
            {stats?.total_cost_usd ? ` | $${stats.total_cost_usd.toFixed(2)} total cost` : ""}
          </p>
        </div>
        <div className="flex items-center gap-2">
          <select
            value={priorityFilter}
            onChange={(e) => setPriorityFilter(e.target.value)}
            className="rounded-lg border border-border bg-card px-3 py-1.5 text-sm text-foreground"
          >
            <option value="">All priorities</option>
            <option value="1">P1 — Critical</option>
            <option value="2">P2 — High</option>
            <option value="3">P3 — Medium</option>
            <option value="4">P4 — Low</option>
            <option value="5">P5 — Minimal</option>
          </select>
          <select
            value={domainFilter}
            onChange={(e) => setDomainFilter(e.target.value)}
            className="rounded-lg border border-border bg-card px-3 py-1.5 text-sm text-foreground"
          >
            <option value="">All domains</option>
            <option value="ecm">ECM</option>
            <option value="incubator">Incubator</option>
            <option value="ge">Global Equities</option>
          </select>
        </div>
      </div>

      {/* Stats row */}
      {stats && (
        <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
          {columns.map((col) => (
            <div key={col.key} className={`rounded-lg border-l-2 bg-card shadow-sm border border-border p-3 ${ticketColumnColors[col.key] || ""}`}>
              <div className="text-xs text-muted-foreground">{col.label}</div>
              <div className="text-2xl font-bold text-foreground">
                {(stats as unknown as Record<string, number>)[col.key] || 0}
              </div>
            </div>
          ))}
        </div>
      )}

      {/* Kanban board */}
      {isLoading ? (
        <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
          {columns.map((col) => (
            <div key={col.key} className="h-64 rounded-xl bg-muted dark:bg-card/50 animate-pulse border border-border" />
          ))}
        </div>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-4 gap-4">
          {columns.map((col) => (
            <div key={col.key} className="space-y-2">
              <h3 className={`text-sm font-semibold text-foreground border-b-2 pb-2 ${ticketColumnColors[col.key] || ""}`}>
                {col.label}
                <span className="ml-2 text-xs font-normal text-muted-foreground">
                  ({ticketsByStatus[col.key]?.length || 0})
                </span>
              </h3>
              <div className="space-y-2 max-h-[600px] overflow-y-auto">
                {(ticketsByStatus[col.key] || []).map((ticket) => (
                  <Link
                    key={ticket.id}
                    href={`/dashboard/tickets/${ticket.id}`}
                    className="block rounded-lg border border-border bg-card shadow-sm p-3 hover:shadow-md transition-all"
                  >
                    <div className="flex items-start justify-between gap-2">
                      <h4 className="text-sm font-medium text-foreground line-clamp-2">{ticket.title}</h4>
                      <span className={`flex-shrink-0 rounded px-1.5 py-0.5 text-[10px] font-medium ${priorityColors[ticket.priority] || priorityColors[3]}`}>
                        P{ticket.priority}
                      </span>
                    </div>
                    <div className="mt-2 flex items-center justify-between text-xs text-muted-foreground">
                      <span className="font-mono">{ticket.domain}</span>
                      <span>{timeAgo(ticket.created_at)}</span>
                    </div>
                    {ticket.assigned_to && (
                      <div className="mt-1 text-xs text-muted-foreground truncate">
                        {agentMap.get(ticket.assigned_to) || ticket.assigned_to}
                      </div>
                    )}
                    {ticket.cost_usd > 0 && (
                      <div className="mt-1 text-xs text-muted-foreground">
                        ${ticket.cost_usd.toFixed(4)}
                      </div>
                    )}
                  </Link>
                ))}
                {(!ticketsByStatus[col.key] || ticketsByStatus[col.key].length === 0) && (
                  <div className="text-center py-8 text-xs text-muted-foreground">No tickets</div>
                )}
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
