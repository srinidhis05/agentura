"use client";

import { useParams } from "next/navigation";
import { useQuery } from "@tanstack/react-query";
import Link from "next/link";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { getDomainDetail } from "@/lib/api";
import { SkillDAG } from "@/components/topology/skill-dag";

const roleColors: Record<string, string> = {
  manager: "bg-blue-500/20 text-blue-400 border-blue-500/30",
  specialist: "bg-emerald-500/20 text-emerald-400 border-emerald-500/30",
  field: "bg-amber-500/20 text-amber-400 border-amber-500/30",
};

const healthDots: Record<string, string> = {
  healthy: "bg-emerald-500 shadow-[0_0_4px_rgba(16,185,129,0.6)]",
  degraded: "bg-amber-500 shadow-[0_0_4px_rgba(245,158,11,0.6)]",
  failing: "bg-red-500 shadow-[0_0_4px_rgba(239,68,68,0.6)]",
  unknown: "bg-gray-500",
};

const deployBadgeStyles: Record<string, string> = {
  active: "bg-emerald-500/10 text-emerald-400 border-emerald-500/20",
  canary: "bg-amber-500/10 text-amber-400 border-amber-500/20",
  shadow: "bg-blue-500/10 text-blue-400 border-blue-500/20",
  disabled: "bg-red-500/10 text-red-400 border-red-500/20",
};

const roleNodeColors: Record<string, string> = {
  manager: "border-blue-500/50 bg-blue-500/10",
  specialist: "border-emerald-500/50 bg-emerald-500/10",
  field: "border-amber-500/50 bg-amber-500/10",
};

const outcomeStyles: Record<string, string> = {
  accepted: "bg-emerald-500/10 text-emerald-400 border-emerald-500/20",
  corrected: "bg-amber-500/10 text-amber-400 border-amber-500/20",
  pending_review: "bg-blue-500/10 text-blue-400 border-blue-500/20",
};

