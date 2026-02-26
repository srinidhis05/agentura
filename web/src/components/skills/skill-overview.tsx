import ReactMarkdown from "react-markdown";
import remarkGfm from "remark-gfm";
import { Badge } from "@/components/ui/badge";
import type { SkillDetail } from "@/lib/types";

export function SkillOverview({ detail }: { detail: SkillDetail }) {
  // Use skill_body (full SKILL.md) if available, otherwise fall back to fragments
  const body = detail.skill_body?.trim();

  if (body) {
    return (
      <div className="space-y-6">
        {/* Metadata ribbon */}
        <div className="flex flex-wrap items-center gap-2 text-xs">
          {detail.mcp_tools.length > 0 && (
            <>
              <span className="text-muted-foreground">MCP Tools:</span>
              {detail.mcp_tools.map((tool) => (
                <Badge key={tool} variant="secondary" className="text-[10px]">
                  {tool}
                </Badge>
              ))}
            </>
          )}
          {detail.feedback_enabled && (
            <Badge variant="outline" className="border-emerald-200 bg-emerald-50 text-[10px] text-emerald-600">
              feedback enabled
            </Badge>
          )}
        </div>

        {/* Full SKILL.md rendered as markdown */}
        <article className="prose prose-sm max-w-none prose-headings:text-foreground prose-p:text-foreground/80 prose-li:text-foreground/80 prose-strong:text-foreground prose-code:rounded prose-code:bg-muted prose-code:px-1.5 prose-code:py-0.5 prose-code:text-xs prose-code:text-foreground prose-code:before:content-none prose-code:after:content-none prose-pre:rounded-lg prose-pre:border prose-pre:border-border prose-pre:bg-muted prose-a:text-primary">
          <ReactMarkdown remarkPlugins={[remarkGfm]}>{body}</ReactMarkdown>
        </article>
      </div>
    );
  }

  // Fallback: structured view from extracted fields
  return (
    <div className="space-y-6">
      {detail.task_description && (
        <div className="rounded-lg border border-border p-5">
          <h3 className="mb-2 text-sm font-semibold">Task</h3>
          <p className="text-sm leading-relaxed text-muted-foreground">
            {detail.task_description}
          </p>
        </div>
      )}

      <div className="grid gap-4 md:grid-cols-2">
        {detail.input_schema && (
          <div className="rounded-lg border border-border p-5">
            <h3 className="mb-2 text-sm font-semibold">Input Schema</h3>
            <pre className="max-h-80 overflow-auto rounded-md bg-muted p-3 text-xs">
              {detail.input_schema}
            </pre>
          </div>
        )}
        {detail.output_schema && (
          <div className="rounded-lg border border-border p-5">
            <h3 className="mb-2 text-sm font-semibold">Output Schema</h3>
            <pre className="max-h-80 overflow-auto rounded-md bg-muted p-3 text-xs">
              {detail.output_schema}
            </pre>
          </div>
        )}
      </div>

      {detail.skill_guardrails.length > 0 && (
        <div className="rounded-lg border border-border p-5">
          <h3 className="mb-2 text-sm font-semibold">Guardrails</h3>
          <ul className="space-y-2">
            {detail.skill_guardrails.map((g, i) => (
              <li key={i} className="flex items-start gap-2 text-sm text-muted-foreground">
                <span className="mt-1.5 h-1.5 w-1.5 shrink-0 rounded-full bg-amber-400" />
                {g}
              </li>
            ))}
          </ul>
        </div>
      )}
    </div>
  );
}
