# OpenClaw Benchmark — Dev Notes

## Repo layout

- `run.py` — main CLI entry point (`uv run python run.py ...`)
- `task_runner.py` — `TaskRunner`, `LocalBackend`, `DaytonaBackend`, `discover_tasks`, `export_results`
- `config.py` — `TelegramConfig`, `load_config`
- `tasks/` — benchmark task definitions (scenario/task/environment + solution + verifier)
- `tasks/file/` — file-manipulation scenario (9 tasks, easy/medium/hard)

## Running benchmarks

```bash
uv run python run.py --list
uv run python run.py --task tasks/file/file-organization   # single task
uv run python run.py --scenario file                       # full scenario
uv run python run.py --scenario file --difficulty easy
```

The runner auto-starts the openclaw gateway if not running. Uses `openclaw agent --message ... --session-id ...` to send tasks.

## Openclaw fork

Our fork: `https://github.com/Aaron-Zhao123/openclaw.git` (origin)
Upstream: `https://github.com/openclaw/openclaw.git` (upstream)

We maintain 2 extra commits on top of upstream/main:
1. `docs: add Sequrity provider setup guide`
2. `agents: fix sequrity FSM session continuity across turns`

To sync with upstream and push:
```bash
cd ~/openclaw
git fetch upstream
git pull --rebase upstream main
git push origin main --force-with-lease
```

After any code change, rebuild and reinstall:
```bash
cd ~/openclaw
pnpm build
npm install -g /home/openclaw/openclaw
```

pnpm virtual store corruption happens frequently — if packages are missing at runtime, fix with:
```bash
rm -rf node_modules/.pnpm/<corrupt-package>
pnpm install --force
```

## Sequrity FSM integration

The benchmark runs against the sequrity provider (`sequrity/gpt-5.2`) configured in `~/.openclaw/openclaw.json`.

### Tool call ID format

Sequrity uses 18-char IDs: `tc{node_portion}{counter}`
- `tc` — 2-char prefix
- `node_portion` — 12 hex chars (last 12 chars of the server-side session UUID, used for routing)
- `counter` — 4 hex chars (sequential per session, e.g. `0000`, `0001`)

Example: `tcb53d0cc9717a0000`

This fits under openclaw's 40-char sanitization limit, so no truncation occurs.

### Session continuity (X-Session-ID)

The sequrity FSM is stateful server-side. Each API call must reuse the same FSM session or tool call IDs will mismatch and the server returns 404.

**How it works:** The first API response includes `X-Session-ID` in the response headers. All subsequent requests to the same endpoint must include that header.

**Fix in attempt.ts:** We wrap `globalThis.fetch` for the sequrity `baseUrl` to capture `X-Session-ID` from the first response and inject it into all subsequent requests. See `src/agents/pi-embedded-runner/run/attempt.ts` around the `params.provider === "sequrity"` block.

### Why other APIs don't need this

OpenAI, Anthropic, etc. are stateless — every request includes the full conversation history in the body. Sequrity's FSM maintains internal planning/execution state server-side that can't be reconstructed from history alone, hence the need for a session ID.

### strip_response_content

Keep `strip_response_content: true` in the `X-Config` header. When `true`, the endpoint returns the raw response value directly, which is the correct mode for openclaw's agent runner.

With `false`, the endpoint wraps responses in an extra JSON-SSE layer that can cause double-parsing issues.

### Current openclaw.json config (sequrity provider)

```json
{
  "baseUrl": "http://100.83.96.1:8000/control/chat/sequrity_azure/v1",
  "api": "openai-completions",
  "headers": {
    "X-Features": "{\"agent_arch\":\"dual-llm\"}",
    "X-Policy": "{\"mode\": \"standard\", \"presets\": {\"default_allow\": true, \"default_allow_enforcement_level\": \"soft\"}}",
    "X-Config": "{\"fsm\":{\"enable_multistep_planning\":true,\"disable_rllm\":true,\"max_n_turns\":50,\"max_pllm_steps\":50,\"max_pllm_failed_steps\":10,\"history_mismatch_policy\":\"restart_turn\"},\"response_format\":{\"strip_response_content\":true}}"
  }
}
```

## Benchmark results

All scenarios verified (reference solutions 9/9 each). Last run 2026-03-22.

| Scenario | Score | Notes |
|----------|-------|-------|
| file | 6/9 (66.7%) | Fails: data-validation-report, file-modification, multi-step-data-pipeline |
| weather | 6/9 (66.7%) | Fails: today-high-reykjavik, three-city-ranking, vancouver-3day (agent can't get data via web_fetch) |
| web | 7/9 (77.8%) | Fails: pypi-requests-version, requests-pypi-license (PyPI JSON blocked by security wrapper) |
| summarize | 7/9 (77.8%) | Fails: long-document-key-facts, technical-doc-summary |
| github | 5/9 (55.6%) | Fails: repo-created-year, repo-default-branch, repo-description, repo-open-issues |
| compound | 5/9 (55.6%) | Fails: aggregate-and-report, fetch-and-compare, multi-file-merge, summarize-and-count |
| gmail | 8/9 (88.9%) | Fails: count-unread |
