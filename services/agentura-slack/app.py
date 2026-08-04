"""Agentura Slack Bot — 2-way integration via Slack Bolt SDK.

Features:
- @CortexMesh run <domain/skill> — execute a skill via @mention
- @CortexMesh status — platform health check
- /agentura run <domain/skill> — execute via slash command (if configured)
- Interactive approval buttons on pending executions
"""

from __future__ import annotations

import json
import os
import re

import httpx
from slack_bolt import App
from slack_bolt.adapter.socket_mode import SocketModeHandler

EXECUTOR_URL = os.environ.get("AGENTURA_EXECUTOR_URL", "http://localhost:3001")

app = App(
    token=os.environ.get("SLACK_BOT_TOKEN"),
    signing_secret=os.environ.get("SLACK_SIGNING_SECRET", "placeholder"),
)

http = httpx.Client(timeout=120.0)
BOT_USER_ID = None


def _api_get(path: str) -> dict:
    resp = http.get(f"{EXECUTOR_URL}{path}")
    resp.raise_for_status()
    return resp.json()


def _api_post(path: str, data: dict | None = None) -> dict:
    resp = http.post(f"{EXECUTOR_URL}{path}", json=data or {})
    resp.raise_for_status()
    return resp.json()


def _parse_command(text: str) -> tuple[str, str]:
    """Parse a command string into (subcommand, args)."""
    text = text.strip()
    # Strip bot mention if present
    text = re.sub(r"<@[A-Z0-9]+>\s*", "", text).strip()
    # Strip "agentura" prefix if typed manually
    if text.lower().startswith("agentura "):
        text = text[9:].strip()
    parts = text.split(maxsplit=1)
    subcommand = parts[0].lower() if parts else "help"
    args = parts[1] if len(parts) > 1 else ""
    return subcommand, args


KNOWN_COMMANDS = {"run", "exec", "execute", "approve", "reject", "status", "approvals", "pending", "skills", "list", "help"}


def _dispatch(say, subcommand: str, args: str, full_text: str = "", user_id: str = ""):
    """Route a parsed command to the right handler."""
    if subcommand in ("run", "exec", "execute"):
        _handle_run(say, args)
    elif subcommand == "approve":
        _handle_approve(say, args, approved=True)
    elif subcommand == "reject":
        _handle_approve(say, args, approved=False)
    elif subcommand == "status":
        _handle_status(say)
    elif subcommand in ("approvals", "pending"):
        _handle_list_approvals(say)
    elif subcommand in ("skills", "list"):
        _handle_list_skills(say)
    elif subcommand == "help":
        _handle_help(say)
    else:
        # Treat unrecognised input as a free-form question → code-review-bot
        question = full_text.strip() or f"{subcommand} {args}".strip()
        _handle_question(say, question, user_id=user_id)


# ─── @mention handler (works without slash command setup) ──────────

@app.middleware
def log_request(body, next):
    """Log every incoming Slack payload for debugging."""
    ptype = body.get("type", "?")
    event = body.get("event", {}) or {}
    etype = event.get("type", "")
    print(f"[debug:incoming] type={ptype} event={etype} subtype={event.get('subtype','')} channel_type={event.get('channel_type','')} text={str(event.get('text',''))[:50]}", flush=True)
    return next()


def _threaded_say(say, thread_ts: str | None):
    """Wrap say() so all replies go into the same thread."""
    if not thread_ts:
        return say
    def _say(*args, **kwargs):
        kwargs.setdefault("thread_ts", thread_ts)
        return say(*args, **kwargs)
    return _say


