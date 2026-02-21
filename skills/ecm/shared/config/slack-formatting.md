# Slack Message Formatting Guide

**Every Slack message from ECM Manager MUST follow these rules.**

---

## Message Catalog

ECM Manager sends exactly 3 report types. Each has a fixed title and schedule.

### 1. Backlog Report

```
Title:    :bar_chart: ECM Backlog — {date} {time} IST
Schedule: 7:00 AM IST daily (part of daily flow)
Purpose:  How big is the backlog? Growing or shrinking? Where are orders stuck?
```

**Main message content:**
- Backlog count + direction (growing/shrinking vs yesterday)
- Severity split (critical / action required / warning)
- Total value at risk
- Top 3 actions needed

**Thread replies:**
- Reply 1: Waterfall (carryover + yesterday + today) + 7-day inflow chart
- Reply 2: Currency split + sub-state breakdown

---

### 2. Triage Report

```
Title:    :dart: ECM Triage — {date} {time} IST
Schedule: 7:00 AM IST (daily flow), 2:00 PM UAE, 8:00 PM UAE
Purpose:  What got assigned? To whom? What should agents do first?
```

**Main message content:**
- Orders assigned count + total value
- Agent capacity status (who has room, who's full)
- Top 3 critical assignments
- Link to getting started

**Thread replies:**
- Reply 1: Full assignment list (code block)
- Reply per agent: Their specific orders + actions

---

### 3. Pattern Intelligence

```
Title:    :microscope: ECM Patterns — {date} {time} IST
Schedule: 7:00 AM IST daily (part of daily flow, runs after triage)
Purpose:  What systemic issues exist? What's growing? Any new failure modes?
```

**Main message content:**
- Total orders in patterns + distinct pattern count
- Top 3 patterns (name, order count, amount, trend arrow)
- Novel patterns alert (if any)
- Trend headline (what's growing, what's shrinking)

**Thread replies:**
- Reply 1: Top 10 pattern table (code block)
- Reply 2: Novel patterns detail + recommended actions (if any)

---

### 4. Error Alert (automatic on failure)

```
Title:    :rotating_light: ECM Manager Error
Schedule: Only on failure
Purpose:  Something broke — which phase failed and exit code
```

Single message, no thread. Keep under 500 chars.

---

## Schedule Summary

```
7:00 AM IST   daily flow = Backlog → Triage → Patterns (3 reports)
2:00 PM UAE   triage only (1 report)
8:00 PM UAE   triage only (1 report)
```

That's 5 Slack reports per day in #wg-asap-agent-pilot.

---

## Title Format (MANDATORY — use exactly as written)

Every main message MUST start with the exact title from the catalog above.

```
CORRECT:
:bar_chart: *ECM Backlog* — Feb 17, 2026 07:00 IST
:dart: *ECM Triage* — Feb 17, 2026 07:05 IST
:microscope: *ECM Patterns* — Feb 17, 2026 07:10 IST

INCORRECT:
ECM Manager Triage Report
Pattern Intelligence Report — 2026-02-17 21:40 IST
ECM Backlog Flow — Feb 17, 2026 (Live)
Sentinel Triage Report
```

---

## Slack mrkdwn Syntax (NOT standard markdown)

```
*bold*           (not **bold**)
_italic_
~strikethrough~
`inline code`
> blockquote
```

Use bullet character `•` or emoji bullets (`:white_small_square:`), not `-`.

---

## Formatting Rules

### Numbers lead sentences

```
CORRECT:   *397* actionable orders — 70% critical
INCORRECT: The current actionable backlog contains 397 orders
```

### Code blocks for aligned data (NOT markdown tables)

```
CORRECT:
` ` `
Pattern          Orders  Amount    Trend
refund_pending      54   276K AED  SAME
stuck_at_lulu       86   165K AED  UP +1
GBP falcon         105    37K GBP  SAME
` ` `

INCORRECT:
| Pattern | Orders | Amount | Trend |
|---------|--------|--------|-------|
| refund_pending | 54 | 276K AED | SAME |
```

### Bullets with bold lead for key items

```
CORRECT:
:red_circle: *54 refund orders* — 276K AED, ALL >36h stuck
:large_orange_diamond: *86 stuck at Lulu* — 165K AED, 68 critical

INCORRECT:
Pattern #2: refund_pending (AED)
  Signature: REFUND_TRIGGERED | Lulu: CANCELLATION_COMPLETED | ...
  Orders: 54 | Total: 276K AED | Stuck avg 285.7h (max 714.2h)
  ... (8 more lines)
```

### Inflow charts use bar characters in code blocks

```
:chart_with_upwards_trend: *7-Day Inflow*
` ` `
Feb 11  ██               14
Feb 12  █                11
Feb 13  █████            40
Feb 14  ████████████    102
Feb 15  ████████████████████████████████  334  SPIKE
` ` `
```

---

## Pre-Send Checklist

Before posting ANY Slack message:

- [ ] Title matches catalog exactly (emoji + bold name + date IST)
- [ ] Main message < 2000 chars
- [ ] No markdown tables — code blocks or bullets only
- [ ] Numbers lead sentences
- [ ] Details in thread, not main message
- [ ] Max 3-5 bullets per section
- [ ] Uses `*bold*` not `**bold**`
- [ ] Actionable items are numbered and specific
- [ ] No wall of text — no "Pattern Details" dump in main message
- [ ] No full signatures (e.g. `FULFILLMENT_PENDING|AML_MARKED_FOR_EDD|no|N/A`)

---

## Anti-Patterns

1. **Inventing titles** — Use the catalog title exactly, every time
2. **Wall of text** — Dumping terminal output into Slack
3. **Markdown tables** — `| col | col |` doesn't render in Slack
4. **Repeating data** — Summary + detail saying the same numbers twice
5. **Pattern Details in main message** — Goes in thread reply only
6. **Full signatures** — Technical noise for Slack readers
7. **Emoji spam** — Max 1 emoji per section header
