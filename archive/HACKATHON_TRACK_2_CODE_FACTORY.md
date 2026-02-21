# Track 2: Code Factory Platform

**Tagline**: "AI Coding Agent That Writes & Reviews 100% of Your Code"

**What You're Building**: Build-time coding agent that reads product specs and generates production-grade FastAPI services with automated review, risk-aware CI/CD, and zero human coding.

**Demo Pitch**: "PM writes spec. Agent writes code. Review agent validates. Auto-merges to main. Zero human coding. From spec to production in 5 minutes—risk-aware, evidence-backed, harness-protected."

---

## Strategic Positioning

### The Problem You're Solving
Software teams waste 60% of time on:
- Boilerplate (CRUD APIs, database models, tests)
- Code review iterations (back-and-forth on style, bugs)
- Manual testing (running pytest, fixing failures)
- Deployment friction (CI/CD config, merge conflicts)

**Pain**: Developers write repetitive code. PRs sit for days. Tests fail in CI. Bugs ship to production.

### The Solution
Code Factory: AI agent that writes 100% of code from specs
- PM writes `spec.md` → Coding Agent generates FastAPI service
- Risk Policy Gate assigns tier (critical/high/medium/low)
- Code Review Agent (Greptile) finds issues
- Remediation Agent auto-fixes findings
- GitHub Actions auto-merges if tier permits

**Moat**: Risk-aware automation. Critical code gets human review + evidence. Low-risk code auto-ships. Harness gap loop prevents production incidents from recurring.

---

## Tech Stack

| Component | Technology | Why |
|-----------|-----------|-----|
| **Coding Agent** | Claude Opus 4.6 + Pydantic AI | Best coding model, structured outputs |
| **Code Review Agent** | Greptile API + CodeRabbit | Codebase-aware, catches context bugs |
| **Remediation Agent** | Claude Sonnet 4.5 | Fast fixes for minor issues |
| **Risk Policy Engine** | Python + JSON schema | Tiered merge rules based on file paths |
| **Evidence Capture** | Playwright (browser tests) | Visual proof UI changes work |
| **Harness Gap Tracking** | GitHub Issues + Agent | Production incident → test case |
| **CI/CD** | GitHub Actions | Industry standard, free for public repos |
| **Generated Output** | FastAPI + PostgreSQL | Modern Python stack, production-ready |

---

## Architecture

```
┌──────────────────────────────────────────────────────────────────┐
│  PRODUCT MANAGER                                                 │
│  - Writes spec.md in /specs/                                     │
│  - Defines acceptance criteria                                   │
│  - Creates GitHub issue                                          │
└──────────────────────────────────────────────────────────────────┘
                            ↓
┌──────────────────────────────────────────────────────────────────┐
│  CODE FACTORY ORCHESTRATOR                                       │
│  1. Detect new spec.md (GitHub webhook or manual trigger)        │
│  2. Read spec + codebase context                                 │
│  3. Route to Coding Agent                                        │
└──────────────────────────────────────────────────────────────────┘
                            ↓
┌──────────────────────────────────────────────────────────────────┐
│  CODING AGENT (Claude Opus 4.6)                                  │
│  - Read spec.md                                                  │
│  - Generate:                                                     │
│    * FastAPI routes (api/v1/*.py)                                │
│    * Service layer (services/*.py)                               │
│    * Database models (models/*.py)                               │
│    * Tests (tests/*.py)                                          │
│  - Create PR with changes                                        │
└──────────────────────────────────────────────────────────────────┘
                            ↓
┌──────────────────────────────────────────────────────────────────┐
│  RISK POLICY GATE (GitHub Action)                                │
│  - Load .aspora/risk-policy.json                                 │
│  - Check changed files against tier rules:                       │
│    * Critical: api/v1/trades/**, db/migrations/**                │
│    * High: api/v1/**, services/risk_*.py                         │
│    * Medium: channels/**, workers/**                             │
│    * Low: tests/**, docs/**                                      │
│  - Assign tier to PR                                             │
│  - Enforce merge policy (critical → human approval required)     │
└──────────────────────────────────────────────────────────────────┘
                            ↓
┌──────────────────────────────────────────────────────────────────┐
│  CODE REVIEW AGENT (Greptile + CodeRabbit)                       │
│  - Greptile: Codebase-aware semantic search                      │
│    * "Does this break existing auth flow?"                       │
│    * "Are there similar endpoints I should match?"               │
│  - CodeRabbit: Static analysis                                   │
│    * Security issues (SQL injection, XSS)                        │
│    * Style violations (PEP 8, type hints)                        │
│  - Post review comments on PR                                    │
└──────────────────────────────────────────────────────────────────┘
                            ↓
┌──────────────────────────────────────────────────────────────────┐
│  REMEDIATION AGENT (Claude Sonnet 4.5)                           │
│  - Read review comments                                          │
│  - Auto-fix issues:                                              │
│    * Add missing type hints                                      │
│    * Fix SQL injection (use parameterized queries)               │
│    * Reformat code (Black, isort)                                │
│  - Push fixes to same PR                                         │
│  - Re-trigger review cycle                                       │
└──────────────────────────────────────────────────────────────────┘
                            ↓
┌──────────────────────────────────────────────────────────────────┐
│  EVIDENCE CAPTURE (for UI changes)                               │
│  - If PR touches frontend/API with UI impact:                    │
│    * Run Playwright tests                                        │
│    * Capture screenshots (before/after)                          │
│    * Record video of user flow                                   │
│  - Attach to PR as GitHub Actions artifact                       │
│  - Require human verification for critical tier                  │
└──────────────────────────────────────────────────────────────────┘
                            ↓
┌──────────────────────────────────────────────────────────────────┐
│  AUTO-MERGE (GitHub Actions)                                     │
│  - If tier = low/medium AND all checks pass:                     │
│    * Auto-merge PR                                               │
│    * Deploy to staging                                           │
│  - If tier = high/critical:                                      │
│    * Request human review                                        │
│    * Require 1 approval + evidence validation                    │
│    * Human approves → auto-merge + deploy                        │
└──────────────────────────────────────────────────────────────────┘
                            ↓
┌──────────────────────────────────────────────────────────────────┐
│  HARNESS GAP LOOP (Production Incident → Test Case)             │
│  - GitHub webhook on production incident tagged issue            │
│  - Agent reads incident description                              │
│  - Searches codebase for root cause                              │
│  - Generates test case that would have caught bug                │
│  - Creates PR with new test                                      │
│  - Tracks SLA: test written within 24h                           │
└──────────────────────────────────────────────────────────────────┘
```

