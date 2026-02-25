"use client";

import { useState } from "react";
import { useParams } from "next/navigation";
import { useQuery } from "@tanstack/react-query";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { Badge } from "@/components/ui/badge";
import { Card, CardContent } from "@/components/ui/card";
import { ExecuteForm } from "@/components/skills/execute-form";
import { ResultPanel } from "@/components/skills/result-panel";
import { CorrectForm } from "@/components/skills/correct-form";
import { SkillOverview } from "@/components/skills/skill-overview";
import { ConfigPanel } from "@/components/skills/config-panel";
import { getSkillDetail, listExecutions, listReflexions, listTests } from "@/lib/api";
import type { SkillResult } from "@/lib/types";

const domainColors: Record<string, string> = {
  platform: "bg-violet-50 text-violet-700 border-violet-200",
};

const healthDots: Record<string, string> = {
  healthy: "bg-emerald-500",
  degraded: "bg-amber-500",
  failing: "bg-red-500",
  unknown: "bg-gray-400",
};

const deployStyles: Record<string, string> = {
  active: "bg-emerald-50 text-emerald-700 border-emerald-200",
  canary: "bg-amber-50 text-amber-700 border-amber-200",
  shadow: "bg-blue-50 text-blue-700 border-blue-200",
  disabled: "bg-red-50 text-red-700 border-red-200",
};

const outcomeStyles: Record<string, string> = {
  accepted: "bg-emerald-50 text-emerald-700 border-emerald-200",
  corrected: "bg-amber-50 text-amber-700 border-amber-200",
  pending_review: "bg-blue-50 text-blue-700 border-blue-200",
};

