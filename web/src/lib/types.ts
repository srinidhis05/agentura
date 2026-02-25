export interface SkillInfo {
  domain: string;
  name: string;
  role: string;
  model: string;
  trigger: string;
  description: string;
  cost_budget: string;
  timeout: string;
  mcp_tools: string[];
  domain_description: string;
  domain_owner: string;
  guardrails_count: number;
  corrections_count: number;
  // Lifecycle (K8s pod-like)
  deploy_status: string; // active | canary | shadow | disabled
  health: string; // healthy | degraded | failing | unknown
  version: string;
  last_deployed: string;
  executions_total: number;
  accept_rate: number;
}

export interface SkillDetail extends SkillInfo {
  // Lifecycle inherited from SkillInfo
  task_description: string;
  input_schema: string;
  output_schema: string;
  skill_body: string;
  skill_guardrails: string[];
  triggers: Record<string, unknown>[];
  feedback_enabled: boolean;
}

export interface SkillResult {
  skill_name: string;
  success: boolean;
  output: Record<string, unknown>;
  reasoning_trace: string[];
  model_used: string;
  cost_usd: number;
  latency_ms: number;
  route_to: string | null;
  context_for_next: Record<string, unknown>;
  approval_required: boolean;
  pending_action: string;
}

export interface ExecuteRequest {
  input_data: Record<string, unknown>;
  model_override?: string;
  dry_run: boolean;
}

export interface CorrectRequest {
  execution_id: string;
  correction: string;
}

export interface CorrectResponse {
  correction_id: string;
  reflexion_id: string;
  deepeval_test: string | null;
  promptfoo_test: string | null;
}

export interface ExecutionEntry {
  execution_id: string;
  skill: string;
  timestamp: string;
  input_summary: unknown;
  output_summary: unknown;
  outcome: string;
  cost_usd: number;
  latency_ms: number;
  model_used: string;
  user_feedback: string | null;
  correction_generated_test: boolean;
  reflexion_applied: string | null;
  reviewer_notes: string;
}

export interface ApprovalRequest {
  approved: boolean;
  reviewer_notes: string;
}

export interface ApprovalResponse {
  execution_id: string;
  outcome: string;
  reviewer_notes: string;
}

export interface CorrectionEntry {
  correction_id: string;
  execution_id: string;
  skill: string;
  timestamp: string;
  original_output: unknown;
  user_correction: string;
}

export interface ReflexionEntry {
  reflexion_id: string;
  correction_id: string;
  skill: string;
  created_at: string;
  rule: string;
  applies_when: string;
  confidence: number;
  validated_by_test: boolean;
}

export interface ExecutionDetail {
  execution: ExecutionEntry;
  corrections: CorrectionEntry[];
  reflexions: ReflexionEntry[];
}

export interface Analytics {
  total_executions: number;
  accepted: number;
  corrected: number;
  pending_review: number;
  accept_rate: number;
  total_cost_usd: number;
  avg_cost_usd: number;
  avg_latency_ms: number;
  total_corrections: number;
  total_reflexions: number;
  correction_to_test_rate: number;
  executions_by_skill: Record<string, number>;
  cost_by_skill: Record<string, number>;
  latency_by_skill: Record<string, number>;
  recent_executions: ExecutionEntry[];
}

// Knowledge Layer types

export interface KnowledgeReflexionEntry {
  reflexion_id: string;
  skill: string;
  rule: string;
  applies_when: string;
  confidence: number;
  validated_by_test: boolean;
  source_correction_id: string;
  created_at: string;
}

export interface KnowledgeCorrectionEntry {
  correction_id: string;
  skill: string;
  execution_id: string;
  original_output: unknown;
  corrected_output: string;
  correction_type: string;
  generated_reflexion_id: string | null;
  generated_test_ids: string[];
  created_at: string;
}

export interface TestEntry {
  test_id: string;
  skill: string;
  test_type: string;
  source: string;
  description: string;
  status: string;
  source_correction_id: string | null;
}

export interface KnowledgeStats {
  total_corrections: number;
  total_reflexions: number;
  total_tests: number;
  validated_reflexions: number;
  learning_rate: number;
  skills_with_reflexions: number;
  skills_with_tests: number;
}

// Test Validation result

export interface TestValidationResult {
  skill: string;
  tests_run: number;
  tests_passed: number;
  tests_failed: number;
  reflexions_validated: string[];
}

// Events types (kubectl get events equivalent)

export interface PlatformEvent {
  event_id: string;
  event_type: string; // skill_executed | correction_submitted | reflexion_generated | test_generated
  severity: string; // info | warning | error
  domain: string;
  skill: string;
  message: string;
  timestamp: string;
  metadata: Record<string, unknown>;
}

// Resource Quota (K8s ResourceQuota equivalent)

export interface ResourceQuota {
  cost_budget: string;
  cost_spent: string;
  budget_utilization: number;
  max_cost_per_session: string;
  max_skills_per_session: number;
  rate_limit_rpm: number;
  human_approval_thresholds: { action: string; threshold: string }[];
  blocked_actions: string[];
}

// Domain types

export interface SkillRoute {
  from_skill: string;
  to_skill: string;
  route_condition: string;
}

export interface DomainSummary {
  name: string;
  description: string;
  owner: string;
  skills_count: number;
  managers_count: number;
  specialists_count: number;
  field_agents_count: number;
  total_executions: number;
  accept_rate: number;
  total_corrections: number;
  total_reflexions: number;
  cost_budget: string;
  cost_spent: string;
  mcp_tools: string[];
  resource_quota: ResourceQuota;
}

export interface DomainDetail extends DomainSummary {
  identity: string;
  skills: SkillInfo[];
  topology: SkillRoute[];
  guardrails: string[];
  recent_executions: ExecutionEntry[];
  recent_corrections: CorrectionEntry[];
}

// Platform Health types

export interface ComponentHealth {
  name: string;
  status: string;
  latency_ms: number;
  version: string;
  last_check: string;
}

export interface MCPToolHealth {
  name: string;
  status: string;
  domains_using: string[];
}

// Skill Creation types

export interface CreateSkillRequest {
  domain: string;
  name: string;
  role: "manager" | "specialist" | "field";
  lang: "python" | "typescript" | "go";
  description: string;
  model: string;
  trigger: string;
  cost_budget: string;
}

export interface CreateSkillResponse {
  domain: string;
  name: string;
  skill_path: string;
  files_created: string[];
  is_new_domain: boolean;
  message: string;
}

export interface PlatformHealth {
  gateway: ComponentHealth;
  executor: ComponentHealth;
  database: ComponentHealth;
  mcp_tools: MCPToolHealth[];
}

// Memory Explorer types

export interface MemoryStatus {
  backend: string;
  vector_store: string;
  embedder: string;
  llm_provider: string;
  total_memories: number;
  execution_memories: number;
  correction_memories: number;
  reflexion_memories: number;
  skills_tracked: string[];
}

export interface MemorySearchResult {
  results: Record<string, unknown>[];
  backend: string;
  query: string;
  skills_searched: string[];
}

export interface PromptAssemblyLayer {
  name: string;
  source: string;
  content: string;
}

export interface PromptAssembly {
  skill: string;
  domain_context: string;
  reflexion_context: string;
  skill_prompt: string;
  composed_prompt: string;
  layers: PromptAssemblyLayer[];
}
