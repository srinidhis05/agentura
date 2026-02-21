# Aspora as Code Factory: The Right Architecture

**Current Thinking (WRONG)**: Aspora Platform = Production runtime that executes skills for users

**Better Thinking (RIGHT)**: Aspora Platform = Internal coding agent that GENERATES standalone products

---

## The Architectural Shift

### What We Were Building (Old)

```
┌─────────────────────────────────────────────┐
│  Aspora Platform (PRODUCTION RUNTIME)       │
│                                             │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐ │
│  │   ECM    │  │ FinCrime │  │  Wealth  │ │  ← Domains on platform
│  │ Domain   │  │  Domain  │  │  Domain  │ │
│  └──────────┘  └──────────┘  └──────────┘ │
│                                             │
│  Users interact via Slack/WhatsApp          │
│  SkillExecutor calls OpenRouter             │
│  Platform serves production traffic         │
└─────────────────────────────────────────────┘

Problems:
- Shared fate (executor crash = all domains down)
- Mixed concerns (ops tooling + consumer product)
- Hard to scale (noisy neighbor)
- Platform is production critical infrastructure
```

### What We Should Build (New)

```
┌─────────────────────────────────────────────┐
│  Aspora Platform (CODE FACTORY)             │
│  Internal tool for engineering team         │
│                                             │
│  ┌──────────────────────────────────────┐  │
│  │  Coding Agent                        │  │
│  │  - Reads requirements                │  │
│  │  - Generates FastAPI/Go services     │  │
│  │  - Writes tests                      │  │
│  │  - Creates PRs with evidence         │  │
│  └──────────────────────────────────────┘  │
│                                             │
│  ┌──────────────────────────────────────┐  │
│  │  Review Agent (Greptile/CodeRabbit)  │  │
│  │  - Checks generated code             │  │
│  │  - Validates security/quality        │  │
│  │  - Runs harness tests                │  │
│  └──────────────────────────────────────┘  │
│                                             │
│  ┌──────────────────────────────────────┐  │
│  │  Risk Policy Gate                    │  │
│  │  - Enforces merge policy             │  │
│  │  - Requires evidence for high-risk   │  │
│  │  - Blocks merge if not clean         │  │
│  └──────────────────────────────────────┘  │
└─────────────────────────────────────────────┘
                    │
                    │ GENERATES
                    ▼
┌─────────────────────────────────────────────┐
│  Generated Products (STANDALONE)            │
│                                             │
│  ┌─────────────┐  ┌─────────────┐         │
│  │ ECM Product │  │FinCrime Prod│         │
│  │ (FastAPI)   │  │ (FastAPI)   │         │
│  │ - Postgres  │  │ - Postgres  │         │
│  │ - Redis     │  │ - Redis     │         │
│  │ - 100% test │  │ - 100% test │         │
│  │   coverage  │  │   coverage  │         │
│  └─────────────┘  └─────────────┘         │
│                                             │
│  ┌─────────────┐                           │
│  │Wealth Product│  ← Each product is       │
│  │(FastAPI/Go) │     isolated, scalable   │
│  │ - Postgres  │                           │
│  │ - Redis     │                           │
│  │ - Mobile App│                           │
│  └─────────────┘                           │
└─────────────────────────────────────────────┘

Benefits:
✅ Products are isolated (blast radius = 0)
✅ Each product scales independently
✅ Platform is NOT production critical
✅ Agents generate code faster than humans
✅ Quality enforced by automated review + tests
```

---

## How It Works: The Code Factory Loop

### Example: Building Wealth Product

