# CLAUDE.md — Agentic DQ for KDB

This file provides guidance for AI assistants (Claude and others) working in this repository. It documents the project's purpose, architecture, conventions, and development workflows.

**Reference whitepaper:** [Agentic Workflow for Data Quality — ExeQution Analytics](https://exequtionanalytics.com/wp-content/uploads/2026/01/Agentic-Workflow-for-Data-Quality.pdf)

---

## Project Overview

**Agentic-DQ-for-KDB** is an AI-agent-driven **Data Quality (DQ)** framework targeting **KDB+/q** (KDB-X) databases. It uses **MCP (Model Context Protocol)** to connect Claude to KDB-X, enabling natural-language-driven data quality checks without writing pre-defined q queries for every check.

The project is inspired directly by ExeQution Analytics' research demonstrating that AI agents — given the right MCP tools, resources, and prompts — can autonomously detect data completeness gaps, timestamp inconsistencies, bad data points, anomalies, outliers, duplicates, and trade-quote misalignment in high-frequency financial market data.

### Goals

- Use Claude + KDB-X MCP Server to perform DQ checks via natural language prompts
- Build reusable q-language tool wrappers as MCP tools (preferred over SQL for performance)
- Provide rich context via MCP resources (table schemas, venue hours, index constituents)
- Automate the four DQ check categories: Completeness, Timestamp Consistency, Validation, Understanding
- Reduce the burden on development teams maintaining bespoke DQ query libraries
- Always pair AI analysis with human domain-expert verification checkpoints

### Validated DQ Check Categories (from whitepaper)

| Category | What it checks |
|---|---|
| **Data Completeness** | Gaps in data, distribution across trading sessions vs. venue hours |
| **Timestamp Consistency** | Temporal gaps (30-min and 3-min granularity), event ordering vs. venue schedule |
| **Data Validation** | Null/negative values, crossed quotes (bid > ask), price/size outliers, duplicate reference data |
| **Data Understanding** | Auction trade classification, trade-quote alignment via `aj`, latency risk zones |

---

## Repository State

> **Status: Early-stage / skeleton.** As of the initial commit, only `README.md` and `LICENSE` exist. Source code, configuration, and tests are yet to be added. This CLAUDE.md serves as the authoritative guide for how the project should be structured as it evolves.

---

## Architecture: MCP-Based Agentic DQ

The core architecture follows the **KDB-X MCP Server** pattern established by KX:

```
Claude (LLM client)
    │
    │  natural language prompts
    ▼
MCP Server (KDB-X MCP Server + custom extensions)
    ├── TOOLS      → Python/q functions that query the database
    ├── RESOURCES  → Context files: schemas, venue config, scripts
    └── PROMPTS    → Auto-generated prompt templates for users
    │
    ▼
KDB-X Process (trade, quote, reference tables)
```

### MCP Concepts

| Concept | Role | Examples |
|---|---|---|
| **Tools** | Functions that query the database | `xqa_get_venue_syms`, `xqa_get_venue_hours`, `xqa_get_index_syms`, alignment tool wrapping `aj` |
| **Resources** | Context scripts/text files the AI reads to understand data | Table schemas, venue config, `kdbx_describe_tables`, `kdbx_sql_query_guidance` |
| **Prompts** | Auto-generated prompt templates | `kdbx_table_analysis` |

### Built-in KDB-X MCP Tools (from KX)

- `kdbx_describe_tables` — gives AI a general overview of all tables
- `kdbx_sql_query_guidance` — supplements SQL tools with query best practices
- `kdbx_run_sql_query` — translates natural language to SQL, runs in KDB-X
- `kdbx_table_analysis` — generates a data analysis prompt template

> **Important:** SQL via `kdbx_run_sql_query` is flexible but slow on large tick data. Prefer custom q-language tool wrappers for performance-sensitive checks.

### Custom Tools to Implement

Follow the `xqa_` prefix convention for project-specific tools:

| Tool name | Purpose |
|---|---|
| `xqa_get_venue_syms` | Returns all symbols traded on a specific venue |
| `xqa_get_index_syms` | Returns index constituents (e.g., TOPIX top 50) for scoped analysis |
| `xqa_get_venue_hours` | Returns venue trading hours and timezone offset config |
| `xqa_align_trade_quote` | Wraps q's `aj` function for trade-quote timestamp alignment |
| `xqa_get_condition_codes` | Returns exchange condition code definitions |

New tools should provide **general-purpose context** (venue metadata, schema info, symbol lists) rather than check-specific queries. General tools are reusable; AI generates the specific check logic dynamically.

---

## Expected Technology Stack

| Layer | Technology |
|---|---|
| Database | KDB-X / KDB+/q |
| MCP Server | KDB-X MCP Server (by KX) |
| AI client | Claude Desktop / Anthropic API (`claude-sonnet-4-6`) |
| Python runtime | Python 3.11+ managed with `uv` |
| KDB+ Python bridge | `pykx` (preferred) or `qpython` |
| q tool wrappers | Native q language (not SQL) for performance |
| Config | YAML / TOML |
| Testing | `pytest` |
| Linting | `ruff`, `mypy` |
| Packaging | `pyproject.toml` / `uv` |
| CI | GitHub Actions |

---

## Intended Directory Structure

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
│       ├── mcp/                # MCP server layer
│       │   ├── __init__.py
│       │   ├── server.py       # MCP server entry point (extends KDB-X MCP)
│       │   ├── tools.py        # Custom xqa_* tool registrations
│       │   ├── resources.py    # Resource file registration (schemas, config)
│       │   └── prompts.py      # Prompt template definitions
│       ├── kdb/                # KDB+ integration layer
│       │   ├── __init__.py
│       │   ├── connection.py   # KDB+ connection management
│       │   ├── query.py        # q query builders and executors
│       │   └── schema.py       # Table schema introspection
│       ├── dq/                 # DQ check category implementations
│       │   ├── __init__.py
│       │   ├── completeness.py # Gap detection, session distribution checks
│       │   ├── timestamp.py    # Temporal gap analysis, 1-min bin checks
│       │   ├── validation.py   # Bad data, crossed quotes, outliers, duplicates
│       │   └── understanding.py# Auction classification, trade-quote alignment
│       ├── pipeline/           # Orchestration
│       │   ├── __init__.py
│       │   ├── runner.py       # DQ pipeline runner
│       │   └── scheduler.py    # Cron/event-based scheduling
│       └── reporting/          # Output and alerting
│           ├── __init__.py
│           ├── report.py       # DQ report generation
│           └── alerts.py       # Alert dispatching (Slack, email, etc.)
│
├── q/                          # KDB+/q scripts (tool wrappers)
│   ├── init.q                  # Startup / bootstrapping script
│   ├── tools/
│   │   ├── venue.q             # xqa_get_venue_syms, xqa_get_venue_hours
│   │   ├── index.q             # xqa_get_index_syms
│   │   └── alignment.q         # xqa_align_trade_quote (aj wrapper)
│   └── utils.q                 # Shared q utilities
│
├── config/
│   ├── venues.yaml             # Venue trading hours & timezone offsets
│   ├── indices.yaml            # Index constituent definitions
│   └── connections.yaml        # KDB+ connection profiles (no credentials)
│
├── resources/                  # MCP resource files (context for AI)
│   ├── schemas/                # Table schema descriptions
│   │   ├── trade.md
│   │   └── quote.md
│   └── guides/                 # Domain knowledge context
│       ├── auction_types.md
│       └── condition_codes.md
│
├── tests/
│   ├── conftest.py             # Shared pytest fixtures
│   ├── unit/
│   │   ├── test_tools.py
│   │   ├── test_dq_checks.py
│   │   └── test_kdb_query.py
│   └── integration/
│       └── test_pipeline.py    # Requires live KDB-X instance
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

## DQ Check Implementation Guide

### 1. Data Completeness

Checks whether data covers the expected trading sessions without gaps.

**Approach:**
- Use `xqa_get_venue_hours` to retrieve official trading hours and timezone offset
- Convert venue local time to storage timezone before comparing (e.g., JST −1h = UTC+8)
- Aggregate trade/quote counts by time period (pre-open, morning session, lunch, afternoon, post-close)
- Flag sessions with zero or anomalously low record counts

**Key lesson from whitepaper:** The AI correctly deduced timezone offset from config *without being prompted*, converting JST to storage timezone automatically. 99.93% of trades and 96.4% of quotes fell within official trading hours on clean data.

### 2. Timestamp Consistency

Checks for temporal gaps and event ordering within trading sessions.

**Approach:**
- Bin trade/quote records into 1-minute intervals
- Flag bins with zero records during expected continuous-trading windows
- Cross-reference gaps against auction schedule (opening/closing auction periods may legitimately have sparse data)

**Key lessons from whitepaper:**
- Large gaps (30 min) are detected reliably by default
- Small gaps (≤3 min) require explicit instruction: *"Check 1-minute bins and flag any minute with zero trades during continuous trading hours"*
- The AI may misattribute gaps to auction periods even when auction config says otherwise — always verify against `xqa_get_venue_hours` auction timings

### 3. Data Validation

#### Bad Data (Nulls / Negatives)
- Check `price` and `size` columns for null values and negative entries
- Report count and percentage of affected records
- The AI reliably identifies these when given the full dataset (not sampled)

#### Crossed Quotes
- During continuous trading, `bid < ask` must always hold
- `bid >= ask` = crossed quote — indicates feed error or special market condition
- On TSE, crossed quotes during auction periods are expected (special quotation mechanism)
- Filter to continuous trading hours before flagging; use `xqa_get_venue_hours` for session boundaries

#### Outliers
- Detect price deviations >N standard deviations from rolling average
- Provide context window (trades ±30 seconds around outlier) to confirm it is not a genuine market move
- Common causes: fat-finger, data-feed glitch, decimal-point misplacement

#### Duplicates
- Reference tables (`stockCodes`, `venueMap`) must be checked for duplicates
- Not all duplicates are errors — the AI should apply domain reasoning:
  - `stockCodes`: Duplicate ISINs/names may be cross-listings, ETF families, or multi-venue stocks
  - `venueMap`: Duplicate venue codes with different effective dates = operating hours change (valid)
- Always confirm AI's reasoning with a domain expert

### 4. Data Understanding

#### Auction Classification
- Auction trades should be flagged in a `flag` column with values `"opening"` / `"closing"`
- Opening auction: concentrated execution at market open, typically 1-second window, large average size
- Closing auction: similar characteristics at market close
- Verify: auction trade count matches expected symbol count; average size >> continuous session trades

#### Trade-Quote Alignment
- Use q's `aj` (asof join) to align each trade with its immediately preceding quote
- A correctly aligned trade has `trade_price == bid` or `trade_price == ask`
- Alignment degrades during high-volatility periods (market open/close) due to quote-to-trade ratio spikes
- Quote-to-trade ratios >50:1 indicate high latency risk zones — flag these periods in the DQ report

---

## Prompt Engineering for DQ Checks

Effective prompts follow this structure (derived from whitepaper best practices):

```
SCOPE:
- Time period: ONLY USE DATA FOR [DATE], DO NOT LOOK AT ANY OTHER DATES
- Symbols: use symbols from the [INDEX] index
- trade table schema: date, sym, time, price, size, code, flag
- quote table schema: date, sym, time, ask, asize, bid, bsize

Answer the following questions:
[DQ question 1]
[DQ question 2]

Constraints:
- Ensure ALL data is used (no sampling)
- Always use date-partitioned queries
- For each finding, state exactly which data was used
```

### Prompt Engineering Rules

| Rule | Why it matters |
|---|---|
| Always specify exact date(s) | Prevents the AI from querying unbounded time ranges → timeouts |
| Always provide table schema | Prevents malformed queries against large tables |
| Explicitly ban sampling | AI defaults to sampling large datasets; must be overridden |
| Use index symbols, not all symbols | Focuses analysis on the most liquid, representative instruments |
| Add verification checkpoints | "State what data was used" forces the AI to confirm coverage |
| Request date-partitioned queries | Critical for KDB-X performance on partitioned HDB tables |
| Specify timezone in prompt | AI handles timezone math correctly when offset is explicit |
| For gap detection: specify 1-min bins | AI misses small gaps without explicit granularity instruction |

### Phased Analysis Strategy

For large historical datasets, use a 3-phase approach:

```
Phase 1 — Statistical Sample (1–2 weeks)
  • Top 100 symbols (or one index)
  • 5–10 representative dates
  • Full daily analysis with date partitioning
  • Achievable within current MCP constraints ✓

Phase 2 — Problem Period Deep-Dive
  • Focus on dates where Phase 1 found issues
  • Expand symbol coverage for those specific dates
  • Achievable with careful partitioning ✓

Phase 3 — Full Historical Scan
  • Requires distributed compute or pre-aggregated summary tables
  • Or query optimisation at database level
  • Not achievable with standard MCP tool constraints ✗
```

---

## KDB+/q Conventions

### Tool Implementation: q over SQL

Custom MCP tools **must** be implemented as q-language wrappers, not SQL:
- SQL via `kdbx_run_sql_query` is flexible but slow on millions of tick records
- q direct calls offer significantly better performance on large datasets
- Wrap q functions in Python using `pykx` and register them as MCP tools

```python
# Preferred: q wrapper tool
import pykx as kx

def xqa_get_venue_hours(venue_code: str) -> dict:
    """Returns trading hours and UTC offset for the specified venue."""
    result = kx.q(f'select from venueMap where venue=`{venue_code}')
    return result.pd().to_dict(orient="records")
```

### Connection Management

- Always use context managers or explicit `.close()` for KDB+ connections
- Connection pooling is preferred for high-frequency DQ runs
- Use `pykx` as the primary Python-KDB+ bridge; fall back to `qpython` only if unavailable

### q Script Style

- Namespace all DQ utilities under `.dq` (e.g., `.dq.checkNull`, `.dq.profileTable`)
- Namespace custom MCP tool functions under `.xqa` (e.g., `.xqa.getVenueHours`)
- Keep q scripts short; complex orchestration logic belongs in Python

### Key q Functions for DQ

| Function | Use case |
|---|---|
| `aj` (asof join) | Trade-quote alignment — join each trade to its immediately preceding quote |
| `wj` (window join) | Quote statistics within a time window around each trade |
| `select ... by` | Aggregations by symbol/time for session-level completeness checks |
| `differ` | Detect consecutive duplicate timestamps |
| `mavg`, `mdev` | Rolling statistics for outlier detection |
| `count where null` | Null completeness checks |

### Query Safety

- Never interpolate user-supplied strings directly into q queries (injection risk)
- Use parameterized IPC calls via `pykx` when passing Python values to q
- Validate symbol names against `xqa_get_venue_syms` before using in queries

### Timezone Handling

KDB-X stores tick data in a configured "storage timezone" that may differ from the venue's local timezone. Always:
1. Read the timezone offset from `venueMap` config via `xqa_get_venue_hours`
2. Convert venue local trading hours to the storage timezone before applying time filters
3. Document the offset in resource files and prompt context (e.g., "JST −1h = data stored in UTC+8")

---

## Agent / LLM Conventions

### Model Selection

- Default to `claude-sonnet-4-6` for all DQ analysis tasks (ExeQution Analytics validated Sonnet-class models for this use case)
- Use `claude-opus-4-6` for complex multi-step reasoning or ambiguous data patterns
- Use `claude-haiku-4-5-20251001` only for high-volume, simple classification sub-tasks

### MCP Tool Design Principles

Tools should provide **general context**, not encode specific DQ logic:

```python
# Good: general-purpose, reusable context tool
{
    "name": "xqa_get_venue_hours",
    "description": "Returns trading session hours, auction times, and UTC offset for a venue.",
    "input_schema": {
        "type": "object",
        "properties": {
            "venue_code": {"type": "string", "description": "Exchange code, e.g. XTKS"}
        },
        "required": ["venue_code"]
    }
}

# Avoid: check-specific tool that can't be reused
{
    "name": "check_if_data_outside_trading_hours",  # Too specific
    ...
}
```

The AI generates specific check logic dynamically; tools give it the raw data and context to reason from.

### MCP Resource Files

Place context documents in `resources/` and register them with the MCP server:
- Table schemas: column names, types, descriptions, known quirks
- Venue guides: auction mechanics, condition code meanings, special quotation rules
- Domain guides: what crossed quotes mean, how `aj` works, expected auction characteristics

Explicit schema resources prevent the AI from issuing malformed queries against large tables.

### Agentic DQ Loop

```
1. User submits DQ prompt (with SCOPE block: date, symbols, schema, constraints)
         │
2. AI selects appropriate MCP tools (venue hours, index syms, schema resources)
         │
3. AI calls tools iteratively, building context about the data
         │
4. AI executes q-based analysis queries (partitioned, scoped, no sampling)
         │
5. AI generates structured DQ report:
         • Coverage summary (rows analyzed, symbol count, date range)
         • Findings per DQ category with severity (INFO / WARNING / CRITICAL)
         • Root cause assessment with domain reasoning
         • Recommended action
         │
6. Human domain expert reviews and validates AI's reasoning
         │
7. Confirmed issues escalate to alerting / remediation pipeline
```

### Known AI Limitations (from whitepaper)

Be aware of these failure modes and mitigate with prompt engineering:

| Limitation | Mitigation |
|---|---|
| AI defaults to sampling large datasets | Explicitly instruct "use ALL data, no sampling" in every prompt |
| Small gaps (≤3 min) missed in default analysis | Instruct "check 1-minute bins explicitly" |
| AI may misattribute gaps to auction periods | Require AI to cross-check against venue auction schedule tool |
| AI may give plausible-but-wrong explanations for duplicates | Build in verification checkpoints; human review is mandatory |
| SQL queries timeout on large tick tables | Use q-language tools, never SQL for tick data at scale |
| Context window limits scope to subset of symbols/dates | Use phased analysis strategy (Phase 1 → 2 → 3) |

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
Add xqa_get_venue_hours MCP tool with timezone support

Wraps venueMap table query to return session boundaries and UTC offset.
Required by completeness and timestamp consistency DQ checks.
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

# KDB-X Connection
KDB_HOST=localhost
KDB_PORT=5000
KDB_USERNAME=
KDB_PASSWORD=

# MCP Server
MCP_SERVER_PORT=8080

# Optional: alerting
SLACK_WEBHOOK_URL=
```

Copy `.env.example` to `.env` and fill in values. **Never commit `.env`.**

### Installing Dependencies

```bash
# Recommended: use uv (manages Python + packages, used by KDB-X MCP Server)
pip install uv
uv sync                 # installs from pyproject.toml lock

# Alternative:
pip install -e ".[dev]"
```

### Running the MCP Server

```bash
# Start KDB-X MCP Server with custom tools
uv run python -m agentic_dq.mcp.server --kdb-host localhost --kdb-port 5000
```

### Running Tests

```bash
pytest tests/unit/                    # fast, no KDB-X required
pytest tests/integration/ --kdb-live  # requires live KDB-X connection
```

### Linting and Type Checking

```bash
ruff check src/ tests/
ruff format src/ tests/
mypy src/
```

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
- Log at `DEBUG` for MCP tool calls, `INFO` for DQ pipeline milestones, `WARNING`/`ERROR` for failures
- Never log credentials, API keys, or raw query results that may contain PII

---

## Testing Guidelines

- Unit tests must be fast and KDB-X-independent (mock the KDB+ connection layer)
- Integration tests must be clearly marked and skipped by default unless a live KDB-X instance is available
- Aim for >80% coverage on `src/agentic_dq/`
- Tests for MCP tools should verify q query correctness against known fixture data
- Tests for DQ logic should inject known bad data (nulls, negatives, outliers) and assert correct detection

---

## Security Considerations

- API keys and credentials are always loaded from environment variables, never hardcoded
- q queries constructed from external input must be validated before execution
- The agent must not be given write/delete permissions on KDB-X unless explicitly configured
- Review any auto-remediation actions before enabling them in production
- MCP tool descriptions must not expose internal table structures or connection details

---

## License

Apache License 2.0. See [LICENSE](./LICENSE) for details. All contributions must be compatible with this license.
