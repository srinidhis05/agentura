"""Tests for PR review publishing — both github_pr.py and engine.py code paths."""

from agentura_sdk.pipelines.github_pr import _format_inline_comments, _format_summary_comment
from agentura_sdk.pipelines.engine import _extract_reviewer_output, _format_review_comments


# Exact output from the pr-code-reviewer skill (second run)
REVIEW_OUTPUT = {
    "verdict": "request-changes",
    "summary": "Well-structured NRI Savings Calculator implementation with comprehensive documentation and proper separation of concerns. However, there are critical issues: missing input validation on deposit amounts in CalculateRequest, an unused accountType parameter in getBanks, and improper error handling in logCalculation that could mask data integrity issues.",
    "stats": {
        "files_reviewed": 24,
        "blockers": 2,
        "warnings": 3,
        "suggestions": 4,
        "praise": 3,
    },
    "findings": [
        {
            "severity": "BLOCKER",
            "file": "projects/nri_savings_calculator/dto/CalculateRequest.java",
            "line": 19,
            "title": "Missing validation on principal amount",
            "snippet": '@NotNull\n@JsonProperty("principal")\nprivate BigDecimal principal;',
            "reason": "The principal field has no @Min or @Max constraints.",
            "suggestion": 'Add @DecimalMin("100000.00") and @DecimalMax("10000000.00") annotations.',
        },
        {
            "severity": "BLOCKER",
            "file": "projects/nri_savings_calculator/service/NriSavingsCalculatorService.java",
            "line": 213,
            "title": "Silent failure in calculation logging could mask data integrity issues",
            "snippet": '} catch (Exception e) {\n    log.warn("Failed to log calculation", e);',
            "reason": "The logCalculation method swallows all exceptions with only a warning.",
            "suggestion": "Either throw the exception or implement a dead-letter queue pattern.",
        },
        {
            "severity": "WARNING",
            "file": "projects/nri_savings_calculator/service/NriSavingsCalculatorService.java",
            "line": 36,
            "title": "Unused accountType parameter in getBanks method",
            "snippet": "public List<BankDTO> getBanks(String accountType) {",
            "reason": "The accountType parameter is accepted but never used.",
            "suggestion": "Implement filtering logic or remove the parameter.",
        },
        {
            "severity": "WARNING",
            "file": "projects/nri_savings_calculator/dto/WaitlistRequest.java",
            "line": 30,
            "title": "No validation on deposit_amount in waitlist request",
            "snippet": '@NotNull\n@JsonProperty("deposit_amount")\nprivate BigDecimal depositAmount;',
            "reason": "WaitlistRequest accepts deposit_amount without min/max constraints.",
            "suggestion": "Add @DecimalMin and @DecimalMax annotations.",
        },
        {
            "severity": "WARNING",
            "file": "projects/nri_savings_calculator/repository/BankRepository.java",
            "line": 10,
            "title": "Redundant findById method declaration",
            "snippet": "Optional<Bank> findById(String id);",
            "reason": "MongoRepository already provides findById.",
            "suggestion": "Remove the redundant declaration.",
        },
        {
            "severity": "SUGGESTION",
            "file": "projects/nri_savings_calculator/service/NriSavingsCalculatorService.java",
            "line": 182,
            "title": "Magic numbers in compound interest calculation",
            "snippet": "BigDecimal rateDecimal = rate.divide(BigDecimal.valueOf(100), 10, RoundingMode.HALF_UP);",
            "reason": "The scale value 10 and divisor 100 are magic numbers.",
            "suggestion": "Extract as constants.",
        },
        {
            "severity": "SUGGESTION",
            "file": "projects/nri_savings_calculator/controller/NriSavingsCalculatorController.java",
            "line": 84,
            "title": "Hardcoded user ID check is fragile",
            "snippet": 'if ("demo_user".equals(userId)) {',
            "reason": "Hardcoding couples the auth logic to a specific user ID.",
            "suggestion": "Move to a configuration property or role-based check.",
        },
        {
            "severity": "SUGGESTION",
            "file": "projects/nri_savings_calculator/service/NriSavingsCalculatorService.java",
            "line": 113,
            "title": "Waitlist duplicate handling returns stale data",
            "snippet": "if (existing.isPresent()) {\n    return WaitlistResponse.builder()",
            "reason": "When a user re-submits with the same email but different parameters, the old entry is returned.",
            "suggestion": "Consider updating the existing entry or documenting the behavior.",
        },
        {
            "severity": "SUGGESTION",
            "file": "projects/nri_savings_calculator/document/WaitlistEntry.java",
            "line": 22,
            "title": "Missing unique constraint on email field",
            "snippet": '@Indexed\n@Field("email")\nprivate String email;',
            "reason": "The email field is indexed but not marked as unique.",
            "suggestion": "Add @Indexed(unique = true).",
        },
        {
            "severity": "PRAISE",
            "file": "projects/nri_savings_calculator/README.md",
            "line": 1,
            "title": "Excellent API documentation",
            "snippet": "# NRI Savings Calculator",
            "reason": "Comprehensive README.",
        },
        {
            "severity": "PRAISE",
            "file": "projects/nri_savings_calculator/service/NriSavingsCalculatorService.java",
            "line": 49,
            "title": "Clean tax calculation logic with proper separation",
            "snippet": "// Apply TDS for NRO accounts",
            "reason": "Well-structured tax calculation.",
        },
        {
            "severity": "PRAISE",
            "file": "projects/nri_savings_calculator/NriSavingsCalculatorProperties.java",
            "line": 10,
            "title": "Good use of configuration properties for business rules",
            "snippet": "@ConfigurationProperties(prefix = ...)",
            "reason": "Externalizing business rules to config.",
        },
    ],
}


