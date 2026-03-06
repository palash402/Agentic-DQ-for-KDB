# CLAUDE.md — Agentic DQ for KDB

This file provides guidance for AI assistants (Claude and others) working in this repository. It documents the project's purpose, architecture, conventions, and development workflows.

---

## Project Overview

**Agentic-DQ-for-KDB** is an AI-agent-driven **Data Quality (DQ)** framework targeting **KDB+/q** databases. The project aims to automate data quality checks, anomaly detection, validation pipelines, and corrective workflows using agentic LLM patterns — primarily powered by the Anthropic Claude API.

### Goals
- Automatically profile, validate, and monitor data stored in KDB+/q
- Use LLM agents to interpret DQ failures, generate corrective SQL/q queries, and escalate issues
- Provide a reusable, extensible framework for defining DQ rules declaratively
- Support both batch and streaming (tick) KDB+ architectures

---

## Repository State

> **Status: Early-stage / skeleton.** As of the initial commit, only `README.md` and `LICENSE` exist. Source code, configuration, and tests are yet to be added. This CLAUDE.md serves as the authoritative guide for how the project should be structured as it evolves.

---

## Expected Technology Stack

| Layer | Technology |
|---|---|
| Database | KDB+/q (kdb+ process, qIPC) |
| Agent framework | Anthropic Claude API (claude-sonnet-4-6 or claude-opus-4-6) |
| Primary language | Python 3.11+ |
| KDB+ Python bridge | `pykx` (preferred) or `qpython` |
| Config | YAML / TOML |
| Testing | `pytest` |
| Linting | `ruff`, `mypy` |
| Packaging | `pyproject.toml` / `uv` or `pip` |
| CI | GitHub Actions |

---

## Intended Directory Structure

When source code is added, follow this layout:

```
Agentic-DQ-for-KDB/
├── CLAUDE.md                   # This file
├── README.md                   # User-facing overview
├── LICENSE                     # Apache 2.0
├── pyproject.toml              # Python project config & dependencies
├── .env.example                # Template for required env vars (never commit .env)
├── .gitignore
│
├── src/
│   └── agentic_dq/             # Main Python package
│       ├── __init__.py
│       ├── agent/              # LLM agent logic
│       │   ├── __init__.py
│       │   ├── dq_agent.py     # Main DQ agent entry point
│       │   ├── tools.py        # Agent tool definitions (function calling)
│       │   └── prompts.py      # System/user prompt templates
│       ├── kdb/                # KDB+ integration layer
│       │   ├── __init__.py
│       │   ├── connection.py   # KDB+ connection management
│       │   ├── query.py        # q query builders and executors
│       │   └── schema.py       # Table schema introspection
│       ├── rules/              # DQ rule definitions
│       │   ├── __init__.py
│       │   ├── base.py         # Abstract rule base class
│       │   ├── completeness.py # Null/missing checks
│       │   ├── freshness.py    # Data recency checks
│       │   ├── consistency.py  # Cross-column/table consistency
│       │   └── custom.py       # User-defined rules
│       ├── pipeline/           # Orchestration
│       │   ├── __init__.py
│       │   ├── runner.py       # DQ pipeline runner
│       │   └── scheduler.py    # Cron/event-based scheduling
│       └── reporting/          # Output and alerting
│           ├── __init__.py
│           ├── report.py       # DQ report generation
│           └── alerts.py       # Alert dispatching (Slack, email, etc.)
│
├── q/                          # KDB+/q scripts
│   ├── init.q                  # Startup / bootstrapping script
│   ├── dq_checks.q             # Native q DQ check functions
│   └── utils.q                 # Shared q utilities
│
├── config/
│   ├── rules.yaml              # Declarative DQ rule definitions
│   └── connections.yaml        # KDB+ connection profiles (no credentials)
│
├── tests/
│   ├── conftest.py             # Shared pytest fixtures
│   ├── unit/
│   │   ├── test_rules.py
│   │   ├── test_agent.py
│   │   └── test_kdb_query.py
│   └── integration/
│       └── test_pipeline.py    # Requires live KDB+ instance
│
├── scripts/
│   └── run_dq.py              # CLI entry point
│
└── .github/
    └── workflows/
        ├── ci.yml             # Run tests and lint on PRs
        └── release.yml        # Publish releases
```

---

## Development Workflow

### Branch Conventions

- `main` — stable, production-ready code
- `master` — legacy default (treat same as `main` until unified)
- `claude/<description>-<session-id>` — AI-assisted development branches
- `feature/<ticket-or-description>` — human feature branches
- `fix/<description>` — bug fix branches

Always develop on feature branches, never commit directly to `main`/`master`.

### Commit Messages

Use the imperative mood with a short subject line (≤72 chars). Include a body when the change needs explanation:

```
Add completeness rule for null-ratio threshold

Implements DQRule subclass that flags columns exceeding a configurable
null percentage. Tested against mock KDB+ table fixtures.
```

