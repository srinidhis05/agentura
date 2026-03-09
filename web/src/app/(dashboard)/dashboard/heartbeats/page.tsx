"use client";

import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { listHeartbeatRuns, getHeartbeatSchedule, triggerHeartbeat } from "@/lib/api";
import { heartbeatStatusColors } from "@/lib/colors";

export default function HeartbeatsPage() {
  const queryClient = useQueryClient();

  const { data: runs = [], isLoading: runsLoading } = useQuery({
    queryKey: ["heartbeat-runs"],
    queryFn: () => listHeartbeatRuns({ limit: 50 }),
    refetchInterval: 8000,
  });

  const { data: schedule = [] } = useQuery({
    queryKey: ["heartbeat-schedule"],
    queryFn: getHeartbeatSchedule,
    refetchInterval: 30000,
  });

  const triggerMutation = useMutation({
    mutationFn: (agentId: string) => triggerHeartbeat(agentId),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["heartbeat-runs"] });
      queryClient.invalidateQueries({ queryKey: ["heartbeat-schedule"] });
    },
  });

  return (
    <div className="space-y-8">
      <div>
        <h1 className="text-2xl font-bold text-foreground">Heartbeats</h1>
        <p className="text-sm text-muted-foreground mt-1">
          Scheduled agent check-ins and manual triggers
        </p>
      </div>

      {/* Schedule */}
      <div className="rounded-xl border border-border bg-card shadow-sm p-5">
        <h2 className="text-lg font-semibold text-foreground mb-4">Schedule</h2>
        {schedule.length > 0 ? (
          <div className="overflow-x-auto">
            <table className="w-full text-sm">
              <thead>
                <tr className="border-b border-border text-left">
                  <th className="pb-2 text-xs font-medium text-muted-foreground">Agent</th>
                  <th className="pb-2 text-xs font-medium text-muted-foreground">Schedule</th>
                  <th className="pb-2 text-xs font-medium text-muted-foreground">Status</th>
                  <th className="pb-2 text-xs font-medium text-muted-foreground">Last Run</th>
                  <th className="pb-2 text-xs font-medium text-muted-foreground">Cost</th>
                  <th className="pb-2 text-xs font-medium text-muted-foreground"></th>
                </tr>
              </thead>
              <tbody>
                {schedule.map((entry) => (
                  <tr key={entry.agent_id} className="border-b border-border/50">
                    <td className="py-3">
                      <span className="font-medium text-foreground">{entry.agent_name}</span>
                    </td>
                    <td className="py-3">
                      <span className="text-xs text-muted-foreground font-mono">
                        {entry.heartbeat_schedule}
                      </span>
                    </td>
                    <td className="py-3">
                      {entry.last_run_status ? (
                        <span className={`rounded px-2 py-0.5 text-[10px] font-medium ${heartbeatStatusColors[entry.last_run_status] || heartbeatStatusColors.completed}`}>
                          {entry.last_run_status}
                        </span>
                      ) : (
                        <span className="text-xs text-muted-foreground">Never run</span>
                      )}
                    </td>
                    <td className="py-3 text-xs text-muted-foreground">
                      {entry.last_run_at
                        ? new Date(entry.last_run_at).toLocaleString()
                        : "—"}
                    </td>
                    <td className="py-3 text-xs text-muted-foreground">
                      {entry.last_cost_usd != null ? `$${entry.last_cost_usd.toFixed(4)}` : "—"}
                    </td>
                    <td className="py-3">
                      <button
                        onClick={() => triggerMutation.mutate(entry.agent_id)}
                        disabled={triggerMutation.isPending}
                        className="rounded-md bg-blue-100 dark:bg-blue-500/20 px-3 py-1 text-xs font-medium text-blue-700 dark:text-blue-400 hover:bg-blue-200 dark:hover:bg-blue-500/30 transition-colors disabled:opacity-50"
                      >
                        {triggerMutation.isPending ? "..." : "Trigger"}
                      </button>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        ) : (
          <p className="text-sm text-muted-foreground">No heartbeat schedules configured</p>
        )}
      </div>

      {/* Recent Runs */}
      <div className="rounded-xl border border-border bg-card shadow-sm p-5">
        <h2 className="text-lg font-semibold text-foreground mb-4">Recent Runs</h2>
        {runsLoading ? (
          <div className="space-y-2">
            {[...Array(5)].map((_, i) => (
              <div key={i} className="h-12 rounded-lg bg-muted dark:bg-card/50 animate-pulse" />
            ))}
          </div>
        ) : runs.length > 0 ? (
          <div className="overflow-x-auto">
            <table className="w-full text-sm">
              <thead>
                <tr className="border-b border-border text-left">
                  <th className="pb-2 text-xs font-medium text-muted-foreground">Agent</th>
                  <th className="pb-2 text-xs font-medium text-muted-foreground">Status</th>
                  <th className="pb-2 text-xs font-medium text-muted-foreground">Trigger</th>
                  <th className="pb-2 text-xs font-medium text-muted-foreground">Cost</th>
                  <th className="pb-2 text-xs font-medium text-muted-foreground">Started</th>
                  <th className="pb-2 text-xs font-medium text-muted-foreground">Summary</th>
                </tr>
              </thead>
              <tbody>
                {runs.map((run) => (
                  <tr key={run.id} className="border-b border-border/50">
                    <td className="py-3">
                      <span className="font-medium text-foreground">{run.agent_name || run.agent_id}</span>
                    </td>
                    <td className="py-3">
                      <span className={`rounded px-2 py-0.5 text-[10px] font-medium ${heartbeatStatusColors[run.status] || heartbeatStatusColors.completed}`}>
                        {run.status}
                      </span>
                    </td>
                    <td className="py-3 text-xs text-muted-foreground">{run.trigger}</td>
                    <td className="py-3 text-xs text-muted-foreground">
                      {run.cost_usd > 0 ? `$${run.cost_usd.toFixed(4)}` : "—"}
                    </td>
                    <td className="py-3 text-xs text-muted-foreground">
                      {new Date(run.started_at).toLocaleString()}
                    </td>
                    <td className="py-3 text-xs text-muted-foreground max-w-[200px] truncate">
                      {run.summary || run.error_message || "—"}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        ) : (
          <p className="text-sm text-muted-foreground">No heartbeat runs yet</p>
        )}
      </div>
    </div>
  );
}