```
┌─────────────────────────────────────────────────────────────┐
│ Product Manager (Human)                                     │
│ "We need a portfolio risk checker for Wealth product"      │
└─────────────────────┬───────────────────────────────────────┘
                      │
                      ▼
┌─────────────────────────────────────────────────────────────┐
│ 1. Aspora Coding Agent (Codex/Claude)                      │
│                                                             │
│ Reads:                                                      │
│ - Product spec: wealth-product/SPEC.md                     │
│ - Existing code: wealth-product/services/                  │
│ - Risk rules: .aspora/risk-policy.json                     │
│ - Harness cases: tests/harness/                            │
│                                                             │
│ Generates:                                                  │
│ - FastAPI endpoint: api/v1/risk_check.py                   │
│ - Service layer: services/risk_checker.py                  │
│ - Tests: tests/test_risk_checker.py                        │
│ - Browser evidence: tests/browser/risk_check.spec.ts       │
│ - Docs: docs/risk-checker.md                               │
│                                                             │
│ Creates PR: "feat: Add portfolio risk checker"             │
└─────────────────────┬───────────────────────────────────────┘
                      │
                      ▼
┌─────────────────────────────────────────────────────────────┐
│ 2. Risk Policy Gate (Preflight Check)                      │
│                                                             │
│ Changed files:                                              │
│ - api/v1/risk_check.py           → HIGH RISK (API path)    │
│ - services/risk_checker.py       → HIGH RISK (financial)   │
│ - tests/test_risk_checker.py     → LOW RISK (test)         │
│                                                             │
│ Required checks for HIGH RISK:                             │
│ ✓ risk-policy-gate                                         │
│ ✓ harness-smoke                                            │
│ ✓ Browser Evidence                                         │
│ ✓ Code Review Agent                                        │
│ ✓ CI Pipeline                                              │
│                                                             │
│ Status: WAITING for code review agent...                   │
└─────────────────────┬───────────────────────────────────────┘
                      │
                      ▼
┌─────────────────────────────────────────────────────────────┐
│ 3. Code Review Agent (Greptile/CodeRabbit)                 │
│                                                             │
│ Runs on PR head SHA: abc123                                │
│                                                             │
│ Review findings:                                            │
│ 🔴 CRITICAL: risk_checker.py line 45                       │
│    "Division by zero if portfolio_value is 0"              │
│                                                             │
│ 🟡 MEDIUM: risk_check.py line 12                           │
│    "Missing input validation for user_id parameter"        │
│                                                             │
│ Status: BLOCKED (2 actionable findings)                    │
└─────────────────────┬───────────────────────────────────────┘
                      │
                      ▼
┌─────────────────────────────────────────────────────────────┐
│ 4. Remediation Agent (Automated Fix)                       │
│                                                             │
│ Reads review findings for SHA abc123                       │
│                                                             │
│ Generates fixes:                                            │
│                                                             │
│ Fix 1 (CRITICAL):                                          │
│ ```python                                                   │
│ # Before                                                    │
│ risk_pct = daily_loss / portfolio_value                    │
│                                                             │
│ # After                                                     │
│ if portfolio_value == 0:                                   │
│     raise ValueError("Portfolio value cannot be zero")     │
│ risk_pct = daily_loss / portfolio_value                    │
│ ```                                                         │
│                                                             │
│ Fix 2 (MEDIUM):                                            │
│ ```python                                                   │
│ # Add validation                                            │
│ if not user_id or not isinstance(user_id, str):           │
│     raise HTTPException(400, "Invalid user_id")            │
│ ```                                                         │
│                                                             │
│ Runs local tests:                                           │
│ ✓ test_risk_checker_zero_portfolio (NEW)                  │
│ ✓ test_risk_checker_invalid_user_id (NEW)                 │
│                                                             │
│ Pushes fix commit: def456 → PR head is now def456         │
└─────────────────────┬───────────────────────────────────────┘
                      │
                      ▼ (PR synchronize triggers rerun)
┌─────────────────────────────────────────────────────────────┐
│ 5. Code Review Agent (Rerun on New Head)                   │
│                                                             │
│ Runs on PR head SHA: def456                                │
│                                                             │
│ Review findings:                                            │
│ ✅ No actionable findings                                  │
│                                                             │
│ Status: CLEAN (ready to merge)                             │
└─────────────────────┬───────────────────────────────────────┘
                      │
                      ▼
┌─────────────────────────────────────────────────────────────┐
│ 6. Risk Policy Gate (Final Check)                          │
│                                                             │
│ Required checks for HIGH RISK:                             │
│ ✓ risk-policy-gate                                         │
│ ✓ harness-smoke                                            │
│ ✓ Browser Evidence                                         │
│ ✓ Code Review Agent (CLEAN on def456)                     │
│ ✓ CI Pipeline (tests pass)                                │
│                                                             │
│ Status: ALL CHECKS PASSED                                  │
│                                                             │
│ Action: AUTO-MERGE to main                                 │
└─────────────────────┬───────────────────────────────────────┘
                      │
                      ▼
┌─────────────────────────────────────────────────────────────┐
│ 7. Production Deployment                                    │
│                                                             │
│ wealth-product/services/risk_checker.py deployed           │
│                                                             │
│ Users can now call:                                         │
│ POST /api/v1/risk-check                                    │
│ {                                                           │
│   "user_id": "priya@aspora.com",                           │
│   "portfolio_value": 1545000,                              │
│   "daily_loss": -12340                                     │
│ }                                                           │
│                                                             │
│ Response:                                                   │
│ {                                                           │
│   "risk_pct": -0.008,                                      │
│   "status": "GREEN",                                       │
│   "limit": -0.05,                                          │
│   "remaining": 0.042                                       │
│ }                                                           │
└─────────────────────────────────────────────────────────────┘
```