---

## 36-Hour Timeline (5 People)

### Team Roles
- **Person A (Orchestrator Lead)**: Main agent loop, spec parsing, PR creation
- **Person B (Risk Policy Lead)**: Risk policy engine, GitHub Actions, tier validation
- **Person C (Review Lead)**: Greptile/CodeRabbit integration, remediation agent
- **Person D (Evidence Lead)**: Playwright tests, screenshot capture, video recording
- **Person E (Harness Lead)**: Production incident tracking, test generation

---

### Hour 0-6: Core Coding Agent

**Person A (Orchestrator)**:

```bash
# Create project
mkdir code-factory
cd code-factory

# Setup structure
mkdir -p {agents,specs,generated,tests,.aspora}

# Install dependencies
pip install pydantic-ai anthropic fastapi pytest playwright
```

```python
# agents/coding_agent.py
from pydantic_ai import Agent
from anthropic import Anthropic
import os
from pathlib import Path

class CodingAgent:
    def __init__(self, anthropic_key: str, output_dir: str = "generated"):
        self.client = Anthropic(api_key=anthropic_key)
        self.output_dir = Path(output_dir)

    async def generate_service(self, spec_path: str) -> dict:
        """Read spec and generate complete FastAPI service"""

        # Read spec
        spec_content = open(spec_path).read()

        # Build prompt
        prompt = f"""
You are a senior Python engineer. Generate a production-grade FastAPI service from this spec.

SPEC:
{spec_content}

REQUIREMENTS:
1. Create FastAPI routes in api/v1/
2. Create service layer in services/
3. Create Pydantic models in models/
4. Create pytest tests in tests/
5. Follow best practices:
   - Type hints everywhere
   - Docstrings for all functions
   - Error handling with proper status codes
   - Input validation with Pydantic
   - Dependency injection for services
6. Use PostgreSQL with SQLAlchemy
7. Include edge cases in tests

OUTPUT FORMAT:
Return JSON with:
{{
  "files": [
    {{"path": "api/v1/portfolio.py", "content": "..."}},
    {{"path": "services/portfolio_service.py", "content": "..."}},
    {{"path": "models/portfolio.py", "content": "..."}},
    {{"path": "tests/test_portfolio.py", "content": "..."}}
  ],
  "summary": "Brief description of what was generated"
}}
"""

        # Call Claude Opus (best coding model)
        response = await self.client.messages.create(
            model="claude-opus-4-20250514",
            max_tokens=16000,
            messages=[{"role": "user", "content": prompt}]
        )

        # Parse response
        result = json.loads(response.content[0].text)

        # Write files
        for file_info in result['files']:
            file_path = self.output_dir / file_info['path']
            file_path.parent.mkdir(parents=True, exist_ok=True)
            file_path.write_text(file_info['content'])

        return {
            "files_generated": [f['path'] for f in result['files']],
            "summary": result['summary'],
            "tokens_used": response.usage.input_tokens + response.usage.output_tokens,
            "cost": self._calculate_cost(response.usage)
        }

    def _calculate_cost(self, usage):
        """Calculate cost based on Opus pricing"""
        input_cost = usage.input_tokens / 1_000_000 * 15  # $15/MTok
        output_cost = usage.output_tokens / 1_000_000 * 75  # $75/MTok
        return input_cost + output_cost
```

