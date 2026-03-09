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
  AgentInfo,
  OrgChartNode,
  TicketInfo,
  TicketStats,
  HeartbeatRun,
  HeartbeatScheduleEntry,
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

// Pipeline API

export interface PipelineInfo {
  name: string;
  description: string;
  steps: number;
}

export function listPipelines(): Promise<PipelineInfo[]> {
  return request<PipelineInfo[]>("/api/v1/pipelines");
}

export interface PipelineResult {
  pipeline?: string;
  success: boolean;
  steps_completed: number;
  total_steps?: number;
  total_latency_ms: number;
  total_cost_usd: number;
  url: string | null;
  steps?: Array<{
    step: number;
    skill: string;
    success: boolean;
    latency_ms: number;
    cost_usd: number;
  }>;
}

export async function executePipeline(
  name: string,
  input: Record<string, unknown>,
): Promise<PipelineResult> {
  return request<PipelineResult>(`/api/v1/pipelines/${name}/execute`, {
    method: "POST",
    body: JSON.stringify({ input_data: input }),
  }, 300000);
}

// SSE streaming pipeline execution

export interface PipelineSSEEvent {
  type: "step_started" | "iteration" | "step_completed" | "pipeline_done";
  data: Record<string, unknown>;
}

const SSE_BASE = BASE;

export async function* executePipelineStream(
  name: string,
  input: Record<string, unknown>,
): AsyncGenerator<PipelineSSEEvent> {
  const resp = await fetch(`${SSE_BASE}/api/v1/pipelines/${name}/execute-stream`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ input_data: input }),
  });

  if (!resp.ok) {
    const body = await resp.text().catch(() => "");
    throw new Error(`Pipeline stream API ${resp.status}: ${body}`);
  }

  const reader = resp.body!.getReader();
  const decoder = new TextDecoder();
  let buffer = "";

  while (true) {
    const { done, value } = await reader.read();
    if (done) break;

    buffer += decoder.decode(value, { stream: true });

    // Parse SSE frames: "event: <type>\ndata: <json>\n\n"
    const frames = buffer.split("\n\n");
    buffer = frames.pop()!; // keep incomplete frame in buffer

    for (const frame of frames) {
      if (!frame.trim()) continue;
      let eventType = "";
      let dataStr = "";
      for (const line of frame.split("\n")) {
        if (line.startsWith("event: ")) eventType = line.slice(7).trim();
        else if (line.startsWith("data: ")) dataStr = line.slice(6);
      }
      if (eventType && dataStr) {
        try {
          yield { type: eventType as PipelineSSEEvent["type"], data: JSON.parse(dataStr) };
        } catch {
          // skip malformed SSE frames
        }
      }
    }
  }
}

// Agent Registry API

export function listAgents(params?: { domain?: string; status?: string }): Promise<AgentInfo[]> {
  const searchParams = new URLSearchParams();
  if (params?.domain) searchParams.set("domain", params.domain);
  if (params?.status) searchParams.set("status", params.status);
  const qs = searchParams.toString();
  return request<AgentInfo[]>(`/api/v1/agents${qs ? `?${qs}` : ""}`);
}

export function getAgent(agentId: string): Promise<AgentInfo> {
  return request<AgentInfo>(`/api/v1/agents/${agentId}`);
}

export function getOrgChart(): Promise<OrgChartNode[]> {
  return request<OrgChartNode[]>("/api/v1/agents/org-chart");
}

export function createAgent(data: Partial<AgentInfo>): Promise<{ id: string; name: string }> {
  return request("/api/v1/agents", { method: "POST", body: JSON.stringify(data) });
}

export function updateAgent(agentId: string, data: Partial<AgentInfo>): Promise<{ id: string; updated: boolean }> {
  return request(`/api/v1/agents/${agentId}`, { method: "PUT", body: JSON.stringify(data) });
}

export function deleteAgent(agentId: string): Promise<{ id: string; status: string }> {
  return request(`/api/v1/agents/${agentId}`, { method: "DELETE" });
}

export function delegateTicket(agentId: string, data: { title: string; description: string; priority?: number }): Promise<{ ticket_id: string }> {
  return request(`/api/v1/agents/${agentId}/delegate`, { method: "POST", body: JSON.stringify(data) });
}

// Ticket API

export function listTickets(params?: { domain?: string; status?: string; assigned_to?: string; limit?: number }): Promise<TicketInfo[]> {
  const searchParams = new URLSearchParams();
  if (params?.domain) searchParams.set("domain", params.domain);
  if (params?.status) searchParams.set("status", params.status);
  if (params?.assigned_to) searchParams.set("assigned_to", params.assigned_to);
  if (params?.limit) searchParams.set("limit", String(params.limit));
  const qs = searchParams.toString();
  return request<TicketInfo[]>(`/api/v1/tickets${qs ? `?${qs}` : ""}`);
}

export function getTicket(ticketId: string): Promise<TicketInfo> {
  return request<TicketInfo>(`/api/v1/tickets/${ticketId}`);
}