**Total time**: ~1 hour (agent writes → review → fix → merge → deploy)

**Human involvement**: Write initial requirement, approve final merge (optional)

---

## The Risk Policy Contract

### .aspora/risk-policy.json

```json
{
  "version": "1",
  "products": {
    "wealth": {
      "riskTierRules": {
        "critical": [
          "api/v1/trades/**",
          "services/broker_gateway.py",
          "db/migrations/**"
        ],
        "high": [
          "api/v1/**",
          "services/risk_*.py",
          "services/portfolio_*.py",
          "lib/kelly_criterion.py"
        ],
        "medium": [
          "channels/**",
          "formatters/**"
        ],
        "low": [
          "tests/**",
          "docs/**",
          "**"
        ]
      },
      "mergePolicy": {
        "critical": {
          "requiredChecks": [
            "risk-policy-gate",
            "harness-smoke",
            "harness-integration",
            "Browser Evidence",
            "Security Scan",
            "Code Review Agent",
            "CI Pipeline"
          ],
          "requiredApprovals": 2,
          "requiresHumanApproval": true
        },
        "high": {
          "requiredChecks": [
            "risk-policy-gate",
            "harness-smoke",
            "Browser Evidence",
            "Code Review Agent",
            "CI Pipeline"
          ],
          "requiredApprovals": 1,
          "requiresHumanApproval": false
        },
        "medium": {
          "requiredChecks": [
            "risk-policy-gate",
            "Code Review Agent",
            "CI Pipeline"
          ],
          "requiredApprovals": 0,
          "requiresHumanApproval": false
        },
        "low": {
          "requiredChecks": [
            "risk-policy-gate",
            "CI Pipeline"
          ],
          "requiredApprovals": 0,
          "requiresHumanApproval": false
        }
      },
      "evidenceRequirements": {
        "ui_changes": {
          "requiredFlows": [
            "portfolio-view",
            "trade-execution",
            "goal-tracking"
          ],
          "captureMethod": "playwright",
          "assertionChecks": [
            "expected_entrypoint_exists",
            "expected_account_identity_present",
            "no_console_errors"
          ]
        }
      }
    },
    "ecm": {
      "riskTierRules": {
        "critical": [
          "api/v1/runbooks/**",
          "services/remediation_*.py"
        ],
        "high": [
          "api/v1/**",
          "services/**"
        ],
        "low": ["**"]
      },
      "mergePolicy": {
        "critical": {
          "requiredChecks": [
            "risk-policy-gate",
            "harness-smoke",
            "Code Review Agent",
            "CI Pipeline"
          ],
          "requiredApprovals": 1,
          "requiresHumanApproval": true
        },
        "high": {
          "requiredChecks": [
            "risk-policy-gate",
            "Code Review Agent",
            "CI Pipeline"
          ],
          "requiredApprovals": 0,
          "requiresHumanApproval": false
        },
        "low": {
          "requiredChecks": ["risk-policy-gate", "CI Pipeline"],
          "requiredApprovals": 0,
          "requiresHumanApproval": false
        }
      }
    }
  },
  "docsDriftRules": {
    "requireDocsUpdate": [
      ".aspora/risk-policy.json",
      "api/v1/**"
    ],
    "docsFiles": [
      "docs/API.md",
      "docs/ARCHITECTURE.md"
    ]
  },
  "harnessGapSLA": {
    "productionIncident": {
      "maxTimeToHarnessCase": "48h",
      "trackingLabel": "harness-gap"
    }
  }
}
```

