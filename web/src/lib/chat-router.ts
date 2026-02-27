import type { ChatMessage, ConversationScope } from "./chat-types";
import type { PipelineResult } from "./api";
import {
  listSkills,
  listExecutions,
  listDomains,
  listReflexions,
  listEvents,
  getSkillDetail,
  executeSkill,
  correctSkill,
  approveExecution,
  getPlatformHealth,
  getMemoryStatus,
  memorySearch,
  executePipeline,
  executePipelineStream,
} from "./api";

function generateId(): string {
  return `${Date.now()}-${Math.random().toString(36).slice(2, 9)}`;
}

const HELP_TEXT = `Available commands:
  <natural language>      Ask anything — auto-routes to the right skill
  get skills              List all deployed agents
  get executions          List recent executions
  get domains             List domains
  get reflexions          List reflexions
  get events              List recent events
  get approvals           List pending approvals
  describe skill <d/s>    Show agent details
  status                  Platform health check
  memory status           Memory store status
  memory search <query>   Search memory
  run <domain/skill>      Execute an agent
  correct <exec-id> "text"  Submit a correction
  approve <exec-id>       Approve a pending execution
  reject <exec-id>        Reject a pending execution
  help                    Show this help

Examples:
  "interview questions for a product manager"
  "review my pull request"
  "analyze expenses for January"
  "how many sick days do I get"`;

const KNOWN_VERBS = new Set([
  "help", "get", "list", "describe", "status", "memory",
  "run", "exec", "correct", "approve", "reject", "ask",
]);

/**
 * Unwrap LLM output that may be wrapped as {raw_output: "```json\n{...}\n```"}.
 * Strips markdown code fences and parses the inner JSON.
 */
function unwrapOutput(output: Record<string, unknown>): Record<string, unknown> {
  if (typeof output.raw_output === "string" && Object.keys(output).length === 1) {
    const raw = output.raw_output;
    // Strip ```json ... ``` code fences
    const fenceMatch = raw.match(/```(?:json)?\s*\n?([\s\S]*?)```/);
    const jsonStr = fenceMatch ? fenceMatch[1].trim() : raw.trim();
    try {
      const parsed = JSON.parse(jsonStr);
      if (typeof parsed === "object" && parsed !== null) return parsed;
    } catch {
      // Fall through to return original
    }
  }
  return output;
}

export interface RouteOptions {
  scope?: ConversationScope;
  messages?: ChatMessage[];
  onUpdate?: (content: string) => void;
}

export async function routeCommand(input: string, opts?: RouteOptions | ConversationScope): Promise<ChatMessage> {
  // Backwards compat: accept bare scope or options object
  const options: RouteOptions = opts && "type" in opts ? { scope: opts } : (opts ?? {});
  const { scope, messages, onUpdate } = options;

  const cmd = input.trim().replace(/^agentura\s+/, "");
  const parts = cmd.split(/\s+/);
  const verb = parts[0];
  const noun = parts[1];

  const base: Omit<ChatMessage, "content" | "metadata"> = {
    id: generateId(),
    role: "assistant",
    timestamp: Date.now(),
  };

  try {
    if (verb === "help" || !verb) {
      return { ...base, content: HELP_TEXT };
    }

    if (verb === "get" || verb === "list") {
      return await handleGet(base, noun?.replace(/^--/, ""), parts.slice(2));
    }

    if (verb === "describe") {
      return await handleDescribe(base, noun, parts.slice(2));
    }

    if (verb === "status") {
      return await handleStatus(base);
    }

    if (verb === "memory") {
      return await handleMemory(base, noun, parts.slice(2));
    }

    if (verb === "run" || verb === "exec") {
      return await handleRun(base, parts.slice(1));
    }

    if (verb === "correct") {
      return await handleCorrect(base, cmd);
    }

    if (verb === "approve" || verb === "reject") {
      return await handleApprove(base, parts[1], verb === "approve");
    }

    if (verb === "ask") {
      return await handleAsk(base, parts.slice(1).join(" "));
    }

    // Natural language fallback — scoped or classifier routing
    if (!KNOWN_VERBS.has(verb)) {
      if (scope?.type === "domain") return await handleScopedDomain(base, cmd, scope, onUpdate);
      if (scope?.type === "pipeline") {
        // Follow-up detection: if previous messages have a pipeline result, answer from context
        const lastAssistant = messages?.filter((m) => m.role === "assistant").pop();
        if (lastAssistant?.metadata?.pipelineResult) {
          return handlePipelineFollowUp(base, cmd, scope, lastAssistant.metadata.pipelineResult);
        }
        return await handleScopedPipeline(base, cmd, scope, onUpdate);
      }
      return await handleAsk(base, cmd);
    }

    return {
      ...base,
      content: `Unknown command: ${verb}. Type "help" for available commands.`,
      metadata: { error: `Unknown command: ${verb}` },
    };
  } catch (err) {
    const message = err instanceof Error ? err.message : String(err);
    return { ...base, content: `Error: ${message}`, metadata: { error: message } };
  }
}