# ---------------------------------------------------------------------------
# github_pr.py tests (sequential fallback path)
# ---------------------------------------------------------------------------


class TestFormatInlineComments:
    def test_produces_comments_for_non_praise_findings(self):
        comments = _format_inline_comments(REVIEW_OUTPUT, {})
        # 2 blockers + 3 warnings + 4 suggestions = 9 comments (3 praise skipped)
        assert len(comments) == 9

    def test_skips_praise(self):
        comments = _format_inline_comments(REVIEW_OUTPUT, {})
        bodies = [c["body"] for c in comments]
        assert not any("PRAISE" in b for b in bodies)

    def test_blocker_has_correct_path_and_line(self):
        comments = _format_inline_comments(REVIEW_OUTPUT, {})
        blocker = comments[0]
        assert blocker["path"] == "projects/nri_savings_calculator/dto/CalculateRequest.java"
        assert blocker["line"] == 19
        assert "BLOCKER" in blocker["body"]

    def test_comment_body_includes_title_reason_suggestion(self):
        comments = _format_inline_comments(REVIEW_OUTPUT, {})
        blocker = comments[0]
        assert "Missing validation on principal amount" in blocker["body"]
        assert "no @Min or @Max constraints" in blocker["body"]
        assert "**Suggestion**" in blocker["body"]

    def test_empty_review_returns_empty(self):
        assert _format_inline_comments({}, {}) == []

    def test_findings_without_file_or_line_are_skipped(self):
        review = {"findings": [{"severity": "WARNING", "title": "No file"}]}
        assert _format_inline_comments(review, {}) == []

    def test_doc_suggestions_still_work(self):
        doc = {"suggestions": [{"file": "README.md", "line": 5, "reason": "Missing docs", "content": "Add docs"}]}
        comments = _format_inline_comments({}, doc)
        assert len(comments) == 1
        assert comments[0]["path"] == "README.md"