**Person A (GitHub Integration)**:

```python
# agents/github_client.py
from github import Github
import subprocess

class GitHubClient:
    def __init__(self, token: str, repo_name: str):
        self.gh = Github(token)
        self.repo = self.gh.get_repo(repo_name)

    async def create_pr_from_spec(self, spec_path: str, generated_files: list):
        """Create PR with generated code"""

        # Create branch
        branch_name = f"code-factory/{spec_path.stem}"
        base_branch = self.repo.default_branch
        base_sha = self.repo.get_branch(base_branch).commit.sha

        ref = self.repo.create_git_ref(
            ref=f"refs/heads/{branch_name}",
            sha=base_sha
        )

        # Commit generated files
        for file_path in generated_files:
            content = open(file_path).read()
            self.repo.create_file(
                path=str(file_path),
                message=f"Generate {file_path} from {spec_path.name}",
                content=content,
                branch=branch_name
            )

        # Create PR
        pr = self.repo.create_pull(
            title=f"[Code Factory] Implement {spec_path.stem}",
            body=f"""
# Auto-generated by Code Factory

Spec: `{spec_path}`

## Generated Files
{chr(10).join(f'- `{f}`' for f in generated_files)}

## Next Steps
1. Risk Policy Gate will assign tier
2. Code Review Agent will scan for issues
3. Remediation Agent will auto-fix if needed
4. Auto-merge if tier permits

---
🤖 Generated by Code Factory
""",
            head=branch_name,
            base=base_branch
        )

        return {
            "pr_number": pr.number,
            "pr_url": pr.html_url,
            "branch": branch_name
        }
```

**Person B (Risk Policy Schema)**:

```json
// .aspora/risk-policy.json
{
  "version": "1.0",
  "riskTierRules": {
    "critical": {
      "description": "Changes that can cause data loss or financial impact",
      "patterns": [
        "api/v1/trades/**",
        "api/v1/payments/**",
        "db/migrations/**",
        "services/risk_*.py",
        "models/portfolio.py"
      ]
    },
    "high": {
      "description": "Changes to core business logic",
      "patterns": [
        "api/v1/**",
        "services/**",
        "models/**"
      ]
    },
    "medium": {
      "description": "Changes to integrations and workers",
      "patterns": [
        "channels/**",
        "workers/**",
        "utils/**"
      ]
    },
    "low": {
      "description": "Tests, docs, config",
      "patterns": [
        "tests/**",
        "docs/**",
        "*.md",
        ".github/**"
      ]
    }
  },
  "mergePolicy": {
    "critical": {
      "requiredChecks": [
        "risk-policy-gate",
        "code-review-agent",
        "harness-smoke",
        "browser-evidence"
      ],
      "requiresHumanApproval": true,
      "requiresEvidenceValidation": true,
      "autoMerge": false
    },
    "high": {
      "requiredChecks": [
        "risk-policy-gate",
        "code-review-agent",
        "harness-smoke"
      ],
      "requiresHumanApproval": true,
      "autoMerge": false
    },
    "medium": {
      "requiredChecks": [
        "risk-policy-gate",
        "code-review-agent"
      ],
      "requiresHumanApproval": false,
      "autoMerge": true
    },
    "low": {
      "requiredChecks": [
        "risk-policy-gate"
      ],
      "requiresHumanApproval": false,
      "autoMerge": true
    }
  },
  "shaValidation": {
    "enabled": true,
    "description": "Prevent stale reviews from approving new code",
    "enforcement": "All review comments must reference current HEAD SHA"
  }
}
```

---

### Hour 6-12: Risk Policy Gate + Review Agent

**Person B (Risk Policy Gate - GitHub Action)**:

