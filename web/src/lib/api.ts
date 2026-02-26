import type {
  SkillInfo,
  SkillDetail,
  SkillResult,
  ExecuteRequest,
  CorrectRequest,
  CorrectResponse,
  CreateSkillRequest,
  CreateSkillResponse,
  ExecutionEntry,
  ExecutionDetail,
  Analytics,
  KnowledgeReflexionEntry,
  KnowledgeCorrectionEntry,
  TestEntry,
  KnowledgeStats,
  TestValidationResult,
  DomainSummary,
  DomainDetail,
  PlatformHealth,
  PlatformEvent,
  MemoryStatus,
  MemorySearchResult,
  PromptAssembly,
  ApprovalResponse,
} from "./types";

// In dev mode, Next.js rewrites /api/* to the executor. In production, use the gateway.
const BASE = process.env.NEXT_PUBLIC_API_URL || "";

async function request<T>(path: string, init?: RequestInit, timeoutMs = 15000): Promise<T> {
  const controller = new AbortController();
  const timeout = setTimeout(() => controller.abort(), timeoutMs);
  try {
    const res = await fetch(`${BASE}${path}`, {
      headers: { "Content-Type": "application/json" },
      signal: controller.signal,
      ...init,
    });
    if (!res.ok) {
      const body = await res.text().catch(() => "");
      throw new Error(`API ${res.status}: ${body}`);
    }
    return res.json() as Promise<T>;
  } catch (err) {
    if (err instanceof DOMException && err.name === "AbortError") {
      throw new Error("API unreachable — is the backend running? (agentura-server)");
    }
    throw err;
  } finally {
    clearTimeout(timeout);
  }
}

export function createSkill(req: CreateSkillRequest): Promise<CreateSkillResponse> {
  return request<CreateSkillResponse>("/api/v1/skills", {
    method: "POST",
    body: JSON.stringify(req),
  });
}

export function listSkills(): Promise<SkillInfo[]> {
  return request<SkillInfo[]>("/api/v1/skills");
}

export function getSkillDetail(
  domain: string,
  skill: string,
): Promise<SkillDetail> {
  return request<SkillDetail>(`/api/v1/skills/${domain}/${skill}`);
}

export function executeSkill(
  domain: string,
  skill: string,
  req: ExecuteRequest,
): Promise<SkillResult> {
  return request<SkillResult>(`/api/v1/skills/${domain}/${skill}/execute`, {
    method: "POST",
    body: JSON.stringify(req),
  }, 60000);
}

export function correctSkill(
  domain: string,
  skill: string,
  req: CorrectRequest,
): Promise<CorrectResponse> {
  return request<CorrectResponse>(`/api/v1/skills/${domain}/${skill}/correct`, {
    method: "POST",
    body: JSON.stringify(req),
  });
}

export function listExecutions(skill?: string): Promise<ExecutionEntry[]> {
  const params = skill ? `?skill=${encodeURIComponent(skill)}` : "";
  return request<ExecutionEntry[]>(`/api/v1/executions${params}`);
}

export function getExecution(executionId: string): Promise<ExecutionDetail> {
  return request<ExecutionDetail>(`/api/v1/executions/${executionId}`);
}

export function approveExecution(
  executionId: string,
  approved: boolean,
  reviewerNotes: string = "",
): Promise<ApprovalResponse> {
  return request<ApprovalResponse>(`/api/v1/executions/${executionId}/approve`, {
    method: "POST",
    body: JSON.stringify({ approved, reviewer_notes: reviewerNotes }),
  });
}

export function getAnalytics(): Promise<Analytics> {
  return request<Analytics>("/api/v1/analytics");
}

export async function checkHealth(): Promise<boolean> {
  try {
    const res = await fetch(`${BASE}/healthz`);
    return res.ok;
  } catch {
    return false;
  }
}

// Knowledge Layer API

export function listReflexions(skill?: string): Promise<KnowledgeReflexionEntry[]> {
  const params = skill ? `?skill=${encodeURIComponent(skill)}` : "";
  return request<KnowledgeReflexionEntry[]>(`/api/v1/knowledge/reflexions${params}`);
}

export function listCorrections(skill?: string): Promise<KnowledgeCorrectionEntry[]> {
  const params = skill ? `?skill=${encodeURIComponent(skill)}` : "";
  return request<KnowledgeCorrectionEntry[]>(`/api/v1/knowledge/corrections${params}`);
}

export function listTests(skill?: string): Promise<TestEntry[]> {
  const params = skill ? `?skill=${encodeURIComponent(skill)}` : "";
  return request<TestEntry[]>(`/api/v1/knowledge/tests${params}`);
}

export function getKnowledgeStats(): Promise<KnowledgeStats> {
  return request<KnowledgeStats>("/api/v1/knowledge/stats");
}

export function validateTests(domain: string, skill: string): Promise<TestValidationResult> {
  return request<TestValidationResult>(`/api/v1/knowledge/validate/${domain}/${skill}`, {
    method: "POST",
  });
}

// Domain API

export function listDomains(): Promise<DomainSummary[]> {
  return request<DomainSummary[]>("/api/v1/domains");
}

export function getDomainDetail(domain: string): Promise<DomainDetail> {
  return request<DomainDetail>(`/api/v1/domains/${domain}`);
}

// Platform API

export function getPlatformHealth(): Promise<PlatformHealth> {
  return request<PlatformHealth>("/api/v1/platform/health");
}

// Events API

export function listEvents(params?: { domain?: string; event_type?: string; limit?: number }): Promise<PlatformEvent[]> {
  const searchParams = new URLSearchParams();
  if (params?.domain) searchParams.set("domain", params.domain);
  if (params?.event_type) searchParams.set("event_type", params.event_type);
  if (params?.limit) searchParams.set("limit", String(params.limit));
  const qs = searchParams.toString();
  return request<PlatformEvent[]>(`/api/v1/events${qs ? `?${qs}` : ""}`);
}

// Memory Explorer API

export function getMemoryStatus(): Promise<MemoryStatus> {
  return request<MemoryStatus>("/api/v1/memory/status");
}

export function memorySearch(query: string, limit: number = 10): Promise<MemorySearchResult> {
  return request<MemorySearchResult>("/api/v1/memory/search", {
    method: "POST",
    body: JSON.stringify({ query, limit }),
  });
}

export function getPromptAssembly(domain: string, skill: string): Promise<PromptAssembly> {
  return request<PromptAssembly>(`/api/v1/memory/prompt-assembly/${domain}/${skill}`);
}