async function handleGet(
  base: Omit<ChatMessage, "content" | "metadata">,
  resource: string,
  _args: string[],
): Promise<ChatMessage> {
  if (resource === "skills" || resource === "agents") {
    const data = await listSkills();
    if (!data.length) return { ...base, content: "No agents deployed." };
    return {
      ...base,
      content: `Found ${data.length} agents`,
      metadata: {
        command: "get skills",
        tableData: {
          headers: ["Domain", "Agent", "Role", "Model", "Health"],
          rows: data.map((s) => [
            s.domain,
            s.name,
            s.role,
            (s.model || "").split("/").pop() || "",
            s.health || "unknown",
          ]),
        },
      },
    };
  }

  if (resource === "executions") {
    const data = await listExecutions();
    const entries = data.slice(0, 15);
    if (!entries.length) return { ...base, content: "No executions recorded." };
    return {
      ...base,
      content: `Showing ${entries.length} recent executions`,
      metadata: {
        command: "get executions",
        tableData: {
          headers: ["ID", "Skill", "Outcome", "Cost", "Latency"],
          rows: entries.map((e) => [
            String(e.execution_id).slice(0, 20),
            e.skill,
            e.outcome,
            `$${(e.cost_usd ?? 0).toFixed(3)}`,
            `${((e.latency_ms ?? 0) / 1000).toFixed(1)}s`,
          ]),
        },
      },
    };
  }

  if (resource === "domains") {
    const data = await listDomains();
    if (!data.length) return { ...base, content: "No domains." };
    return {
      ...base,
      content: `Found ${data.length} domains`,
      metadata: {
        command: "get domains",
        tableData: {
          headers: ["Domain", "Skills", "Execs", "Accept%", "Owner"],
          rows: data.map((d) => [
            d.name,
            String(d.skills_count),
            String(d.total_executions),
            `${Math.round((d.accept_rate || 0) * 100)}%`,
            d.owner || "",
          ]),
        },
      },
    };
  }

  if (resource === "reflexions") {
    const data = await listReflexions();
    if (!data.length) return { ...base, content: "No reflexions." };
    return {
      ...base,
      content: data
        .slice(0, 10)
        .map((r) => `${r.reflexion_id?.slice(0, 16)}  ${r.skill}  ${r.rule}`)
        .join("\n"),
    };
  }

  if (resource === "events") {
    const data = await listEvents({ limit: 10 });
    if (!data.length) return { ...base, content: "No events." };
    return {
      ...base,
      content: data
        .map(
          (e) =>
            `${e.timestamp?.slice(11, 19) || ""}  ${e.event_type}  ${e.domain}/${e.skill}  ${e.message || ""}`,
        )
        .join("\n"),
    };
  }

  if (resource === "approvals") {
    const data = await listExecutions();
    const pending = data.filter((e) => e.outcome === "pending_approval");
    if (!pending.length) return { ...base, content: "No pending approvals." };
    return {
      ...base,
      content: `${pending.length} pending approvals`,
      metadata: {
        command: "get approvals",
        tableData: {
          headers: ["ID", "Skill", "Cost"],
          rows: pending.map((e) => [
            String(e.execution_id).slice(0, 20),
            e.skill,
            `$${(e.cost_usd ?? 0).toFixed(3)}`,
          ]),
        },
      },
    };
  }

  return {
    ...base,
    content: `Unknown resource: ${resource}. Try: skills, executions, domains, reflexions, events, approvals`,
  };
}