```yaml
# .github/workflows/risk-policy-gate.yml
name: Risk Policy Gate

on:
  pull_request:
    types: [opened, synchronize]

jobs:
  assign-tier:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3

      - name: Assign Risk Tier
        id: tier
        run: |
          python .github/scripts/assign_risk_tier.py \
            --pr-number ${{ github.event.pull_request.number }} \
            --changed-files "${{ github.event.pull_request.changed_files }}"

      - name: Add Tier Label
        uses: actions/github-script@v6
        with:
          script: |
            const tier = '${{ steps.tier.outputs.tier }}';
            github.rest.issues.addLabels({
              owner: context.repo.owner,
              repo: context.repo.repo,
              issue_number: context.issue.number,
              labels: [`risk:${tier}`]
            });

      - name: Post Tier Comment
        uses: actions/github-script@v6
        with:
          script: |
            const tier = '${{ steps.tier.outputs.tier }}';
            const policy = require('./.aspora/risk-policy.json');
            const mergePolicy = policy.mergePolicy[tier];

            const comment = `
            ## 🛡️ Risk Policy Gate

            **Tier**: \`${tier}\`

            **Required Checks**:
            ${mergePolicy.requiredChecks.map(c => `- [ ] ${c}`).join('\n')}

            **Human Approval**: ${mergePolicy.requiresHumanApproval ? '✅ Required' : '❌ Not Required'}

            **Auto-Merge**: ${mergePolicy.autoMerge ? '✅ Enabled' : '❌ Disabled'}

            ${mergePolicy.requiresEvidenceValidation ? '⚠️ **Evidence validation required** (browser screenshots/video)' : ''}
            `;

            github.rest.issues.createComment({
              owner: context.repo.owner,
              repo: context.repo.repo,
              issue_number: context.issue.number,
              body: comment
            });

      - name: Validate SHA Discipline
        run: |
          python .github/scripts/validate_sha_discipline.py \
            --pr-number ${{ github.event.pull_request.number }}
```

```python
# .github/scripts/assign_risk_tier.py
import json
import sys
from pathlib import Path
import fnmatch

def assign_tier(changed_files: list) -> str:
    """Assign risk tier based on changed files"""

    policy = json.load(open('.aspora/risk-policy.json'))
    tier_rules = policy['riskTierRules']

    # Check from highest to lowest tier
    for tier in ['critical', 'high', 'medium', 'low']:
        patterns = tier_rules[tier]['patterns']
        for pattern in patterns:
            for file in changed_files:
                if fnmatch.fnmatch(file, pattern):
                    return tier

    return 'medium'  # Default

if __name__ == '__main__':
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument('--changed-files', required=True)
    args = parser.parse_args()

    changed_files = args.changed_files.split(',')
    tier = assign_tier(changed_files)

    print(f"::set-output name=tier::{tier}")
```

**Person C (Code Review Agent - Greptile Integration)**:

```python
# agents/review_agent.py
import requests
from anthropic import Anthropic

class CodeReviewAgent:
    def __init__(self, greptile_key: str, anthropic_key: str):
        self.greptile_key = greptile_key
        self.client = Anthropic(api_key=anthropic_key)

    async def review_pr(self, pr_number: int, repo: str, changed_files: list):
        """Review PR using Greptile for codebase context + Claude for analysis"""

        # Step 1: Get codebase context from Greptile
        context = await self._get_codebase_context(repo, changed_files)

        # Step 2: Get PR diff
        diff = await self._get_pr_diff(pr_number, repo)

        # Step 3: Review with Claude Sonnet
        prompt = f"""
You are a senior code reviewer. Review this PR for:
1. Security issues (SQL injection, XSS, authentication bugs)
2. Logic errors (edge cases, race conditions)
3. Style violations (PEP 8, missing type hints)
4. Breaking changes (API contract violations)

CODEBASE CONTEXT (from Greptile):
{context}

PR DIFF:
{diff}

OUTPUT FORMAT:
Return JSON array of issues:
[
  {{
    "file": "api/v1/portfolio.py",
    "line": 45,
    "severity": "high",
    "type": "security",
    "issue": "SQL injection vulnerability",
    "suggestion": "Use parameterized queries"
  }}
]
"""

        response = await self.client.messages.create(
            model="claude-sonnet-4-20250514",
            max_tokens=4000,
            messages=[{"role": "user", "content": prompt}]
        )

        issues = json.loads(response.content[0].text)

        # Post review comments
        for issue in issues:
            await self._post_review_comment(pr_number, repo, issue)

        return {
            "issues_found": len(issues),
            "issues": issues
        }

    async def _get_codebase_context(self, repo: str, changed_files: list):
        """Query Greptile for relevant codebase context"""

        response = requests.post(
            "https://api.greptile.com/v1/query",
            headers={"Authorization": f"Bearer {self.greptile_key}"},
            json={
                "repository": repo,
                "query": f"Show me existing patterns for: {', '.join(changed_files)}",
                "files": changed_files
            }
        )

        return response.json()['context']
