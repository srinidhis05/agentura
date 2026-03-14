#!/usr/bin/env python3
"""
Comprehensive PM Skills Test Suite
Tests all 15 skills from PR #10 + 3 new hybrid/approval skills
"""

import json
import os
import sys
from datetime import datetime, timedelta
import requests
from typing import Dict, List, Any

# Configuration
GATEWAY_URL = os.getenv("GATEWAY_URL", "http://localhost:3001")
PROJECT_SLUG = "gold"  # Test project

class PMSkillsTester:
    def __init__(self, gateway_url: str):
        self.gateway_url = gateway_url
        self.results = []
        self.passed = 0
        self.failed = 0

    def log(self, message: str, level: str = "INFO"):
        """Log test message"""
        timestamp = datetime.now().strftime("%H:%M:%S")
        print(f"[{timestamp}] [{level}] {message}")

    def test_skill(
        self,
        skill_name: str,
        test_name: str,
        payload: Dict[str, Any],
        expected_keys: List[str] = None,
        expected_status: str = "success"
    ) -> bool:
        """Test a single skill execution"""
        self.log(f"Testing: {skill_name} - {test_name}", "TEST")

        try:
            response = requests.post(
                f"{self.gateway_url}/api/v1/skills/pm/{skill_name}/execute",
                json=payload,
                timeout=60
            )

            if response.status_code != 200:
                self.log(f"❌ Failed: HTTP {response.status_code}", "FAIL")
                self.failed += 1
                return False

            result = response.json()

            # Check expected keys
            if expected_keys:
                missing_keys = [k for k in expected_keys if k not in result]
                if missing_keys:
                    self.log(f"❌ Missing keys: {missing_keys}", "FAIL")
                    self.failed += 1
                    return False

            self.log(f"✅ Passed: {test_name}", "PASS")
            self.passed += 1
            self.results.append({
                "skill": skill_name,
                "test": test_name,
                "status": "passed",
                "result": result
            })
            return True

        except Exception as e:
            self.log(f"❌ Error: {str(e)}", "FAIL")
            self.failed += 1
            self.results.append({
                "skill": skill_name,
                "test": test_name,
                "status": "failed",
                "error": str(e)
            })
            return False

    def test_triage(self):
        """Test 1: Triage - Routes messages to correct skills"""
        self.log("=== Testing Triage Skill ===", "SECTION")

        # Test 1a: Meeting update routing
        self.test_skill(
            "triage",
            "Route meeting notes to meeting-update",
            {
                "message": "Process this Granola meeting: https://granola.so/meeting/abc123",
                "context": {}
            },
            expected_keys=["route_to", "confidence"]
        )

        # Test 1b: Query routing
        self.test_skill(
            "triage",
            "Route question to pm-query",
            {
                "message": "What's the status of E-005?",
                "context": {}
            },
            expected_keys=["route_to", "confidence"]
        )

    def test_meeting_update(self):
        """Test 2: Meeting Update - Process meeting notes with classification"""
        self.log("=== Testing Meeting Update Skill ===", "SECTION")

        self.test_skill(
            "meeting-update",
            "Process meeting with factual changes",
            {
                "project_slug": PROJECT_SLUG,
                "meeting_search": "test",
                "systems": ["notion"],
                "dry_run": True  # Don't actually write
            },
            expected_keys=["meeting_title", "systems_updated"]
        )

    def test_meeting_scan(self):
        """Test 3: Meeting Scan - Find unprocessed meetings"""
        self.log("=== Testing Meeting Scan Skill ===", "SECTION")

        self.test_skill(
            "meeting-scan",
            "Scan for unprocessed meetings",
            {
                "project_slug": PROJECT_SLUG,
                "time_range": "7d"
            },
            expected_keys=["meetings_found"]
        )

    def test_meeting_prep(self):
        """Test 4: Meeting Prep - Generate briefing"""
        self.log("=== Testing Meeting Prep Skill ===", "SECTION")

        self.test_skill(
            "meeting-prep",
            "Prepare briefing for upcoming meeting",
            {
                "project_slug": PROJECT_SLUG,
                "meeting_title": "Weekly Partner Sync"
            },
            expected_keys=["briefing"]
        )

    def test_pm_query(self):
        """Test 5: PM Query - Answer questions from Notion"""
        self.log("=== Testing PM Query Skill ===", "SECTION")

        self.test_skill(
            "pm-query",
            "Query item status",
            {
                "project_slug": PROJECT_SLUG,
                "query": "What items are in progress?"
            },
            expected_keys=["answer"]
        )

    def test_daily_briefing(self):
        """Test 6: Daily Briefing - Morning status"""
        self.log("=== Testing Daily Briefing Skill ===", "SECTION")

        self.test_skill(
            "daily-briefing",
            "Generate morning briefing",
            {
                "project_slug": PROJECT_SLUG,
                "date": datetime.now().strftime("%Y-%m-%d")
            },
            expected_keys=["briefing", "tasks_today"]
        )

    def test_daily_wrap(self):
        """Test 7: Daily Wrap - End of day summary"""
        self.log("=== Testing Daily Wrap Skill ===", "SECTION")

        self.test_skill(
            "daily-wrap",
            "Generate end of day summary",
            {
                "project_slug": PROJECT_SLUG,
                "date": datetime.now().strftime("%Y-%m-%d")
            },
            expected_keys=["summary", "completed_today"]
        )

    def test_weekly_digest(self):
        """Test 8: Weekly Digest - Week summary"""
        self.log("=== Testing Weekly Digest Skill ===", "SECTION")

        self.test_skill(
            "weekly-digest",
            "Generate weekly summary",
            {
                "project_slug": PROJECT_SLUG,
                "week_start": (datetime.now() - timedelta(days=7)).strftime("%Y-%m-%d")
            },
            expected_keys=["digest", "highlights"]
        )

    def test_action_tracker(self):
        """Test 9: Action Tracker - Find overdue items"""
        self.log("=== Testing Action Tracker Skill ===", "SECTION")

        self.test_skill(
            "action-tracker",
            "Find overdue items",
            {
                "project_slug": PROJECT_SLUG,
                "check_type": "overdue"
            },
            expected_keys=["overdue_items"]
        )

    def test_project_status(self):
        """Test 10: Project Status - Health dashboard"""
        self.log("=== Testing Project Status Skill ===", "SECTION")

        self.test_skill(
            "project-status",
            "Get project health",
            {
                "project_slug": PROJECT_SLUG
            },
            expected_keys=["status", "health"]
        )

    def test_pm_heartbeat(self):
        """Test 11: PM Heartbeat - System health check"""
        self.log("=== Testing PM Heartbeat Skill ===", "SECTION")

        self.test_skill(
            "pm-heartbeat",
            "System health check",
            {
                "project_slug": PROJECT_SLUG
            },
            expected_keys=["health", "issues"]
        )

    def test_channel_digest(self):
        """Test 12: Channel Digest - Slack summary"""
        self.log("=== Testing Channel Digest Skill ===", "SECTION")

        self.test_skill(
            "channel-digest",
            "Digest Slack channel",
            {
                "project_slug": PROJECT_SLUG,
                "time_range": "24h"
            },
            expected_keys=["digest", "message_count"]
        )

    def test_notion_sync(self):
        """Test 13: Notion Sync - Multi-source updates with classification"""
        self.log("=== Testing Notion Sync Skill ===", "SECTION")

        # Test 13a: Item update (factual)
        self.test_skill(
            "notion-sync",
            "Item update (factual)",
            {
                "project_slug": PROJECT_SLUG,
                "mode": "item-update",
                "item_id": "E-999",
                "changes": "status: done",
                "dry_run": True
            },
            expected_keys=["updated"]
        )

        # Test 13b: Multi-source sync
        self.test_skill(
            "notion-sync",
            "Multi-source sync",
            {
                "project_slug": PROJECT_SLUG,
                "mode": "sync",
                "sources": ["slack"],
                "time_range": "24h",
                "dry_run": True
            },
            expected_keys=["items_extracted"]
        )

    def test_context_refresh(self):
        """Test 14: Context Refresh - Rebuild context file"""
        self.log("=== Testing Context Refresh Skill ===", "SECTION")

        self.test_skill(
            "context-refresh",
            "Rebuild context",
            {
                "project_slug": PROJECT_SLUG
            },
            expected_keys=["context_updated"]
        )

    def test_project_setup(self):
        """Test 15: Project Setup - Initialize new project"""
        self.log("=== Testing Project Setup Skill ===", "SECTION")

        self.test_skill(
            "project-setup",
            "Setup new project",
            {
                "project_slug": "test-project",
                "project_name": "Test Project",
                "dry_run": True  # Don't actually create
            },
            expected_keys=["setup_complete"]
        )

    def test_task_form_opener(self):
        """Test 16: Task Form Opener - Hybrid workflow entry (Phase 1)"""
        self.log("=== Testing Task Form Opener Skill ===", "SECTION")

        self.test_skill(
            "task-form-opener",
            "Open task creation modal",
            {
                "pre_fill": {
                    "title": "Test task",
                    "project": PROJECT_SLUG
                }
            },
            expected_keys=["type", "callback_id"]  # Slack modal JSON
        )

    def test_task_creator(self):
        """Test 17: Task Creator - Execute from modal (Phase 1)"""
        self.log("=== Testing Task Creator Skill ===", "SECTION")

        self.test_skill(
            "task-creator",
            "Create task from form",
            {
                "form_data": {
                    "title": {"value": "Test task creation"},
                    "description": {"value": "Testing hybrid workflow"},
                    "project": {"value": PROJECT_SLUG},
                    "assignee": {"value": "U123ABC"},
                    "priority": {"value": "high"}
                },
                "user": {"id": "U123", "name": "test-user"},
                "channel": "C456",
                "dry_run": True
            },
            expected_keys=["task_created"]
        )

    def test_intake(self):
        """Test 18: Intake - Universal entrypoint (Phase 2)"""
        self.log("=== Testing Intake Skill ===", "SECTION")

        # Test 18a: New message routing
        self.test_skill(
            "intake",
            "Route new message to triage",
            {
                "message": "What's the status of E-005?",
                "channel": "C123",
                "user": "U456",
                "ts": "1710428400.123456"
            },
            expected_keys=["action", "route"]
        )

    def run_all_tests(self):
        """Run all skill tests"""
        self.log("=" * 60, "HEADER")
        self.log("PM SKILLS COMPREHENSIVE TEST SUITE", "HEADER")
        self.log("=" * 60, "HEADER")

        # PR #10 Skills (15 skills)
        self.test_triage()              # 1
        self.test_meeting_update()      # 2
        self.test_meeting_scan()        # 3
        self.test_meeting_prep()        # 4
        self.test_pm_query()            # 5
        self.test_daily_briefing()      # 6
        self.test_daily_wrap()          # 7
        self.test_weekly_digest()       # 8
        self.test_action_tracker()      # 9
        self.test_project_status()      # 10
        self.test_pm_heartbeat()        # 11
        self.test_channel_digest()      # 12
        self.test_notion_sync()         # 13 (2 tests)
        self.test_context_refresh()     # 14
        self.test_project_setup()       # 15

        # New Skills (Phase 1-2)
        self.test_task_form_opener()    # 16
        self.test_task_creator()        # 17
        self.test_intake()              # 18

        # Summary
        self.print_summary()

    def print_summary(self):
        """Print test results summary"""
        self.log("=" * 60, "HEADER")
        self.log("TEST SUMMARY", "HEADER")
        self.log("=" * 60, "HEADER")
        self.log(f"Total Tests: {self.passed + self.failed}")
        self.log(f"✅ Passed: {self.passed}", "PASS")
        self.log(f"❌ Failed: {self.failed}", "FAIL")
        self.log(f"Success Rate: {self.passed / (self.passed + self.failed) * 100:.1f}%")

        # Failed tests detail
        if self.failed > 0:
            self.log("\n=== FAILED TESTS ===", "FAIL")
            for result in self.results:
                if result["status"] == "failed":
                    self.log(f"  • {result['skill']} - {result['test']}: {result.get('error', 'Unknown error')}", "FAIL")

        # Save results
        with open("test_results.json", "w") as f:
            json.dump({
                "timestamp": datetime.now().isoformat(),
                "total": self.passed + self.failed,
                "passed": self.passed,
                "failed": self.failed,
                "results": self.results
            }, f, indent=2)

        self.log(f"\nResults saved to: test_results.json")

        return self.failed == 0


if __name__ == "__main__":
    # Check gateway URL
    gateway_url = os.getenv("GATEWAY_URL", "http://localhost:3001")
    print(f"Testing against gateway: {gateway_url}")
    print(f"Set GATEWAY_URL env var to override")
    print()

    # Run tests
    tester = PMSkillsTester(gateway_url)
    success = tester.run_all_tests()

    sys.exit(0 if success else 1)