---

## GitHub Workflow: Risk Policy Gate

### .github/workflows/risk-policy-gate.yml

```yaml
name: Risk Policy Gate

on:
  pull_request:
    types: [opened, synchronize, reopened]

jobs:
  risk-policy-gate:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4

      - name: Compute Risk Tier
        id: risk
        run: |
          # Install risk-tier calculator
          npm install -g @aspora/risk-tier-cli

          # Analyze changed files
          TIER=$(aspora-risk-tier \
            --policy .aspora/risk-policy.json \
            --product wealth \
            --base ${{ github.event.pull_request.base.sha }} \
            --head ${{ github.event.pull_request.head.sha }})

          echo "tier=$TIER" >> $GITHUB_OUTPUT
          echo "Changed files are tier: $TIER"

      - name: Assert Docs Drift Rules
        if: steps.risk.outputs.tier == 'critical' || steps.risk.outputs.tier == 'high'
        run: |
          # Check if control-plane files changed
          CONTROL_PLANE_CHANGED=$(git diff --name-only ${{ github.event.pull_request.base.sha }}...${{ github.event.pull_request.head.sha }} | grep -E '.aspora/risk-policy.json|api/v1/')

          if [ -n "$CONTROL_PLANE_CHANGED" ]; then
            # Require docs update
            DOCS_CHANGED=$(git diff --name-only ${{ github.event.pull_request.base.sha }}...${{ github.event.pull_request.head.sha }} | grep -E 'docs/')

            if [ -z "$DOCS_CHANGED" ]; then
              echo "❌ Control-plane files changed but docs not updated"
              echo "Changed: $CONTROL_PLANE_CHANGED"
              echo "Required: Update docs/API.md or docs/ARCHITECTURE.md"
              exit 1
            fi
          fi

      - name: Get Required Checks for Tier
        id: checks
        run: |
          # Query policy for required checks
          REQUIRED=$(jq -r \
            --arg tier "${{ steps.risk.outputs.tier }}" \
            '.products.wealth.mergePolicy[$tier].requiredChecks | join(",")' \
            .aspora/risk-policy.json)

          echo "required=$REQUIRED" >> $GITHUB_OUTPUT
          echo "Required checks: $REQUIRED"

      - name: Wait for Code Review Agent
        if: contains(steps.checks.outputs.required, 'Code Review Agent')
        uses: ./.github/actions/wait-for-code-review
        with:
          head_sha: ${{ github.event.pull_request.head.sha }}
          timeout_minutes: 20

      - name: Assert No Actionable Findings
        if: contains(steps.checks.outputs.required, 'Code Review Agent')
        run: |
          # Query review agent API for findings on current head
          FINDINGS=$(curl -s \
            "https://api.greptile.com/v1/reviews/${{ github.repository }}/pr/${{ github.event.pull_request.number }}/findings?sha=${{ github.event.pull_request.head.sha }}" \
            -H "Authorization: Bearer ${{ secrets.GREPTILE_API_KEY }}")

          ACTIONABLE_COUNT=$(echo "$FINDINGS" | jq '[.[] | select(.severity == "critical" or .severity == "high")] | length')

          if [ "$ACTIONABLE_COUNT" -gt 0 ]; then
            echo "❌ Code review found $ACTIONABLE_COUNT actionable findings"
            echo "$FINDINGS" | jq '.[] | select(.severity == "critical" or .severity == "high")'
            exit 1
          fi

          echo "✅ Code review clean (no actionable findings)"

      - name: Assert Required Checks Successful
        run: |
          # Get all check runs for current head
          CHECKS=$(gh api \
            repos/${{ github.repository }}/commits/${{ github.event.pull_request.head.sha }}/check-runs \
            --jq '.check_runs')

          # Parse required checks
          IFS=',' read -ra REQUIRED_ARRAY <<< "${{ steps.checks.outputs.required }}"

          for CHECK_NAME in "${REQUIRED_ARRAY[@]}"; do
            STATUS=$(echo "$CHECKS" | jq -r --arg name "$CHECK_NAME" '.[] | select(.name == $name) | .status')
            CONCLUSION=$(echo "$CHECKS" | jq -r --arg name "$CHECK_NAME" '.[] | select(.name == $name) | .conclusion')

            if [ "$STATUS" != "completed" ] || [ "$CONCLUSION" != "success" ]; then
              echo "❌ Required check '$CHECK_NAME' not successful"
              echo "Status: $STATUS, Conclusion: $CONCLUSION"
              exit 1
            fi
          done

          echo "✅ All required checks successful"

      - name: Summary
        run: |
          echo "## Risk Policy Gate ✅" >> $GITHUB_STEP_SUMMARY
          echo "" >> $GITHUB_STEP_SUMMARY
          echo "**Risk Tier**: ${{ steps.risk.outputs.tier }}" >> $GITHUB_STEP_SUMMARY
          echo "**Required Checks**: ${{ steps.checks.outputs.required }}" >> $GITHUB_STEP_SUMMARY
          echo "" >> $GITHUB_STEP_SUMMARY
          echo "All policy requirements satisfied. Ready to merge." >> $GITHUB_STEP_SUMMARY
```

