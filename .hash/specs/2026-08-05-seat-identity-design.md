---
Date: 2026-08-05
Status: Draft
Subsystem: 1 of 6 (Agent Lifecycle)
Depends on: nothing (foundation)
---

# Seat Identity — Design Spec

## 1. Problem

Agentura agents are anonymous and amnesiac.

- The `agents` table (`agent_store.py`) is persistent config synced from `agency/` SOUL.md files but carries no track record — zero run counts, success rates, or memory of past work. It is a static registry, not a living identity.
- The `fleet_agents` table (`fleet_store.py`) records each run but its `agent_id` is a fresh random UUID per run that does not reference `agents.id`. Sessions are never bound to a persistent identity.
- Consequence: no agent can accumulate a history, so per-agent reliability/track-record is structurally impossible today, and the only thing primed on wake is the static SOUL text.

## 2. Concept: Seat vs Session

| Concept | Definition |
|---|---|
| Seat | Persistent identity occupying a role; stable id, mutable name; the "person" |
| Session | One ephemeral run = existing `fleet_agents` row; the "day" |
| seat_events | Append-only ledger; every outcome/gate/rename is one immutable row; the shared substrate later subsystems reuse |

Provenance: this seat/session split is from Gastown's Polecat model (steveyegge/gastown, OSS) and Yegge's model-welfare essay (yegge.ai, Aug 2026) — seat = persistent identity + history, session = one workday.

## 3. Data Model

```sql
CREATE TABLE seats (
  id            TEXT PRIMARY KEY,          -- stable, never changes
  name          TEXT UNIQUE NOT NULL,      -- mutable (rename keeps id)
  role          TEXT NOT NULL DEFAULT '',
  domain        TEXT NOT NULL DEFAULT '',
  pronouns      TEXT NOT NULL DEFAULT 'they/them',  -- self-declared (model-welfare essay)
  current_model TEXT DEFAULT '',
  renamed_from  TEXT DEFAULT '',
  status        TEXT NOT NULL DEFAULT 'active',
  created_at    TIMESTAMPTZ DEFAULT NOW()
);

CREATE TABLE seat_events (        -- APPEND ONLY. no UPDATE/DELETE method exists.
  id         BIGSERIAL PRIMARY KEY,
  seat_id    TEXT NOT NULL REFERENCES seats(id),
  session_id TEXT,                          -- nullable (renames have no session)
  type       TEXT NOT NULL,                 -- session_completed|session_failed|gate_passed|gate_failed|renamed|escalated
  model      TEXT DEFAULT '',               -- track record can slice pre/post model upgrade
  payload    JSONB DEFAULT '{}',            -- {cost_usd, latency_ms, success, gate, outcome,...}
  created_at TIMESTAMPTZ DEFAULT NOW()
);
CREATE INDEX idx_seat_events_seat ON seat_events(seat_id, created_at);

ALTER TABLE fleet_agents ADD COLUMN seat_id TEXT REFERENCES seats(id);
```

`seats` is deliberately separate from the declarative `agents` config table. `agents` stays config synced from `agency/`; `seats` is the living identity. A seat may reference an agency agent but does not require one, so the PR-review fleet (which has no `agency/` definition) still gets seats. The `escalated` event type is reserved now; its mechanism is deferred (Subsystem 6).

**Ledger fidelity and projection.** `seat_events` records cheap completion metadata by default (Level 2: outcome, cost, latency, gate); full reasoning/detail (Level 3) is captured only for novel or reopened work, bounding ledger cost (Gastown ledger-export-triggers; addresses the unbounded memory-stream cost failure mode). Track record is a projection folded from events (event-sourcing; Temporal history+mutable-state, Letta messages+block_history), never an authoritative field. `get_track_record` aggregates events on read; add a materialized `seat_state` cache only if reads become hot (YAGNI until then).

## 4. Components

| Component | Responsibility | Depends on |
|---|---|---|
| SeatStore | Persist seats + append events + `get_track_record` SQL rollup | Postgres |
| SeatResolver | `(skill_path, role) -> seat_id`, deterministic get-or-create | SeatStore |
| WakePacket | `seat_id -> priming text`: a fixed always-present header (identity + track-record summary + top-k recent wins by recency×importance×relevance + active Engram rules); deterministic injection, not RAG recall | SeatStore + memory rules |
| Binding hook | Stamp `seat_id` on session, append `session_*` event on completion; called from `agent_executor` | SeatStore, SeatResolver |
| Track-record read | Roster/CLI/endpoint extending existing agents endpoints in `server/app.py` | SeatStore |

## 5. Data Flow

**SESSION START**: resolve seat -> build wake-packet -> inject -> run.

**SESSION END**: record outcome with `seat_id` -> append seat_event.

**READ**: `get_track_record` = SQL aggregate.

Defining behavioral guarantee: two sequential runs of the same skill resolve the same `seat_id` and the seat run count goes 1 -> 2.