async function handleDescribe(
  base: Omit<ChatMessage, "content" | "metadata">,
  noun: string,
  args: string[],
): Promise<ChatMessage> {
  if (noun === "skill" && args[0]) {
    const [domain, skill] = args[0].includes("/") ? args[0].split("/") : ["", args[0]];
    if (!domain || !skill) return { ...base, content: "Usage: describe skill <domain/skill>" };
    const data = await getSkillDetail(domain, skill);
    return { ...base, content: JSON.stringify(data, null, 2), metadata: { command: `describe skill ${args[0]}` } };
  }
  return { ...base, content: "Usage: describe skill <domain/skill>" };
}

async function handleStatus(
  base: Omit<ChatMessage, "content" | "metadata">,
): Promise<ChatMessage> {
  const data = await getPlatformHealth();
  return {
    ...base,
    content: [
      `Gateway:   ${data.gateway?.status || "unknown"} (${data.gateway?.version || ""})`,
      `Executor:  ${data.executor?.status || "unknown"} (${data.executor?.version || ""})`,
      `Database:  ${data.database?.status || "unknown"} (${data.database?.version || ""})`,
    ].join("\n"),
    metadata: { command: "status" },
  };
}

async function handleMemory(
  base: Omit<ChatMessage, "content" | "metadata">,
  noun: string,
  args: string[],
): Promise<ChatMessage> {
  if (noun === "status") {
    const data = await getMemoryStatus();
    return {
      ...base,
      content: [
        `Backend:     ${data.backend}`,
        `Vector:      ${data.vector_store}`,
        `Embedder:    ${data.embedder}`,
        `LLM:         ${data.llm_provider}`,
        `Memories:    ${data.total_memories}`,
        `  Exec:      ${data.execution_memories}`,
        `  Correct:   ${data.correction_memories}`,
        `  Reflexion:  ${data.reflexion_memories}`,
      ].join("\n"),
      metadata: { command: "memory status" },
    };
  }
  if (noun === "search" && args.length > 0) {
    const query = args.join(" ");
    const data = await memorySearch(query, 5);
    if (!data.results?.length) return { ...base, content: `No results for "${query}"` };
    return {
      ...base,
      content: data.results
        .map((r, i) => `[${i + 1}] ${JSON.stringify(r).slice(0, 200)}`)
        .join("\n\n"),
      metadata: { command: `memory search ${query}` },
    };
  }
  return { ...base, content: "Usage: memory status | memory search <query>" };
}

async function handleRun(
  base: Omit<ChatMessage, "content" | "metadata">,
  args: string[],
): Promise<ChatMessage> {
  let skillPath = args[0];

  const agentIdx = args.indexOf("--agent");
  if (agentIdx >= 0 && args[agentIdx + 1]) {
    skillPath = args[agentIdx + 1];
  }

  if (!skillPath) return { ...base, content: "Usage: run <domain/skill>" };
  const [domain, skill] = skillPath.includes("/") ? skillPath.split("/") : ["", skillPath];
  if (!domain || !skill) return { ...base, content: "Usage: run <domain/skill>" };

  const inputIdx = args.indexOf("--input");
  let inputData: Record<string, unknown> = {};
  if (inputIdx >= 0 && args[inputIdx + 1]) {
    try {
      inputData = JSON.parse(args.slice(inputIdx + 1).join(" ").replace(/^'|'$/g, ""));
    } catch {
      inputData = { query: args.slice(inputIdx + 1).join(" ").replace(/^'|'$/g, "") };
    }
  }

  const result = await executeSkill(domain, skill, { input_data: inputData, dry_run: false });
  return {
    ...base,
    content: result.success
      ? `Skill ${domain}/${skill} executed successfully`
      : `Skill ${domain}/${skill} execution failed`,
    metadata: { command: `run ${skillPath}`, skillResult: result },
  };
}

