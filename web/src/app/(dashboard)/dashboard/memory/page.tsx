"use client";

import { useQuery } from "@tanstack/react-query";
import { useState } from "react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { getMemoryStatus, memorySearch, listReflexions, listCorrections } from "@/lib/api";

const backendColors: Record<string, string> = {
  postgresql: "text-blue-700 bg-blue-50 border-blue-200",
  pg: "text-blue-700 bg-blue-50 border-blue-200",
  mem0: "text-violet-700 bg-violet-50 border-violet-200",
  json: "text-amber-700 bg-amber-50 border-amber-200",
};

function getBackendStyle(backend: string): string {
  const key = backend.toLowerCase();
  for (const [k, v] of Object.entries(backendColors)) {
    if (key.includes(k)) return v;
  }
  return "text-gray-700 bg-gray-50 border-gray-200";
}

export default function MemoryPage() {
  const [searchQuery, setSearchQuery] = useState("");
  const [searchResults, setSearchResults] = useState<Record<string, unknown>[] | null>(null);
  const [searchBackend, setSearchBackend] = useState("");
  const [searching, setSearching] = useState(false);

  const { data: status, isLoading: statusLoading } = useQuery({
    queryKey: ["memory-status"],
    queryFn: getMemoryStatus,
    refetchInterval: 30_000,
  });

  const { data: reflexions } = useQuery({
    queryKey: ["reflexions-all"],
    queryFn: () => listReflexions(),
  });

  const { data: corrections } = useQuery({
    queryKey: ["corrections-all"],
    queryFn: () => listCorrections(),
  });

  async function handleSearch() {
    if (!searchQuery.trim()) return;
    setSearching(true);
    try {
      const result = await memorySearch(searchQuery.trim(), 20);
      setSearchResults(result.results);
      setSearchBackend(result.backend);
    } catch {
      setSearchResults([]);
      setSearchBackend("error");
    } finally {
      setSearching(false);
    }
  }

  if (statusLoading) {
    return (
      <div className="flex items-center justify-center py-20">
        <div className="h-8 w-8 animate-spin rounded-full border-4 border-primary border-t-transparent" />
      </div>
    );
  }

  const allReflexions = reflexions ?? [];
  const allCorrections = corrections ?? [];
  const validatedCount = allReflexions.filter((r) => r.validated_by_test).length;
  const skillsWithMemory = [...new Set([
    ...allReflexions.map((r) => r.skill),
    ...allCorrections.map((c) => c.skill),
  ])];

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <h2 className="text-lg font-semibold">Memory Layer</h2>
        {status && (
          <Badge variant="outline" className={getBackendStyle(status.backend)}>
            {status.backend.toUpperCase()}
          </Badge>
        )}
      </div>

      {/* Backend Status */}
      {status && (
        <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
          <Card className="border-l-2 border-l-blue-500">
            <CardHeader className="pb-2">
              <CardTitle className="text-xs font-medium text-muted-foreground">Backend</CardTitle>
            </CardHeader>
            <CardContent>
              <p className="text-xl font-bold capitalize">{status.backend}</p>
              <div className="mt-1 space-y-0.5 text-[10px] text-muted-foreground">
                <p>Vector: {status.vector_store}</p>
                <p>Embedder: {status.embedder}</p>
                <p>LLM: {status.llm_provider}</p>
              </div>
            </CardContent>
          </Card>

          <Card className="border-l-2 border-l-emerald-500">
            <CardHeader className="pb-2">
              <CardTitle className="text-xs font-medium text-muted-foreground">Total Memories</CardTitle>
            </CardHeader>
            <CardContent>
              <p className="text-2xl font-bold text-emerald-600">{status.total_memories}</p>
              <div className="mt-1 flex gap-3 text-[10px] text-muted-foreground">
                <span>{status.execution_memories} exec</span>
                <span>{status.correction_memories} corr</span>
                <span>{status.reflexion_memories} refl</span>
              </div>
            </CardContent>
          </Card>

          <Card className="border-l-2 border-l-violet-500">
            <CardHeader className="pb-2">
              <CardTitle className="text-xs font-medium text-muted-foreground">Reflexion Rules</CardTitle>
            </CardHeader>
            <CardContent>
              <p className="text-2xl font-bold text-violet-600">{allReflexions.length}</p>
              <div className="mt-1 text-[10px] text-muted-foreground">
                <span className="text-emerald-600">{validatedCount} validated</span>
                <span className="mx-1">/</span>
                <span>{allReflexions.length - validatedCount} pending</span>
              </div>
            </CardContent>
          </Card>

          <Card className="border-l-2 border-l-amber-500">
            <CardHeader className="pb-2">
              <CardTitle className="text-xs font-medium text-muted-foreground">Skills Tracked</CardTitle>
            </CardHeader>
            <CardContent>
              <p className="text-2xl font-bold text-amber-600">{status.skills_tracked.length}</p>
              <div className="mt-1 flex flex-wrap gap-1">
                {status.skills_tracked.slice(0, 6).map((s) => (
                  <span key={s} className="rounded bg-accent/50 px-1 py-0.5 font-mono text-[9px]">
                    {s}
                  </span>
                ))}
                {status.skills_tracked.length > 6 && (
                  <span className="text-[9px] text-muted-foreground">+{status.skills_tracked.length - 6}</span>
                )}
              </div>
            </CardContent>
          </Card>
        </div>
      )}

      {/* Cross-Domain Search */}
      <Card>
        <CardHeader>
          <CardTitle className="text-sm">Cross-Domain Memory Search</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="flex gap-2">
            <input
              type="text"
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              onKeyDown={(e) => e.key === "Enter" && handleSearch()}
              placeholder="Search across all skill memories..."
              className="flex-1 rounded-md border border-border bg-background px-3 py-2 text-sm placeholder:text-muted-foreground focus:outline-none focus:ring-1 focus:ring-ring"
            />
            <Button
              onClick={handleSearch}
              disabled={searching || !searchQuery.trim()}
              className="px-4"
            >
              {searching ? "..." : "Search"}
            </Button>
          </div>

          {searchResults !== null && (
            <div className="mt-4">
              <div className="mb-2 flex items-center justify-between">
                <span className="text-xs text-muted-foreground">
                  {searchResults.length} results via {searchBackend}
                </span>
              </div>
              {searchResults.length === 0 ? (
                <p className="py-4 text-center text-xs text-muted-foreground">No matching memories found.</p>
              ) : (
                <div className="space-y-2">
                  {searchResults.map((result, i) => (
                    <div
                      key={i}
                      className="rounded-md border border-border bg-accent/50 p-3"
                    >
                      <div className="flex items-center gap-2">
                        <Badge variant="outline" className="text-[9px]">
                          {(result.type as string) ?? "memory"}
                        </Badge>
                        <span className="font-mono text-[11px] text-muted-foreground">
                          {(result.skill as string) ?? ""}
                        </span>
                        {result.score != null && (
                          <span className="ml-auto text-[10px] text-emerald-600">
                            {((result.score as number) * 100).toFixed(0)}% match
                          </span>
                        )}
                      </div>
                      <p className="mt-1 text-xs">
                        {(result.memory as string) ?? (result.rule as string) ?? JSON.stringify(result).slice(0, 200)}
                      </p>
                    </div>
                  ))}
                </div>
              )}
            </div>
          )}
        </CardContent>
      </Card>

      <div className="grid gap-6 lg:grid-cols-2">
        {/* Reflexion Rules */}
        <Card>
          <CardHeader>
            <div className="flex items-center justify-between">
              <CardTitle className="text-sm">Reflexion Rules</CardTitle>
              <span className="text-[10px] text-muted-foreground">{allReflexions.length} total</span>
            </div>
          </CardHeader>
          <CardContent>
            {allReflexions.length === 0 ? (
              <p className="py-6 text-center text-xs text-muted-foreground">
                No reflexions yet. Correct a skill execution to generate rules.
              </p>
            ) : (
              <div className="space-y-2 max-h-96 overflow-y-auto">
                {allReflexions.map((r) => (
                  <div
                    key={r.reflexion_id}
                    className="rounded-md border border-border p-3"
                  >
                    <div className="flex items-center gap-2">
                      <span className="font-mono text-[10px] text-violet-600">{r.reflexion_id}</span>
                      <span className="font-mono text-[10px] text-muted-foreground">{r.skill}</span>
                      {r.validated_by_test && (
                        <Badge variant="outline" className="text-[8px] bg-emerald-50 text-emerald-700 border-emerald-200">
                          validated
                        </Badge>
                      )}
                      <span className="ml-auto text-[10px] text-muted-foreground">
                        {(r.confidence * 100).toFixed(0)}% conf
                      </span>
                    </div>
                    <p className="mt-1 text-xs font-medium">{r.rule}</p>
                    {r.applies_when && (
                      <p className="mt-0.5 text-[11px] text-muted-foreground">
                        When: {r.applies_when}
                      </p>
                    )}
                  </div>
                ))}
              </div>
            )}
          </CardContent>
        </Card>

        {/* Corrections Feed */}
        <Card>
          <CardHeader>
            <div className="flex items-center justify-between">
              <CardTitle className="text-sm">Corrections</CardTitle>
              <span className="text-[10px] text-muted-foreground">{allCorrections.length} total</span>
            </div>
          </CardHeader>
          <CardContent>
            {allCorrections.length === 0 ? (
              <p className="py-6 text-center text-xs text-muted-foreground">
                No corrections yet. Use the CLI or UI to correct skill outputs.
              </p>
            ) : (
              <div className="space-y-2 max-h-96 overflow-y-auto">
                {allCorrections.map((c) => (
                  <div
                    key={c.correction_id}
                    className="rounded-md border border-border p-3"
                  >
                    <div className="flex items-center gap-2">
                      <span className="font-mono text-[10px] text-amber-600">{c.correction_id}</span>
                      <span className="font-mono text-[10px] text-muted-foreground">{c.skill}</span>
                      {c.generated_reflexion_id && (
                        <Badge variant="outline" className="text-[8px] bg-violet-50 text-violet-700 border-violet-200">
                          reflexion
                        </Badge>
                      )}
                    </div>
                    <p className="mt-1 text-xs">{c.corrected_output || "—"}</p>
                    <p className="mt-0.5 text-[10px] text-muted-foreground">
                      Execution: {c.execution_id} | {c.created_at ? new Date(c.created_at).toLocaleDateString() : ""}
                    </p>
                  </div>
                ))}
              </div>
            )}
          </CardContent>
        </Card>
      </div>

      {/* Skills with Memory — by domain */}
      {skillsWithMemory.length > 0 && (
        <Card>
          <CardHeader>
            <CardTitle className="text-sm">Memory Coverage by Skill</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="grid gap-2 sm:grid-cols-2 lg:grid-cols-3">
              {skillsWithMemory.map((skill) => {
                const reflexionCount = allReflexions.filter((r) => r.skill === skill).length;
                const correctionCount = allCorrections.filter((c) => c.skill === skill).length;
                const domain = skill.split("/")[0];
                return (
                  <div
                    key={skill}
                    className="flex items-center justify-between rounded-md border border-border px-3 py-2"
                  >
                    <span className="font-mono text-xs">{skill}</span>
                    <div className="flex gap-2 text-[10px]">
                      {reflexionCount > 0 && (
                        <span className="text-violet-600">{reflexionCount} refl</span>
                      )}
                      {correctionCount > 0 && (
                        <span className="text-amber-600">{correctionCount} corr</span>
                      )}
                    </div>
                  </div>
                );
              })}
            </div>
          </CardContent>
        </Card>
      )}
    </div>
  );
}