export default function SkillDetailPage() {
  const params = useParams<{ domain: string; skill: string }>();
  const [result, setResult] = useState<SkillResult | null>(null);
  const [activeTab, setActiveTab] = useState("overview");

  const skillPath = `${params.domain}/${params.skill}`;

  const { data: detail, isLoading } = useQuery({
    queryKey: ["skill-detail", params.domain, params.skill],
    queryFn: () => getSkillDetail(params.domain, params.skill),
  });

  const { data: runs } = useQuery({
    queryKey: ["skill-runs", params.domain, params.skill],
    queryFn: () => listExecutions(skillPath),
  });

  const { data: reflexions } = useQuery({
    queryKey: ["skill-reflexions", skillPath],
    queryFn: () => listReflexions(skillPath),
  });

  const { data: tests } = useQuery({
    queryKey: ["skill-tests", skillPath],
    queryFn: () => listTests(skillPath),
  });

  const allRuns = runs ?? [];
  const allReflexions = reflexions ?? [];
  const allTests = tests ?? [];

  // Compute skill health metrics
  const acceptedCount = allRuns.filter((r) => r.outcome === "accepted").length;
  const correctedCount = allRuns.filter((r) => r.outcome === "corrected").length;
  const acceptRate = allRuns.length > 0 ? acceptedCount / allRuns.length : 0;

  function handleResult(r: SkillResult) {
    setResult(r);
    setActiveTab("results");
  }

  if (isLoading) {
    return (
      <div className="flex items-center justify-center py-20">
        <div className="h-8 w-8 animate-spin rounded-full border-4 border-primary border-t-transparent" />
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Hero section */}
      <div className="space-y-3">
        <div className="flex items-center gap-3">
          {/* Health dot */}
          {detail && (
            <span
              className={`inline-block h-3 w-3 shrink-0 rounded-full ${healthDots[detail.health] ?? healthDots.unknown}`}
              title={`Health: ${detail.health}`}
            />
          )}
          <h2 className="text-2xl font-bold">{params.skill}</h2>
          <Badge
            variant="outline"
            className={domainColors[params.domain] ?? ""}
          >
            {params.domain}
          </Badge>
          {detail && (
            <>
              <Badge variant="secondary" className="text-xs">{detail.role}</Badge>
              <Badge variant="outline" className={`text-[10px] ${deployStyles[detail.deploy_status] ?? ""}`}>
                {detail.deploy_status}
              </Badge>
              <Badge variant="outline" className="font-mono text-[10px]">
                {detail.version}
              </Badge>
            </>
          )}
        </div>

        {/* Lifecycle metrics bar */}
        {detail && (
          <div className="flex flex-wrap items-center gap-4 rounded-md border border-border bg-card px-4 py-2 text-xs">
            <span className="text-muted-foreground">
              <span className="font-semibold text-foreground">{detail.executions_total}</span> executions
            </span>
            <span className={`font-semibold ${
              detail.accept_rate >= 0.8 ? "text-emerald-600" :
              detail.accept_rate >= 0.5 ? "text-amber-600" : "text-red-600"
            }`}>
              {Math.round(detail.accept_rate * 100)}% accept rate
            </span>
            <span className="font-mono text-muted-foreground">
              {detail.model.split("/").pop()}
            </span>
            {detail.cost_budget && (
              <span className="text-muted-foreground">{detail.cost_budget}/run</span>
            )}
            {detail.timeout && (
              <span className="text-muted-foreground">timeout: {detail.timeout}</span>
            )}
            {detail.last_deployed && (
              <span className="ml-auto text-[10px] text-muted-foreground">
                deployed {new Date(detail.last_deployed).toLocaleDateString()}
              </span>
            )}
          </div>
        )}

        {detail?.description && (
          <p className="text-sm text-muted-foreground">{detail.description}</p>
        )}
      </div>

      {/* Tabs */}
      <Tabs value={activeTab} onValueChange={setActiveTab}>
        <TabsList>
          <TabsTrigger value="overview">Overview</TabsTrigger>
          <TabsTrigger value="execute">Execute</TabsTrigger>
          <TabsTrigger value="results" disabled={!result}>
            Results
          </TabsTrigger>
          <TabsTrigger value="correct" disabled={!result?.success}>
            Correct
          </TabsTrigger>
          <TabsTrigger value="config">Config</TabsTrigger>
          <TabsTrigger value="runs">
            Runs{allRuns.length > 0 ? ` (${allRuns.length})` : ""}
          </TabsTrigger>
        </TabsList>

        <TabsContent value="overview" className="mt-4">
          {detail ? (
            <SkillOverview detail={detail} />
          ) : (
            <p className="text-sm text-muted-foreground">Loading skill details...</p>
          )}
        </TabsContent>

        <TabsContent value="execute" className="mt-4">
          <ExecuteForm
            domain={params.domain}
            skill={params.skill}
            onResult={handleResult}
          />
        </TabsContent>

        <TabsContent value="results" className="mt-4">
          {result ? (
            <ResultPanel result={result} />
          ) : (
            <p className="text-sm text-muted-foreground">
              Execute a skill first to see results.
            </p>
          )}
        </TabsContent>

        <TabsContent value="correct" className="mt-4">
          {result?.success ? (
            <CorrectForm
              domain={params.domain}
              skill={params.skill}
              executionId={result.skill_name}
            />
          ) : (
            <p className="text-sm text-muted-foreground">
              Run a successful execution first to submit corrections.
            </p>
          )}
        </TabsContent>

        <TabsContent value="config" className="mt-4">
          {detail ? (
            <ConfigPanel detail={detail} />
          ) : (
            <p className="text-sm text-muted-foreground">Loading configuration...</p>
          )}
        </TabsContent>

        <TabsContent value="runs" className="mt-4">
          <div className="space-y-6">
            {/* Skill Health Summary */}
            <div className="grid gap-3 sm:grid-cols-4">
              <Card>
                <CardContent className="py-3 text-center">
                  <p className="text-lg font-bold text-emerald-600">
                    {Math.round(acceptRate * 100)}%
                  </p>
                  <p className="text-[9px] text-muted-foreground">Accept Rate</p>
                </CardContent>
              </Card>
              <Card>
                <CardContent className="py-3 text-center">
                  <p className="text-lg font-bold text-amber-600">{correctedCount}</p>
                  <p className="text-[9px] text-muted-foreground">Corrections</p>
                </CardContent>
              </Card>
              <Card>
                <CardContent className="py-3 text-center">
                  <p className="text-lg font-bold text-violet-600">{allReflexions.length}</p>
                  <p className="text-[9px] text-muted-foreground">Reflexion Rules</p>
                </CardContent>
              </Card>
              <Card>
                <CardContent className="py-3 text-center">
                  <p className="text-lg font-bold text-blue-600">{allTests.length}</p>
                  <p className="text-[9px] text-muted-foreground">Generated Tests</p>
                </CardContent>
              </Card>
            </div>

            {/* Active Reflexion Rules */}
            {allReflexions.length > 0 && (
              <div>
                <h4 className="mb-2 text-xs font-semibold uppercase tracking-wider text-muted-foreground">
                  Active Reflexion Rules
                </h4>
                <div className="space-y-2">
                  {allReflexions.map((r) => (
                    <div
                      key={r.reflexion_id}
                      className="flex items-start gap-3 rounded-md border border-violet-200 bg-violet-50 px-4 py-3"
                    >
                      <span className="mt-0.5 h-1.5 w-1.5 shrink-0 rounded-full bg-violet-400" />
                      <div className="min-w-0 flex-1">
                        <p className="text-xs">{r.rule}</p>
                        <div className="mt-1 flex items-center gap-3 text-[10px] text-muted-foreground">
                          <span>Confidence: {Math.round(r.confidence * 100)}%</span>
                          {r.validated_by_test && (
                            <Badge variant="outline" className="border-emerald-200 bg-emerald-50 text-[8px] text-emerald-600">
                              validated
                            </Badge>
                          )}
                        </div>
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            )}

            {/* Generated Tests */}
            {allTests.length > 0 && (
              <div>
                <h4 className="mb-2 text-xs font-semibold uppercase tracking-wider text-muted-foreground">
                  Generated Tests
                </h4>
                <div className="space-y-2">
                  {allTests.map((t) => (
                    <div
                      key={t.test_id}
                      className="flex items-center gap-3 rounded-md border border-border px-4 py-2.5"
                    >
                      <Badge variant="outline" className="text-[9px]">
                        {t.test_type}
                      </Badge>
                      <span className="min-w-0 flex-1 truncate text-xs">{t.description}</span>
                      <Badge
                        variant="outline"
                        className={`text-[8px] ${
                          t.status === "passing" ? "border-emerald-200 bg-emerald-50 text-emerald-600" :
                          t.status === "failing" ? "border-red-200 bg-red-50 text-red-600" :
                          "border-blue-200 bg-blue-50 text-blue-600"
                        }`}
                      >
                        {t.status}
                      </Badge>
                    </div>
                  ))}
                </div>
              </div>
            )}

            {/* Execution History */}
            <div>
              <h4 className="mb-2 text-xs font-semibold uppercase tracking-wider text-muted-foreground">
                Execution History
              </h4>
              {allRuns.length > 0 ? (
                <div className="space-y-2">
                  {allRuns.map((exec) => (
                    <a
                      key={exec.execution_id}
                      href={`/dashboard/executions/${exec.execution_id}`}
                      className="flex items-center gap-3 rounded-md border border-border px-4 py-3 text-sm transition-colors hover:bg-accent/50"
                    >
                      <span className="font-mono text-xs">{exec.execution_id}</span>
                      <Badge variant="outline" className={`text-[10px] ${outcomeStyles[exec.outcome] ?? ""}`}>
                        {exec.outcome === "pending_review" ? "review" : exec.outcome}
                      </Badge>
                      <span className="ml-auto flex items-center gap-3 text-xs text-muted-foreground">
                        <span className="font-mono">${exec.cost_usd.toFixed(2)}</span>
                        <span className="font-mono">{(exec.latency_ms / 1000).toFixed(1)}s</span>
                        <span>{exec.timestamp ? new Date(exec.timestamp).toLocaleDateString() : ""}</span>
                      </span>
                    </a>
                  ))}
                </div>
              ) : (
                <p className="py-4 text-sm text-muted-foreground">
                  No executions recorded for this skill yet.
                </p>
              )}
            </div>
          </div>
        </TabsContent>
      </Tabs>
    </div>
  );
}