```

**Person C (Remediation Agent)**:

```python
# agents/remediation_agent.py
class RemediationAgent:
    def __init__(self, anthropic_key: str):
        self.client = Anthropic(api_key=anthropic_key)

    async def fix_issues(self, issues: list, file_contents: dict):
        """Auto-fix review issues"""

        fixes = []

        for issue in issues:
            if issue['severity'] in ['low', 'medium']:
                # Auto-fix minor issues
                fix = await self._generate_fix(issue, file_contents[issue['file']])
                fixes.append(fix)
            else:
                # High/critical issues need human review
                continue

        # Apply fixes
        for fix in fixes:
            file_path = fix['file']
            with open(file_path, 'w') as f:
                f.write(fix['fixed_content'])

        return {
            "fixes_applied": len(fixes),
            "fixes": fixes
        }

    async def _generate_fix(self, issue: dict, file_content: str):
        """Generate fix for single issue"""

        prompt = f"""
Fix this code issue:

FILE: {issue['file']}
LINE: {issue['line']}
ISSUE: {issue['issue']}
SUGGESTION: {issue['suggestion']}

CURRENT CODE:
{file_content}

OUTPUT: Return the FULL fixed file content.
"""

        response = await self.client.messages.create(
            model="claude-sonnet-4-20250514",
            max_tokens=8000,
            messages=[{"role": "user", "content": prompt}]
        )

        return {
            "file": issue['file'],
            "fixed_content": response.content[0].text
        }
```

---

### Hour 12-18: Evidence Capture + Harness Gap

**Person D (Browser Evidence Capture)**:

```python
# agents/evidence_agent.py
from playwright.async_api import async_playwright
from pathlib import Path

class EvidenceAgent:
    def __init__(self, output_dir: str = "evidence"):
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(exist_ok=True)

    async def capture_ui_changes(self, pr_number: int, test_scenarios: list):
        """Capture screenshots and video of UI changes"""

        async with async_playwright() as p:
            browser = await p.chromium.launch()
            context = await browser.new_context(
                record_video_dir=str(self.output_dir / f"pr-{pr_number}")
            )
            page = await context.new_page()

            evidence = []

            for scenario in test_scenarios:
                # Navigate to test URL
                await page.goto(scenario['url'])

                # Execute test steps
                for step in scenario['steps']:
                    await self._execute_step(page, step)

                # Capture screenshot
                screenshot_path = self.output_dir / f"pr-{pr_number}" / f"{scenario['name']}.png"
                await page.screenshot(path=screenshot_path)

                # Validate assertions
                assertions = await self._validate_assertions(page, scenario['assertions'])

                evidence.append({
                    "scenario": scenario['name'],
                    "screenshot": str(screenshot_path),
                    "assertions_passed": all(a['passed'] for a in assertions),
                    "assertions": assertions
                })

            # Close browser (saves video)
            await context.close()
            await browser.close()

            return {
                "pr_number": pr_number,
                "scenarios_tested": len(test_scenarios),
                "evidence": evidence,
                "video_dir": str(self.output_dir / f"pr-{pr_number}")
            }

    async def _execute_step(self, page, step):
        """Execute single test step"""
        if step['type'] == 'click':
            await page.click(step['selector'])
        elif step['type'] == 'fill':
            await page.fill(step['selector'], step['value'])
        elif step['type'] == 'wait':
            await page.wait_for_timeout(step['ms'])

    async def _validate_assertions(self, page, assertions):
        """Validate page assertions"""
        results = []
        for assertion in assertions:
            if assertion['type'] == 'text_visible':
                try:
                    await page.wait_for_selector(f"text={assertion['text']}", timeout=2000)
                    results.append({"assertion": assertion, "passed": True})
                except:
                    results.append({"assertion": assertion, "passed": False})

        return results
```

```yaml
# evidence/scenarios/portfolio-check.yml
scenario:
  name: portfolio-check-ui
  url: http://localhost:8000/portfolio
  description: Verify portfolio page displays correctly

  steps:
    - type: fill
      selector: "#user-id-input"
      value: "priya@aspora.com"

    - type: click
      selector: "#check-portfolio-btn"

    - type: wait
      ms: 1000

  assertions:
    - type: text_visible
      text: "Portfolio Value"
      description: "Portfolio value should be displayed"

    - type: text_visible
      text: "RELIANCE.NS"
      description: "Holdings should include RELIANCE stock"

    - type: text_visible
      text: "Risk Status: Green"
      description: "Risk status should be shown"