## 6. Key Decisions

- DECISION 1 — Seat grain = `(skill_path, role)`; repo is a payload tag to slice by, not part of the key. Revisit if reliability needs to differ per repo.
- DECISION 2 — Record both signals: task-success now (`fleet_agents.success`), plus gate/outcome fields left in payload for Subsystems 3/4 (judge score, merge-clean, no-rollback) to fill. Raw task-success alone is a weak reliability signal.
- DECISION 3 — WakePacket is a deterministic, always-present header: identity + track-record summary + top-k recent wins (recency×importance×relevance, per Generative Agents) + active Engram rules. It does not inject raw failure percentages (self-fulfilling bias) and does not depend on RAG recall for the load-bearing part (Letta/ADK pattern). Revisit if priming proves unhelpful.
- DECISION 4 — Track record is read-only in v1. Routing work away from unreliable seats is deferred to its own spec (feedback-loop and new-seat-starvation risks).
- DECISION 5 — Scope fence below is deliberate; deferred items are cheap because each is one event type or one WakePacket line.

## 7. Error Handling

Seat identity is observability-grade additive (Zero Logic Mutation): must never change whether a run succeeds.

- SeatStore/DB down -> SeatResolver and WakePacket fail soft (log warning, run proceeds unstamped, outcome identical to today).
- `get_track_record` must aggregate in SQL (single GROUP BY over `seat_events` bounded by `seat_id` + a LIMITed recent-failures query), never SELECT * into Python. Hard guardrail from a prior production OOM where a store loaded all 20K rows into memory.
- Get-or-create race: `INSERT ... ON CONFLICT (name) DO UPDATE RETURNING id` (same pattern AgentStore already uses).
- `seat_events` append is the only write path; no UPDATE/DELETE method exists — "never falsify the record" enforced by absence.

## 8. Testing

- Identity test (same skill twice -> same `seat_id`, run count 1->2) — the core test.
- Track-record math, table-driven over `seat_events` fixtures: empty = zero record, no divide-by-zero; single; many; all-failed -> `success_rate`/`avg_cost`/`gate_pass_rate`.
- Degradation: SeatStore raises -> session still completes.
- Resolver determinism.
- Rename: name changes, id stable, `renamed` event appended.
- WakePacket assembly with/without history.

## 9. Scope Fence

**IN v1**: `seats` (+ pronouns) & `seat_events` tables, session->seat binding, SeatResolver get-or-create, `get_track_record` SQL rollup, WakePacket (identity + recent wins + Engram rules), read endpoint/roster, `escalated` event type reserved.

**OUT** (later specs, no rework — each is an event type or WakePacket line): Session Handoff/closure (Sub 2), blameless->Engram (Sub 3), Portcullis merge queue (Sub 4), laurels (Sub 5), escalate mechanism (Sub 6), mailbox/addressable messaging, model-upgrade slicing UI, play/vacation.

## 10. Success Criteria

1. Two runs of a skill share a `seat_id` and the seat run count increments.
2. Track record is a bounded SQL aggregate, not load-all.
3. WakePacket is injected and visible in a run's context.
4. Run success/failure is byte-identical to today when SeatStore is disabled.

## 11. Roadmap: two tracks

Gastown's value splits across two axes. Track A is agent lifecycle (welfare-derived); Track B is work-and-operations throughput. Seat identity (this spec) is the foundation both tracks attribute to.

### Track A — Agent Lifecycle (6 subsystems)

| Subsystem | Name | Essay principle |
|---|---|---|
| 1 | Seat Identity (this spec) | Persistent identity vs ephemeral session; wake-with-purpose (folded into WakePacket) |
| 2 | Session Handoff/closure | Handoff not `/exit`; closure; bounded workdays; distinct from Harness v2 HandoffArtifact (stage-level) |
| 3 | Blameless learning | Structural blamelessness (red landing -> postmortem, amend constitution) |
| 4 | Portcullis/Refinery merge queue | Design out drudgery (polling/idle -> gates) |
| 5 | Laurels/recognition | Recognition, non-gameable, injected on wake |
| 6 | Escalation | Right to refuse + escalate |

All bolt onto `seat_events` + WakePacket built here.

### Track B — Operational Autonomy

| Item | Gastown source | Status in Agentura |
|---|---|---|
| OA-1 Stall-detection watchdog | Witness/Deacon/Dogs | Absent — autonomous runs can hang with no recovery |
| OA-2 Pipeline checkpoint recovery | Molecules ("poured wisps") | Absent — pipelines re-run from scratch on failure |
| Work ledger | Beads | Present as `tickets` (attributable, hierarchical via `parent_id`, claimable via `checked_out_by`, `trace_log` audit) — no git substrate needed on a central Postgres |
| Durable work bundles | Convoys | Partial — `tickets.parent_id` gives hierarchy |