def _fetch_thread_context(client, channel: str, thread_ts: str, current_ts: str) -> str:
    """Return recent thread messages (excluding the triggering one) as context.

    Includes the bot's own prior replies so multi-turn conversations retain
    continuity — without them, follow-up questions like "who wrote it?" can't
    resolve references from earlier bot answers. Each line is labelled with
    the speaker so the LLM can parse turn-taking.
    """
    try:
        result = client.conversations_replies(channel=channel, ts=thread_ts, limit=30)
        messages = result.get("messages", [])
        ctx_lines: list[str] = []
        for m in messages:
            if m.get("ts") == current_ts:
                continue
            text = (m.get("text") or "").strip()
            if not text:
                continue
            speaker = "codelens" if m.get("bot_id") else "user"
            snippet = text[:400] + ("…" if len(text) > 400 else "")
            ctx_lines.append(f"[{speaker}] {snippet}")
        if ctx_lines:
            kept = ctx_lines[-20:]
            joined = "\n".join(kept)
            print(
                f"[thread] fetched {len(ctx_lines)} context messages, kept {len(kept)}",
                flush=True,
            )
            return (
                f"\n\n[Thread context (most recent {len(kept)} messages):\n"
                f"{joined}\n]"
            )
    except Exception as e:
        print(f"[thread] failed to fetch context: {e}", flush=True)
    return ""


@app.event("app_mention")
def handle_mention(event, say, client):
    """Handle @CortexMesh mentions in channels and threads."""
    text = event.get("text", "")
    user_id = event.get("user", "")
    channel = event.get("channel", "")
    thread_ts = event.get("thread_ts")   # set only when mention is inside a thread
    current_ts = event.get("ts", "")

    subcommand, args = _parse_command(text)
    clean_text = re.sub(r"<@[A-Z0-9]+>\s*", "", text).strip()

    # If in a thread, include prior thread messages as context
    if thread_ts:
        context = _fetch_thread_context(client, channel, thread_ts, current_ts)
        clean_text = clean_text + context

    # Wrap say() so all responses go back into the same thread
    threaded = _threaded_say(say, thread_ts)
    _dispatch(threaded, subcommand, args, full_text=clean_text, user_id=user_id)


@app.event("message")
def handle_dm(event, say):
    """Handle direct messages only. In channels the bot responds only to explicit
    @mentions (see handle_mention) or slash commands — no keyword-based triggers."""
    # Ignore bot's own messages
    if event.get("bot_id"):
        return
    # Ignore message edits/deletes
    if event.get("subtype"):
        return

    channel_type = event.get("channel_type", "")
    if channel_type != "im":
        # Channel message without an @mention — ignore. Users must tag the bot
        # (handled by handle_mention) or use a slash command.
        return

    text = (event.get("text") or "").strip()
    user_id = event.get("user", "")
    subcommand, args = _parse_command(text)
    _dispatch(say, subcommand, args, full_text=text, user_id=user_id)


# ─── Slash command handler (if /agentura is configured) ────────────

def _command_ack(ack):
    """Acknowledge slash commands immediately to beat Slack's 3-second timeout."""
    ack()


def _command_lazy(command, say):
    """Heavy work runs in a background thread after ack is already sent."""
    text = command.get("text", "").strip()
    user_id = command.get("user_id", "")
    subcommand, args = _parse_command(text)
    _dispatch(say, subcommand, args, full_text=text, user_id=user_id)


def _command_silent_lazy(command, respond):
    """Same as _command_lazy but replies are ephemeral."""
    text = command.get("text", "").strip()
    user_id = command.get("user_id", "")
    subcommand, args = _parse_command(text)

    def ephemeral_say(*args, **kwargs):
        if args:
            kwargs["text"] = args[0]
        kwargs["response_type"] = "ephemeral"
        respond(**kwargs)

    _dispatch(ephemeral_say, subcommand, args, full_text=text, user_id=user_id)


app.command("/agentura")(ack=_command_ack, lazy=[_command_lazy])
app.command("/codeinsight")(ack=_command_ack, lazy=[_command_lazy])
app.command("/codeinsightsilent")(ack=_command_ack, lazy=[_command_silent_lazy])


# ─── Command implementations ──────────────────────────────────────

