#!/usr/bin/env bash
# ─────────────────────────────────────────────────────────
# Agentura Demo Script
# Run this while screen recording to showcase the platform.
#
# Prerequisites:
#   - .env with OPENROUTER_API_KEY
#   - Executor running on :8000
#   - Gateway running on :3001
#   - Web UI running on :3000
#
# Usage:
#   cd agentura
#   bash hack/demo.sh            # normal run
#   bash hack/demo.sh --reset    # clean state first
# ─────────────────────────────────────────────────────────

set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"

# --reset flag: clean knowledge layer for a fresh demo
if [[ "${1:-}" == "--reset" ]]; then
  rm -f .agentura/episodic_memory.json .agentura/corrections.json .agentura/reflexion_entries.json
  rm -rf skills/hr/interview-questions/tests/generated
  printf "  Cleaned .agentura/ and generated tests. Starting fresh.\n\n"
fi

# Load env
source .env
export SKILLS_DIR="$ROOT/skills"

# Colors
CYAN='\033[0;36m'
GREEN='\033[0;32m'
YELLOW='\033[0;33m'
BOLD='\033[1m'
DIM='\033[2m'
RESET='\033[0m'

step=0

banner() {
  step=$((step + 1))
  printf "\n"
  printf "${CYAN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${RESET}\n"
  printf "${BOLD}  Step %d: %s${RESET}\n" "$step" "$1"
  printf "${CYAN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${RESET}\n"
  printf "\n"
}

pause() {
  printf "\n"
  printf "${DIM}  Press Enter to continue...${RESET}\n"
  read -r
}

run_cmd() {
  printf "${GREEN}  \$ %s${RESET}\n\n" "$1"
  eval "$1"
}

# ─────────────────────────────────────────────────────────
printf "\n"
printf "${BOLD}${CYAN}"
printf "   ╔═══════════════════════════════════════════╗\n"
printf "   ║         Agentura Platform Demo            ║\n"
printf "   ║   Kubernetes for AI Agent Swarms          ║\n"
printf "   ╚═══════════════════════════════════════════╝\n"
printf "${RESET}"
printf "  ${DIM}Config-driven skills · Self-improving · Observable${RESET}\n"
printf "\n"
pause

# ─────────────────────────────────────────────────────────
banner "List all deployed skills (like kubectl get pods)"
run_cmd "sdk/.venv/bin/agentura list"
pause

# ─────────────────────────────────────────────────────────
banner "Run a skill — HR Interview Questions"
printf "  ${DIM}Input: Senior Backend Engineer, 45-min interview, system design focus${RESET}\n\n"
run_cmd "sdk/.venv/bin/agentura run hr/interview-questions --input skills/hr/interview-questions/fixtures/sample_input.json"
pause

# ─────────────────────────────────────────────────────────
banner "Run a skill — Finance Expense Analyzer"
printf "  ${DIM}Input: January 2026 expense report with budget limits${RESET}\n\n"
run_cmd "sdk/.venv/bin/agentura run finance/expense-analyzer --input skills/finance/expense-analyzer/fixtures/sample_input.json"
pause

# ─────────────────────────────────────────────────────────
banner "Correct a mistake — The Learning Loop"
printf "  ${DIM}User feedback: interview questions need more system design depth${RESET}\n\n"

# Get the latest execution ID for hr/interview-questions
EXEC_ID=$(sdk/.venv/bin/python -c "
import json
from pathlib import Path
data = json.loads((Path('.agentura/episodic_memory.json')).read_text())
execs = [e for e in data['entries'] if e['skill'] == 'hr/interview-questions']
print(execs[-1]['execution_id'] if execs else 'EXEC-DEMO')
")
printf "  ${DIM}Correcting execution: %s${RESET}\n\n" "$EXEC_ID"

run_cmd "sdk/.venv/bin/agentura correct hr/interview-questions --execution-id $EXEC_ID --correction 'For senior backend roles, include at least 2 system design questions that test distributed systems knowledge. Ask about CAP theorem trade-offs and data partitioning strategies, not just generic architecture questions.'"
pause

# ─────────────────────────────────────────────────────────
banner "Check memory status — reflexion created"
run_cmd "sdk/.venv/bin/agentura memory status"
pause

# ─────────────────────────────────────────────────────────
banner "View learned reflexion rules"
printf "  ${DIM}The learned rules get injected into the skill's system prompt on next execution${RESET}\n\n"
printf "${GREEN}  \$ cat .agentura/reflexion_entries.json${RESET}\n\n"
sdk/.venv/bin/python -c "
import json
from pathlib import Path
data = json.loads(Path('.agentura/reflexion_entries.json').read_text())
for entry in data.get('entries', []):
    print(f\"  ID:         {entry['reflexion_id']}\")
    print(f\"  Skill:      {entry['skill']}\")
    print(f\"  Correction: {entry['correction_id']}\")
    print(f\"  Confidence: {entry['confidence']}\")
    rule = entry['rule']
    if len(rule) > 120:
        rule = rule[:120] + '...'
    print(f\"  Rule:       {rule}\")
    print()
"
pause

# ─────────────────────────────────────────────────────────
banner "Re-run — skill is now smarter"
printf "  ${DIM}Same input, but the reflexion rule guides better output${RESET}\n\n"
run_cmd "sdk/.venv/bin/agentura run hr/interview-questions --input skills/hr/interview-questions/fixtures/sample_input.json"
pause

# ─────────────────────────────────────────────────────────
banner "Validate skill structure"
printf "${GREEN}  \$ agentura validate hr/interview-questions${RESET}\n\n"
sdk/.venv/bin/agentura validate hr/interview-questions || true
pause

# ─────────────────────────────────────────────────────────
banner "Watch executions live (Ctrl+C to stop)"
printf "  ${DIM}Real-time execution feed — like kubectl get pods --watch${RESET}\n\n"
printf "${GREEN}  \$ agentura watch --limit 10${RESET}\n\n"
# Run watch for 5 seconds then kill
timeout 6 sdk/.venv/bin/agentura watch --limit 10 2>/dev/null || true
pause

# ─────────────────────────────────────────────────────────
printf "\n"
printf "${BOLD}${CYAN}"
printf "   ╔═══════════════════════════════════════════╗\n"
printf "   ║            Demo Complete!                 ║\n"
printf "   ╚═══════════════════════════════════════════╝\n"
printf "${RESET}\n"
printf "  ${BOLD}What you just saw:${RESET}\n"
printf "  1. 18 skills across 4 domains — deployed as config, not code\n"
printf "  2. Skills executed via CLI with structured JSON output\n"
printf "  3. User correction → reflexion rule → auto-generated test\n"
printf "  4. Re-execution with learned rule injected into prompt\n"
printf "  5. Full observability: validate, watch, memory status\n"
printf "\n"
printf "  ${DIM}Dashboard: http://localhost:3000/dashboard${RESET}\n"
printf "  ${DIM}Chat UI:   http://localhost:3000/chat${RESET}\n"
printf "  ${DIM}API:       http://localhost:3001/api/v1/skills${RESET}\n"
printf "\n"