Avoid vague messages like "fix stuff" or "update code".

### Git Push Protocol

```bash
git push -u origin <branch-name>
```

- Branch names starting with `claude/` must end with the matching session ID
- Retry up to 4 times on network failure with exponential backoff (2s, 4s, 8s, 16s)

---

## Environment Setup

### Required Environment Variables

```bash
# Anthropic API
ANTHROPIC_API_KEY=sk-ant-...

# KDB+ Connection
KDB_HOST=localhost
KDB_PORT=5000
KDB_USERNAME=
KDB_PASSWORD=

# Optional: alerting
SLACK_WEBHOOK_URL=
```

Copy `.env.example` to `.env` and fill in values. **Never commit `.env`.**

### Installing Dependencies

```bash
pip install uv          # or use pip directly
uv sync                 # installs from pyproject.toml lock
# or:
pip install -e ".[dev]"
```

### Running Tests

```bash
pytest tests/unit/                    # fast, no KDB+ required
pytest tests/integration/ --kdb-live  # requires live KDB+ connection
```

### Linting and Type Checking

```bash
ruff check src/ tests/
ruff format src/ tests/
mypy src/
```

---

## KDB+/q Conventions

### Connection Management

- Always use context managers or explicit `.close()` for KDB+ connections
- Connection pooling is preferred for high-frequency DQ runs
- Use `pykx` as the primary Python-KDB+ bridge; fall back to `qpython` only if needed

### q Script Style

- Use lowercase snake_case for function and variable names in q (e.g., `check.nulls`, `get.schema`)
- Namespace DQ utilities under `.dq` (e.g., `.dq.checkNull`, `.dq.profileTable`)
- Keep q scripts short and functional; complex logic belongs in Python

### Query Safety

- Never interpolate user-supplied strings directly into q queries (injection risk)
- Use parameterized IPC calls via `pykx` when passing Python values to q

---

## Agent / LLM Conventions

### Model Selection

- Default to `claude-sonnet-4-6` for most agent tasks (cost/performance balance)
- Use `claude-opus-4-6` for complex multi-step reasoning or when accuracy is critical
- Use `claude-haiku-4-5-20251001` only for high-volume classification sub-tasks

### Tool Use Pattern

Define agent tools as typed Python functions and register them with the Anthropic SDK's tool-use API. Example pattern:

```python
tools = [
    {
        "name": "run_kdb_query",
        "description": "Execute a q query against the connected KDB+ instance and return results as JSON.",
        "input_schema": {
            "type": "object",
            "properties": {
                "query": {"type": "string", "description": "The q expression to run"}
            },
            "required": ["query"]
        }
    }
]
```

### Prompt Design

- Store all system prompts in `src/agentic_dq/agent/prompts.py` as module-level constants
- Keep prompts versioned with a comment (e.g., `# v1.2 — 2026-03-06`)
- Never hardcode prompts inside business logic functions
- Separate system prompts from user-turn templates

### Agentic Loop

The DQ agent follows a tool-use loop pattern:
1. Agent receives DQ failure context and available tools
2. Agent calls tools (e.g., query KDB+ for more data, look up schema)
3. Tool results are fed back to the agent
4. Agent produces a structured DQ report with severity, root cause, and recommended action
5. Pipeline dispatches alerts or auto-remediation based on the report

---

## Code Style and Quality

### Python

- **Python 3.11+** minimum
- All new modules must have type annotations
- Use `ruff` for formatting and linting (replaces `black`, `isort`, `flake8`)
- Use `mypy` in strict mode for the `src/` package
- Avoid mutable default arguments, bare `except` clauses, and wildcard imports
- Keep functions small and single-purpose; prefer composition over inheritance

### Error Handling

- Raise specific, descriptive exceptions (define custom exceptions in `exceptions.py` per package)
- Never swallow exceptions silently; at minimum log them
- KDB+ connection errors should be caught and retried with backoff before escalating

### Logging

- Use Python's `logging` module; configure via `logging.yaml` or at the app entry point
- Log at `DEBUG` for agent tool calls, `INFO` for pipeline milestones, `WARNING`/`ERROR` for failures
- Never log credentials, API keys, or raw query results that may contain PII

---

## Testing Guidelines

- Unit tests must be fast and KDB+-independent (mock the KDB+ connection layer)
- Integration tests must be clearly marked and skipped by default unless a live KDB+ instance is available
- Aim for >80% coverage on `src/agentic_dq/`
- Tests for agent logic should mock Anthropic API calls using `pytest-mock` or `respx`

---

## Security Considerations

- API keys and credentials are always loaded from environment variables, never hardcoded
- q queries constructed from external input must be validated before execution
- The agent must not be given write/delete permissions on KDB+ unless explicitly configured
- Review any auto-remediation actions before enabling them in production

---

## License

Apache License 2.0. See [LICENSE](./LICENSE) for details. All contributions must be compatible with this license.