def _handle_help(say):
    say(
        text="Agentura Help",
        blocks=[
            {
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": "*How to use the bot*\n\n"
                    "*Ask a question (any channel):*\n"
                    "`ask <your question>` — routes to Android or iOS code review bot\n"
                    "_e.g._ `ask who wrote the send flow?`\n"
                    "_e.g._ `ask how does navigation work in iOS?`\n\n"
                    "*Run a skill (any channel):*\n"
                    "`run <domain/skill>` — execute a specific skill\n"
                    "_e.g._ `run dev/code-review-bot`\n\n"
                    "*Other commands (via DM or @mention):*\n"
                    "`status` — Platform health\n"
                    "`skills` — List all deployed skills\n"
                    "`approvals` — Pending approvals\n\n"
                    "_You can also @mention the bot or DM it directly._",
                },
            }
        ]
    )


def _format_market_brief(data: dict) -> list[dict]:
    """Format market-brief output as rich Slack blocks."""
    blocks = []
    # Summary
    if data.get("summary"):
        blocks.append({"type": "section", "text": {"type": "mrkdwn", "text": f"*:chart_with_upwards_trend: Market Brief — {data.get('date', 'Today')}*\n\n{data['summary']}"}})
        blocks.append({"type": "divider"})
    # Markets
    markets = data.get("markets", {})
    if markets.get("india"):
        india = markets["india"]
        lines = ["*:flag-in: Indian Markets*"]
        for idx, val in india.items():
            arrow = ":arrow_up:" if val.get("change_pct", 0) >= 0 else ":arrow_down:"
            lines.append(f"  {arrow} *{idx.upper()}*: {val.get('level', '')} ({val.get('change_pct', 0):+.1f}%) — {val.get('note', '')}")
        blocks.append({"type": "section", "text": {"type": "mrkdwn", "text": "\n".join(lines)}})
    if markets.get("forex"):
        forex = markets["forex"]
        lines = ["*:currency_exchange: Forex*"]
        for pair, val in forex.items():
            arrow = ":arrow_up:" if val.get("change_pct", 0) >= 0 else ":arrow_down:"
            lines.append(f"  {arrow} *{pair.upper()}*: {val.get('rate', '')} ({val.get('change_pct', 0):+.1f}%) — {val.get('note', '')}")
        blocks.append({"type": "section", "text": {"type": "mrkdwn", "text": "\n".join(lines)}})
    if markets.get("commodities"):
        commod = markets["commodities"]
        lines = ["*:gem: Commodities*"]
        for name, val in commod.items():
            arrow = ":arrow_up:" if val.get("change_pct", 0) >= 0 else ":arrow_down:"
            lines.append(f"  {arrow} *{name.replace('_', ' ').upper()}*: {val.get('level', '')} ({val.get('change_pct', 0):+.1f}%)")
        blocks.append({"type": "section", "text": {"type": "mrkdwn", "text": "\n".join(lines)}})
    # NRI Alerts
    alerts = data.get("nri_alerts", [])
    if alerts:
        blocks.append({"type": "divider"})
        lines = ["*:bell: NRI Alerts*"]
        for a in alerts[:4]:
            icon = ":red_circle:" if a.get("priority") == "critical" else ":large_orange_circle:" if a.get("priority") == "high" else ":large_yellow_circle:"
            lines.append(f"  {icon} {a.get('message', '')}")
            lines.append(f"     _Action: {a.get('action', '')}_")
        blocks.append({"type": "section", "text": {"type": "mrkdwn", "text": "\n".join(lines)}})
    # What to watch
    watch = data.get("what_to_watch_today", [])
    if watch:
        blocks.append({"type": "divider"})
        lines = ["*:eyes: What to Watch Today*"]
        for w in watch[:5]:
            lines.append(f"  • {w}")
        blocks.append({"type": "section", "text": {"type": "mrkdwn", "text": "\n".join(lines)}})
    return blocks