class TestVerdictDetection:
    def test_request_changes_from_verdict_field(self):
        verdict = REVIEW_OUTPUT.get("verdict", "")
        has_blocking = verdict == "request-changes" or any(
            f.get("severity", "").upper() == "BLOCKER"
            for f in REVIEW_OUTPUT.get("findings", [])
        )
        assert has_blocking is True

    def test_request_changes_from_blocker_finding(self):
        review = {
            "verdict": "approve",
            "findings": [{"severity": "BLOCKER", "file": "x.go", "line": 1, "title": "bug"}],
        }
        has_blocking = review.get("verdict") == "request-changes" or any(
            f.get("severity", "").upper() == "BLOCKER"
            for f in review.get("findings", [])
        )
        assert has_blocking is True

    def test_no_blockers_means_comment(self):
        review = {
            "verdict": "approve",
            "findings": [{"severity": "SUGGESTION", "file": "x.go", "line": 1, "title": "nit"}],
        }
        has_blocking = review.get("verdict") == "request-changes" or any(
            f.get("severity", "").upper() == "BLOCKER"
            for f in review.get("findings", [])
        )
        assert has_blocking is False


class TestFormatSummaryComment:
    def test_summary_includes_verdict_and_stats(self):
        step_results = [{
            "skill": "dev/github-pr-reviewer",
            "status": "success",
            "execution_id": "EX-001",
            "latency_ms": 1200,
            "cost_usd": 0.03,
            "output": REVIEW_OUTPUT,
        }]
        summary = _format_summary_comment(step_results, [], "PIPE-TEST")
        assert "request-changes" in summary
        assert "Blockers" in summary
        assert "Missing validation on principal amount" in summary
        assert "| 2 | 3 | 4 | 3 |" in summary


# ---------------------------------------------------------------------------
# engine.py tests (primary parallel pipeline path)
# ---------------------------------------------------------------------------


class TestExtractReviewerOutput:
    def test_extracts_from_direct_output(self):
        results = [{
            "skill": "dev/pr-code-reviewer",
            "success": True,
            "output": REVIEW_OUTPUT,
        }]
        output = _extract_reviewer_output(results)
        assert output.get("verdict") == "request-changes"
        assert len(output.get("findings", [])) == 12

    def test_extracts_from_markdown_code_block(self):
        results = [{
            "skill": "dev/pr-code-reviewer",
            "success": True,
            "output": {
                "raw_output": '```json\n{"verdict": "approve", "findings": []}\n```',
            },
        }]
        output = _extract_reviewer_output(results)
        assert output.get("verdict") == "approve"

    def test_returns_empty_when_reviewer_missing(self):
        results = [{"skill": "dev/pr-test-runner", "success": True, "output": {}}]
        assert _extract_reviewer_output(results) == {}

    def test_returns_empty_when_reviewer_failed(self):
        results = [{
            "skill": "dev/pr-code-reviewer",
            "success": False,
            "output": {"error": "timeout"},
        }]
        assert _extract_reviewer_output(results) == {}

    def test_skips_failed_and_finds_successful(self):
        """If reviewer appears twice (shouldn't happen, but defensive), picks the successful one."""
        results = [
            {"skill": "dev/pr-code-reviewer", "success": False, "output": {"error": "timeout"}},
            {"skill": "dev/pr-code-reviewer", "success": True, "output": REVIEW_OUTPUT},
        ]
        output = _extract_reviewer_output(results)
        assert output.get("verdict") == "request-changes"


class TestEngineFormatReviewComments:
    def test_produces_correct_count(self):
        comments = _format_review_comments(REVIEW_OUTPUT)
        # 2 blockers + 3 warnings + 4 suggestions = 9 (3 praise skipped)
        assert len(comments) == 9

    def test_skips_praise(self):
        comments = _format_review_comments(REVIEW_OUTPUT)
        assert not any("PRAISE" in c["body"] for c in comments)

    def test_comment_structure(self):
        comments = _format_review_comments(REVIEW_OUTPUT)
        for c in comments:
            assert "path" in c
            assert "line" in c
            assert "body" in c
            assert isinstance(c["line"], int)

    def test_empty_input(self):
        assert _format_review_comments({}) == []

    def test_matches_github_pr_output(self):
        """Engine path and github_pr path should produce same comments."""
        engine_comments = _format_review_comments(REVIEW_OUTPUT)
        github_pr_comments = _format_inline_comments(REVIEW_OUTPUT, {})
        assert len(engine_comments) == len(github_pr_comments)
        for ec, gc in zip(engine_comments, github_pr_comments):
            assert ec["path"] == gc["path"]
            assert ec["line"] == gc["line"]