async function handleCorrect(
  base: Omit<ChatMessage, "content" | "metadata">,
  cmd: string,
): Promise<ChatMessage> {
  const match = cmd.match(/^correct\s+(\S+)\s+(?:"([^"]+)"|(.+))$/);
  if (!match) return { ...base, content: 'Usage: correct <execution-id> "your correction text"' };

  const execId = match[1];
  const correctionText = match[2] || match[3];

  const executions = await listExecutions();
  const exec = executions.find((e) => String(e.execution_id).startsWith(execId));
  if (!exec) return { ...base, content: `Execution not found: ${execId}` };

  const skill = exec.skill;
  const [domain, ...rest] = skill.split("/");
  const skillName = rest.join("/");
  if (!domain || !skillName) return { ...base, content: `Invalid skill path: ${skill}` };

  const result = await correctSkill(domain, skillName, {
    execution_id: String(exec.execution_id),
    correction: correctionText,
  });

  return {
    ...base,
    content: [
      `Correction submitted for ${skill}`,
      `  Correction ID:  ${result.correction_id}`,
      `  Reflexion ID:   ${result.reflexion_id}`,
      result.deepeval_test ? `  DeepEval test:  ${result.deepeval_test}` : null,
      result.promptfoo_test ? `  Promptfoo test: ${result.promptfoo_test}` : null,
      "",
      "Run the same skill again to see the correction applied.",
    ]
      .filter(Boolean)
      .join("\n"),
    metadata: { command: `correct ${execId}`, correctionResult: result },
  };
}

async function handleAsk(
  base: Omit<ChatMessage, "content" | "metadata">,
  query: string,
): Promise<ChatMessage> {
  if (!query.trim()) {
    return { ...base, content: 'Usage: ask "your question"\nOr just type naturally: "interview questions for a PM"' };
  }

  // Step 1: Route through classifier
  const routing = await executeSkill("platform", "classifier", {
    input_data: { query },
    dry_run: false,
  });

  const output = unwrapOutput(routing.output || {});
  const domain = output.domain as string | undefined;
  const confidence = Number(output.confidence ?? 0);
  const reasoning = (output.reasoning as string) || "";
  const entities = (output.extracted_entities || {}) as Record<string, unknown>;

  if (!domain || domain === "unknown" || confidence < 0.5) {
    return {
      ...base,
      content: [
        `I couldn't confidently route your query.`,
        reasoning ? `Reasoning: ${reasoning}` : "",
        ``,
        `Try being more specific, or use: run <domain/skill>`,
      ].filter(Boolean).join("\n"),
      metadata: { command: "ask" },
    };
  }

  // Step 2: Route through domain triage
  const triage = await executeSkill(domain, "triage", {
    input_data: { query, ...entities },
    dry_run: false,
  });

  const triageOutput = unwrapOutput(triage.output || {});
  const routeTo = (triageOutput.route_to as string) || "";
  const triageReasoning = (triageOutput.reasoning as string) || "";

  if (!routeTo) {
    return {
      ...base,
      content: [
        `Routed to **${domain}** domain, but triage couldn't pick a specific skill.`,
        triageReasoning ? `Reasoning: ${triageReasoning}` : "",
        ``,
        `Available skills in ${domain}: use \`get skills\` to see options.`,
      ].filter(Boolean).join("\n"),
      metadata: { command: "ask" },
    };
  }

  // Step 3a: Pipeline routing (e.g. "pipeline:build-deploy")
  if (routeTo.startsWith("pipeline:")) {
    const pipelineName = routeTo.split(":")[1];
    const triageEntities = (triageOutput.entities || {}) as Record<string, unknown>;
    const description = (triageEntities.description as string) || query;
    const appName = (triageEntities.app_name as string) || "my-app";
    const pipelineResult = await executePipeline(pipelineName, {
      description,
      app_name: appName,
      port: 9000,
      ...triageEntities,
    });
    return {
      ...base,
      content: pipelineResult.success
        ? [
            `Pipeline **${pipelineName}** completed successfully.`,
            `Steps: ${pipelineResult.steps_completed}/${pipelineResult.total_steps ?? "?"}`,
            `Cost: $${pipelineResult.total_cost_usd.toFixed(3)}`,
            `Latency: ${(pipelineResult.total_latency_ms / 1000).toFixed(1)}s`,
            pipelineResult.url ? `URL: ${pipelineResult.url}` : "",
          ].filter(Boolean).join("\n")
        : `Pipeline **${pipelineName}** failed at step ${pipelineResult.steps_completed}.`,
      metadata: {
        command: `ask → pipeline:${pipelineName}`,
        pipelineResult,
        routing: {
          classifier: { domain, confidence, reasoning },
          triage: { route_to: routeTo, reasoning: triageReasoning },
        },
      },
    };
  }

  // Step 3b: Execute the target skill
  const [targetDomain, targetSkill] = routeTo.includes("/")
    ? routeTo.split("/")
    : [domain, routeTo];

  const result = await executeSkill(targetDomain, targetSkill, {
    input_data: { ...entities, query },
    dry_run: false,
  });

  return {
    ...base,
    content: result.success
      ? `Ran **${targetDomain}/${targetSkill}** successfully.`
      : `**${targetDomain}/${targetSkill}** execution failed.`,
    metadata: {
      command: `ask → ${targetDomain}/${targetSkill}`,
      skillResult: result,
      routing: {
        classifier: { domain, confidence, reasoning },
        triage: { route_to: routeTo, reasoning: triageReasoning },
      },
    },
  };
}