---

## GitHub Workflow: Coding Agent (Remediation Loop)

### .github/workflows/remediation-agent.yml

```yaml
name: Remediation Agent

on:
  issue_comment:
    types: [created]

jobs:
  remediate:
    # Only run when review agent posts findings
    if: |
      github.event.comment.user.login == 'greptile-bot' &&
      contains(github.event.comment.body, 'Actionable findings')
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
        with:
          ref: ${{ github.event.issue.pull_request.head.ref }}

      - name: Parse Review Findings
        id: findings
        run: |
          # Extract findings from review comment
          FINDINGS=$(echo '${{ github.event.comment.body }}' | \
            jq -R -s 'split("\n") | map(select(startswith("🔴") or startswith("🟡"))) | join("\n")')

          echo "findings<<EOF" >> $GITHUB_OUTPUT
          echo "$FINDINGS" >> $GITHUB_OUTPUT
          echo "EOF" >> $GITHUB_OUTPUT

      - name: Call Remediation Agent
        id: remediate
        run: |
          # Call Aspora coding agent API
          FIXES=$(curl -s -X POST \
            "https://aspora-platform.internal/api/v1/coding-agent/remediate" \
            -H "Content-Type: application/json" \
            -H "Authorization: Bearer ${{ secrets.ASPORA_AGENT_KEY }}" \
            -d '{
              "repo": "${{ github.repository }}",
              "pr_number": ${{ github.event.issue.number }},
              "head_sha": "${{ github.event.issue.pull_request.head.sha }}",
              "findings": ${{ toJSON(steps.findings.outputs.findings) }},
              "context": {
                "product": "wealth",
                "changed_files": ["api/v1/risk_check.py", "services/risk_checker.py"]
              }
            }')

          echo "fixes<<EOF" >> $GITHUB_OUTPUT
          echo "$FIXES" >> $GITHUB_OUTPUT
          echo "EOF" >> $GITHUB_OUTPUT

      - name: Apply Fixes
        run: |
          # Agent returned patch files
          echo '${{ steps.remediate.outputs.fixes }}' | jq -r '.patches[]' | while read PATCH; do
            echo "$PATCH" | git apply
          done

      - name: Run Local Tests
        run: |
          # Run tests to verify fixes
          npm test -- --coverage --changedSince=origin/main

      - name: Commit and Push Fixes
        run: |
          git config user.name "aspora-coding-agent[bot]"
          git config user.email "bot@aspora.ai"

          git add .
          git commit -m "fix: Auto-remediate review findings

          Applied fixes for:
          ${{ steps.findings.outputs.findings }}

          Generated by Aspora Coding Agent
          Review findings: ${{ github.event.comment.html_url }}"

          git push origin HEAD
```

---

## Browser Evidence: Required for UI Changes

### tests/browser/portfolio-view.spec.ts

