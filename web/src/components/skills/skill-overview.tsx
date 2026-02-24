import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import type { SkillDetail } from "@/lib/types";

export function SkillOverview({ detail }: { detail: SkillDetail }) {
  return (
    <div className="space-y-6">
      {/* Task description */}
      {detail.task_description && (
        <Card>
          <CardHeader className="pb-2">
            <CardTitle className="text-sm">Task</CardTitle>
          </CardHeader>
          <CardContent>
            <p className="text-sm leading-relaxed text-muted-foreground">
              {detail.task_description}
            </p>
          </CardContent>
        </Card>
      )}

      {/* Input / Output schemas side by side */}
      <div className="grid gap-4 md:grid-cols-2">
        {detail.input_schema && (
          <Card>
            <CardHeader className="pb-2">
              <CardTitle className="text-sm">Input Schema</CardTitle>
            </CardHeader>
            <CardContent>
              <pre className="max-h-60 overflow-auto rounded-md bg-accent/50 p-3 text-xs">
                {detail.input_schema}
              </pre>
            </CardContent>
          </Card>
        )}
        {detail.output_schema && (
          <Card>
            <CardHeader className="pb-2">
              <CardTitle className="text-sm">Output Schema</CardTitle>
            </CardHeader>
            <CardContent>
              <pre className="max-h-60 overflow-auto rounded-md bg-accent/50 p-3 text-xs">
                {detail.output_schema}
              </pre>
            </CardContent>
          </Card>
        )}
      </div>

      {/* Guardrails */}
      {detail.skill_guardrails.length > 0 && (
        <Card>
          <CardHeader className="pb-2">
            <CardTitle className="flex items-center gap-2 text-sm">
              <svg className="h-4 w-4 text-amber-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12l2 2 4-4m5.618-4.016A11.955 11.955 0 0112 2.944a11.955 11.955 0 01-8.618 3.04A12.02 12.02 0 003 9c0 5.591 3.824 10.29 9 11.622 5.176-1.332 9-6.03 9-11.622 0-1.042-.133-2.052-.382-3.016z" />
              </svg>
              Guardrails
            </CardTitle>
          </CardHeader>
          <CardContent>
            <ul className="space-y-2">
              {detail.skill_guardrails.map((g, i) => (
                <li key={i} className="flex items-start gap-2 text-sm text-muted-foreground">
                  <span className="mt-1 h-1.5 w-1.5 shrink-0 rounded-full bg-amber-400" />
                  {g}
                </li>
              ))}
            </ul>
          </CardContent>
        </Card>
      )}

      {/* Trigger patterns + MCP tools */}
      <div className="grid gap-4 md:grid-cols-2">
        {detail.triggers.length > 0 && (
          <Card>
            <CardHeader className="pb-2">
              <CardTitle className="text-sm">Trigger Patterns</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="space-y-2">
                {detail.triggers.map((t, i) => (
                  <div key={i} className="flex items-center gap-2">
                    <Badge variant="outline" className="text-[10px]">
                      {String(t.type ?? "command")}
                    </Badge>
                    <code className="text-xs text-muted-foreground">
                      {String(t.pattern ?? "")}
                    </code>
                  </div>
                ))}
              </div>
            </CardContent>
          </Card>
        )}

        {detail.mcp_tools.length > 0 && (
          <Card>
            <CardHeader className="pb-2">
              <CardTitle className="text-sm">MCP Tools</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="flex flex-wrap gap-2">
                {detail.mcp_tools.map((tool) => (
                  <Badge key={tool} variant="secondary" className="text-xs">
                    {tool}
                  </Badge>
                ))}
              </div>
            </CardContent>
          </Card>
        )}
      </div>
    </div>
  );
}
