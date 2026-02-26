import { Badge } from "@/components/ui/badge";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Separator } from "@/components/ui/separator";
import type { SkillResult } from "@/lib/types";
import { formatOutput } from "@/lib/format-output";

export function ResultPanel({ result }: { result: SkillResult }) {
  return (
    <div className="space-y-4">
      <div className="flex flex-wrap items-center gap-2">
        <Badge variant={result.success ? "default" : "destructive"}>
          {result.success ? "Success" : "Error"}
        </Badge>
        <Badge variant="outline" className="font-mono text-xs">
          {result.model_used}
        </Badge>
        <Badge variant="outline">${result.cost_usd.toFixed(4)}</Badge>
        <Badge variant="outline">{result.latency_ms}ms</Badge>
        {result.route_to && (
          <Badge variant="secondary">Route to: {result.route_to}</Badge>
        )}
      </div>

      <Card>
        <CardHeader className="pb-2">
          <CardTitle className="text-sm">Output</CardTitle>
        </CardHeader>
        <CardContent>
          <pre className="max-h-[600px] overflow-auto whitespace-pre-wrap break-words rounded-md bg-muted p-4 text-xs leading-relaxed text-foreground">
            {formatOutput(result.output)}
          </pre>
        </CardContent>
      </Card>

      {result.reasoning_trace.length > 0 && (
        <>
          <Separator />
          <Card>
            <CardHeader className="pb-2">
              <CardTitle className="text-sm">Reasoning Trace</CardTitle>
            </CardHeader>
            <CardContent>
              <ol className="list-inside list-decimal space-y-1 text-sm text-muted-foreground">
                {result.reasoning_trace.map((step, i) => (
                  <li key={i}>{step}</li>
                ))}
              </ol>
            </CardContent>
          </Card>
        </>
      )}

      {Object.keys(result.context_for_next).length > 0 && (
        <>
          <Separator />
          <Card>
            <CardHeader className="pb-2">
              <CardTitle className="text-sm">Context for Next</CardTitle>
            </CardHeader>
            <CardContent>
              <pre className="max-h-40 overflow-auto whitespace-pre-wrap break-words rounded-md bg-muted p-3 text-xs text-foreground">
                {JSON.stringify(result.context_for_next, null, 2)}
              </pre>
            </CardContent>
          </Card>
        </>
      )}
    </div>
  );
}