```typescript
import { test, expect } from '@playwright/test';
import { generateEvidence } from '@aspora/browser-evidence';

test.describe('Portfolio View Flow', () => {
  test('should display portfolio with correct calculations', async ({ page }) => {
    // Evidence manifest
    const evidence = await generateEvidence({
      flow: 'portfolio-view',
      entrypoint: '/dashboard/portfolio',
      requiredIdentity: 'priya@aspora.com',
      assertions: [
        'portfolio_value_displayed',
        'holdings_table_rendered',
        'risk_status_visible',
        'no_console_errors'
      ]
    });

    // Navigate to portfolio
    await page.goto('http://localhost:3000/dashboard/portfolio');

    // Assert expected account identity
    await expect(page.locator('[data-testid="user-email"]'))
      .toHaveText('priya@aspora.com');

    // Assert portfolio value rendered
    const portfolioValue = page.locator('[data-testid="portfolio-total-value"]');
    await expect(portfolioValue).toBeVisible();

    // Capture screenshot for evidence
    await page.screenshot({
      path: `tests/evidence/portfolio-view-${Date.now()}.png`,
      fullPage: true
    });

    // Assert no console errors
    const consoleErrors = [];
    page.on('console', msg => {
      if (msg.type() === 'error') consoleErrors.push(msg.text());
    });

    await page.waitForTimeout(1000);
    expect(consoleErrors).toHaveLength(0);

    // Save evidence manifest
    await evidence.save({
      screenshots: [`portfolio-view-${Date.now()}.png`],
      assertions_passed: [
        'portfolio_value_displayed',
        'holdings_table_rendered',
        'risk_status_visible',
        'no_console_errors'
      ]
    });
  });

  test('should handle risk limit breach correctly', async ({ page }) => {
    // ... similar evidence generation for risk breach flow
  });
});
```

### .github/workflows/browser-evidence.yml

```yaml
name: Browser Evidence

on:
  pull_request:
    paths:
      - 'frontend/**'
      - 'api/v1/**'

jobs:
  capture-evidence:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4

      - name: Install Dependencies
        run: |
          npm install
          npx playwright install

      - name: Start Test Server
        run: |
          npm run dev &
          npx wait-on http://localhost:3000

      - name: Run Evidence Capture
        run: |
          npm run test:browser:evidence

      - name: Verify Evidence Manifest
        run: |
          # Ensure all required flows have evidence
          REQUIRED_FLOWS=$(jq -r '.products.wealth.evidenceRequirements.ui_changes.requiredFlows[]' .aspora/risk-policy.json)

          for FLOW in $REQUIRED_FLOWS; do
            if [ ! -f "tests/evidence/${FLOW}.manifest.json" ]; then
              echo "❌ Missing evidence for flow: $FLOW"
              exit 1
            fi

            # Verify assertions passed
            PASSED=$(jq -r '.assertions_passed | length' "tests/evidence/${FLOW}.manifest.json")
            if [ "$PASSED" -eq 0 ]; then
              echo "❌ No assertions passed for flow: $FLOW"
              exit 1
            fi
          done

          echo "✅ All required flows have valid evidence"

      - name: Upload Evidence Artifacts
        uses: actions/upload-artifact@v3
        with:
          name: browser-evidence
          path: tests/evidence/
```

---

## Harness Gap Loop: Production Incident → Test Case

### Process

```
1. Production incident occurs
   - User reports: "Portfolio showed wrong value"
   - Sentry alert: "Division by zero in risk_checker.py"

2. Engineer creates harness-gap issue
   - Title: "[HARNESS GAP] Portfolio calculation fails for zero balance"
   - Label: harness-gap
   - Due date: +48h (SLA)

3. Aspora coding agent reads issue
   - Reproduces bug locally
   - Writes failing test case
   - Generates fix
   - Submits PR with test + fix

4. Review agent validates
   - Test now fails on main (reproduces bug)
   - Test passes with fix (validates fix)
   - No regression in existing tests

5. Merge and track
   - PR merged
   - Harness coverage increases
   - Close harness-gap issue
   - Track in metrics dashboard
```

### .github/workflows/harness-gap-tracker.yml