async function handleScopedDomain(
  base: Omit<ChatMessage, "content" | "metadata">,
  query: string,
  scope: ConversationScope,
  onUpdate?: (content: string) => void,
): Promise<ChatMessage> {
  const domain = scope.id;

  // Step 1: Route through domain triage (skip classifier — we know the domain)
  const triage = await executeSkill(domain, "triage", {
    input_data: { query },
    dry_run: false,
  });

  const triageOutput = unwrapOutput(triage.output || {});
  const routeTo = (triageOutput.route_to as string) || "";
  const triageReasoning = (triageOutput.reasoning as string) || "";
  const entities = (triageOutput.entities || {}) as Record<string, unknown>;

  if (!routeTo) {
    // Fetch domain skills to show what's available
    const allSkills = await listSkills();
    const domainSkills = allSkills
      .filter((s) => s.domain === domain && s.role !== "manager")
      .map((s) => `- **${s.display_title || s.name}**: ${s.display_subtitle || s.description || s.role}`);

    return {
      ...base,
      content: [
        `I'm the **${domain}** domain assistant. Here's what I can help with:`,
        ``,
        ...domainSkills,
        ``,
        `Just describe what you need and I'll route to the right specialist.`,
      ].join("\n"),
      metadata: { command: `scoped → ${domain}/triage` },
    };
  }

  // Step 2a: Pipeline routing — use streaming via handleScopedPipeline
  if (routeTo.startsWith("pipeline:")) {
    const pipelineName = routeTo.split(":")[1];
    const pipelineScope: ConversationScope = {
      type: "pipeline",
      id: pipelineName,
      displayTitle: pipelineName.replace(/-/g, " ").replace(/\b\w/g, (c) => c.toUpperCase()),
      displayAvatar: pipelineName.slice(0, 2).toUpperCase(),
      displayColor: "#8b5cf6",
    };
    return handleScopedPipeline(base, query, pipelineScope, onUpdate);
  }

  // Step 2b: Execute the target skill
  const [targetDomain, targetSkill] = routeTo.includes("/")
    ? routeTo.split("/")
    : [domain, routeTo];

  const result = await executeSkill(targetDomain, targetSkill, {
    input_data: { ...entities, query },
    dry_run: false,
  });

  return {
    ...base,
    content: result.success
      ? `Ran **${targetDomain}/${targetSkill}** successfully.`
      : `**${targetDomain}/${targetSkill}** execution failed.`,
    metadata: {
      command: `scoped → ${domain} → ${targetDomain}/${targetSkill}`,
      skillResult: result,
      routing: {
        classifier: { domain, confidence: 1, reasoning: "domain-scoped" },
        triage: { route_to: routeTo, reasoning: triageReasoning },
      },
    },
  };
}

