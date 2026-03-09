"use client";

import { useState } from "react";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { useParams } from "next/navigation";
import Link from "next/link";
import { getTicket, getAgent, updateTicket } from "@/lib/api";
import { Tabs, TabsList, TabsTrigger, TabsContent } from "@/components/ui/tabs";
import { Badge } from "@/components/ui/badge";
import { cn } from "@/lib/utils";
import { ticketStatusColors, priorityConfig, traceBorderColors } from "@/lib/colors";

const statusFlow = ["open", "in_progress", "resolved", "escalated"] as const;

const traceIcons: Record<string, string> = {
  tool_call: "W",
  status_change: "S",
  delegation: "D",
  escalation: "!",
  note: "N",
};

function timeAgo(dateStr: string): string {
  const diff = Date.now() - new Date(dateStr).getTime();
  const mins = Math.floor(diff / 60000);
  if (mins < 1) return "just now";
  if (mins < 60) return `${mins}m ago`;
  const hrs = Math.floor(mins / 60);
  if (hrs < 24) return `${hrs}h ago`;
  return `${Math.floor(hrs / 24)}d ago`;
}

function guessTraceType(tool: string): string {
  if (tool.includes("status")) return "status_change";
  if (tool.includes("delegat")) return "delegation";
  if (tool.includes("escalat")) return "escalation";
  return "tool_call";
}