def _format_allocation(data: dict) -> list[dict]:
    """Format suggest-allocation output as rich Slack blocks."""
    blocks = []
    blocks.append({"type": "section", "text": {"type": "mrkdwn", "text": f"*:moneybag: Portfolio Allocation*\n\n_{data.get('client_summary', '')}_"}})
    # Risk assessment
    risk = data.get("risk_assessment", {})
    if risk:
        blocks.append({"type": "section", "text": {"type": "mrkdwn", "text": f"*Risk:* {risk.get('stated_tolerance', '')} stated → *{risk.get('assessed_capacity', '')}* assessed\n_{risk.get('reasoning', '')}_"}})
    blocks.append({"type": "divider"})
    # Allocation breakdown
    alloc = data.get("allocation", {})
    for asset_class, details in alloc.items():
        if not isinstance(details, dict) or "percentage" not in details:
            continue
        pct = details.get("percentage", 0)
        amt = details.get("amount_usd", 0)
        bar = "█" * (pct // 5) + "░" * ((100 - pct) // 5)
        lines = [f"*{asset_class.upper()}* — {pct}% (${amt:,.0f})", f"`{bar}`"]
        for inst in details.get("instruments", [])[:3]:
            if isinstance(inst, dict):
                name = inst.get("name", "")
                amt_i = inst.get("amount_usd", 0)
                mode = inst.get("sip_or_lump", "")
                acct = inst.get("account", "")
                lines.append(f"  • *{name}* — ${amt_i:,.0f} | {mode} | {acct}")
                if inst.get("rationale"):
                    lines.append(f"    _{inst['rationale'][:120]}_")
        blocks.append({"type": "section", "text": {"type": "mrkdwn", "text": "\n".join(lines)}})
    # Tax notes
    tax = data.get("tax_notes", [])
    if tax:
        blocks.append({"type": "divider"})
        lines = ["*:receipt: Tax Notes*"]
        for t in tax[:4]:
            lines.append(f"  • {t}")
        blocks.append({"type": "section", "text": {"type": "mrkdwn", "text": "\n".join(lines)}})
    # Warnings
    warnings = data.get("warnings", [])
    if warnings:
        lines = ["*:warning: Warnings*"]
        for w in warnings[:3]:
            lines.append(f"  • {w}")
        blocks.append({"type": "section", "text": {"type": "mrkdwn", "text": "\n".join(lines)}})
    return blocks


def _format_goal_planner(data: dict) -> list[dict]:
    """Format goal-planner output as rich Slack blocks."""
    blocks = []
    blocks.append({"type": "section", "text": {"type": "mrkdwn", "text": f"*:dart: Goal Planner*\n\n_{data.get('goal_summary', '')}_"}})
    # Feasibility
    feas = data.get("feasibility", {})
    if feas:
        verdict = feas.get("verdict", "")
        icon = ":white_check_mark:" if "ACHIEV" in verdict else ":warning:" if "STRETCH" in verdict else ":x:"
        blocks.append({"type": "section", "text": {"type": "mrkdwn", "text": (
            f"{icon} *{verdict}* (confidence: {feas.get('confidence', '')})\n"
            f"  Required: *${feas.get('required_monthly_usd', 0):,.0f}/mo* | "
            f"Available: ${feas.get('available_monthly_usd', 0):,.0f}/mo | "
            f"Using {feas.get('utilization_pct', 0):.0f}% capacity\n"
            f"  _{feas.get('buffer', '')}_"
        )}})
    blocks.append({"type": "divider"})
    # Strategy phases
    strategy = data.get("strategy", {})
    for phase_key in ("phase_1", "phase_2", "phase_3"):
        phase = strategy.get(phase_key, {})
        if not phase:
            continue
        alloc = phase.get("allocation", {})
        alloc_parts = []
        for cls, det in alloc.items():
            if isinstance(det, dict) and "pct" in det:
                alloc_parts.append(f"{cls} {det['pct']}%")
        alloc_str = " | ".join(alloc_parts)
        lines = [f"*{phase.get('name', '')}* (Years {phase.get('years', '')})", f"  {alloc_str}", f"  _{phase.get('rationale', '')}_"]
        # Show instruments for phase 1
        if phase_key == "phase_1":
            for cls, det in alloc.items():
                if isinstance(det, dict):
                    for inst in det.get("instruments", [])[:2]:
                        if isinstance(inst, str):
                            lines.append(f"    • {inst}")
                        elif isinstance(inst, dict):
                            lines.append(f"    • {inst.get('name', '')}")
        blocks.append({"type": "section", "text": {"type": "mrkdwn", "text": "\n".join(lines)}})
    # Projection
    proj = data.get("projection", [])
    if proj:
        blocks.append({"type": "divider"})
        lines = ["*:chart_with_upwards_trend: Projection*"]
        for p in proj:
            lines.append(f"  Year {p.get('year', '')}: invested ${p.get('invested_cumulative_usd', 0):,.0f} → corpus *${p.get('corpus_usd', 0):,.0f}* (+${p.get('growth_usd', 0):,.0f})")
        blocks.append({"type": "section", "text": {"type": "mrkdwn", "text": "\n".join(lines)}})
    # Action items
    actions = data.get("action_items", [])
    if actions:
        blocks.append({"type": "divider"})
        lines = ["*:rocket: Action Items*"]
        for a in actions[:4]:
            lines.append(f"  • {a}")
        blocks.append({"type": "section", "text": {"type": "mrkdwn", "text": "\n".join(lines)}})
    return blocks


def _format_skill_output(skill_path: str, raw: str) -> list[dict] | None:
    """Try to format known skill outputs as rich Slack blocks. Returns None if unknown."""
    try:
        cleaned = re.sub(r"^```(?:json)?\n?", "", raw.strip())
        cleaned = re.sub(r"\n?```$", "", cleaned.strip())
        data = json.loads(cleaned)
    except (json.JSONDecodeError, AttributeError):
        return None

    if "market-brief" in skill_path and data.get("markets"):
        return _format_market_brief(data)
    if "suggest-allocation" in skill_path and data.get("allocation"):
        return _format_allocation(data)
    if "goal-planner" in skill_path and data.get("feasibility"):
        return _format_goal_planner(data)
    return None


def _detect_platform(question: str) -> str:
    """Return 'ios' or 'android' based on keywords in the question."""
    q = question.lower()
    ios_keywords = ["ios", "swift", "swiftui", "xcode", "iphone", "cocoapods", "viewmodel", "usecase", "coordinator", "router", "uikit"]
    android_keywords = ["android", "kotlin", "compose", "gradle", "fragment", "activity", "viewmodel", "room", "hilt", "coroutine"]
    ios_score = sum(1 for k in ios_keywords if k in q)
    android_score = sum(1 for k in android_keywords if k in q)
    return "ios" if ios_score > android_score else "android"


def _detect_role(question: str) -> str:
    """Deduce whether the asker is a 'product_manager' or 'developer' from the question text.

    Strategy:
    - Start with PM score = 1 (slight bias toward PM for plain questions)
    - Add to PM score for business/user/conceptual signals
    - Add to dev score only for specific technical signals
    - Developer wins only when there are clear technical markers
    """
    q = question.lower()

    # Strong PM signals — asking for conceptual understanding, user impact, business context
    pm_signals = [
        ("why do we", 3), ("why does this", 3), ("why is there", 2),
        ("what does", 2), ("what is the purpose", 3), ("what is the goal", 3),
        ("user experience", 3), ("user journey", 3), ("user flow", 2),
        ("from a user", 3), ("from the user", 3), ("from a product", 3),
        ("business", 2), ("customer", 2), ("impact", 2), ("roadmap", 3),
        ("timeline", 2), ("strategy", 2), ("non-technical", 3), ("non technical", 3),
        ("in simple terms", 3), ("explain simply", 3), ("plain english", 3),
        ("high level", 2), ("overview", 2), ("tell me about", 2),
        ("explain", 1), ("how does", 1), ("what happens", 1),
        ("what is", 1), ("what are", 1), ("how do users", 2), ("what can", 1),
    ]

    # Strong dev signals — asking for code, files, specific implementation details
    dev_signals = [
        ("which file", 4), ("file path", 4), ("which class", 4), ("class name", 4),
        ("which function", 4), ("which method", 4), ("how to implement", 4),
        ("how do i", 3), ("how can i", 3), ("how to fix", 3),
        ("bug", 3), ("crash", 3), ("error", 3), ("exception", 3), ("stacktrace", 4),
        ("git blame", 4), ("git log", 4), ("who wrote", 3), ("who built", 3), ("contributor", 3),
        ("commit", 2), ("pull request", 3), ("pr ", 2), ("merge", 2),
        ("gradle", 4), ("hilt", 4), ("coroutine", 4), ("viewmodel", 3),
        ("repository", 3), ("usecase", 3), ("dependency injection", 4), (" di ", 3),
        ("unit test", 3), ("test case", 3), ("mock", 3),
        ("api endpoint", 4), ("rest api", 3), ("network call", 3), ("retrofit", 4),
        ("room database", 4), ("sql query", 4), ("schema", 3),
        ("refactor", 3), ("migration", 2), ("compile", 3), ("build error", 4),
        ("swift ", 2), ("swiftui ", 2), ("kotlin ", 2), ("compose ", 2),
    ]

    # Slight default bias toward PM (plain questions like "how does X work?" → PM)
    pm_score = 1
    dev_score = 0

    for signal, weight in pm_signals:
        if signal in q:
            pm_score += weight

    for signal, weight in dev_signals:
        if signal in q:
            dev_score += weight

    role = "product_manager" if pm_score >= dev_score else "developer"
    print(f"[role-detect] pm={pm_score} dev={dev_score} → {role} | q={question[:60]}", flush=True)
    return role


def _handle_question(say, question: str, user_id: str = ""):
    """Forward a free-form question to the appropriate code review bot."""
    if not question:
        _handle_help(say)
        return
    platform = _detect_platform(question)
    role = _detect_role(question)
    skill_path = "dev/ios-code-review-bot" if platform == "ios" else "dev/code-review-bot"
    platform_label = "iOS" if platform == "ios" else "Android"
    role_label = "PM" if role == "product_manager" else "Dev"
    print(f"[question] platform={platform} role={role} skill={skill_path} q={question[:80]}", flush=True)
    say(f":hourglass_flowing_sand: [{role_label}] Looking into your {platform_label} question... (may take up to 90s)")
    try:
        result = _api_post(
            f"/api/v1/skills/{skill_path}/execute",
            {"input_data": {"question": question, "user_id": user_id or "developer", "role": role}},
        )
        print(f"[question] result success={result.get('success')} output_keys={list(result.get('output', {}).keys())}", flush=True)
        success = result.get("success", False)
        output = result.get("output", {})
        # agent skills return output.summary; specialist skills return output.raw_output
        raw = output.get("raw_output") or output.get("summary") or output.get("error")
        # Fallback: stitch together tool outputs from iterations if no summary was produced
        if not raw:
            iterations = output.get("iterations", [])
            if iterations:
                last = iterations[-1]
                raw = last.get("tool_output", "") or "No response"
            else:
                raw = "No response"

        latency = result.get("latency_ms", 0)
        latency_str = f"{latency / 1000:.1f}s" if latency > 1000 else f"{latency:.0f}ms"
        answer_preview = raw[:60].replace("\n", " ")
        print(f"[question] sending answer: {answer_preview!r}", flush=True)

        role_icon = ":briefcase:" if role == "product_manager" else ":technologist:"
        header = {
            "type": "section",
            "text": {
                "type": "mrkdwn",
                "text": f"{'✅' if success else '❌'} *Code Review Bot* {role_icon} _{role_label}_ — {latency_str} | `${result.get('cost_usd', 0):.4f}`",
            },
        }
        question_block = {
            "type": "section",
            "text": {"type": "mrkdwn", "text": f"*Question:* {question[:500]}"},
        }
        body = {
            "type": "section",
            "text": {"type": "mrkdwn", "text": raw[:3000]},
        }
        say(text=raw[:200], blocks=[header, question_block, {"type": "divider"}, body])
    except httpx.HTTPStatusError as e:
        print(f"[question] HTTP error: {e.response.status_code} {e.response.text[:200]}", flush=True)
        say(f":x: Error: {e.response.status_code} — {e.response.text[:300]}")
    except Exception as e:
        print(f"[question] exception: {e}", flush=True)
        say(f":x: Error: {e}")


def _handle_run(say, args: str):
    if not args:
        say("Usage: `run <domain/skill>` (e.g., `run hr/interview-questions`)")
        return

    skill_path = args.strip()
    parts = skill_path.split("/")
    if len(parts) != 2:
        say(f"Invalid skill path: `{skill_path}`. Use format: `domain/skill`")
        return

    domain, skill_name = parts
    say(f":hourglass_flowing_sand: Executing `{skill_path}`... (may take up to 90s)")

    try:
        result = _api_post(
            f"/api/v1/skills/{domain}/{skill_name}/execute",
            {"input_data": {}, "dry_run": False},
        )
        success = result.get("success", False)
        output = result.get("output", {})
        raw = output.get("raw_output", "")

        latency = result.get("latency_ms", 0)
        latency_str = f"{latency / 1000:.1f}s" if latency > 1000 else f"{latency:.0f}ms"

        # Header block
        header = {
            "type": "section",
            "text": {
                "type": "mrkdwn",
                "text": f"{'✅' if success else '❌'} *{skill_path}* — {'Success' if success else 'Failed'}\n"
                f"Model: `{result.get('model_used', 'unknown')}` | "
                f"Latency: `{latency_str}` | "
                f"Cost: `${result.get('cost_usd', 0):.4f}`",
            },
        }

        # Try rich formatting for known skills
        rich_blocks = _format_skill_output(skill_path, raw) if raw else None

        if rich_blocks:
            blocks = [header, {"type": "divider"}] + rich_blocks
        else:
            # Fallback: show summary or truncated text
            if raw:
                cleaned = re.sub(r"^```(?:json)?\n?", "", raw.strip())
                cleaned = re.sub(r"\n?```$", "", cleaned.strip())
                try:
                    parsed = json.loads(cleaned)
                    fallback = parsed.get("summary") or parsed.get("raw_output") or cleaned[:2000]
                except (json.JSONDecodeError, AttributeError):
                    fallback = cleaned[:2000]
            else:
                fallback = json.dumps(output, indent=2)[:2000]
            blocks = [header, {"type": "section", "text": {"type": "mrkdwn", "text": fallback}}]

        # Approval buttons if needed
        if result.get("approval_required"):
            exec_id = result.get("skill_name", skill_path)
            blocks.append(
                {
                    "type": "actions",
                    "elements": [
                        {
                            "type": "button",
                            "text": {"type": "plain_text", "text": "Approve"},
                            "style": "primary",
                            "action_id": "approve_execution",
                            "value": exec_id,
                        },
                        {
                            "type": "button",
                            "text": {"type": "plain_text", "text": "Reject"},
                            "style": "danger",
                            "action_id": "reject_execution",
                            "value": exec_id,
                        },
                    ],
                }
            )

        # Slack limits blocks to 50 — trim if needed
        say(blocks=blocks[:50])
    except httpx.HTTPStatusError as e:
        say(f":x: Error executing `{skill_path}`: {e.response.status_code} — {e.response.text[:500]}")
    except Exception as e:
        say(f":x: Error: {e}")


def _handle_approve(say, args: str, approved: bool):
    execution_id = args.strip()
    if not execution_id:
        action = "approve" if approved else "reject"
        say(f"Usage: `{action} <execution-id>`")
        return

    try:
        result = _api_post(
            f"/api/v1/executions/{execution_id}/approve",
            {"approved": approved, "reviewer_notes": "Via Slack"},
        )
        emoji = ":white_check_mark:" if approved else ":no_entry_sign:"
        action = "approved" if approved else "rejected"
        say(f"{emoji} Execution `{execution_id}` {action}.")
    except httpx.HTTPStatusError as e:
        say(f":x: Error: {e.response.status_code} — {e.response.text[:300]}")
    except Exception as e:
        say(f":x: Error: {e}")


def _handle_status(say):
    try:
        health = _api_get("/api/v1/platform/health")
        executor = health.get("executor", {})
        db = health.get("database", {})
        mcp = health.get("mcp_tools", [])

        # Get skill count
        try:
            skills = _api_get("/api/v1/skills")
            skill_count = len(skills) if isinstance(skills, list) else 0
        except Exception:
            skill_count = "?"

        say(
            blocks=[
                {
                    "type": "section",
                    "text": {
                        "type": "mrkdwn",
                        "text": "*Platform Health* :green_circle:\n\n"
                        f"*Executor:* `{executor.get('status', 'unknown')}`\n"
                        f"*Database:* `{db.get('status', 'unknown')}` ({db.get('version', '')})\n"
                        f"*MCP Tools:* {len(mcp)} configured\n"
                        f"*Skills:* {skill_count} deployed",
                    },
                }
            ]
        )
    except Exception as e:
        say(f":x: Error checking status: {e}")


def _handle_list_skills(say):
    try:
        skills = _api_get("/api/v1/skills")
        if not skills:
            say("No skills deployed.")
            return

        # Group by domain
        domains: dict[str, list] = {}
        for s in skills:
            d = s.get("domain", "unknown")
            domains.setdefault(d, []).append(s)

        lines = ["*Deployed Skills*\n"]
        for domain, domain_skills in sorted(domains.items()):
            lines.append(f"\n*{domain}* ({len(domain_skills)} skills)")
            for s in domain_skills:
                health = s.get("health", "unknown")
                emoji = ":green_circle:" if health == "healthy" else ":yellow_circle:" if health == "degraded" else ":red_circle:"
                lines.append(
                    f"  {emoji} `{domain}/{s.get('name', '')}` — {s.get('role', '')} | {s.get('deploy_status', '')}"
                )

        say("\n".join(lines))
    except Exception as e:
        say(f":x: Error: {e}")


def _handle_list_approvals(say):
    try:
        executions = _api_get("/api/v1/executions?outcome=pending_approval")
        if not executions:
            say(":white_check_mark: No pending approvals.")
            return

        lines = ["*Pending Approvals*\n"]
        for e in executions[:10]:
            lines.append(
                f"• `{e.get('execution_id', '')}` — {e.get('skill', '')} "
                f"({e.get('timestamp', '')[:16]})"
            )

        say("\n".join(lines))
    except Exception as e:
        say(f":x: Error: {e}")


# ─── Interactive button handlers ───────────────────────────────────

@app.action("approve_execution")
def handle_approve_button(ack, action, say):
    ack()
    execution_id = action.get("value", "")
    try:
        _api_post(
            f"/api/v1/executions/{execution_id}/approve",
            {"approved": True, "reviewer_notes": "Approved via Slack button"},
        )
        say(f":white_check_mark: Execution `{execution_id}` approved.")
    except Exception as e:
        say(f":x: Error approving: {e}")


@app.action("reject_execution")
def handle_reject_button(ack, action, say):
    ack()
    execution_id = action.get("value", "")
    try:
        _api_post(
            f"/api/v1/executions/{execution_id}/approve",
            {"approved": False, "reviewer_notes": "Rejected via Slack button"},
        )
        say(f":no_entry_sign: Execution `{execution_id}` rejected.")
    except Exception as e:
        say(f":x: Error rejecting: {e}")


def main():
    """Start the Slack bot in Socket Mode."""
    # Cache bot user ID
    global BOT_USER_ID
    try:
        auth = app.client.auth_test()
        BOT_USER_ID = auth.get("user_id")
        print(f"Bot: {auth.get('user')} ({BOT_USER_ID}) in {auth.get('team')}")
    except Exception as e:
        print(f"Auth warning: {e}")

    handler = SocketModeHandler(
        app, os.environ.get("SLACK_APP_TOKEN")
    )
    print("Agentura Slack bot starting (Socket Mode)...")
    print("Listening for: @mentions, DMs, /agentura slash command, button actions")
    handler.start()


if __name__ == "__main__":
    main()
