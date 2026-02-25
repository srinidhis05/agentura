"""agentura correct <domain>/<name> — Capture correction and auto-generate tests."""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path

import click
from rich.console import Console
from rich.panel import Panel


@click.command()
@click.argument("skill_path")
@click.option("--execution-id", required=True, help="Execution ID to correct (from agentura run output).")
@click.option("--correction", required=True, help="What was wrong and what should it have been.")
@click.option(
    "--skills-dir",
    type=click.Path(exists=True),
    default=None,
    help="Root directory for skills.",
)
def correct(skill_path: str, execution_id: str, correction: str, skills_dir: str | None):
    if skills_dir is None:
        from agentura_sdk.cli.run import _find_skills_dir
        skills_dir = _find_skills_dir()
    """Capture a user correction and auto-generate regression tests.

    This is the learning loop (DEC-006): every correction becomes a test,
    a guardrail, and a reflexion entry that improves future executions.

    SKILL_PATH should be domain/skill-name, e.g. hr/interview-questions.
    """
    console = Console()

    parts = skill_path.strip("/").split("/")
    if len(parts) != 2:
        console.print("[red]Error: skill path must be domain/name[/]")
        raise SystemExit(1)

    domain, skill_name = parts
    skill_dir = Path(skills_dir) / domain / skill_name

    if not skill_dir.exists():
        console.print(f"[red]Error: skill not found at {skill_dir}[/]")
        raise SystemExit(1)

    # 1. Load the original execution from episodic memory
    execution = _load_execution(execution_id)
    if not execution:
        console.print(f"[red]Error: execution {execution_id} not found in episodic memory.[/]")
        console.print("[dim]Run a skill first with 'agentura run' to generate executions.[/]")
        raise SystemExit(1)

    console.print(Panel(f"[cyan]Processing correction for {skill_path}[/]\n"
                        f"Execution: {execution_id}\n"
                        f"Correction: {correction[:100]}{'...' if len(correction) > 100 else ''}"))

    # 2. Store correction
    correction_id = _store_correction(
        skill_path=skill_path,
        execution_id=execution_id,
        correction=correction,
        original_output=execution.get("output_summary", {}),
    )
    console.print(f"  [green]Correction stored:[/] {correction_id}")

    # 3. Generate reflexion entry
    reflexion_id = _generate_reflexion(
        skill_path=skill_path,
        correction_id=correction_id,
        original_output=execution.get("output_summary", {}),
        correction=correction,
        input_data=execution.get("input_summary"),
    )
    console.print(f"  [green]Reflexion entry:[/] {reflexion_id}")

    # 4. Auto-generate DeepEval test
    from agentura_sdk.testing.deepeval_runner import generate_test_from_correction

    deepeval_file = generate_test_from_correction(
        skill_dir=skill_dir,
        input_data=execution.get("input_summary", {}),
        actual_output=execution.get("output_summary", {}),
        corrected_output={"correction": correction},
    )
    console.print(f"  [green]DeepEval test:[/] {deepeval_file.relative_to(skill_dir)}")

    # 5. Auto-generate Promptfoo test
    from agentura_sdk.testing.test_generator import generate_promptfoo_test

    promptfoo_file = generate_promptfoo_test(
        skill_dir=skill_dir,
        input_data=execution.get("input_summary", {}),
        expected_output={"correction": correction},
        description=f"Correction {correction_id}: {correction[:80]}",
    )
    console.print(f"  [green]Promptfoo test:[/] {promptfoo_file.relative_to(skill_dir)}")

    # 6. Update GUARDRAILS.md
    guardrails_updated = _update_guardrails(skill_dir, correction)
    if guardrails_updated:
        console.print(f"  [green]GUARDRAILS.md:[/] updated with new anti-pattern")

    # Summary
    _print_summary(console, skill_path, correction_id, reflexion_id, deepeval_file, promptfoo_file)


def _load_execution(execution_id: str) -> dict | None:
    """Load an execution from episodic memory."""
    import os
    knowledge_dir = Path(os.environ.get("AGENTURA_KNOWLEDGE_DIR") or str(Path.cwd() / ".agentura"))
    memory_file = knowledge_dir / "episodic_memory.json"

    if not memory_file.exists():
        return None

    data = json.loads(memory_file.read_text())
    for entry in data.get("entries", []):
        if entry.get("execution_id") == execution_id:
            return entry
    return None