async function handleScopedPipeline(
  base: Omit<ChatMessage, "content" | "metadata">,
  query: string,
  scope: ConversationScope,
  onUpdate?: (content: string) => void,
): Promise<ChatMessage> {
  let content = `Running pipeline **${scope.id}**...\n`;
  onUpdate?.(content);

  // Collect result data for metadata
  const resultData: Partial<PipelineResult> = {
    pipeline: scope.id,
    success: false,
    steps_completed: 0,
    total_latency_ms: 0,
    total_cost_usd: 0,
    url: null,
  };

  try {
    for await (const event of executePipelineStream(scope.id, { description: query })) {
      if (event.type === "step_started") {
        const skillName = (event.data.skill as string).split("/").pop() || event.data.skill;
        content += `\n**Step ${event.data.step}**: ${skillName} — running...`;
        onUpdate?.(content);
      } else if (event.type === "iteration") {
        const toolName = (event.data.tool_name as string) || (event.data.action as string) || "thinking";
        const toolInput = event.data.tool_input as Record<string, unknown> | undefined;
        let detail = "";
        if (toolName === "write_file" && toolInput?.path) {
          detail = ` → \`${toolInput.path}\``;
        } else if (toolName === "read_file" && toolInput?.path) {
          detail = ` → \`${toolInput.path}\``;
        } else if (toolName === "run_command" && toolInput?.command) {
          const cmd = String(toolInput.command).slice(0, 60);
          detail = ` → \`${cmd}${String(toolInput.command).length > 60 ? "..." : ""}\``;
        } else if (toolName === "run_code") {
          detail = " → executing in sandbox";
        }
        content += `\n  ↳ ${toolName}${detail}`;
        onUpdate?.(content);
      } else if (event.type === "step_completed") {
        const latencySec = ((event.data.latency_ms as number) / 1000).toFixed(1);
        const costUsd = (event.data.cost_usd as number) ?? 0;
        if (event.data.success) {
          content += ` ✓ (${latencySec}s, $${costUsd.toFixed(3)})`;
        } else {
          content += ` ✗ ${event.data.error || "failed"} (${latencySec}s)`;
        }
        onUpdate?.(content);
      } else if (event.type === "pipeline_done") {
        resultData.success = event.data.success as boolean;
        resultData.steps_completed = event.data.steps_completed as number;
        resultData.total_steps = event.data.total_steps as number;
        resultData.total_latency_ms = event.data.total_latency_ms as number;
        resultData.total_cost_usd = event.data.total_cost_usd as number;
        resultData.url = (event.data.url as string) || null;

        content += "\n\n---\n";
        const cost = (event.data.total_cost_usd as number) ?? 0;
        const latency = (event.data.total_latency_ms as number) ?? 0;
        if (event.data.success) {
          content += `**Pipeline complete** — ${event.data.steps_completed} steps in ${(latency / 1000).toFixed(0)}s ($${cost.toFixed(3)})`;
          if (event.data.url) content += `\n\n**Your app is live at:** ${event.data.url}`;
          content += `\n\nDeployed to K8s namespace \`agentura\`. Check status with \`kubectl get pods -n agentura\`.`;
        } else {
          content += `**Pipeline failed** at step ${event.data.steps_completed} of ${event.data.total_steps} (${(latency / 1000).toFixed(0)}s, $${cost.toFixed(3)})`;
        }
        onUpdate?.(content);
      }
    }
  } catch (err) {
    // SSE stream failed — fall back to sync execution
    const message = err instanceof Error ? err.message : String(err);
    content += `\n\nStreaming failed (${message}), running synchronously...`;
    onUpdate?.(content);

    const pipelineResult = await executePipeline(scope.id, { description: query });
    resultData.success = pipelineResult.success;
    resultData.steps_completed = pipelineResult.steps_completed;
    resultData.total_steps = pipelineResult.total_steps;
    resultData.total_latency_ms = pipelineResult.total_latency_ms;
    resultData.total_cost_usd = pipelineResult.total_cost_usd;
    resultData.url = pipelineResult.url;

    content += pipelineResult.success
      ? `\n\n**Completed** — ${pipelineResult.steps_completed} steps | $${pipelineResult.total_cost_usd.toFixed(3)}`
      : `\n\n**Failed** at step ${pipelineResult.steps_completed}.`;
    if (pipelineResult.url) content += `\nURL: ${pipelineResult.url}`;
    onUpdate?.(content);
  }

  return {
    ...base,
    content,
    metadata: {
      command: `scoped → pipeline:${scope.id}`,
      pipelineResult: resultData as PipelineResult,
    },
  };
}

