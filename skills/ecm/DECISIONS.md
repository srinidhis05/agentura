# ECM Operations — Decision Record

> Domain-level decisions. Platform decisions are in the root DECISIONS.md.

---

## DEC-001: Redshift MCP Over Direct DB Queries

**Chose**: MCP server for Redshift access (read-only SQL)
**Over**: Direct database connection from skill handler
**Why**: MCP provides query sandboxing, audit trail, and rate limiting. Skill authors don't need DB credentials.
**Constraint**: All Redshift access MUST go through MCP. No direct connections.

---

## DEC-002: Manager + Specialist Role Split

**Chose**: ECM manager skill routes to order-details, my-tickets, escalate-ticket, etc.
**Over**: Single monolithic ECM skill handling everything
**Why**: Context bloat (40K+ tokens loading all runbooks) and role confusion (batch vs interactive).
**Constraint**: Manager NEVER loads runbooks. Specialists NEVER compute priority scores.