Beads is not ported: the `tickets` table already provides its properties; its git/Dolt substrate solves Gastown's local-first federation (Wasteland), a problem a central-Postgres platform does not have. Seat identity activates `tickets`' attribution FKs, which are nominal today because runtime work is unbound.

## 12. Prior art & guardrails

Researched across Gastown internals, commercial/OSS agent platforms, and the agent-memory literature (full notes in scratchpad). Two framing findings:

- This is white space: market "durable agent" features are scoped to a thread or a user, not to a persistent agent with an eval-derived track record. Only Letta (agent-as-entity) is a true analog.
- Call it a track record, not learning: no shipping product has a closed eval->behavior loop; "self-improves" claims (Devin, Factory) are unverified and vendor memory benchmarks (Zep LoCoMo, Mem0) are disputed. Claim only what the ledger proves.

Borrowed patterns:

| Source | Borrowed |
|---|---|
| Event sourcing + actor model (Fowler; Hewitt) | Immutable log; track record = projection; idempotent consumers; corrections are compensating events, never mutations |
| CoALA (arXiv:2309.02427) | Tag events episodic/semantic/procedural; wake pulls a per-type mix |
| Generative Agents (arXiv:2304.03442) | Wake-priming ranks by recency×importance×relevance, top-k only |
| Reflexion (arXiv:2303.11366) | Blameless learning = a written lesson from a verified failure, not raw outcome |
| Temporal / Trigger.dev | Stable seat id != rotating run id; reject-on-reuse |
| Zep | Bi-temporal validity (valid_from/valid_until) if we later store current-facts — window-close, never delete |
| Gastown ledger-export-triggers | Fidelity levels 0-3; full detail only on novel/reopened work |
| Factory OTEL / OpenAI Agents SDK | Ready-made session-event schema (tool calls, files/lines, commits/PRs) for payloads |

Failure modes -> guardrails (design against now):

| Failure mode | Guardrail |
|---|---|
| Memory poisoning | Gate every write through provenance + verifier verdict; unverified events are low-trust, down-weighted |
| Reflection drift / rumination | Ground lessons in an external signal; cap reflection depth; dedup before commit |
| Recognition gaming (Goodhart) | Score on independent, outcome-grounded verifiers the seat cannot author; reward verified difficulty, not volume |
| Judge bias (arXiv:2306.05685) | Randomize position, length-normalize, use reference answers; a model never judges its own seat |
| Unbounded ledger/wake cost | Fidelity levels + top-k wake; consolidate cold events; keep raw log out of the hot path |

Most guardrails land in later subsystems (Reflexion -> Sub 3, judge -> existing JudgeRunner). The ledger-write guardrails (poisoning, gaming) and wake top-k constrain this spec directly.

## 13. Mapping to Harness v2 (complementary)

Seat identity is the identity substrate that Harness v2 (`docs/HARNESS_V2.md`) specifies around but never names. The two are complementary: Harness v2 owns execution (deterministic gates, evaluator independence, memory content, tool governance); this spec owns identity (who ran it, their history, what they wake with). Harness v2's roadmap (Phases 0-4) has an identity-shaped hole; seat identity fills it and is a Phase 0/1 substrate, not a Phase 3 add-on.

| Harness v2 mechanism | Seat-identity relationship |
|---|---|
| 4-Layer Memory (episodic/declarative/procedural/reflexion) | Substrate. `seat_events` stores it (episodic = `session_completed` payload; reflexion = Engram owned by a seat); WakePacket retrieves it on wake. v2 names the taxonomy, not the owner or delivery. |
| Evaluator Agent (creator != verifier) | Seat/session lineage makes v2's provenance gate computable. Proof Claim 2: three tasks shared one `session_id`/`checkpoint_dir`, so the reviewer held its own authorship. Mechanizes §12 "a model never judges its own seat." |
| Eval-label capture (Proof Claim 7) | Direct. Discarded 1-5 ratings become `seat_events` outcome signals (DECISION 2). v2's `{task_id, rating, skill, model}` pipe is a subset of the `seat_events` write path. |
| DeterministicNode (exists) | Gate pass/fail = `gate_*` seat_event — the trustworthy write behind the poisoning guardrail. Proof Claim 3 (review ran zero deterministic checks, then self-approved) is the failure this closes. |
| HandoffArtifact (stage->stage) | Distinct from Session Handoff (session->session, Sub 2); both fight state re-discovery (Proof Claim 5). Complementary axes, not duplicates. |
| Tool governance / sandbox boundary (Proof Claims 3, 6) | Seat = the principal a per-execution credential/ServiceAccount scopes (review seat -> comment-only token). The sandbox substrate enforces; the seat is what it enforces against. |

Build-order consequence: eval-label capture (Proof Claim 7) is the cheapest real outcome signal and is being actively discarded in production today — it is the highest-priority `seat_events` writer to land alongside the foundation.
