import Link from "next/link";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import type { SkillInfo } from "@/lib/types";

const domainColors: Record<string, string> = {
  wealth: "bg-emerald-500/10 text-emerald-400 border-emerald-500/20",
  ecm: "bg-blue-500/10 text-blue-400 border-blue-500/20",
  frm: "bg-amber-500/10 text-amber-400 border-amber-500/20",
  platform: "bg-violet-500/10 text-violet-400 border-violet-500/20",
};

const healthDots: Record<string, string> = {
  healthy: "bg-emerald-500 shadow-[0_0_6px_rgba(16,185,129,0.6)]",
  degraded: "bg-amber-500 shadow-[0_0_6px_rgba(245,158,11,0.6)]",
  failing: "bg-red-500 shadow-[0_0_6px_rgba(239,68,68,0.6)]",
  unknown: "bg-gray-500",
};

const deployStatusStyles: Record<string, string> = {
  active: "bg-emerald-500/10 text-emerald-400 border-emerald-500/20",
  canary: "bg-amber-500/10 text-amber-400 border-amber-500/20",
  shadow: "bg-blue-500/10 text-blue-400 border-blue-500/20",
  disabled: "bg-red-500/10 text-red-400 border-red-500/20",
};

export function SkillCard({ skill }: { skill: SkillInfo }) {
  return (
    <Link href={`/dashboard/skills/${skill.domain}/${skill.name}`}>
      <Card className="h-full transition-all hover:border-border hover:bg-accent/30">
        <CardHeader className="pb-3">
          <div className="flex items-start justify-between gap-2">
            <div className="min-w-0 flex-1">
              <div className="flex items-center gap-2">
                {/* Health indicator */}
                <span
                  className={`inline-block h-2 w-2 shrink-0 rounded-full ${healthDots[skill.health] ?? healthDots.unknown}`}
                  title={`Health: ${skill.health}`}
                />
                <CardTitle className="text-sm font-semibold">{skill.name}</CardTitle>
              </div>
              {skill.description && (
                <p className="mt-1 text-xs text-muted-foreground line-clamp-2">
                  {skill.description}
                </p>
              )}
            </div>
            <div className="flex shrink-0 flex-col items-end gap-1">
              <Badge
                variant="outline"
                className={`text-[10px] ${domainColors[skill.domain] ?? ""}`}
              >
                {skill.domain}
              </Badge>
              <Badge
                variant="outline"
                className={`text-[9px] ${deployStatusStyles[skill.deploy_status] ?? ""}`}
              >
                {skill.deploy_status}
              </Badge>
            </div>
          </div>
        </CardHeader>
        <CardContent className="space-y-3">
          {/* Role + trigger badges */}
          <div className="flex flex-wrap gap-1.5">
            <Badge variant="secondary" className="text-[10px]">{skill.role}</Badge>
            <Badge variant="secondary" className="text-[10px]">{skill.trigger}</Badge>
            <Badge variant="outline" className="font-mono text-[10px]">
              {skill.model.split("/").pop()}
            </Badge>
          </div>

          {/* Lifecycle stats row */}
          <div className="flex items-center gap-3 text-[10px]">
            {skill.executions_total > 0 && (
              <span className="flex items-center gap-1 text-muted-foreground">
                <svg className="h-3 w-3" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M14.752 11.168l-3.197-2.132A1 1 0 0010 9.87v4.263a1 1 0 001.555.832l3.197-2.132a1 1 0 000-1.664z" />
                </svg>
                {skill.executions_total} runs
              </span>
            )}
            {skill.executions_total > 0 && (
              <span className={`font-semibold ${
                skill.accept_rate >= 0.8 ? "text-emerald-400" :
                skill.accept_rate >= 0.5 ? "text-amber-400" : "text-red-400"
              }`}>
                {Math.round(skill.accept_rate * 100)}% accept
              </span>
            )}
            {skill.cost_budget && (
              <span className="text-muted-foreground">{skill.cost_budget}/run</span>
            )}
          </div>

          {/* MCP tools */}
          {(skill.mcp_tools ?? []).length > 0 && (
            <div className="flex flex-wrap gap-1.5">
              {(skill.mcp_tools ?? []).map((tool) => (
                <span
                  key={tool}
                  className="inline-flex items-center gap-1 rounded bg-accent px-1.5 py-0.5 text-[10px] text-muted-foreground"
                >
                  <svg className="h-2.5 w-2.5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 7v10c0 2 1 3 3 3h10c2 0 3-1 3-3V7c0-2-1-3-3-3H7C5 4 4 5 4 7z" />
                  </svg>
                  {tool}
                </span>
              ))}
            </div>
          )}

          {/* Bottom indicators */}
          <div className="flex items-center gap-3 border-t border-border/30 pt-2 text-[10px] text-muted-foreground">
            {(skill.guardrails_count ?? 0) > 0 && (
              <span className="flex items-center gap-1">
                <svg className="h-3 w-3" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12l2 2 4-4m5.618-4.016A11.955 11.955 0 0112 2.944a11.955 11.955 0 01-8.618 3.04A12.02 12.02 0 003 9c0 5.591 3.824 10.29 9 11.622 5.176-1.332 9-6.03 9-11.622 0-1.042-.133-2.052-.382-3.016z" />
                </svg>
                {skill.guardrails_count} guardrails
              </span>
            )}
            {(skill.corrections_count ?? 0) > 0 && (
              <span className="flex items-center gap-1">
                <svg className="h-3 w-3" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M11 5H6a2 2 0 00-2 2v11a2 2 0 002 2h11a2 2 0 002-2v-5m-1.414-9.414a2 2 0 112.828 2.828L11.828 15H9v-2.828l8.586-8.586z" />
                </svg>
                {skill.corrections_count} corrections
              </span>
            )}
            {skill.version && (
              <span className="ml-auto font-mono">{skill.version}</span>
            )}
          </div>
        </CardContent>
      </Card>
    </Link>
  );
}
