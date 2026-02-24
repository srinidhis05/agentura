"use client";

import { useState } from "react";
import { Button } from "@/components/ui/button";
import { Textarea } from "@/components/ui/textarea";
import { Input } from "@/components/ui/input";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import type { CorrectResponse } from "@/lib/types";
import { correctSkill } from "@/lib/api";

interface Props {
  domain: string;
  skill: string;
  executionId: string;
}

export function CorrectForm({ domain, skill, executionId }: Props) {
  const [correction, setCorrection] = useState("");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [response, setResponse] = useState<CorrectResponse | null>(null);

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    if (!correction.trim()) return;
    setError(null);
    setLoading(true);

    try {
      const res = await correctSkill(domain, skill, {
        execution_id: executionId,
        correction: correction.trim(),
      });
      setResponse(res);
    } catch (err) {
      setError((err as Error).message);
    } finally {
      setLoading(false);
    }
  }

  if (response) {
    return (
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2 text-sm">
            <Badge>Correction Submitted</Badge>
          </CardTitle>
        </CardHeader>
        <CardContent className="space-y-2 text-sm">
          <p>
            <span className="font-medium">Correction ID:</span>{" "}
            <code className="rounded bg-muted px-1.5 py-0.5 text-xs">
              {response.correction_id}
            </code>
          </p>
          <p>
            <span className="font-medium">Reflexion ID:</span>{" "}
            <code className="rounded bg-muted px-1.5 py-0.5 text-xs">
              {response.reflexion_id}
            </code>
          </p>
          {response.deepeval_test && (
            <p>
              <span className="font-medium">DeepEval Test:</span>{" "}
              <code className="rounded bg-muted px-1.5 py-0.5 text-xs">
                {response.deepeval_test}
              </code>
            </p>
          )}
          {response.promptfoo_test && (
            <p>
              <span className="font-medium">Promptfoo Test:</span>{" "}
              <code className="rounded bg-muted px-1.5 py-0.5 text-xs">
                {response.promptfoo_test}
              </code>
            </p>
          )}
          <Button
            variant="outline"
            size="sm"
            className="mt-2"
            onClick={() => {
              setResponse(null);
              setCorrection("");
            }}
          >
            Submit Another Correction
          </Button>
        </CardContent>
      </Card>
    );
  }

  return (
    <form onSubmit={handleSubmit} className="space-y-4">
      <div>
        <label className="mb-1.5 block text-sm font-medium">Execution ID</label>
        <Input value={executionId} readOnly className="bg-muted font-mono text-xs" />
      </div>

      <div>
        <label className="mb-1.5 block text-sm font-medium">Correction</label>
        <Textarea
          value={correction}
          onChange={(e) => setCorrection(e.target.value)}
          rows={5}
          placeholder="Describe what the skill got wrong and what the correct output should be..."
        />
      </div>

      {error && <p className="text-sm text-destructive">{error}</p>}

      <Button type="submit" disabled={loading || !correction.trim()}>
        {loading ? (
          <span className="flex items-center gap-2">
            <span className="h-4 w-4 animate-spin rounded-full border-2 border-current border-t-transparent" />
            Submitting...
          </span>
        ) : (
          "Submit Correction"
        )}
      </Button>
    </form>
  );
}
