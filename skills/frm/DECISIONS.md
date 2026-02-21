# FRM — Decision Record

> Domain-level decisions. Platform decisions are in the root DECISIONS.md.

---

## DEC-001: Interpret But Never Recommend

**Chose**: Skills present analysis and data, analyst makes final decision.
**Over**: Skills recommend specific actions (approve/deny/hold).
**Why**: Regulatory requirement — automated recommendations require compliance sign-off. Interpretation is safe; recommendation is not.
**Constraint**: No skill output may contain "recommended action" for final disposition.

---

## DEC-002: Threshold Sweep Required for Rule Simulation

**Chose**: Every rule simulation must include 5-7 threshold sweep values.
**Over**: Single-threshold analysis.
**Why**: Analysts need to see trade-offs before choosing a threshold. Single value = false precision.
**Constraint**: Rule simulation output MUST include threshold sweep table.
