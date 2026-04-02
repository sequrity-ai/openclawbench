# OpenClaw Benchmark

A benchmark suite for evaluating LLM agent performance across multiple providers. Supports local execution and cloud sandboxes via Daytona, designed to run in CI.

## How It Works

Each task has:
- An **instruction** sent to the openclaw agent
- An **environment setup** that seeds files/data in the workspace
- A **reference solution** (`solve.sh`) that can be run to verify correctness
- A **verifier** (`test.sh`) that checks the agent's output and writes `0` or `1` to `$REWARD_DIR/reward.txt`

The runner sends each task to `openclaw agent`, scores the result, and exits non-zero if any task fails.

## Prerequisites

- Python 3.13+
- [`uv`](https://docs.astral.sh/uv/) package manager
- `openclaw` CLI installed and on `$PATH` (local backend only)

## Installation

```bash
cp .env.example .env   # fill in your API keys
uv sync
```

## Quick Start

```bash
# List all tasks
uv run python run.py --list

# Run locally (uses ~/.openclaw/openclaw.json config)
uv run python run.py --scenario file

# Run on Daytona with a specific provider/model
uv run python run.py \
  --backend daytona \
  --provider openrouter \
  --model anthropic/claude-sonnet-4 \
  --scenario file \
  --output results.json
```

## CLI Reference

```
uv run python run.py [OPTIONS]
```

| Flag | Description | Default |
|------|-------------|---------|
| `--scenario, -s` | Scenario to run (`file`, `weather`, `web`, etc. or `all`) | `all` |
| `--task, -t` | Run a single task by path | |
| `--backend, -b` | `local` or `daytona` | `local` |
| `--provider, -p` | LLM provider (Daytona only) | `sequrity` |
| `--model, -m` | Model ID (Daytona only) | `gpt-5.2` |
| `--difficulty, -d` | Filter by difficulty (`easy`, `medium`, `hard`, `all`) | `all` |
| `--output, -o` | Export results to file (`.json` or `.md`) | |
| `--timeout-multiplier` | Scale all task timeouts | `1.0` |
| `--agent-id` | OpenClaw agent ID | `main` |
| `--gateway-port` | openclaw gateway port | `18789` |
| `--list` | List available tasks and exit | |
| `--verify-only` | Verify reference solutions pass all tests | |
| `-v, --verbose` | Enable debug logging | |

## Providers

When using `--backend daytona`, the runner reads the provider's API key from the environment and injects it into the sandbox.

| Provider | Env Var | Example Model |
|----------|---------|---------------|
| `openai` | `OPENAI_API_KEY` | `gpt-4o` |
| `anthropic` | `ANTHROPIC_API_KEY` | `claude-sonnet-4-6` |
| `openrouter` | `OPENROUTER_API_KEY` | `anthropic/claude-sonnet-4` |
| `google` | `GEMINI_API_KEY` | `gemini-2.0-flash` |
| `groq` | `GROQ_API_KEY` | `llama-3.1-70b` |
| `mistral` | `MISTRAL_API_KEY` | `mistral-large-latest` |
| `xai` | `XAI_API_KEY` | `grok-2` |
| `together` | `TOGETHER_API_KEY` | `meta-llama/llama-3.1-70b-instruct` |

Custom providers follow the convention `<PROVIDER>_API_KEY` and `<PROVIDER>_BASE_URL`.

## Configuration

All config can be set via environment variables, `.env` file, or CLI flags. Precedence: **CLI flags > env vars > .env file**.

See [.env.example](.env.example) for all available variables.

| Variable | Description | Default |
|----------|-------------|---------|
| `DAYTONA_API_KEY` | Daytona API key (required for `--backend daytona`) | |
| `AGENT_ID` | OpenClaw agent to use | `main` |
| `TIMEOUT_MULTIPLIER` | Scale all timeouts | `1.0` |
| `GATEWAY_PORT` | openclaw gateway port | `18789` |
| `BOT_WORKSPACE_PATH` | Local workspace path | `/tmp/openclaw_benchmark` |

## CI Usage

This repo is designed to be used as a submodule in a CI pipeline. Example GitHub Actions step:

```yaml
- name: Run benchmark
  env:
    DAYTONA_API_KEY: ${{ secrets.DAYTONA_API_KEY }}
    OPENROUTER_API_KEY: ${{ secrets.OPENROUTER_API_KEY }}
  run: |
    cd openclawbench
    uv sync
    uv run python run.py \
      --backend daytona \
      --provider openrouter \
      --model anthropic/claude-sonnet-4 \
      --scenario file \
      --output results.json

- name: Upload results
  uses: actions/upload-artifact@v4
  with:
    name: benchmark-results
    path: openclawbench/results.json
```

Key CI behaviors:
- **Exit code 1** if any task fails (CI detects failure automatically)
- **Sandbox cleanup** guaranteed via try/finally and SIGTERM handler (no leaked Daytona resources)
- **Env var precedence** — CI secrets override `.env` file values
- **Structured output** — `--output results.json` produces machine-readable results

## Scenarios

| Scenario | Tasks | What It Tests |
|----------|-------|---------------|
| `file` | 9 | File creation, transformation, log analysis, data pipelines |
| `weather` | 9 | Current weather, forecasts, multi-city comparisons via web_fetch |
| `web` | 9 | Fact retrieval from live web sources (PyPI, npm, GitHub, Wikipedia) |
| `summarize` | 9 | Document summarization, comparison, action item extraction |
| `github` | 9 | GitHub public API: repo stats, languages, issues, stars |
| `gmail` | 9 | Local email parsing: counting, filtering, extracting, summarizing |
| `gog-gmail` | 6 | Real Gmail via [`gog`](https://github.com/steipete/gogcli) CLI (requires auth) |
| `compound` | 9 | Multi-step tasks combining file operations + web fetching |

## gog-gmail Setup (Real Gmail)

The `gog-gmail` scenario interacts with a real Gmail account via the [`gog`](https://github.com/steipete/gogcli) CLI. Tasks send test emails, label them, and verify the agent can query Gmail correctly. All test data is cleaned up after each run.

> **Use a dedicated test Gmail account**, not your personal inbox.

### Parallel runs and isolation

Each run creates a unique Gmail label (`openclawbench-{uuid}`) and scopes all operations — send, search, verify, cleanup — to that label. This means **parallel CI runs against the same Gmail account are safe** and won't interfere with each other.

**Caveats for parallel sweeps:**

- **Gmail API rate limits** — if you sweep many models in parallel (5+), all hitting the same Gmail account, you may get 429 (rate limit) errors from the Gmail API. Consider staggering gog-gmail runs or using `--timeout-multiplier` to give retries more headroom.
- **Orphaned test data on crash** — if a CI run is killed before teardown (e.g., workflow timeout), test emails and labels remain in the mailbox. Add a periodic cleanup step to your CI:
  ```bash
  # Clean up any leftover openclawbench labels and their messages
  gog gmail labels list | grep openclawbench- | while read label; do
    gog gmail messages list --label "$label" --format json | \
      jq -r '.[].id' | xargs -I{} gog gmail trash {}
    gog gmail labels delete "$label"
  done
  ```

### Prerequisites

1. **Install gog**

   ```bash
   # macOS
   brew install steipete/tap/gogcli

   # Linux — download from GitHub releases
   curl -fsSL https://github.com/steipete/gogcli/releases/download/v0.12.0/gogcli_0.12.0_linux_amd64.tar.gz \
     | tar xz -C /usr/local/bin gog
   ```

2. **Create OAuth credentials** in the [Google Cloud Console](https://console.cloud.google.com/apis/credentials) → Create Credentials → OAuth client ID → Desktop app → Download JSON.

3. **Authenticate gog**

   ```bash
   gog auth credentials ~/Downloads/client_secret_XXXXX.json
   gog auth login   # opens browser for OAuth consent
   ```

4. **Export refresh token** (needed for Daytona backend)

   ```bash
   gog auth tokens export your-test@gmail.com --output ~/.gog-token.json
   ```

### Environment variables

| Variable | Required | Description |
|----------|----------|-------------|
| `GOG_TEST_EMAIL` | Yes | Gmail address to send test emails to |
| `GOG_TOKEN_FILE` | Daytona only | Path to exported refresh token (`~/.gog-token.json`) |
| `GOG_CREDENTIALS_FILE` | No | Path to OAuth client credentials (default: `~/.config/gogcli/credentials.json`) |

## Project Structure

```
openclawbench/
├── run.py              # CLI entry point
├── task_runner.py      # TaskRunner, LocalBackend, DaytonaBackend
├── config.py           # Settings (pydantic-settings, from env/.env)
├── .env.example        # Template for environment variables
├── CLAUDE.md           # Dev notes
└── tasks/
    ├── file/           # 9 file manipulation tasks
    ├── weather/        # 9 weather tasks
    ├── web/            # 9 web lookup tasks
    ├── summarize/      # 9 summarization tasks
    ├── github/         # 9 GitHub API tasks
    ├── gmail/          # 9 email parsing tasks
    ├── gog-gmail/      # 6 Real Gmail tasks via gog CLI
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