export default function DomainDetailPage() {
  const params = useParams<{ domain: string }>();

  const { data: detail, isLoading } = useQuery({
    queryKey: ["domain-detail", params.domain],
    queryFn: () => getDomainDetail(params.domain),
  });

  if (isLoading) {
    return (
      <div className="flex items-center justify-center py-20">
        <div className="h-8 w-8 animate-spin rounded-full border-4 border-primary border-t-transparent" />
      </div>
    );
  }

  if (!detail) {
    return (
      <div className="py-20 text-center text-sm text-muted-foreground">
        Domain not found: {params.domain}
      </div>
    );
  }

  return (
    <div className="space-y-8">
      {/* Hero */}
      <div className="space-y-2">
        <div className="flex items-center gap-3">
          <h2 className="text-2xl font-bold capitalize">{detail.name}</h2>
          {detail.owner && (
            <Badge variant="outline" className="text-xs">{detail.owner}</Badge>
          )}
        </div>
        {detail.description && (
          <p className="text-sm text-muted-foreground">{detail.description}</p>
        )}
      </div>

      {/* Metrics Row */}
      <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-5">
        <Card>
          <CardHeader className="pb-2">
            <CardTitle className="text-xs font-medium text-muted-foreground">Executions</CardTitle>
          </CardHeader>
          <CardContent>
            <p className="text-2xl font-bold">{detail.total_executions}</p>
          </CardContent>
        </Card>
        <Card>
          <CardHeader className="pb-2">
            <CardTitle className="text-xs font-medium text-muted-foreground">Accept Rate</CardTitle>
          </CardHeader>
          <CardContent>
            <p className="text-2xl font-bold text-emerald-400">
              {Math.round(detail.accept_rate * 100)}%
            </p>
          </CardContent>
        </Card>
        <Card>
          <CardHeader className="pb-2">
            <CardTitle className="text-xs font-medium text-muted-foreground">Cost</CardTitle>
          </CardHeader>
          <CardContent>
            <p className="text-2xl font-bold">{detail.cost_spent}</p>
            {detail.cost_budget && (
              <p className="text-[10px] text-muted-foreground">of {detail.cost_budget}</p>
            )}
          </CardContent>
        </Card>
        <Card>
          <CardHeader className="pb-2">
            <CardTitle className="text-xs font-medium text-muted-foreground">Corrections</CardTitle>
          </CardHeader>
          <CardContent>
            <p className="text-2xl font-bold text-amber-400">{detail.total_corrections}</p>
          </CardContent>
        </Card>
        <Card>
          <CardHeader className="pb-2">
            <CardTitle className="text-xs font-medium text-muted-foreground">Reflexions</CardTitle>
          </CardHeader>
          <CardContent>
            <p className="text-2xl font-bold text-violet-400">{detail.total_reflexions}</p>
          </CardContent>
        </Card>
      </div>

      {/* Orchestration Graph */}
      <div>
        <h3 className="mb-3 text-xs font-medium uppercase tracking-wider text-muted-foreground">
          Orchestration Graph
        </h3>
        <SkillDAG skills={detail.skills} topology={detail.topology} domain={detail.name} />
      </div>

      <div className="grid gap-6 lg:grid-cols-5">
        {/* Left: Skills Table + Guardrails */}
        <div className="space-y-6 lg:col-span-3">
          {/* Skills Table */}
          <div>
            <h3 className="mb-3 text-xs font-medium uppercase tracking-wider text-muted-foreground">
              Skills ({detail.skills.length})
            </h3>
            <Card>
              <CardContent className="py-2">
                <div className="divide-y divide-border/30">
                  {detail.skills.map((s) => (
                    <Link key={s.name} href={`/dashboard/skills/${detail.name}/${s.name}`}>
                      <div className="flex items-center gap-3 px-2 py-3 transition-colors hover:bg-accent/30">
                        {/* Health dot */}
                        <span className={`h-2 w-2 shrink-0 rounded-full ${healthDots[s.health] ?? healthDots.unknown}`} />
                        <div className="min-w-0 flex-1">
                          <p className="font-mono text-sm">{s.name}</p>
                          {s.description && (
                            <p className="mt-0.5 truncate text-[10px] text-muted-foreground">
                              {s.description}
                            </p>
                          )}
                        </div>
                        <Badge variant="outline" className={`text-[9px] ${deployBadgeStyles[s.deploy_status] ?? ""}`}>
                          {s.deploy_status}
                        </Badge>
                        <Badge variant="outline" className={`text-[9px] ${roleColors[s.role] ?? ""}`}>
                          {s.role}
                        </Badge>
                        {s.executions_total > 0 && (
                          <span className={`text-[10px] font-semibold ${
                            s.accept_rate >= 0.8 ? "text-emerald-400" :
                            s.accept_rate >= 0.5 ? "text-amber-400" : "text-red-400"
                          }`}>
                            {Math.round(s.accept_rate * 100)}%
                          </span>
                        )}
                        <span className="font-mono text-[10px] text-muted-foreground">
                          {s.model.split("/").pop()}
                        </span>
                      </div>
                    </Link>
                  ))}
                </div>
              </CardContent>
            </Card>
          </div>

          {/* Resource Quotas (K8s ResourceQuota equivalent) */}
          {detail.resource_quota && (
            <div>
              <h3 className="mb-3 text-xs font-medium uppercase tracking-wider text-muted-foreground">
                Resource Quotas
              </h3>
              <Card>
                <CardContent className="py-4 space-y-4">
                  {/* Budget gauge */}
                  {(detail.resource_quota.cost_budget || detail.resource_quota.cost_spent !== "$0.00") && (
                    <div>
                      <div className="flex items-center justify-between text-xs">
                        <span className="text-muted-foreground">Cost Budget</span>
                        <span className="font-mono">
                          {detail.resource_quota.cost_spent}
                          {detail.resource_quota.cost_budget && ` / ${detail.resource_quota.cost_budget}`}
                        </span>
                      </div>
                      <div className="mt-1.5 h-2.5 overflow-hidden rounded-full bg-accent">
                        <div
                          className={`h-full rounded-full transition-all ${
                            detail.resource_quota.budget_utilization >= 0.9 ? "bg-red-500" :
                            detail.resource_quota.budget_utilization >= 0.7 ? "bg-amber-500" : "bg-emerald-500"
                          }`}
                          style={{ width: `${Math.min(detail.resource_quota.budget_utilization * 100, 100)}%` }}
                        />
                      </div>
                      {detail.resource_quota.budget_utilization >= 0.9 && (
                        <p className="mt-1 text-[10px] text-red-400">Budget nearly exhausted</p>
                      )}
                    </div>
                  )}

                  {/* Limits grid */}
                  <div className="grid gap-2 sm:grid-cols-2">
                    {detail.resource_quota.max_cost_per_session && (
                      <div className="rounded-md border border-border/30 px-3 py-2">
                        <p className="text-[10px] text-muted-foreground">Max Cost / Session</p>
                        <p className="font-mono text-sm font-semibold">{detail.resource_quota.max_cost_per_session}</p>
                      </div>
                    )}
                    {detail.resource_quota.max_skills_per_session > 0 && (
                      <div className="rounded-md border border-border/30 px-3 py-2">
                        <p className="text-[10px] text-muted-foreground">Max Skills / Session</p>
                        <p className="text-sm font-semibold">{detail.resource_quota.max_skills_per_session}</p>
                      </div>
                    )}
                    {detail.resource_quota.rate_limit_rpm > 0 && (
                      <div className="rounded-md border border-border/30 px-3 py-2">
                        <p className="text-[10px] text-muted-foreground">Rate Limit</p>
                        <p className="text-sm font-semibold">{detail.resource_quota.rate_limit_rpm} req/min</p>
                      </div>
                    )}
                  </div>

                  {/* Human Approval Thresholds */}
                  {detail.resource_quota.human_approval_thresholds.length > 0 && (
                    <div>
                      <p className="mb-1.5 text-[10px] font-semibold uppercase text-muted-foreground">
                        Human Approval Required
                      </p>
                      <div className="space-y-1">
                        {detail.resource_quota.human_approval_thresholds.map((t, i) => (
                          <div key={i} className="flex items-center gap-2 rounded-md border border-amber-500/20 bg-amber-500/5 px-3 py-1.5 text-xs">
                            <svg className="h-3 w-3 text-amber-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-2.5L13.732 4c-.77-.833-1.964-.833-2.732 0L4.082 16.5c-.77.833.192 2.5 1.732 2.5z" />
                            </svg>
                            <span className="font-mono">{t.action}</span>
                            <span className="text-muted-foreground">when &gt; {t.threshold}</span>
                          </div>
                        ))}
                      </div>
                    </div>
                  )}

                  {/* Blocked Actions */}
                  {detail.resource_quota.blocked_actions.length > 0 && (
                    <div>
                      <p className="mb-1.5 text-[10px] font-semibold uppercase text-muted-foreground">
                        Blocked Actions
                      </p>
                      <div className="flex flex-wrap gap-1.5">
                        {detail.resource_quota.blocked_actions.map((a) => (
                          <span key={a} className="rounded-md border border-red-500/20 bg-red-500/5 px-2 py-1 font-mono text-[10px] text-red-400">
                            {a}
                          </span>
                        ))}
                      </div>
                    </div>
                  )}
                </CardContent>
              </Card>
            </div>
          )}

          {/* Guardrails */}
          {detail.guardrails.length > 0 && (
            <div>
              <h3 className="mb-3 text-xs font-medium uppercase tracking-wider text-muted-foreground">
                Domain Guardrails
              </h3>
              <Card>
                <CardContent className="py-4">
                  <div className="space-y-2">
                    {detail.guardrails.map((g, i) => (
                      <div key={i} className="rounded-md border border-amber-500/20 bg-amber-500/5 px-3 py-2 text-xs">
                        {g.replace(/^##\s+/, "")}
                      </div>
                    ))}
                  </div>
                </CardContent>
              </Card>
            </div>
          )}
        </div>

        {/* Right: Recent Activity */}
        <div className="space-y-6 lg:col-span-2">
          {/* Recent Executions */}
          <div>
            <h3 className="mb-3 text-xs font-medium uppercase tracking-wider text-muted-foreground">
              Recent Executions
            </h3>
            <Card>
              <CardContent className="py-3">
                {detail.recent_executions.length > 0 ? (
                  <div className="space-y-0">
                    {detail.recent_executions.map((exec) => (
                      <Link key={exec.execution_id} href={`/dashboard/executions/${exec.execution_id}`}>
                        <div className="flex items-center gap-2 rounded-md px-2 py-2 transition-colors hover:bg-accent/30">
                          <span
                            className={`h-1.5 w-1.5 shrink-0 rounded-full ${
                              exec.outcome === "accepted" ? "bg-emerald-400" :
                              exec.outcome === "corrected" ? "bg-amber-400" : "bg-blue-400"
                            }`}
                          />
                          <div className="min-w-0 flex-1">
                            <p className="truncate font-mono text-[11px]">
                              {exec.skill.split("/").slice(1).join("/")}
                            </p>
                          </div>
                          <Badge variant="outline" className={`text-[8px] ${outcomeStyles[exec.outcome] ?? ""}`}>
                            {exec.outcome === "pending_review" ? "review" : exec.outcome}
                          </Badge>
                          <span className="font-mono text-[9px] text-muted-foreground">
                            ${exec.cost_usd.toFixed(2)}
                          </span>
                        </div>
                      </Link>
                    ))}
                  </div>
                ) : (
                  <div className="py-4 text-center text-xs text-muted-foreground">
                    No executions in this domain yet
                  </div>
                )}
              </CardContent>
            </Card>
          </div>

          {/* Recent Corrections */}
          {detail.recent_corrections.length > 0 && (
            <div>
              <h3 className="mb-3 text-xs font-medium uppercase tracking-wider text-muted-foreground">
                Recent Corrections
              </h3>
              <Card>
                <CardContent className="py-3">
                  <div className="space-y-0">
                    {detail.recent_corrections.map((c) => (
                      <div key={c.correction_id} className="flex items-start gap-2 rounded-md px-2 py-2">
                        <span className="mt-1 h-1.5 w-1.5 shrink-0 rounded-full bg-amber-400" />
                        <div className="min-w-0 flex-1">
                          <p className="font-mono text-[10px] text-muted-foreground">
                            {c.correction_id}
                          </p>
                          <p className="mt-0.5 line-clamp-2 text-[11px]">
                            {c.user_correction}
                          </p>
                        </div>
                      </div>
                    ))}
                  </div>
                </CardContent>
              </Card>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}

