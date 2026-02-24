import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import type { SkillDetail } from "@/lib/types";

export function ConfigPanel({ detail }: { detail: SkillDetail }) {
  return (
    <div className="space-y-6">
      {/* Domain config */}
      <Card>
        <CardHeader className="pb-2">
          <CardTitle className="text-sm">Domain Configuration</CardTitle>
        </CardHeader>
        <CardContent>
          <dl className="grid grid-cols-[auto_1fr] gap-x-6 gap-y-3 text-sm">
            <dt className="text-muted-foreground">Domain</dt>
            <dd className="font-medium capitalize">{detail.domain}</dd>

            {detail.domain_description && (
              <>
                <dt className="text-muted-foreground">Description</dt>
                <dd>{detail.domain_description}</dd>
              </>
            )}

            {detail.domain_owner && (
              <>
                <dt className="text-muted-foreground">Owner</dt>
                <dd>
                  <Badge variant="outline" className="text-xs">{detail.domain_owner}</Badge>
                </dd>
              </>
            )}
          </dl>
        </CardContent>
      </Card>

      {/* Budget & limits */}
      <Card>
        <CardHeader className="pb-2">
          <CardTitle className="text-sm">Budget & Limits</CardTitle>
        </CardHeader>
        <CardContent>
          <dl className="grid grid-cols-[auto_1fr] gap-x-6 gap-y-3 text-sm">
            <dt className="text-muted-foreground">Cost Budget</dt>
            <dd className="font-mono">{detail.cost_budget || "—"}</dd>

            <dt className="text-muted-foreground">Timeout</dt>
            <dd className="font-mono">{detail.timeout || "—"}</dd>

            <dt className="text-muted-foreground">Model</dt>
            <dd className="font-mono">{detail.model}</dd>
          </dl>
        </CardContent>
      </Card>

      {/* Feedback settings */}
      <Card>
        <CardHeader className="pb-2">
          <CardTitle className="text-sm">Feedback Loop</CardTitle>
        </CardHeader>
        <CardContent>
          <dl className="grid grid-cols-[auto_1fr] gap-x-6 gap-y-3 text-sm">
            <dt className="text-muted-foreground">Corrections</dt>
            <dd>
              <Badge variant={detail.feedback_enabled ? "default" : "secondary"} className="text-xs">
                {detail.feedback_enabled ? "Enabled" : "Disabled"}
              </Badge>
            </dd>

            <dt className="text-muted-foreground">Guardrails</dt>
            <dd>
              {detail.guardrails_count > 0 ? (
                <span>{detail.guardrails_count} domain guardrails active</span>
              ) : (
                <span className="text-muted-foreground">None</span>
              )}
            </dd>

            <dt className="text-muted-foreground">Regression Tests</dt>
            <dd>
              {detail.corrections_count > 0 ? (
                <span>{detail.corrections_count} correction-based tests</span>
              ) : (
                <span className="text-muted-foreground">None yet</span>
              )}
            </dd>
          </dl>
        </CardContent>
      </Card>

      {/* Observability */}
      <Card>
        <CardHeader className="pb-2">
          <CardTitle className="text-sm">Observability</CardTitle>
        </CardHeader>
        <CardContent>
          <p className="text-sm text-muted-foreground">
            Four Golden Signals monitored: Latency, Traffic, Errors, Saturation.
            Traces and metrics collected via Agentura SDK instrumentation.
          </p>
        </CardContent>
      </Card>
    </div>
  );
}