def _store_correction(skill_path: str, execution_id: str, correction: str, original_output: dict) -> str:
    """Store a correction in the knowledge layer. Returns correction_id.

    Idempotent: if a correction already exists for the same (skill, execution_id),
    returns the existing correction_id instead of creating a duplicate.
    """
    import os

    knowledge_dir = Path(os.environ.get("AGENTURA_KNOWLEDGE_DIR") or str(Path.cwd() / ".agentura"))
    knowledge_dir.mkdir(parents=True, exist_ok=True)
    corrections_file = knowledge_dir / "corrections.json"

    if corrections_file.exists():
        file_data = json.loads(corrections_file.read_text())
    else:
        file_data = {"corrections": []}

    # Idempotency: check for existing correction on same (skill, execution_id)
    for existing in file_data["corrections"]:
        if existing.get("skill") == skill_path and existing.get("execution_id") == execution_id:
            return existing["correction_id"]

    data = {
        "execution_id": execution_id,
        "skill": skill_path,
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "original_output": original_output,
        "user_correction": correction,
    }

    # Generate next correction ID based on max existing
    existing_ids = [c.get("correction_id", "") for c in file_data["corrections"]]
    max_idx = 0
    for cid in existing_ids:
        try:
            max_idx = max(max_idx, int(cid.split("-")[1]))
        except (IndexError, ValueError):
            pass
    correction_id = f"CORR-{max_idx + 1:03d}"
    data["correction_id"] = correction_id

    file_data["corrections"].append(data)
    corrections_file.write_text(json.dumps(file_data, indent=2))
    return correction_id


def _generate_reflexion(
    skill_path: str,
    correction_id: str,
    original_output: dict,
    correction: str,
    input_data: dict | None = None,
) -> str:
    """Generate a reflexion entry from the correction. Returns reflexion_id.

    Derives quality signals heuristically:
    - confidence: based on how different the original vs corrected outputs are
    - applies_when: extracted from input data keys and skill path
    - root_cause: summarized from the difference between original and correction
    """
    # Derive quality signals heuristically
    original_str = json.dumps(original_output, sort_keys=True) if original_output else ""
    confidence = _compute_confidence(original_str, correction)
    applies_when = _derive_applies_when(skill_path, input_data)
    root_cause = _derive_root_cause(original_output, correction)

    # Fallback: JSON files
    import os
    knowledge_dir = Path(os.environ.get("AGENTURA_KNOWLEDGE_DIR") or str(Path.cwd() / ".agentura"))
    knowledge_dir.mkdir(parents=True, exist_ok=True)
    reflexion_file = knowledge_dir / "reflexion_entries.json"

    if reflexion_file.exists():
        data = json.loads(reflexion_file.read_text())
    else:
        data = {"entries": []}

    # Idempotency: check for existing reflexion with same rule for same skill
    for existing in data.get("entries", []):
        if existing.get("skill") == skill_path and existing.get("rule") == correction:
            return existing["reflexion_id"]

    entry = {
        "correction_id": correction_id,
        "skill": skill_path,
        "created_at": datetime.now(timezone.utc).isoformat(),
        "mistake": f"Original output was incorrect. User correction: {correction}",
        "root_cause": root_cause,
        "rule": correction,
        "applies_when": applies_when,
        "confidence": confidence,
        "validated_by_test": False,
        "generated_test_ids": [],
    }

    # Generate next reflexion ID based on max existing
    existing_ids = [e.get("reflexion_id", "") for e in data["entries"]]
    max_idx = 0
    for rid in existing_ids:
        try:
            max_idx = max(max_idx, int(rid.split("-")[1]))
        except (IndexError, ValueError):
            pass
    reflexion_id = f"REFL-{max_idx + 1:03d}"
    entry["reflexion_id"] = reflexion_id

    data["entries"].append(entry)
    reflexion_file.write_text(json.dumps(data, indent=2))
    return reflexion_id