export default function TicketDetailPage() {
  const params = useParams();
  const ticketId = params.ticket_id as string;
  const queryClient = useQueryClient();

  const [statusOpen, setStatusOpen] = useState(false);
  const [priorityOpen, setPriorityOpen] = useState(false);
  const [expandedTrace, setExpandedTrace] = useState<number | null>(null);

  const { data: ticket, isLoading } = useQuery({
    queryKey: ["ticket", ticketId],
    queryFn: () => getTicket(ticketId),
  });

  const { data: assignee } = useQuery({
    queryKey: ["agent", ticket?.assigned_to],
    queryFn: () => getAgent(ticket!.assigned_to!),
    enabled: !!ticket?.assigned_to,
  });

  const { data: creator } = useQuery({
    queryKey: ["agent", ticket?.created_by],
    queryFn: () => getAgent(ticket!.created_by!),
    enabled: !!ticket?.created_by,
  });

  const statusMutation = useMutation({
    mutationFn: (status: string) => updateTicket(ticketId, { status }),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["ticket", ticketId] });
      queryClient.invalidateQueries({ queryKey: ["tickets"] });
      setStatusOpen(false);
    },
  });

  const priorityMutation = useMutation({
    mutationFn: (priority: number) => updateTicket(ticketId, { priority }),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["ticket", ticketId] });
      queryClient.invalidateQueries({ queryKey: ["tickets"] });
      setPriorityOpen(false);
    },
  });

  if (isLoading) {
    return (
      <div className="space-y-4">
        <div className="h-4 w-32 rounded bg-muted dark:bg-card/50 animate-pulse" />
        <div className="h-8 w-80 rounded bg-muted dark:bg-card/50 animate-pulse" />
        <div className="flex gap-6">
          <div className="flex-1 h-96 rounded-xl bg-muted dark:bg-card/50 animate-pulse border border-border" />
          <div className="w-80 h-96 rounded-xl bg-muted dark:bg-card/50 animate-pulse border border-border hidden lg:block" />
        </div>
      </div>
    );
  }

  if (!ticket) {
    return <div className="text-muted-foreground">Ticket not found</div>;
  }

  const hasSubTickets = ticket.sub_tickets && ticket.sub_tickets.length > 0;

  return (
    <div className="space-y-5">
      {/* Breadcrumb */}
      <div className="flex items-center gap-2 text-sm text-muted-foreground">
        <Link href="/dashboard/tickets" className="hover:text-foreground transition-colors">
          Tickets
        </Link>
        <span>/</span>
        <span className="text-foreground font-mono text-xs">{ticket.id}</span>
      </div>

      {/* Title */}
      <div>
        <h1 className="text-xl font-bold text-foreground leading-tight">{ticket.title}</h1>
        <p className="text-xs text-muted-foreground font-mono mt-1">{ticket.id}</p>
      </div>

      {/* Two-column layout */}
      <div className="flex flex-col lg:flex-row gap-6">
        {/* Main content */}
        <div className="flex-1 min-w-0">
          <Tabs defaultValue="activity">
            <TabsList variant="line" className="border-b border-border pb-0 mb-4">
              <TabsTrigger value="activity">Activity</TabsTrigger>
              <TabsTrigger value="details">Details</TabsTrigger>
              {hasSubTickets && <TabsTrigger value="sub-tickets">Sub-tickets</TabsTrigger>}
            </TabsList>

            {/* Activity tab — timeline */}
            <TabsContent value="activity">
              {ticket.trace_log?.length > 0 ? (
                <div className="space-y-2">
                  {ticket.trace_log.map((entry, i) => {
                    const traceType = guessTraceType(entry.tool);
                    const isExpanded = expandedTrace === i;
                    const hasInput = entry.input && Object.keys(entry.input).length > 0;

                    return (
                      <div
                        key={i}
                        className={cn(
                          "relative flex gap-3 pl-5 border-l-2 ml-2",
                          traceBorderColors[traceType] || "border-l-border"
                        )}
                      >
                        {/* Timeline dot */}
                        <div
                          className={cn(
                            "absolute -left-[7px] top-3 h-3 w-3 rounded-full border-2 border-background",
                            traceType === "tool_call" ? "bg-blue-400" :
                            traceType === "status_change" ? "bg-amber-400" :
                            traceType === "escalation" ? "bg-red-400" :
                            traceType === "delegation" ? "bg-purple-400" : "bg-gray-400"
                          )}
                        />

                        <div className="flex-1 rounded-lg border border-border bg-card shadow-sm p-3">
                          <div className="flex items-center justify-between gap-2">
                            <div className="flex items-center gap-2">
                              <span className="flex h-5 w-5 items-center justify-center rounded bg-muted dark:bg-card text-[10px] font-bold text-muted-foreground border border-border">
                                {traceIcons[traceType] || "?"}
                              </span>
                              <span className="text-sm font-medium text-foreground">{entry.tool}</span>
                            </div>
                            <span className="text-[10px] text-muted-foreground whitespace-nowrap">
                              {timeAgo(entry.ts)}
                            </span>
                          </div>

                          {/* Output summary */}
                          {entry.output && (
                            <p className="mt-1.5 text-xs text-muted-foreground line-clamp-2">
                              {entry.output}
                            </p>
                          )}

                          {/* Collapsible input JSON */}
                          {hasInput && (
                            <div className="mt-2">
                              <button
                                onClick={() => setExpandedTrace(isExpanded ? null : i)}
                                className="text-[10px] text-muted-foreground hover:text-foreground transition-colors"
                              >
                                {isExpanded ? "Hide input" : "Show input"}
                              </button>
                              {isExpanded && (
                                <pre className="mt-1 text-[10px] text-muted-foreground overflow-auto max-h-48 font-mono bg-muted dark:bg-card/80 rounded-md p-2 border border-border">
                                  {JSON.stringify(entry.input, null, 2)}
                                </pre>
                              )}
                            </div>
                          )}
                        </div>
                      </div>
                    );
                  })}
                </div>
              ) : (
                <div className="text-center py-12 text-sm text-muted-foreground">
                  No activity yet
                </div>
              )}
            </TabsContent>

            {/* Details tab */}
            <TabsContent value="details">
              <div className="space-y-4">
                {ticket.input_data && Object.keys(ticket.input_data).length > 0 && (
                  <div>
                    <h3 className="text-sm font-semibold text-foreground mb-2">Input Data</h3>
                    <pre className="text-xs text-muted-foreground overflow-auto max-h-80 font-mono bg-muted dark:bg-card/80 rounded-lg p-3 border border-border">
                      {JSON.stringify(ticket.input_data, null, 2)}
                    </pre>
                  </div>
                )}
                {ticket.result && (
                  <div>
                    <h3 className="text-sm font-semibold text-foreground mb-2">Result</h3>
                    <pre className="text-xs text-muted-foreground overflow-auto max-h-80 font-mono bg-muted dark:bg-card/80 rounded-lg p-3 border border-border">
                      {JSON.stringify(ticket.result, null, 2)}
                    </pre>
                  </div>
                )}
                {!ticket.input_data && !ticket.result && (
                  <div className="text-center py-12 text-sm text-muted-foreground">
                    No details available
                  </div>
                )}
              </div>
            </TabsContent>

            {/* Sub-tickets tab */}
            {hasSubTickets && (
              <TabsContent value="sub-tickets">
                <div className="space-y-2">
                  {ticket.sub_tickets!.map((sub) => (
                    <Link
                      key={sub.id}
                      href={`/dashboard/tickets/${sub.id}`}
                      className="flex items-center justify-between rounded-lg border border-border bg-card shadow-sm px-4 py-3 hover:shadow-md transition-all"
                    >
                      <div className="flex items-center gap-3">
                        <div
                          className={cn(
                            "h-2 w-2 rounded-full",
                            sub.status === "resolved" ? "bg-emerald-400" :
                            sub.status === "in_progress" ? "bg-amber-400" :
                            sub.status === "escalated" ? "bg-red-400" : "bg-gray-400"
                          )}
                        />
                        <div>
                          <span className="text-sm text-foreground">{sub.title}</span>
                          <span className="ml-2 text-xs text-muted-foreground font-mono">{sub.id}</span>
                        </div>
                      </div>
                      <Badge
                        variant="outline"
                        className={cn(
                          "text-[10px] border",
                          ticketStatusColors[sub.status] || ticketStatusColors.open
                        )}
                      >
                        {sub.status}
                      </Badge>
                    </Link>
                  ))}
                </div>
              </TabsContent>
            )}
          </Tabs>
        </div>

        {/* Properties panel */}
        <div className="w-full lg:w-80 flex-shrink-0">
          <div className="rounded-xl border border-border bg-card shadow-sm p-4 space-y-4 lg:sticky lg:top-4">
            <h2 className="text-xs font-semibold text-muted-foreground uppercase tracking-wider">Properties</h2>

            {/* Status */}
            <div className="relative">
              <div className="text-xs text-muted-foreground mb-1">Status</div>
              <button
                onClick={() => { setStatusOpen(!statusOpen); setPriorityOpen(false); }}
                className={cn(
                  "rounded-md px-2.5 py-1 text-xs font-medium border cursor-pointer transition-colors",
                  ticketStatusColors[ticket.status] || ticketStatusColors.open
                )}
              >
                {ticket.status.replace("_", " ")}
              </button>
              {statusOpen && (
                <div className="absolute top-full left-0 mt-1 z-10 rounded-lg border border-border bg-card shadow-lg py-1 min-w-[140px]">
                  {statusFlow.map((s) => (
                    <button
                      key={s}
                      onClick={() => statusMutation.mutate(s)}
                      disabled={s === ticket.status}
                      className={cn(
                        "w-full text-left px-3 py-1.5 text-xs hover:bg-accent transition-colors flex items-center gap-2",
                        s === ticket.status && "opacity-50 cursor-default"
                      )}
                    >
                      <span className={cn("h-2 w-2 rounded-full", ticketStatusColors[s]?.split(" ")[0])} />
                      {s.replace("_", " ")}
                    </button>
                  ))}
                </div>
              )}
            </div>

            {/* Priority */}
            <div className="relative">
              <div className="text-xs text-muted-foreground mb-1">Priority</div>
              <button
                onClick={() => { setPriorityOpen(!priorityOpen); setStatusOpen(false); }}
                className={cn(
                  "rounded-md px-2.5 py-1 text-xs font-medium border cursor-pointer transition-colors",
                  priorityConfig[ticket.priority]?.color || priorityConfig[3].color
                )}
              >
                P{ticket.priority} — {priorityConfig[ticket.priority]?.label || "Medium"}
              </button>
              {priorityOpen && (
                <div className="absolute top-full left-0 mt-1 z-10 rounded-lg border border-border bg-card shadow-lg py-1 min-w-[160px]">
                  {[1, 2, 3, 4, 5].map((p) => (
                    <button
                      key={p}
                      onClick={() => priorityMutation.mutate(p)}
                      disabled={p === ticket.priority}
                      className={cn(
                        "w-full text-left px-3 py-1.5 text-xs hover:bg-accent transition-colors flex items-center gap-2",
                        p === ticket.priority && "opacity-50 cursor-default"
                      )}
                    >
                      <span className={cn("h-2 w-2 rounded-full", priorityConfig[p]?.color.split(" ")[0])} />
                      P{p} — {priorityConfig[p]?.label}
                    </button>
                  ))}
                </div>
              )}
            </div>

            <div className="border-t border-border" />

            {/* Assignee */}
            <div>
              <div className="text-xs text-muted-foreground mb-1">Assignee</div>
              {ticket.assigned_to ? (
                <Link
                  href={`/dashboard/agents/${ticket.assigned_to}`}
                  className="text-sm text-foreground hover:underline"
                >
                  {assignee?.display_name || assignee?.name || ticket.assigned_to}
                </Link>
              ) : (
                <span className="text-sm text-muted-foreground">Unassigned</span>
              )}
            </div>

            {/* Created by */}
            <div>
              <div className="text-xs text-muted-foreground mb-1">Created by</div>
              {ticket.created_by ? (
                <Link
                  href={`/dashboard/agents/${ticket.created_by}`}
                  className="text-sm text-foreground hover:underline"
                >
                  {creator?.display_name || creator?.name || ticket.created_by}
                </Link>
              ) : (
                <span className="text-sm text-muted-foreground">System</span>
              )}
            </div>

            {/* Domain */}
            <div>
              <div className="text-xs text-muted-foreground mb-1">Domain</div>
              <Badge variant="outline" className="text-xs">
                {ticket.domain || "—"}
              </Badge>
            </div>

            <div className="border-t border-border" />

            {/* Cost */}
            <div>
              <div className="text-xs text-muted-foreground mb-1">Cost</div>
              <span className="text-sm font-mono text-foreground">${ticket.cost_usd.toFixed(4)}</span>
            </div>

            {/* Execution link */}
            {ticket.execution_id && (
              <div>
                <div className="text-xs text-muted-foreground mb-1">Execution</div>
                <span className="text-xs font-mono text-muted-foreground break-all">
                  {ticket.execution_id}
                </span>
              </div>
            )}

            {/* Timestamps */}
            <div className="border-t border-border" />

            <div>
              <div className="text-xs text-muted-foreground mb-1">Created</div>
              <div className="flex items-center gap-2">
                <span className="text-sm text-foreground">{timeAgo(ticket.created_at)}</span>
                <span className="text-[10px] text-muted-foreground">
                  {new Date(ticket.created_at).toLocaleString()}
                </span>
              </div>
            </div>

            <div>
              <div className="text-xs text-muted-foreground mb-1">Updated</div>
              <div className="flex items-center gap-2">
                <span className="text-sm text-foreground">{timeAgo(ticket.updated_at)}</span>
                <span className="text-[10px] text-muted-foreground">
                  {new Date(ticket.updated_at).toLocaleString()}
                </span>
              </div>
            </div>

            {ticket.resolved_at && (
              <div>
                <div className="text-xs text-muted-foreground mb-1">Resolved</div>
                <div className="flex items-center gap-2">
                  <span className="text-sm text-foreground">{timeAgo(ticket.resolved_at)}</span>
                  <span className="text-[10px] text-muted-foreground">
                    {new Date(ticket.resolved_at).toLocaleString()}
                  </span>
                </div>
              </div>
            )}

            {/* Trace count */}
            {ticket.trace_log?.length > 0 && (
              <>
                <div className="border-t border-border" />
                <div>
                  <div className="text-xs text-muted-foreground mb-1">Activity</div>
                  <span className="text-sm text-foreground">{ticket.trace_log.length} trace entries</span>
                </div>
              </>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}