```

**Person E (Harness Gap Tracking)**:

```python
# agents/harness_agent.py
class HarnessGapAgent:
    def __init__(self, github_token: str, anthropic_key: str):
        self.gh = Github(github_token)
        self.client = Anthropic(api_key=anthropic_key)

    async def process_production_incident(self, issue_number: int, repo_name: str):
        """Production incident → generate test case to prevent recurrence"""

        repo = self.gh.get_repo(repo_name)
        issue = repo.get_issue(issue_number)

        # Verify issue has 'production-incident' label
        if 'production-incident' not in [label.name for label in issue.labels]:
            return

        # Extract incident details
        incident_description = issue.body

        # Search codebase for root cause
        root_cause = await self._find_root_cause(repo_name, incident_description)

        # Generate test case
        test_case = await self._generate_test_case(
            incident_description,
            root_cause
        )

        # Create PR with new test
        pr = await self._create_test_pr(repo, test_case, issue_number)

        # Track SLA (test written within 24h)
        await self._track_harness_sla(issue, pr)

        return {
            "incident_issue": issue_number,
            "test_pr": pr.number,
            "root_cause": root_cause,
            "test_file": test_case['file_path']
        }

    async def _generate_test_case(self, incident: str, root_cause: dict):
        """Generate pytest test case"""

        prompt = f"""
Generate a pytest test case that would have caught this production incident.

INCIDENT:
{incident}

ROOT CAUSE:
File: {root_cause['file']}
Line: {root_cause['line']}
Issue: {root_cause['issue']}

OUTPUT: Python test function using pytest.
"""

        response = await self.client.messages.create(
            model="claude-sonnet-4-20250514",
            max_tokens=2000,
            messages=[{"role": "user", "content": prompt}]
        )

        test_code = response.content[0].text

        return {
            "file_path": f"tests/harness_gaps/test_incident_{issue_number}.py",
            "content": test_code
        }
```

---

### Hour 18-24: Live Demo Flow (End-to-End)

**Person A (Orchestrator - Main Flow)**:

```python
# main.py
import asyncio
from agents.coding_agent import CodingAgent
from agents.github_client import GitHubClient
from agents.review_agent import CodeReviewAgent
from agents.remediation_agent import RemediationAgent
from agents.evidence_agent import EvidenceAgent

async def code_factory_flow(spec_path: str):
    """Complete Code Factory flow: spec → code → review → merge"""

    print(f"🏭 Code Factory: Processing {spec_path}")

    # Step 1: Generate code
    print("📝 Coding Agent: Generating code from spec...")
    coding_agent = CodingAgent(os.getenv('ANTHROPIC_API_KEY'))
    result = await coding_agent.generate_service(spec_path)

    print(f"✅ Generated {len(result['files_generated'])} files")
    print(f"💰 Cost: ${result['cost']:.4f}")

    # Step 2: Create PR
    print("📤 Creating GitHub PR...")
    gh_client = GitHubClient(os.getenv('GITHUB_TOKEN'), 'your-org/your-repo')
    pr = await gh_client.create_pr_from_spec(spec_path, result['files_generated'])

    print(f"✅ PR created: {pr['pr_url']}")

    # Step 3: Wait for Risk Policy Gate (GitHub Action runs)
    print("🛡️ Risk Policy Gate: Assigning tier...")
    await asyncio.sleep(30)  # Wait for GitHub Action

    # Step 4: Code Review
    print("🔍 Code Review Agent: Scanning for issues...")
    review_agent = CodeReviewAgent(
        os.getenv('GREPTILE_API_KEY'),
        os.getenv('ANTHROPIC_API_KEY')
    )
    review = await review_agent.review_pr(
        pr['pr_number'],
        'your-org/your-repo',
        result['files_generated']
    )

    print(f"⚠️ Found {review['issues_found']} issues")

    # Step 5: Remediation (if issues are low/medium severity)
    if review['issues_found'] > 0:
        print("🔧 Remediation Agent: Auto-fixing issues...")
        remediation_agent = RemediationAgent(os.getenv('ANTHROPIC_API_KEY'))
        fixes = await remediation_agent.fix_issues(
            review['issues'],
            {f: open(f).read() for f in result['files_generated']}
        )

        print(f"✅ Fixed {fixes['fixes_applied']} issues")

        # Push fixes to PR
        # (Git commit + push logic)

    # Step 6: Evidence Capture (if UI changes)
    if any('api/v1' in f for f in result['files_generated']):
        print("📸 Evidence Agent: Capturing browser evidence...")
        evidence_agent = EvidenceAgent()
        evidence = await evidence_agent.capture_ui_changes(
            pr['pr_number'],
            [{
                "name": "portfolio-check",
                "url": "http://localhost:8000/portfolio",
                "steps": [
                    {"type": "fill", "selector": "#user-id", "value": "demo"},
                    {"type": "click", "selector": "#submit"}
                ],
                "assertions": [
                    {"type": "text_visible", "text": "Portfolio Value"}
                ]
            }]
        )

        print(f"✅ Evidence captured: {evidence['scenarios_tested']} scenarios")

    # Step 7: Auto-merge (if tier permits)
    print("🚀 Auto-merge: Checking merge policy...")
    # GitHub Actions handles auto-merge based on tier

    print(f"""

🎉 Code Factory Complete!

PR: {pr['pr_url']}
Files: {len(result['files_generated'])}
Cost: ${result['cost']:.4f}
Issues Fixed: {fixes['fixes_applied'] if review['issues_found'] > 0 else 0}
    """)

