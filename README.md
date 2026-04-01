# OpenClaw Benchmark

A benchmark suite for evaluating OpenClaw agent performance across 7 scenarios and 63 tasks.

## How It Works

Each task has:
- An **instruction** sent to the openclaw agent
- An **environment setup** that seeds files/data in the workspace
- A **reference solution** (`solve.sh`) that can be run to verify correctness
- A **verifier** (`test.sh`) that checks the agent's output and writes `0` or `1` to `$REWARD_DIR/reward.txt`

The runner sends each task to `openclaw agent` as a local subprocess and scores the result.

## Prerequisites

- Python 3.13+
- [`uv`](https://docs.astral.sh/uv/) package manager
- `openclaw` CLI installed and on `$PATH`

## Installation

```bash
uv sync
```

## Running Benchmarks

```bash
# List all tasks
uv run python run.py --list

# Run all scenarios (63 tasks)
uv run python run.py --all

# Run a single scenario
uv run python run.py --scenario file
uv run python run.py --scenario weather
uv run python run.py --scenario web
uv run python run.py --scenario summarize
uv run python run.py --scenario github
uv run python run.py --scenario gmail
uv run python run.py --scenario compound

# Run a single task
uv run python run.py --task tasks/file/file-organization

# Filter by difficulty
uv run python run.py --scenario file --difficulty easy

# Verify reference solutions pass
uv run python run.py --verify-only --scenario file

# Export results to JSON
uv run python run.py --all -o results.json
```

## Scenarios

| Scenario | Tasks | What It Tests |
|----------|-------|---------------|
| `file` | 9 | File creation, transformation, log analysis, data pipelines |
| `weather` | 9 | Current weather, forecasts, multi-city comparisons via web_fetch |
| `web` | 9 | Fact retrieval from live web sources (PyPI, npm, GitHub, Wikipedia) |
| `summarize` | 9 | Document summarization, comparison, action item extraction |
| `github` | 9 | GitHub public API: repo stats, languages, issues, stars |
| `gmail` | 9 | Local email parsing: counting, filtering, extracting, summarizing |
| `gog-gmail` | — | Real Gmail via [`gog`](https://github.com/steipete/gogcli) CLI (requires auth) |
| `compound` | 9 | Multi-step tasks combining file operations + web fetching |

## gog-gmail Setup (Real Gmail)

The `gog-gmail` scenario interacts with a real Gmail account via the [`gog`](https://github.com/steipete/gogcli) CLI. Tasks send test emails, label them, and verify the agent can query Gmail correctly. All test data is cleaned up after each run.

> **Use a dedicated test Gmail account**, not your personal inbox.

### 1. Install gog

```bash
# macOS
brew install steipete/tap/gogcli

# Linux — download from GitHub releases
curl -fsSL https://github.com/steipete/gogcli/releases/download/v0.12.0/gogcli_0.12.0_linux_amd64.tar.gz \
  | tar xz -C /usr/local/bin gog
```

### 2. Authenticate

Create OAuth credentials in the [Google Cloud Console](https://console.cloud.google.com/apis/credentials) (Desktop app type), download the JSON, then:

```bash
gog auth credentials /path/to/client_credentials.json
gog auth login   # opens browser for OAuth consent
```

### 3. Run locally

```bash
export GOG_TEST_EMAIL="your-test@gmail.com"
uv run python run.py --task tasks/gog-gmail/count-unread
```

### 4. Run on Daytona

Sandboxes have no browser or OS keychain, so export your refresh token:

```bash
# One-time: export token file
gog auth tokens export your-test@gmail.com --output ~/.gog-token.json

# Run
export GOG_TEST_EMAIL="your-test@gmail.com"
export GOG_TOKEN_FILE=~/.gog-token.json
uv run python run.py --backend daytona --task tasks/gog-gmail/count-unread --provider=openai --model=gpt-5.2
```

The runner uploads the `gog` binary and token into the sandbox automatically. `GOG_KEYRING_PASSWORD` and `GOG_ACCOUNT` are set by the runner — you don't need to export them.

## Configuration

Configuration via `.env` or environment variables:

```bash
AGENT_ID=main               # OpenClaw agent to use (default: main)
TIMEOUT_MULTIPLIER=1.0      # Scale all timeouts (use >1 on slow machines)
BOT_WORKSPACE_PATH=/tmp/openclaw_benchmark  # Local workspace path
```

## Project Structure

```
openclawbench/
├── run.py              # CLI entry point
├── task_runner.py      # TaskRunner, LocalBackend, DaytonaBackend
├── config.py           # Settings (pydantic, from .env)
├── CLAUDE.md           # Dev notes
└── tasks/
    ├── file/           # 9 file manipulation tasks
    ├── weather/        # 9 weather tasks
    ├── web/            # 9 web lookup tasks
    ├── summarize/      # 9 summarization tasks
    ├── github/         # 9 GitHub API tasks
    ├── gmail/          # 9 email parsing tasks
    ├── gog-gmail/      # Real Gmail tasks via gog CLI
    └── compound/       # 9 multi-step tasks
```

Each task follows the structure:
```
tasks/<scenario>/<task-name>/
├── task.toml                       # Metadata (difficulty, timeout, allow_internet)
├── instruction.md                  # Task prompt sent to the agent
├── environment/setup_workspace.py  # Seeds files/data before the task
├── solution/solve.sh               # Reference solution
└── tests/test.sh                   # Verifier
```
