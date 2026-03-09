# Agency

Agent configurations for the Agentura platform.

## Structure

```
agency/
  agents.yaml           # Global agent registry (auto-generated)
  {domain}/
    {agent-name}/
      agent.yaml        # Agent config (role, executor, skills, budget)
      SOUL.md           # Agent personality and behavior
      HEARTBEAT.md      # Scheduled task definitions
```

## Creating Agents

```bash
agentura create agent --role manager --executor claude-code --model anthropic/claude-sonnet-4-5-20250929 my-agent
```

## Using Your Own Agents

Point `AGENCY_DIR` to your own agency directory:

```bash
export AGENCY_DIR=~/my-workspace/agency
```