function handlePipelineFollowUp(
  base: Omit<ChatMessage, "content" | "metadata">,
  query: string,
  scope: ConversationScope,
  result: PipelineResult,
): ChatMessage {
  const q = query.toLowerCase();

  // Location / URL questions
  if (q.includes("where") || q.includes("url") || q.includes("service") || q.includes("access")) {
    const lines: string[] = [];
    if (result.url) {
      lines.push(`Your app was deployed and is accessible at: **${result.url}**`);
    } else {
      lines.push("The pipeline completed but no external URL was produced.");
    }
    lines.push(`\nK8s namespace: **agentura** | Pipeline: **${result.pipeline || scope.id}**`);
    lines.push(`\nTo check status: \`kubectl get pods -n agentura\``);
    return { ...base, content: lines.join("\n"), metadata: { command: `follow-up → ${scope.id}` } };
  }

  // What was built / summary
  if (q.includes("what") || q.includes("summary") || q.includes("steps") || q.includes("built")) {
    const stepsSummary = result.steps
      ?.map((s) => `${s.step}. **${s.skill}** — ${s.success ? "✓" : "✗"} (${(s.latency_ms / 1000).toFixed(1)}s, $${s.cost_usd.toFixed(3)})`)
      .join("\n") || `${result.steps_completed} steps completed`;

    return {
      ...base,
      content: [
        `Pipeline **${result.pipeline || scope.id}** ran ${result.steps_completed} steps:`,
        "",
        stepsSummary,
        "",
        `Total: $${result.total_cost_usd.toFixed(3)} | ${(result.total_latency_ms / 1000).toFixed(1)}s`,
        result.url ? `URL: ${result.url}` : "",
      ].filter(Boolean).join("\n"),
      metadata: { command: `follow-up → ${scope.id}` },
    };
  }

  // Generic follow-up
  return {
    ...base,
    content: [
      `I ran the **${result.pipeline || scope.id}** pipeline earlier.`,
      result.success ? "It completed successfully." : `It failed at step ${result.steps_completed}.`,
      result.url ? `The deployed service is at: **${result.url}**` : "",
      "",
      "For a new build, start a new chat and pick the pipeline again.",
    ].filter(Boolean).join("\n"),
    metadata: { command: `follow-up → ${scope.id}` },
  };
}

async function handleApprove(
  base: Omit<ChatMessage, "content" | "metadata">,
  execId: string | undefined,
  approved: boolean,
): Promise<ChatMessage> {
  if (!execId)
    return { ...base, content: `Usage: ${approved ? "approve" : "reject"} <execution-id>` };

  const executions = await listExecutions();
  const exec = executions.find((e) => String(e.execution_id).startsWith(execId));
  if (!exec) return { ...base, content: `Execution not found: ${execId}` };

  const result = await approveExecution(String(exec.execution_id), approved);
  return {
    ...base,
    content: `Execution ${result.execution_id} → ${result.outcome}`,
    metadata: {
      command: `${approved ? "approve" : "reject"} ${execId}`,
      approvalResult: result,
    },
  };
}
