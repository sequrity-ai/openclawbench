# OpenClaw Benchmark Setup Guide

This guide covers everything needed to set up and run the OpenClaw benchmark suite from scratch. A human or AI agent should be able to replicate the full setup by following these steps.

---

## Overview

The benchmark evaluates AI models through 7 scenarios (63 total tasks) using OpenClaw as the agent runtime. It supports two modes:

- **Local mode**: Calls `openclaw agent` CLI directly (fast, ~2-5s/response)
- **Telegram mode**: Sends messages to a deployed OpenClaw bot via Telegram (slower, ~30s/response)

This guide focuses on **local mode** since it's simpler and faster.

---

## Prerequisites

- Linux server with OpenClaw installed and running (`openclaw gateway` systemd service)
- Python 3.12+ with `uv` package manager
- Node.js (for OpenClaw CLI)
- GitHub account with a personal access token
- API keys: OpenAI, Tavily

---

## 1. Clone and Install

```bash
git clone <repo-url> ~/opencalw-sandbox
cd ~/opencalw-sandbox
uv sync
```

---

## 2. Environment Configuration

Copy the example and fill in:

```bash
cp .env.example .env
```

### Required `.env` variables

```bash
# Mode
LOCAL_MODE=true
AGENT_ID=main

# OpenAI (for the AI agent that simulates a user in multi-turn conversations)
OPENAI_API_KEY=sk-proj-...

# AI agent model (drives the benchmark's user-simulator, NOT the model being tested)
AI_AGENT_MODEL=gpt-4o-mini

# Tavily (for Web Search scenario validation - fetches ground truth)
TAVILY_API_KEY=tvly-...

# GitHub (for GitHub + Compound scenarios)
GITHUB_TOKEN=ghp_...
GITHUB_TEST_REPO_OWNER=your-org-or-username
GITHUB_TEST_REPO_NAME=openclaw-sandbox
```

### Optional `.env` variables (for Gmail scenario)

```bash
GOOGLE_CLIENT_ID=...
GOOGLE_CLIENT_SECRET=...
GOOGLE_REFRESH_TOKEN=...
GMAIL_BENCHMARK_EMAIL=benchmark@gmail.com
GMAIL_BOT_EMAIL=bot@gmail.com
```

### Optional `.env` variables (for Telegram mode)

```bash
TELEGRAM_API_ID=12345678
TELEGRAM_API_HASH=abc123...
TELEGRAM_PHONE=+1234567890
OPENCLAW_BOT_USERNAME=your_bot

# SSH to bot server (for file-based validation in Telegram mode)
BOT_SSH_HOST=your-server.com
BOT_SSH_USER=openclaw
BOT_SSH_KEY_PATH=~/.ssh/id_rsa
```

---

## 3. OpenClaw Skills

The benchmark requires these OpenClaw skills to be installed on the bot:

| Skill | Used by Scenarios | Install |
|-------|------------------|---------|
| `weather` (steipete/weather) | Weather, Compound | `openclaw skills install steipete/weather` |
| `tavily-search` | Web Search, Compound | `openclaw skills install tavily-search` |
| `github` (steipete/github) | GitHub, Compound | `openclaw skills install steipete/github` |
| `summarize` (steipete/summarize) | Summarize, Compound | `openclaw skills install steipete/summarize` |
| `gog` (Gmail) | Gmail | `openclaw skills install gog` |

**File scenario** requires no skills — it uses built-in read/write/exec tools.

### Skill API keys

Skills need their own API keys configured in OpenClaw. These go in `~/.openclaw/openclaw.json` under `skills.entries`:

```json
{
  "skills": {
    "entries": {
      "tavily-search": {
        "env": {
          "TAVILY_API_KEY": "tvly-..."
        }
      }
    }
  }
}
```

The weather skill uses Open-Meteo (free, no key needed). The GitHub skill uses the bot's configured GitHub token. The summarize skill uses the bot's web fetch capability.

### Verify skills are installed

```bash
openclaw skills list --json
```

All required skills should show `eligible: true`.

---

## 4. GitHub Test Repository

The GitHub and Compound scenarios need a test repository that gets seeded with benchmark data.

### Create the repo

1. Create a **public** GitHub repository (e.g., `your-org/openclaw-sandbox`)
2. Set `GITHUB_TEST_REPO_OWNER` and `GITHUB_TEST_REPO_NAME` in `.env`
3. The benchmark's setup phase automatically seeds the repo with:
   - README.md
   - `src/utils.js` (with `fetchData()` and `processItems()` functions)
   - 5 JS source files with commit history
   - 1 feature branch + open PR
   - Release `v1.0.0-benchmark`
   - Label `benchmark-seed`
   - 3 seeded issues