```yaml
name: Harness Gap Tracker

on:
  issues:
    types: [opened, closed]

jobs:
  track-harness-gap:
    if: contains(github.event.issue.labels.*.name, 'harness-gap')
    runs-on: ubuntu-latest
    steps:
      - name: Check SLA
        if: github.event.action == 'opened'
        run: |
          # Calculate due date (48h from creation)
          CREATED_AT="${{ github.event.issue.created_at }}"
          DUE_AT=$(date -d "$CREATED_AT + 48 hours" -Iseconds)

          echo "⏱️ Harness gap SLA: 48 hours" >> $GITHUB_STEP_SUMMARY
          echo "Created: $CREATED_AT" >> $GITHUB_STEP_SUMMARY
          echo "Due: $DUE_AT" >> $GITHUB_STEP_SUMMARY

          # Set reminder
          gh issue comment ${{ github.event.issue.number }} \
            --body "⏱️ Harness gap SLA: Test case must be added within 48 hours (by $DUE_AT)"

      - name: Verify Test Case Added
        if: github.event.action == 'closed'
        run: |
          # Check if linked PR added test case
          LINKED_PRS=$(gh pr list --search "closes #${{ github.event.issue.number }}" --json number,files)

          if [ -z "$LINKED_PRS" ]; then
            echo "❌ No linked PR found for harness gap issue"
            exit 1
          fi

          # Verify PR added test file
          TEST_FILE_ADDED=$(echo "$LINKED_PRS" | jq '.[] | .files[] | select(.path | startswith("tests/harness/"))')

          if [ -z "$TEST_FILE_ADDED" ]; then
            echo "❌ Linked PR did not add harness test case"
            exit 1
          fi

          echo "✅ Harness gap closed with test case"

      - name: Update Metrics
        if: github.event.action == 'closed'
        run: |
          # Track harness coverage growth
          TOTAL_GAPS=$(gh issue list --label harness-gap --state all --json number | jq 'length')
          CLOSED_GAPS=$(gh issue list --label harness-gap --state closed --json number | jq 'length')

          echo "## Harness Gap Metrics" >> $GITHUB_STEP_SUMMARY
          echo "Total incidents tracked: $TOTAL_GAPS" >> $GITHUB_STEP_SUMMARY
          echo "Converted to test cases: $CLOSED_GAPS" >> $GITHUB_STEP_SUMMARY
          echo "Coverage improvement: $(($CLOSED_GAPS * 100 / $TOTAL_GAPS))%" >> $GITHUB_STEP_SUMMARY
```

---

## What This Means for Aspora Platform

### The Platform's NEW Role

```
Aspora Platform is now a CODE FACTORY, not a PRODUCT RUNTIME

┌───────────────────────────────────────────────────────────┐
│  Aspora Platform (Internal Tooling Only)                  │
│                                                            │
│  Components:                                               │
│  1. Coding Agent (Codex/Claude Opus)                      │
│     - Generates FastAPI/Go services                       │
│     - Writes tests with 100% coverage                     │
│     - Creates PRs with evidence                           │
│                                                            │
│  2. Review Agent (Greptile/CodeRabbit)                    │
│     - Security scanning                                    │
│     - Quality checks                                       │
│     - Validates evidence                                   │
│                                                            │
│  3. Risk Policy Engine                                     │
│     - Enforces merge requirements                         │
│     - Tracks harness gaps                                 │
│     - Monitors SLAs                                        │
│                                                            │
│  4. Remediation Agent (Auto-Fix)                          │
│     - Reads review findings                               │
│     - Generates patches                                    │
│     - Pushes fixes to PR                                   │
│                                                            │
│  5. Evidence Capture System                               │
│     - Browser automation (Playwright)                      │
│     - Screenshot + assertion validation                    │
│     - Manifest generation                                  │
│                                                            │
│  Users: ONLY internal engineering team                    │
│  Output: Standalone product repos (ECM, FinCrime, Wealth) │
│  Production traffic: ZERO (not customer-facing)           │
└───────────────────────────────────────────────────────────┘
```

### What Gets Generated

```
wealth-product/
├── api/
│   └── v1/
│       ├── portfolio.py           ← Generated by coding agent
│       ├── risk_check.py          ← Generated by coding agent
│       └── goals.py               ← Generated by coding agent
├── services/
│   ├── portfolio_service.py      ← Generated by coding agent
│   ├── risk_service.py           ← Generated by coding agent
│   └── trading_service.py        ← Generated by coding agent
├── tests/
│   ├── test_portfolio_service.py ← Generated by coding agent
│   ├── test_risk_service.py      ← Generated by coding agent
│   └── harness/
│       ├── test_zero_portfolio.py ← Generated from production incident
│       └── test_risk_breach.py    ← Generated from production incident
├── tests/browser/
│   ├── portfolio-view.spec.ts     ← Generated by coding agent
│   └── trade-execution.spec.ts    ← Generated by coding agent
├── .aspora/
│   └── risk-policy.json           ← Defines merge requirements
└── README.md                       ← Generated by coding agent

All code written by agents, validated by automated review + tests.
Humans only write requirements and approve critical merges.
```

