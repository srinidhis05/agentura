"""Tests for Cortex CLI command module."""

from pathlib import Path

from click.testing import CliRunner

from agentura_sdk.cli.cortex_cmd import (
    _build_interview_system_prompt,
    _extract_frontmatter_field,
    _gather_skills_context,
    _load_cortex_skill,
    _parse_interview_spec,
    cortex,
)


def test_cortex_help():
    runner = CliRunner()
    result = runner.invoke(cortex, ["--help"])
    assert result.exit_code == 0
    assert "Interactive skill creation wizard" in result.output


def test_cortex_existing_skill(tmp_path):
    """Cortex should fail if skill already exists."""
    (tmp_path / "hr" / "existing").mkdir(parents=True)
    runner = CliRunner()
    result = runner.invoke(
        cortex, ["--skills-dir", str(tmp_path), "--quick"], input="hr\nexisting\n",
    )
    assert result.exit_code == 1


def test_cortex_quick_flag_shows_in_help():
    runner = CliRunner()
    result = runner.invoke(cortex, ["--help"])
    assert "--quick" in result.output


# ---------------------------------------------------------------------------
# _gather_skills_context
# ---------------------------------------------------------------------------

def test_gather_skills_context_empty(tmp_path):
    """Empty skills dir returns 'no skills' message."""
    result = _gather_skills_context(tmp_path)
    # No domain dirs → only header
    assert "Existing Skills" in result


def test_gather_skills_context_with_skills(tmp_path):
    """Finds domains and skills from directory structure."""
    # Create hr/interview-questions with a minimal SKILL.md
    skill_dir = tmp_path / "hr" / "interview-questions"
    skill_dir.mkdir(parents=True)
    (skill_dir / "SKILL.md").write_text(
        "---\nname: interview-questions\nrole: specialist\ndomain: hr\n---\n# Interview Questions\n"
    )

    # Create hr/DOMAIN.md
    (tmp_path / "hr" / "DOMAIN.md").write_text("# HR Domain\nHuman resources.")

    result = _gather_skills_context(tmp_path)
    assert "hr" in result
    assert "interview-questions" in result
    assert "specialist" in result


def test_gather_skills_context_nonexistent_dir():
    """Nonexistent path returns fallback message."""
    result = _gather_skills_context(Path("/nonexistent/path"))
    assert "No existing skills found" in result


def test_gather_skills_context_collects_examples(tmp_path):
    """Collects up to 2 example SKILL.md excerpts."""
    for i in range(3):
        skill_dir = tmp_path / "domain" / f"skill-{i}"
        skill_dir.mkdir(parents=True)
        (skill_dir / "SKILL.md").write_text(
            f"---\nname: skill-{i}\nrole: specialist\n---\n# Skill {i}\nContent.\n"
        )

    result = _gather_skills_context(tmp_path)
    assert result.count("### Example:") == 2  # max 2


# ---------------------------------------------------------------------------
# _extract_frontmatter_field
# ---------------------------------------------------------------------------

def test_extract_frontmatter_field(tmp_path):
    skill_md = tmp_path / "SKILL.md"
    skill_md.write_text("---\nname: test\nrole: specialist\ndomain: hr\n---\n# Test\n")

    assert _extract_frontmatter_field(skill_md, "role") == "specialist"
    assert _extract_frontmatter_field(skill_md, "name") == "test"
    assert _extract_frontmatter_field(skill_md, "missing") is None


def test_extract_frontmatter_field_no_frontmatter(tmp_path):
    skill_md = tmp_path / "SKILL.md"
    skill_md.write_text("# Just a heading\nNo frontmatter here.")

    assert _extract_frontmatter_field(skill_md, "role") is None


def test_extract_frontmatter_field_missing_file(tmp_path):
    assert _extract_frontmatter_field(tmp_path / "nope.md", "role") is None


# ---------------------------------------------------------------------------
# _parse_interview_spec
# ---------------------------------------------------------------------------

def test_parse_interview_spec_valid():
    response = """Based on our conversation, here's the spec:

```json
{
  "domain": "hr",
  "skill_name": "refund-checker",
  "role": "field",
  "description": "Checks refund eligibility for stuck orders",
  "model": "anthropic/claude-sonnet-4.5",
  "input_fields": ["order_id"],
  "output_fields": ["eligible", "reason"],
  "guardrails": ["Never auto-approve refunds over $500"]
}
```

This should fit well in the hr domain."""

    spec = _parse_interview_spec(response)
    assert spec is not None
    assert spec["domain"] == "hr"
    assert spec["skill_name"] == "refund-checker"
    assert spec["role"] == "field"
    assert "order_id" in spec["input_fields"]


