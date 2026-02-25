# CLI Reference

> **Purpose**: CLI command reference and operational workflows. Engineers operate the platform via CLI first; the UI is a thin, functional mirror.

## Core Concepts

- Runs: an execution entry (execution_id, skill, input_summary, outcome).
- Threads: a logical session from input_summary.session_id or input_summary.thread_id.
- Memory: shared knowledge store (executions, corrections, reflexions, tests).
- Replay: re-run a past execution with the same input.

## CLI Surface (kubectl-style)

Operate everything from the CLI:

- `get skills|domains|executions|events|threads`
- `describe skill|execution`
- `logs <execution-id>`
- `memory status|search|prompt`
- `replay <execution-id>`

### CLI Flows

1) Find a failing run
- `get executions -n 20`
- `describe execution <id>`
- `logs <id>`

2) Understand shared memory
- `memory status`
- `memory search "stuck payout"`
- `memory prompt hr/interview-questions`

3) Replay and validate
- `replay <execution-id> --dry-run`
- `replay <execution-id> --model anthropic/claude-sonnet-4.5`

4) Track threads (sessions)
- `get threads`
- Use session_id in skill inputs to group long-running workflows.

## Minimal UI (Mirror the CLI)

Keep the UI small, fast, and functional. No heavy dashboards.

Screen 1: Console (single-page)
- Health: gateway + executor status
- Recent runs (last 10)
- Memory status (counts)
- Recent events (last 15)
- Quick CLI hints (copy-paste commands)

Screen 2: Run Detail
- Same fields as `describe execution`
- Corrections + reflexions linked
- Replay button (uses same payload as `replay`)

Screen 3: Memory Search
- Text input → results list
- Link out to run detail or skill

## Data Contracts

- Runs: `GET /api/v1/executions`
- Run detail: `GET /api/v1/executions/{id}`
- Memory status: `GET /api/v1/memory/status`
- Memory search: `POST /api/v1/memory/search`
- Events: `GET /api/v1/events`

## Implementation Notes

- Thread grouping is derived from input_summary.session_id or input_summary.thread_id.
- Replay uses execution.input_summary as input_data.
- UI should not introduce new concepts; it reflects CLI semantics.