### Security warning

**Do NOT give the bot's GitHub token write access to repos with sensitive data.** The benchmark tasks ask the bot to create GitHub issues. If the bot's `exec` tool has unescaped shell arguments, environment variables (including API keys) can leak into issue bodies. Use a dedicated throwaway repo.

See [Security Considerations](#9-security-considerations) for details.

---

## 5. Sequrity AI Setup (Optional)

If benchmarking through the Sequrity AI proxy (dual-LLM architecture):

### Problem

Sequrity's dual-LLM mode doesn't support SSE streaming. OpenClaw always sends `stream: true`. Sequrity ignores it and returns raw JSON. OpenClaw's SSE parser fails silently → empty responses.

### Solution: Local proxy

A Python proxy at `127.0.0.1:18899` sits between OpenClaw and Sequrity:

```
OpenClaw --stream:true--> Proxy --stream:false--> Sequrity API
OpenClaw <--SSE chunks--- Proxy <--plain JSON---- Sequrity API
```

### Proxy setup

1. Place the proxy script at `~/.openclaw/sequrity-proxy.py`
2. Create a systemd user service:

```bash
cat > ~/.config/systemd/user/sequrity-proxy.service << 'EOF'
[Unit]
Description=Sequrity AI SSE Proxy
After=network.target

[Service]
ExecStart=/usr/bin/python3 /home/openclaw/.openclaw/sequrity-proxy.py
Restart=always
RestartSec=3
Environment=PYTHONUNBUFFERED=1

[Install]
WantedBy=default.target
EOF

systemctl --user daemon-reload
systemctl --user enable --now sequrity-proxy
```

3. Configure OpenClaw to use the proxy in `~/.openclaw/openclaw.json`:

```json
{
  "models": {
    "providers": {
      "sequrity": {
        "baseUrl": "http://127.0.0.1:18899",
        "apiKey": "your-sequrity-api-key",
        "api": "openai-completions",
        "authHeader": true,
        "headers": {
          "X-Features": "{\"agent_arch\":\"dual-llm\"}",
          "X-Policy": "{\"mode\":\"standard\",\"presets\":{\"default_allow\":true,\"default_allow_enforcement_level\":\"soft\"}}",
          "X-Config": "{\"fsm\":{\"enable_multistep_planning\":true,\"disable_rllm\":true,\"max_n_turns\":50,\"max_pllm_steps\":50,\"max_pllm_failed_steps\":10,\"history_mismatch_policy\":\"restart_turn\"},\"response_format\":{\"strip_response_content\":true}}"
        },
        "models": [
          {
            "id": "openai/gpt-5.2",
            "name": "Sequrity GPT-5.2",
            "reasoning": false,
            "input": ["text"],
            "cost": { "input": 0, "output": 0, "cacheRead": 0, "cacheWrite": 0 },
            "contextWindow": 200000,
            "maxTokens": 16384
          }
        ]
      }
    }
  }
}
```

### Key X-Config parameters

| Parameter | Value | Purpose |
|-----------|-------|---------|
| `enable_multistep_planning` | `true` | FSM multi-step planning |
| `disable_rllm` | `true` | Disable response LLM |
| `max_n_turns` | `50` | Max conversation turns per session |
| `max_pllm_steps` | `50` | Max planning steps per turn (default 10 is too low) |
| `max_pllm_failed_steps` | `10` | Max failed steps before aborting |
| `history_mismatch_policy` | `restart_turn` | Handle message history mismatches gracefully |
| `strip_response_content` | `true` | Return plain text, not JSON envelope |

### Managing the proxy

```bash
systemctl --user status sequrity-proxy    # Check status
systemctl --user restart sequrity-proxy   # Restart
journalctl --user -u sequrity-proxy -f    # Tail logs
```

### Debug logs

The proxy writes full request/response logs to `~/.openclaw/sequrity-debug.log`. The API-level log (what OpenClaw sends/receives) is at `~/.openclaw/sequrity-api.log`.

---

## 6. OpenClaw Configuration

### Key `~/.openclaw/openclaw.json` settings for benchmarking

```json
{
  "agents": {
    "defaults": {
      "model": {
        "primary": "anthropic/claude-sonnet-4-5",
        "fallbacks": []
      },
      "compaction": {
        "mode": "default"
      },
      "timeoutSeconds": 600,
      "maxConcurrent": 4
    }
  }
}
```

### Important settings

- **`model.fallbacks: []`** — Empty! The benchmark clears fallbacks to ensure model isolation. If fallbacks are set, a failing model could silently fall back to another, corrupting results.
- **`compaction.mode: "default"`** — Do NOT use `"safeguard"` mode. Safeguard sends a summarization request to the model during compaction, which can get stuck (especially with Sequrity's FSM) and block tasks indefinitely.
- **`timeoutSeconds: 600`** — 10 minute timeout per agent invocation.

---

## 7. Running Benchmarks

### Single scenario

```bash
# Local mode (recommended for development)
just bench file mode=local
just bench weather mode=local
just bench web mode=local
just bench github mode=local
just bench summarize mode=local
just bench compound mode=local
just bench gmail mode=local

# All scenarios
just bench all mode=local
```

### With model switching

```bash
# Test a specific model
just bench all mode=local model="anthropic/claude-sonnet-4-5"
just bench all mode=local model="sequrity/openai/gpt-5.2"
just bench all mode=local model="openai/gpt-5.2"
```

### Model sweep (all models x all scenarios)

```bash
just sweep mode=local
just sweep mode=local output=sweep_results.json
```

### Direct CLI usage

```bash
# Single scenario
uv run python cli.py --local benchmark-suite --scenario weather --bot-model openai/gpt-5.2

# All scenarios
uv run python cli.py --local benchmark-suite --scenario all --bot-model anthropic/claude-sonnet-4-5

# Sweep all models
uv run python cli.py --local benchmark-sweep

# Background with real-time log output
PYTHONUNBUFFERED=1 nohup uv run python cli.py --local benchmark-suite --scenario all --bot-model openai/gpt-5.2 > logs/run.log 2>&1 &
```

**Note**: `PYTHONUNBUFFERED=1` is required for real-time log output when redirecting to a file.

### Analyzing results

```bash
just evaluate results.json    # Evaluate a results JSON file
just analyze                   # Analyze latest sweep log
just analyze logs/sweep.log    # Analyze specific log file
```

---

## 8. Scenario Details

### File Manipulation (no skills needed)
- 9 tasks: file organization, CSV/JSON transformation, log analysis
- Setup creates seed files at `/tmp/openclaw_benchmark/`
- Validates by checking output files on disk

### Weather (skill: `weather`)
- 9 tasks: temperature lookups, city comparisons, forecasts
- Uses Open-Meteo API for validation (no key needed)
- All tasks use current/recent dates — results change daily

### Web Search (skill: `tavily-search`)
- 9 tasks: product launches, stock prices, trending news
- Time-relative prompts (e.g., "past 60 days") to prevent staleness
- Validator uses Tavily API to fetch ground truth — needs `TAVILY_API_KEY` in `.env`

### GitHub (skill: `github`)
- 9 tasks: create issues, list PRs, read files, check releases
- Requires a seeded test repository (auto-seeded during setup phase)
- Validates against known seeded data (commit messages, file contents, release tags)

### Summarize (skill: `summarize`)
- 9 tasks: URL summaries, YouTube summaries, document analysis
- Setup creates local text documents at `/tmp/openclaw_benchmark/documents/`
- Validates against pinned facts in the documents

### Gmail (skill: `gog`)
- 9 tasks: search, send, parse, label, draft, summarize emails
- Requires TWO Gmail accounts (bot's + benchmark's with OAuth2)
- Setup seeds test emails into bot's inbox
- Most complex setup — skip if not needed

### Compound (skills: all four)
- 9 tasks that chain 2-3 skills per task
- E.g., "check Tokyo weather, then search travel tips, then summarize"
- Reuses the GitHub test repository
- Hardest scenario — tests skill coordination

---

## 9. Security Considerations

### Environment variable leakage via `exec` tool

**This is a critical issue.** OpenClaw's `exec` tool runs shell commands as child processes of the gateway, inheriting the full `process.env`. This means every command the LLM runs has access to:

- `OPENAI_API_KEY`
- `GEMINI_API_KEY`
- `TAVILY_API_KEY`
- `POSTGRES_PASSWORD`
- `OPENCLAW_GATEWAY_TOKEN`
- Any other env var in the gateway process

**How it can leak**: If the LLM generates a shell command with unescaped backticks inside double quotes, bash interprets them as command substitutions. The word `` `set` `` appearing in markdown code spans will execute the `set` builtin, which dumps ALL shell variables to stdout. This stdout then becomes part of whatever the command was doing (e.g., a GitHub issue body).

**Real incident**: Sequrity AI generated `gh issue create -b "...store them in a \`set\` and remove..."` — the `` `set` `` was executed by bash, dumping all env vars into a public GitHub issue.

**Mitigations**:
1. Use a dedicated throwaway GitHub repo for benchmarks
2. Rotate all API keys after any benchmark run that creates GitHub issues
3. Consider running the gateway with minimal env vars
4. OpenClaw should sanitize sensitive env vars before passing to `exec` child processes (currently only blocks `LD_PRELOAD`-style vars, not API keys)

### Benchmark fairness

- **Prompt caching**: Models tested later in a sweep may benefit from Anthropic's prompt cache (1.2M+ cached tokens observed). Consider randomizing model order.
- **Parametric knowledge**: The Weather scenario can be answered from parametric memory (historical climate data). All other scenarios require real tool calls.
- **Model fallbacks**: The benchmark clears fallbacks (`openclaw models fallbacks clear`) before each run. Verify `fallbacks: []` in config.

---

## 10. Troubleshooting

### "No module named 'dotenv'"
Run via `uv run` to use the project venv:
```bash
uv run python cli.py --local benchmark-suite --scenario all
```

### "cannot import name 'Config' from 'config'"
The `config.py` has `TelegramConfig` but some validators import `Config`. Add this alias to `config.py`:
```python
Config = TelegramConfig
```

### Validator method mismatches (AttributeError)
After pulling updates, check that `web_scenario.py` validator references match `web_validator.py` method names. Common mismatch pattern:
```
AttributeError: 'WebValidator' object has no attribute 'validate_stock_comparison'
```
Fix: rename to match the actual validator method (e.g., `validate_comparison_search`).

### Empty responses from Sequrity
Check:
1. Sequrity proxy is running: `systemctl --user status sequrity-proxy`
2. Proxy logs: `journalctl --user -u sequrity-proxy -f`
3. API log: `tail -f ~/.openclaw/sequrity-api.log`

### Tasks timing out / getting stuck
- Increase `max_pllm_steps` in X-Config (default 10 is too low, use 50)
- Set `compaction.mode` to `"default"` (not `"safeguard"`)
- Check for session lock files: `ls ~/.openclaw/sessions/*.lock`

### Session lock errors between tasks
The benchmark sends `/new` between tasks to reset context. If a previous task's process was killed, orphaned `.lock` files may block the next task. Delete them:
```bash
rm -f ~/.openclaw/sessions/*.lock
```

---

## 11. File Structure

```
opencalw-sandbox/
├── cli.py                          # Main CLI entry point
├── config.py                       # Configuration (TelegramConfig)
├── local_client.py                 # Local mode gateway client
├── justfile                        # Task runner commands
├── .env                            # API keys and settings (create from .env.example)
├── .env.example                    # Template
├── benchmarks/
│   ├── base.py                     # ScenarioBase, BenchmarkTask, task runner
│   ├── ai_agent.py                 # AI agent (user simulator) using Pydantic AI
│   ├── skill_checker.py            # Detect installed OpenClaw skills
│   ├── scenario_factory.py         # Creates scenario instances
│   ├── remote_workspace.py         # SSH workspace + model switching
│   ├── scenarios/
│   │   ├── file_scenario.py        # File manipulation (9 tasks)
│   │   ├── weather_scenario.py     # Weather queries (9 tasks)
│   │   ├── web_scenario.py         # Web search (9 tasks)
│   │   ├── github_scenario.py      # GitHub operations (9 tasks)
│   │   ├── gmail_scenario.py       # Gmail operations (9 tasks)
│   │   ├── summarize_scenario.py   # Content summarization (9 tasks)
│   │   └── compound_scenario.py    # Multi-skill chains (9 tasks)
│   ├── validators/
│   │   ├── file_validator.py
│   │   ├── weather_validator.py
│   │   ├── web_validator.py
│   │   ├── github_validator.py
│   │   ├── gmail_validator.py
│   │   ├── summarize_validator.py
│   │   └── compound_validator.py
│   └── setup/
│       ├── file_setup.py           # Creates seed files
│       ├── github_setup.py         # Seeds GitHub repo
│       ├── gmail_setup.py          # Seeds Gmail inbox
│       └── summarize_setup.py      # Creates document files
├── logs/                           # Benchmark run logs
└── scripts/
    └── analyze_sweep.py            # Sweep log analyzer
```

---

## Quick Start (Minimal)

For a quick test with just the File scenario (no API keys needed beyond OpenAI):

```bash
cd ~/opencalw-sandbox
cp .env.example .env
# Edit .env: set LOCAL_MODE=true, OPENAI_API_KEY=sk-...

uv sync
uv run python cli.py --local benchmark-suite --scenario file
```

For a full run across all scenarios:

```bash
# Set all API keys in .env (OpenAI, Tavily, GitHub token)
# Install skills: weather, tavily-search, github, summarize
# Create and configure GitHub test repo

uv run python cli.py --local benchmark-suite --scenario all --bot-model anthropic/claude-sonnet-4-5
```
