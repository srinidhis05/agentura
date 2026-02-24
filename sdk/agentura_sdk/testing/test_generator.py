"""Generate tests from skill corrections and execution history."""

import json
from pathlib import Path

from rich.console import Console


def generate_promptfoo_test(
    skill_dir: Path,
    input_data: dict,
    expected_output: dict,
    description: str = "Generated from correction",
) -> Path:
    """Append a test case to the promptfoo config from a correction."""
    console = Console()
    generated_dir = skill_dir / "tests" / "generated"
    generated_dir.mkdir(parents=True, exist_ok=True)

    test_file = generated_dir / "corrections.yaml"

    # Build the test case
    test_case = {
        "description": description,
        "vars": {"input": json.dumps(input_data)},
        "assert": [
            {"type": "is-json"},
            {"type": "similar", "value": json.dumps(expected_output), "threshold": 0.8},
        ],
    }

    # Append to existing or create new
    import yaml

    if test_file.exists():
        existing = yaml.safe_load(test_file.read_text()) or {}
    else:
        existing = {
            "description": f"Generated regression tests for {skill_dir.name}",
            "tests": [],
        }

    existing.setdefault("tests", []).append(test_case)
    test_file.write_text(yaml.dump(existing, default_flow_style=False))

    console.print(f"[green]Added test case to {test_file}[/]")
    return test_file