def _compute_confidence(original_str: str, correction: str) -> float:
    """Derive confidence from string similarity between original and correction.

    High divergence = high confidence the correction matters.
    Low divergence = lower confidence (minor tweak).
    """
    if not original_str:
        return 0.9  # No original to compare = trust the correction

    # Simple Jaccard similarity on word sets
    orig_words = set(original_str.lower().split())
    corr_words = set(correction.lower().split())
    if not orig_words and not corr_words:
        return 0.5
    intersection = orig_words & corr_words
    union = orig_words | corr_words
    similarity = len(intersection) / len(union) if union else 0.0

    # High similarity = minor correction = lower confidence
    # Low similarity = major correction = higher confidence
    confidence = round(0.5 + (1 - similarity) * 0.5, 2)
    return min(max(confidence, 0.5), 1.0)


def _derive_applies_when(skill_path: str, input_data: dict | None) -> str:
    """Extract specific conditions from input data for applies_when."""
    parts = []
    parts.append(f"When executing {skill_path}")

    if input_data:
        # Extract meaningful input keys as conditions
        key_conditions = []
        for key, value in input_data.items():
            if isinstance(value, str) and len(value) < 100:
                key_conditions.append(f"{key}='{value}'")
            elif isinstance(value, (int, float, bool)):
                key_conditions.append(f"{key}={value}")
            else:
                key_conditions.append(f"{key} is provided")
        if key_conditions:
            parts.append(f"with inputs where {', '.join(key_conditions[:5])}")

    return " ".join(parts) + "."


def _derive_root_cause(original_output: dict, correction: str) -> str:
    """Summarize root cause from the difference."""
    if not original_output:
        return "Original output was empty or missing."

    # Check for common correction patterns
    correction_lower = correction.lower()
    if any(w in correction_lower for w in ["wrong", "incorrect", "error", "mistake"]):
        return "Model produced factually incorrect output."
    if any(w in correction_lower for w in ["missing", "omit", "forgot", "should include"]):
        return "Model omitted required information from output."
    if any(w in correction_lower for w in ["format", "structure", "schema"]):
        return "Model output had incorrect format or structure."
    if any(w in correction_lower for w in ["instead", "should be", "not", "rather"]):
        return "Model chose wrong approach or value."

    return "Model output did not match domain expectations."


def _update_guardrails(skill_dir: Path, correction: str) -> bool:
    """Append a guardrail to the domain's GUARDRAILS.md."""
    domain_dir = skill_dir.parent
    guardrails_file = domain_dir / "GUARDRAILS.md"

    if not guardrails_file.exists():
        return False

    content = guardrails_file.read_text()

    # Find the next GRD number
    import re
    existing = re.findall(r"GRD-(\d+)", content)
    next_num = max((int(n) for n in existing), default=0) + 1

    new_guardrail = f"""
---

## GRD-{next_num:03d}: Auto-generated from correction

**Mistake**: Agent produced incorrect output.
**Impact**: User had to manually correct.
**Rule**: {correction}
**Detection**: Auto-generated — review and refine this guardrail.
"""

    # Insert before "## When to Add New Guardrails" if it exists
    marker = "## When to Add New Guardrails"
    if marker in content:
        content = content.replace(marker, new_guardrail + "\n" + marker)
    else:
        content += new_guardrail

    guardrails_file.write_text(content)
    return True


def _print_summary(console, skill_path, correction_id, reflexion_id, deepeval_file, promptfoo_file):
    """Print a summary of everything generated."""
    console.print()
    console.print(Panel(
        f"[green bold]Correction pipeline complete[/]\n\n"
        f"  Correction: {correction_id}\n"
        f"  Reflexion:  {reflexion_id}\n"
        f"  DeepEval:   {deepeval_file.name}\n"
        f"  Promptfoo:  {promptfoo_file.name}\n"
        f"  Guardrails: updated\n\n"
        f"[dim]Next: Run the skill again to see improvement:[/]\n"
        f"  agentura run {skill_path}\n\n"
        f"[dim]Run tests to verify:[/]\n"
        f"  agentura test {skill_path}",
        title="Learning Loop (DEC-006)",
    ))
