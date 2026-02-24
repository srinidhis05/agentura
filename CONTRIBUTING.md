# Contributing to Agentura

Thanks for your interest in contributing! Here's how to get started.

## Development Setup

```bash
# Clone the repo
git clone https://github.com/agentura-ai/agentura.git
cd agentura

# Python SDK
cd sdk && pip install -e ".[dev,test,server]"

# Go Gateway
cd gateway && go build ./...

# Next.js Dashboard
cd web && npm ci && npm run dev
```

## Making Changes

1. Fork the repo and create a feature branch from `main`
2. Make your changes with tests
3. Run the test suite: `make test`
4. Commit using [conventional commits](https://www.conventionalcommits.org/): `feat:`, `fix:`, `refactor:`, `docs:`, `test:`, `chore:`
5. Open a PR against `main`

## Pull Request Guidelines

- Keep PRs focused — one feature or fix per PR
- Include tests for new functionality
- Update docs if behavior changes
- Ensure CI passes before requesting review

## Skill Contributions

Skills are Markdown files — no code required. See [docs/skill-format.md](docs/skill-format.md) for the format.

```bash
# Create a new skill
agentura create skill <domain>/<skill-name>

# Validate it
agentura validate <domain>/<skill-name>

# Run it
agentura run <domain>/<skill-name> --dry-run
```

## Reporting Issues

Use [GitHub Issues](https://github.com/agentura-ai/agentura/issues). Include:
- Steps to reproduce
- Expected vs actual behavior
- Environment details (OS, Python/Go/Node version)

## Code of Conduct

This project follows the [Contributor Covenant](CODE_OF_CONDUCT.md). Be kind.
