"use client";

import { useState } from "react";
import { Button } from "@/components/ui/button";
import { Textarea } from "@/components/ui/textarea";
import { Input } from "@/components/ui/input";
import { Switch } from "@/components/ui/switch";
import type { ExecuteRequest, SkillResult } from "@/lib/types";
import { executeSkill } from "@/lib/api";

interface Props {
  domain: string;
  skill: string;
  onResult: (result: SkillResult) => void;
}

export function ExecuteForm({ domain, skill, onResult }: Props) {
  const [inputData, setInputData] = useState("{}");
  const [modelOverride, setModelOverride] = useState("");
  const [dryRun, setDryRun] = useState(false);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    setError(null);
    setLoading(true);

    try {
      const parsed = JSON.parse(inputData);
      const req: ExecuteRequest = {
        input_data: parsed,
        dry_run: dryRun,
        ...(modelOverride ? { model_override: modelOverride } : {}),
      };
      const result = await executeSkill(domain, skill, req);
      onResult(result);
    } catch (err) {
      setError(err instanceof SyntaxError ? "Invalid JSON" : (err as Error).message);
    } finally {
      setLoading(false);
    }
  }

  return (
    <form onSubmit={handleSubmit} className="space-y-4">
      <div>
        <label className="mb-1.5 block text-sm font-medium">Input Data (JSON)</label>
        <Textarea
          value={inputData}
          onChange={(e) => setInputData(e.target.value)}
          rows={8}
          className="font-mono text-sm"
          placeholder='{"portfolio": {"cash": 100000}}'
        />
      </div>

      <div>
        <label className="mb-1.5 block text-sm font-medium">
          Model Override <span className="text-muted-foreground">(optional)</span>
        </label>
        <Input
          value={modelOverride}
          onChange={(e) => setModelOverride(e.target.value)}
          placeholder="e.g. anthropic/claude-3.5-sonnet"
        />
      </div>

      <div className="flex items-center gap-3">
        <Switch checked={dryRun} onCheckedChange={setDryRun} id="dry-run" />
        <label htmlFor="dry-run" className="text-sm font-medium">
          Dry Run
        </label>
      </div>

      {error && (
        <p className="text-sm text-destructive">{error}</p>
      )}

      <Button type="submit" disabled={loading} className="w-full">
        {loading ? (
          <span className="flex items-center gap-2">
            <span className="h-4 w-4 animate-spin rounded-full border-2 border-current border-t-transparent" />
            Executing...
          </span>
        ) : (
          "Execute Skill"
        )}
      </Button>
    </form>
  );
}