def test_parse_interview_spec_no_json():
    """Returns None when response has no JSON block."""
    response = "Let me ask you another question: who will use this skill?"
    assert _parse_interview_spec(response) is None


def test_parse_interview_spec_incomplete_json():
    """Returns None when JSON is missing required fields."""
    response = """```json
{"domain": "hr"}
```"""
    assert _parse_interview_spec(response) is None


def test_parse_interview_spec_invalid_json():
    """Returns None for malformed JSON."""
    response = """```json
{not valid json}
```"""
    assert _parse_interview_spec(response) is None


# ---------------------------------------------------------------------------
# _build_interview_system_prompt
# ---------------------------------------------------------------------------

def test_build_interview_system_prompt(tmp_path):
    """System prompt includes skills context."""
    skill_dir = tmp_path / "hr" / "leave-policy"
    skill_dir.mkdir(parents=True)
    (skill_dir / "SKILL.md").write_text(
        "---\nname: leave-policy\nrole: specialist\n---\n# Leave Policy\n"
    )

    prompt = _build_interview_system_prompt(tmp_path)
    assert "hr" in prompt
    assert "leave-policy" in prompt
    assert "```json" in prompt  # completion signal format


def test_build_interview_prompt_uses_skill_when_present(tmp_path):
    """When cortex-interviewer skill exists, prompt loads from SKILL.md."""
    # Create the cortex-interviewer skill
    skill_dir = tmp_path / "platform" / "cortex-interviewer"
    skill_dir.mkdir(parents=True)
    (skill_dir / "SKILL.md").write_text(
        "---\nname: cortex-interviewer\nrole: specialist\n"
        "domain: platform\nmodel: anthropic/claude-haiku-4.5\n---\n"
        "# Cortex Interviewer\n\nLoaded from skill file.\n\n"
        "{skills_context}\n\n{domain_context}\n"
    )

    prompt = _build_interview_system_prompt(tmp_path)
    assert "Loaded from skill file" in prompt


# ---------------------------------------------------------------------------
# _load_cortex_skill
# ---------------------------------------------------------------------------

def test_load_cortex_skill_success(tmp_path):
    """Loads a cortex skill and composes SKILL body."""
    skill_dir = tmp_path / "platform" / "cortex-generator"
    skill_dir.mkdir(parents=True)
    (skill_dir / "SKILL.md").write_text(
        "---\nname: cortex-generator\nrole: specialist\n"
        "domain: platform\nmodel: anthropic/claude-sonnet-4.5\n---\n"
        "# Generator\n\nGenerate skills.\n\n{skills_context}\n"
    )

    result = _load_cortex_skill(tmp_path, "cortex-generator")
    assert result is not None
    assert "Generate skills" in result


def test_load_cortex_skill_missing(tmp_path):
    """Returns None when skill directory doesn't exist."""
    result = _load_cortex_skill(tmp_path, "cortex-nonexistent")
    assert result is None


def test_load_cortex_skill_includes_workspace(tmp_path):
    """Composes WORKSPACE.md context when present."""
    # WORKSPACE.md at skills root
    (tmp_path / "WORKSPACE.md").write_text("PII: never log customer data.")

    skill_dir = tmp_path / "platform" / "cortex-refiner"
    skill_dir.mkdir(parents=True)
    (skill_dir / "SKILL.md").write_text(
        "---\nname: cortex-refiner\nrole: specialist\n"
        "domain: platform\nmodel: anthropic/claude-sonnet-4.5\n---\n"
        "# Refiner\n\nRefine skills.\n"
    )

    result = _load_cortex_skill(tmp_path, "cortex-refiner")
    assert result is not None
    assert "PII" in result
    assert "Refine skills" in result


def test_load_cortex_skill_includes_domain(tmp_path):
    """Composes DOMAIN.md context when present."""
    domain_dir = tmp_path / "platform"
    domain_dir.mkdir(parents=True)
    (domain_dir / "DOMAIN.md").write_text("Platform domain handles routing.")

    skill_dir = domain_dir / "cortex-interviewer"
    skill_dir.mkdir(parents=True)
    (skill_dir / "SKILL.md").write_text(
        "---\nname: cortex-interviewer\nrole: specialist\n"
        "domain: platform\nmodel: anthropic/claude-haiku-4.5\n---\n"
        "# Interviewer\n\nInterview users.\n"
    )

    result = _load_cortex_skill(tmp_path, "cortex-interviewer")
    assert result is not None
    assert "Platform domain handles routing" in result
    assert "Interview users" in result
