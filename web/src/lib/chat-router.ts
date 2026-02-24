import type { ChatMessage } from "./chat-types";
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
} from "./api";

function generateId(): string {
  return `${Date.now()}-${Math.random().toString(36).slice(2, 9)}`;
}

const HELP_TEXT = `Available commands:
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
  help                    Show this help`;

export async function routeCommand(input: string): Promise<ChatMessage> {
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
