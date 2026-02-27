"use client";

import { useState, useMemo } from "react";
import { useQuery } from "@tanstack/react-query";
import { listSkills, listPipelines } from "@/lib/api";
import { domainColors, domainEmojis } from "@/lib/domain-config";
import type { SkillInfo } from "@/lib/types";
import type { PipelineInfo } from "@/lib/api";

export interface DomainEntry {
  name: string;
  description: string;
  emoji: string;
  color: string;
  manager?: SkillInfo;
  specialistCount: number;
}

interface AgentPickerProps {
  onSelectDomain: (domain: DomainEntry) => void;
  onSelectPipeline: (pipeline: PipelineInfo) => void;
}

export function AgentPicker({ onSelectDomain, onSelectPipeline }: AgentPickerProps) {
  const [search, setSearch] = useState("");

  const { data: skills } = useQuery({ queryKey: ["skills"], queryFn: listSkills });
  const { data: pipelines } = useQuery({ queryKey: ["pipelines"], queryFn: listPipelines });

  // Build domain entries: group skills, extract manager, count specialists
  const domains = useMemo(() => {
    const allSkills = skills ?? [];
    const groups: Record<string, SkillInfo[]> = {};
    for (const s of allSkills) {
      if (s.domain === "platform") continue;
      (groups[s.domain] ??= []).push(s);
    }

    return Object.entries(groups).map(([name, domainSkills]): DomainEntry => {
      const manager = domainSkills.find((s) => s.role === "manager");
      const specialists = domainSkills.filter((s) => s.role !== "manager");
      return {
        name,
        description: manager?.display_subtitle || manager?.domain_description || `${specialists.length} specialist agents`,
        emoji: domainEmojis[name] ?? "\u{1F4E6}",
        color: domainColors[name] ?? "#6b7280",
        manager,
        specialistCount: specialists.length,
      };
    });
  }, [skills]);

  const filteredDomains = useMemo(() => {
    if (!search.trim()) return domains;
    const q = search.toLowerCase();
    return domains.filter(
      (d) =>
        d.name.toLowerCase().includes(q) ||
        d.description.toLowerCase().includes(q),
    );
  }, [domains, search]);

  const filteredPipelines = useMemo(() => {
    if (!search.trim()) return pipelines ?? [];
    const q = search.toLowerCase();
    return (pipelines ?? []).filter(
      (p) => p.name.toLowerCase().includes(q) || p.description.toLowerCase().includes(q),
    );
  }, [pipelines, search]);

  return (
    <div className="flex flex-1 flex-col items-center overflow-y-auto px-4 py-8">
      {/* Header */}
      <div className="mb-6 flex flex-col items-center">
        <div className="mb-4 flex h-14 w-14 items-center justify-center rounded-2xl bg-gradient-to-br from-blue-500 to-violet-600">
          <svg className="h-7 w-7 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 10V3L4 14h7v7l9-11h-7z" />
          </svg>
        </div>
        <h1 className="text-2xl font-bold tracking-tight">Agentura</h1>
        <p className="mt-2 text-sm text-muted-foreground">Choose a domain or workflow to start</p>
      </div>

      {/* Search */}
      <div className="mb-6 w-full max-w-2xl">
        <div className="flex items-center gap-2 rounded-xl border border-border bg-card px-3 py-2 focus-within:border-ring focus-within:ring-1 focus-within:ring-ring">
          <svg className="h-4 w-4 text-muted-foreground" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z" />
          </svg>
          <input
            type="text"
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            placeholder="Search domains and workflows..."
            className="flex-1 bg-transparent text-sm outline-none placeholder:text-muted-foreground/60"
          />
        </div>
      </div>

      <div className="w-full max-w-2xl space-y-6">
        {/* Pipeline cards */}
        {filteredPipelines.length > 0 && (
          <div>
            <p className="mb-2 px-1 text-[10px] font-semibold uppercase tracking-wider text-muted-foreground/60">
              Workflows
            </p>
            <div className="flex gap-3 overflow-x-auto pb-1">
              {filteredPipelines.map((p) => (
                <button
                  key={p.name}
                  onClick={() => onSelectPipeline(p)}
                  className="flex min-w-[200px] shrink-0 flex-col rounded-xl border border-violet-500/30 bg-card p-4 text-left transition-colors hover:border-violet-500/60 hover:bg-accent/50"
                >
                  <div className="flex items-center gap-2">
                    <div className="flex h-8 w-8 items-center justify-center rounded-lg bg-gradient-to-br from-violet-500 to-purple-600 text-xs font-bold text-white">
                      <svg className="h-4 w-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15" />
                      </svg>
                    </div>
                    <span className="text-sm font-semibold">{p.name.replace(/-/g, " ").replace(/\b\w/g, (c) => c.toUpperCase())}</span>
                  </div>
                  <p className="mt-2 text-xs text-muted-foreground line-clamp-2">{p.description || `${p.steps}-step pipeline`}</p>
                  <span className="mt-2 text-[10px] text-muted-foreground/60">{p.steps} steps</span>
                </button>
              ))}
            </div>
          </div>
        )}

        {/* Domain cards */}
        {filteredDomains.length > 0 && (
          <div>
            <p className="mb-2 px-1 text-[10px] font-semibold uppercase tracking-wider text-muted-foreground/60">
              Domains
            </p>
            <div className="grid grid-cols-1 gap-3 sm:grid-cols-2">
              {filteredDomains.map((d) => (
                <button
                  key={d.name}
                  onClick={() => onSelectDomain(d)}
                  className="flex items-start gap-3 rounded-xl border bg-card p-4 text-left transition-colors hover:bg-accent/50"
                  style={{ borderColor: `${d.color}30` }}
                >
                  <div
                    className="flex h-11 w-11 shrink-0 items-center justify-center rounded-lg text-lg"
                    style={{ backgroundColor: `${d.color}15` }}
                  >
                    {d.emoji}
                  </div>
                  <div className="min-w-0 flex-1">
                    <div className="flex items-center gap-2">
                      <span className="text-sm font-semibold capitalize">{d.name}</span>
                      <span className="text-[10px] text-muted-foreground/60">
                        {d.specialistCount} agent{d.specialistCount !== 1 ? "s" : ""}
                      </span>
                    </div>
                    <p className="mt-0.5 text-xs text-muted-foreground line-clamp-2">{d.description}</p>
                  </div>
                </button>
              ))}
            </div>
          </div>
        )}

        {filteredDomains.length === 0 && filteredPipelines.length === 0 && (
          <p className="py-8 text-center text-sm text-muted-foreground">
            {search ? `No results matching "${search}"` : "No domains deployed. Use the CLI to create skills."}
          </p>
        )}
      </div>
    </div>
  );
}