export function getTicketStats(domain?: string): Promise<TicketStats> {
  const qs = domain ? `?domain=${encodeURIComponent(domain)}` : "";
  return request<TicketStats>(`/api/v1/tickets/stats${qs}`);
}

export function createTicket(data: Partial<TicketInfo>): Promise<{ id: string }> {
  return request("/api/v1/tickets", { method: "POST", body: JSON.stringify(data) });
}

export function updateTicket(ticketId: string, data: Partial<TicketInfo>): Promise<{ id: string; updated: boolean }> {
  return request(`/api/v1/tickets/${ticketId}`, { method: "PUT", body: JSON.stringify(data) });
}

// Heartbeat API

export function listHeartbeatRuns(params?: { agent_id?: string; status?: string; limit?: number }): Promise<HeartbeatRun[]> {
  const searchParams = new URLSearchParams();
  if (params?.agent_id) searchParams.set("agent_id", params.agent_id);
  if (params?.status) searchParams.set("status", params.status);
  if (params?.limit) searchParams.set("limit", String(params.limit));
  const qs = searchParams.toString();
  return request<HeartbeatRun[]>(`/api/v1/heartbeats${qs ? `?${qs}` : ""}`);
}

export function getHeartbeatRun(runId: string): Promise<HeartbeatRun> {
  return request<HeartbeatRun>(`/api/v1/heartbeats/${runId}`);
}

export function getHeartbeatSchedule(): Promise<HeartbeatScheduleEntry[]> {
  return request<HeartbeatScheduleEntry[]>("/api/v1/heartbeats/schedule");
}

export function triggerHeartbeat(agentId: string): Promise<HeartbeatRun> {
  return request<HeartbeatRun>(`/api/v1/heartbeats/${agentId}/trigger`, { method: "POST" });
}

/** @deprecated Use executePipeline("build-deploy", input) instead. */
export async function executeBuildDeploy(input: {
  description: string;
  app_name?: string;
  port?: number;
}): Promise<PipelineResult> {
  return executePipeline("build-deploy", input);
}

// Fleet API

export interface FleetAgent {
  agent_id: string;
  session_id: string;
  skill_path: string;
  execution_id: string;
  status: "pending" | "running" | "completed" | "failed" | "cancelled";
  pod_name: string;
  success: boolean;
  output: Record<string, unknown> | null;
  cost_usd: number;
  latency_ms: number;
  error_message: string;
  created_at: string;
  updated_at: string;
}

export interface FleetSession {
  session_id: string;
  pipeline_name: string;
  trigger_type: string;
  repo: string;
  pr_number: number;
  pr_url: string;
  head_sha: string;
  status: "pending" | "running" | "completed" | "failed" | "cancelled";
  total_agents: number;
  completed_agents: number;
  failed_agents: number;
  total_cost_usd: number;
  input_data: Record<string, unknown> | null;
  github_check_posted: boolean;
  created_at: string;
  updated_at: string;
  agents?: FleetAgent[];
}

export function listFleetSessions(status?: string): Promise<FleetSession[]> {
  const params = status && status !== "all" ? `?status=${encodeURIComponent(status)}` : "";
  return request<FleetSession[]>(`/api/v1/fleet/sessions${params}`);
}

export function getFleetSession(sessionId: string): Promise<FleetSession> {
  return request<FleetSession>(`/api/v1/fleet/sessions/${sessionId}`);
}

export function cancelFleetSession(sessionId: string): Promise<{ session_id: string; status: string }> {
  return request(`/api/v1/fleet/sessions/${sessionId}/cancel`, { method: "POST" });
}

export interface FleetSSEEvent {
  type: "agent_update" | "session_done" | "error";
  data: Record<string, unknown>;
}

export async function* streamFleetSession(
  sessionId: string,
): AsyncGenerator<FleetSSEEvent> {
  const resp = await fetch(`${SSE_BASE}/api/v1/fleet/sessions/${sessionId}/stream`);

  if (!resp.ok) {
    const body = await resp.text().catch(() => "");
    throw new Error(`Fleet stream API ${resp.status}: ${body}`);
  }

  const reader = resp.body!.getReader();
  const decoder = new TextDecoder();
  let buffer = "";

  while (true) {
    const { done, value } = await reader.read();
    if (done) break;

    buffer += decoder.decode(value, { stream: true });
    const frames = buffer.split("\n\n");
    buffer = frames.pop()!;

    for (const frame of frames) {
      if (!frame.trim()) continue;
      let eventType = "";
      let dataStr = "";
      for (const line of frame.split("\n")) {
        if (line.startsWith("event: ")) eventType = line.slice(7).trim();
        else if (line.startsWith("data: ")) dataStr = line.slice(6);
      }
      if (eventType && dataStr) {
        try {
          yield { type: eventType as FleetSSEEvent["type"], data: JSON.parse(dataStr) };
        } catch {
          // skip malformed frames
        }
      }
    }
  }
}