if __name__ == '__main__':
    import sys
    spec_path = sys.argv[1]  # e.g., specs/portfolio-service.md
    asyncio.run(code_factory_flow(spec_path))
```

**Demo Spec**:

```markdown
# specs/portfolio-service.md

# Portfolio Service

Build a FastAPI service for checking user portfolio.

## Endpoints

### GET /api/v1/portfolio/{user_id}

**Description**: Get user's portfolio with P&L and risk status

**Response**:
```json
{
  "user_id": "priya@aspora.com",
  "portfolio_value_inr": 850000,
  "holdings": [
    {
      "symbol": "RELIANCE.NS",
      "quantity": 15,
      "avg_price": 2450,
      "current_price": 2530,
      "value": 37950,
      "pnl_pct": 3.2
    }
  ],
  "risk_status": "green",
  "daily_pnl": 12340
}
```

## Database Schema

Table: `portfolios`
- user_id (VARCHAR, PK)
- symbol (VARCHAR)
- quantity (DECIMAL)
- avg_price (DECIMAL)
- current_price (DECIMAL)

## Tests

- Test valid user returns portfolio
- Test invalid user returns 404
- Test empty portfolio returns empty array
- Test P&L calculation accuracy
```

---

### Hour 24-30: Dashboard + Metrics

**Person B (Code Factory Dashboard)**:

```python
# dashboard/app.py
from fastapi import FastAPI
from fastapi.responses import HTMLResponse
import json

app = FastAPI()

@app.get('/dashboard')
async def dashboard():
    """Show Code Factory metrics"""

    # Query GitHub API for PRs labeled 'code-factory'
    factory_prs = await get_factory_prs()

    stats = {
        "total_prs": len(factory_prs),
        "auto_merged": len([pr for pr in factory_prs if pr['merged'] and pr['merged_by'] == 'github-actions']),
        "avg_time_to_merge": calculate_avg_time(factory_prs),
        "total_cost": sum(pr.get('cost', 0) for pr in factory_prs),
        "lines_generated": sum(pr.get('lines_added', 0) for pr in factory_prs)
    }

    return HTMLResponse(f"""
    <!DOCTYPE html>
    <html>
    <head><title>Code Factory Dashboard</title></head>
    <body>
      <h1>🏭 Code Factory Dashboard</h1>

      <div class="stats">
        <div class="stat">
          <h2>{stats['total_prs']}</h2>
          <p>Total PRs Generated</p>
        </div>

        <div class="stat">
          <h2>{stats['auto_merged']}</h2>
          <p>Auto-Merged</p>
        </div>

        <div class="stat">
          <h2>{stats['avg_time_to_merge']} min</h2>
          <p>Avg Time to Merge</p>
        </div>

        <div class="stat">
          <h2>${stats['total_cost']:.2f}</h2>
          <p>Total LLM Cost</p>
        </div>

        <div class="stat">
          <h2>{stats['lines_generated']:,}</h2>
          <p>Lines Generated</p>
        </div>
      </div>

      <h2>Recent PRs</h2>
      <table>
        <thead>
          <tr>
            <th>PR</th>
            <th>Spec</th>
            <th>Tier</th>
            <th>Status</th>
            <th>Time to Merge</th>
            <th>Cost</th>
          </tr>
        </thead>
        <tbody>
          {generate_pr_rows(factory_prs)}
        </tbody>
      </table>
    </body>
    </html>
    """)
```

---

### Hour 30-33: Rehearsal

**Demo Script (3 minutes)**:

```
Act 1 (30s): "The Problem"
  [Show developer writing boilerplate FastAPI code, struggling with tests]
  "Developers spend 60% of time on boilerplate. PRs sit for days in review.
   Tests fail in CI. Bugs ship to production."

