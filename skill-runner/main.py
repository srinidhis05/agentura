"""One-shot skill runner for isolated container execution.

Reads an execution request from stdin (JSON) or EXECUTION_REQUEST env var,
runs the skill via existing execute_skill(), writes result to stdout as JSON.

Exit codes: 0 = success, 1 = skill error, 2 = infra error.
"""

import asyncio
import json
import os
import sys


def read_request() -> dict:
    """Read execution request from env var or stdin."""
    env_req = os.environ.get("EXECUTION_REQUEST")
    if env_req:
        return json.loads(env_req)

    if not sys.stdin.isatty():
        data = sys.stdin.read().strip()
        if data:
            return json.loads(data)

    raise RuntimeError("no execution request: set EXECUTION_REQUEST env or pipe JSON to stdin")


async def run() -> int:
    """Execute skill and return exit code."""
    try:
        request = read_request()
    except (json.JSONDecodeError, RuntimeError) as e:
        json.dump({"error": str(e), "type": "infra"}, sys.stderr)
        return 2

    domain = request.get("domain", "")
    skill_name = request.get("skill", "")
    role = request.get("role", "specialist")
    model = request.get("model", "anthropic/claude-sonnet-4.5")
    message = request.get("message", "")
    parameters = request.get("parameters", {})
    system_prompt = request.get("system_prompt", "")

    try:
        from agentura_sdk.types import SkillContext, SkillRole

        role_enum = SkillRole(role)
        ctx = SkillContext(
            skill_name=skill_name,
            domain=domain,
            role=role_enum,
            model=model,
            system_prompt=system_prompt,
            input_data={"message": message, **parameters},
        )

        from agentura_sdk.runner.local_runner import execute_skill

        result = await execute_skill(ctx)

        json.dump(result.model_dump(), sys.stdout)
        sys.stdout.write("\n")
        sys.stdout.flush()

        return 0 if result.success else 1

    except Exception as e:
        json.dump({
            "skill_name": skill_name,
            "success": False,
            "output": {"error": str(e)},
            "type": "infra",
        }, sys.stdout)
        sys.stdout.write("\n")
        sys.stdout.flush()
        return 2


def main():
    exit_code = asyncio.run(run())
    sys.exit(exit_code)


if __name__ == "__main__":
    main()