---

## Comparison: Old Platform vs New Code Factory

| Aspect | Old (Platform Runtime) | New (Code Factory) |
|--------|------------------------|---------------------|
| **What it is** | Production skill executor | Internal coding agent |
| **Who uses it** | End users (via Slack/WhatsApp) | Engineering team only |
| **What it does** | Executes skills, returns results | Generates code, writes tests, creates PRs |
| **Output** | Markdown/JSON responses | Standalone product repos |
| **Production critical** | YES (downtime = users affected) | NO (downtime = slower dev velocity) |
| **Blast radius** | HIGH (executor crash = all domains down) | ZERO (each product isolated) |
| **Scaling** | Noisy neighbor problems | Each product scales independently |
| **Team structure** | Platform team + domain skill writers | Platform team + product teams |
| **Innovation speed** | Fast (new domain = new skills) | FASTER (agents write code 10x faster) |
| **Quality control** | Manual testing | Automated review agents + harness tests |
| **Hackathon demo** | Show 4 domains on platform | Show agent generating a product in 10 minutes |

---

## Revised Hackathon Strategy

### Demo: "Watch Aspora Build a Product in 10 Minutes"

```
Act 1 (2 min): The Problem
"Building fintech products takes months. What if an agent could do it in minutes?"

Act 2 (5 min): Live Coding Agent Demo
PM: "Build a portfolio risk checker for Wealth product"

Agent (live on screen):
  → Reads SPEC.md
  → Generates api/v1/risk_check.py
  → Generates services/risk_checker.py
  → Writes tests/test_risk_checker.py
  → Writes tests/browser/risk-check.spec.ts
  → Creates PR

  [10 seconds later]

Review Agent:
  → Scans code
  → Finds: "Division by zero if portfolio_value is 0"
  → Marks: BLOCKED

Remediation Agent:
  → Reads finding
  → Generates fix:
    if portfolio_value == 0:
        raise ValueError("...")
  → Pushes fix commit

Review Agent (rerun):
  → ✅ Clean (no findings)

Risk Policy Gate:
  → ✅ All checks passed
  → Auto-merges

[Code is now in main, deployed to production]

Act 3 (3 min): The System
"This isn't just one agent. It's a factory."

Show risk-policy.json:
- CRITICAL paths require human approval
- HIGH paths require code review + browser evidence
- All changes require harness tests

Show harness-gap loop:
- Production bug → GitHub issue
- Agent writes failing test
- Agent writes fix
- Test coverage increases forever

Show metrics dashboard:
- 1,247 PRs merged this month
- 98% auto-merged (no human review)
- 100% test coverage maintained
- 0 production incidents from agent-written code

Act 4 (1 min): The Vision
"What if every company had a code factory?
 Not to replace engineers.
 To let engineers focus on WHAT to build,
 while agents handle HOW to build it."

Demo: Aspora itself onboarding a new product in real-time
[Live generate: ECM product, FinCrime product, Wealth product]
[All in 10 minutes, all with 100% test coverage]

"This is Aspora. The code factory for fintech."
```

---

## Summary

**You're absolutely right. The code factory model is superior.**

### Why It's Better

1. **Clean Architecture**: Platform is dev tool, not prod runtime
2. **Zero Blast Radius**: Products are isolated
3. **10x Velocity**: Agents write code faster than humans
4. **Guaranteed Quality**: Review agents + harness tests enforce standards
5. **Hackathon Story**: More impressive (watch agent build a product live)

### What Changes for Hackathon

**Don't build**: Platform that executes skills for users
**Do build**: Platform that generates products for engineers

**Demo**: Live coding agent session
- PM gives requirement
- Agent writes code in 5 minutes
- Review agent validates
- Remediation agent fixes issues
- Code auto-merges and deploys
- Show this 2-3 times (portfolio, trading, goals)

**Result**: Judges see an agent building an entire product during the pitch

This is way more impressive than "we have 4 domains on a platform."

Should I draft the revised hackathon plan with this code factory approach?