Act 2 (90s): "The Solution - Code Factory"

  [Open terminal]
  $ cat specs/portfolio-service.md

  # Portfolio Service
  Build FastAPI endpoint for portfolio check
  GET /api/v1/portfolio/{user_id}
  ...

  [Run Code Factory]
  $ python main.py specs/portfolio-service.md

  🏭 Code Factory: Processing portfolio-service.md
  📝 Coding Agent: Generating code from spec...
  ✅ Generated 4 files:
     - api/v1/portfolio.py
     - services/portfolio_service.py
     - models/portfolio.py
     - tests/test_portfolio.py
  💰 Cost: $2.35

  📤 Creating GitHub PR...
  ✅ PR created: github.com/aspora/wealth-api/pull/42

  [Switch to GitHub]
  [Show PR with generated code]

  🛡️ Risk Policy Gate: Assigned tier = HIGH
  Required checks:
  - [x] risk-policy-gate
  - [x] code-review-agent
  - [ ] harness-smoke (running...)

  🔍 Code Review Agent: Scanning...
  ⚠️ Found 2 issues:
  - Missing type hint on line 45
  - SQL injection risk on line 67

  🔧 Remediation Agent: Auto-fixing...
  ✅ Fixed 2 issues, pushed to PR

  [GitHub Actions runs tests]
  ✅ All checks passed

  📸 Evidence Agent: Browser evidence attached
  [Show screenshot of portfolio UI working]

  [Human reviewer approves]
  ✅ Merged by github-actions[bot]
  🚀 Deployed to staging

  "From spec to production in 5 minutes. Zero human coding."

Act 3 (30s): "Risk-Aware Automation"

  [Show risk-policy.json]
  Critical tier (api/v1/trades/**):
  - Requires human approval ✅
  - Requires browser evidence ✅
  - No auto-merge

  Low tier (tests/**, docs/**):
  - Auto-merge enabled ✅
  - Ships immediately

  "Critical code gets scrutiny. Low-risk code ships fast."

Act 4 (30s): "Harness Gap Loop"

  [Show production incident issue]
  Issue #1234: Portfolio returns wrong P&L for USD holdings

  [Code Factory detects issue]
  🚨 Harness Gap Agent: Production incident detected
  🔍 Searching codebase for root cause...
  📝 Generating test case...
  ✅ PR created: tests/harness_gaps/test_incident_1234.py

  [Show test PR]
  def test_usd_holdings_pnl():
      # Would have caught production bug
      portfolio = get_portfolio("priya@aspora.com")
      assert portfolio['holdings'][0]['pnl_pct'] == 15.6  # USD Bitcoin

  "Production incident → Test case in 10 minutes. Never repeats."

[End: Show dashboard with metrics]
Total PRs: 47
Auto-Merged: 38 (81%)
Avg Time to Merge: 12 minutes
Total Cost: $104.50
Lines Generated: 15,420

"AI writes code. AI reviews code. AI fixes code. Humans focus on product."
```

---

### Hour 33-36: Polish + Video

Same as Track 1 (record video, prep pitch deck, load test)

---

## Success Metrics

### Minimum Viable Demo
- ✅ Coding Agent generates FastAPI service from spec
- ✅ Risk Policy Gate assigns tier correctly
- ✅ Code Review Agent finds issues
- ✅ Remediation Agent fixes minor issues
- ✅ PR auto-merges for low tier

### Stretch Goals
- 🎯 Browser Evidence Capture (Playwright screenshots)
- 🎯 Harness Gap Agent (incident → test case)
- 🎯 SHA-discipline validation
- 🎯 Cost dashboard

### Gold Standard
- 🏆 Live demo generates service in < 5 minutes
- 🏆 Judge asks "Can I use this for my team?"
- 🏆 Evidence capture actually validates UI works
- 🏆 Harness gap loop impresses judges

---

## Why You'll Win

### Technical Excellence
- ✅ Risk-aware automation (tiered merge policy)
- ✅ Codebase-aware review (Greptile integration)
- ✅ Evidence-backed merges (Playwright screenshots)
- ✅ SHA-discipline (prevents stale reviews)

### Business Impact
- ✅ 80% faster shipping (5 min vs 2 days)
- ✅ Zero human coding for boilerplate
- ✅ Production hardening (harness gap loop)

### Differentiator
- ✅ NOT just "AI writes code" (many tools do this)
- ✅ UNIQUE: Risk-aware gates + auto-remediation + evidence capture
- ✅ Production-ready (not a prototype)

---

## Total Code: ~2,500 lines

Simpler than Track 1 (no multi-domain complexity), but deeper automation (full CI/CD loop).

---

**TL;DR**: Build coding agent that writes FastAPI services from specs, with automated review (Greptile), risk-aware merging (tiered policy), browser evidence (Playwright), and harness gap tracking (incident → test). Win with risk-awareness + zero human coding + production hardening.
