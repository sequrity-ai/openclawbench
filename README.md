# OpenClaw Telegram Benchmark Client

A multi-turn conversation benchmark framework for testing OpenClaw bot performance with AI-driven user simulation.

## Features

- **Multi-turn Conversations**: AI agent conducts natural dialogues with the bot to accomplish tasks
- **Dual-mode Support**: Local OpenClaw CLI or remote Telegram bot testing
- **AI-Powered User Simulation**: Uses OpenAI models via Pydantic AI to simulate realistic user behavior
- **Comprehensive Metrics**: Tracks conversation turns, latency, success rate, and full conversation history
- **File Manipulation Testing**: Benchmarks file creation, transformation, and data extraction capabilities
- **Async-first Architecture**: Built for performance with async/await throughout

## Quick Start

See [QUICKSTART.md](QUICKSTART.md) for a quick reference guide.

## Installation

1. Install dependencies using `uv`:

```bash
cd opencalw-sandbox

# Sync dependencies (creates virtual environment automatically)
uv sync

# Or with dev dependencies
uv sync --group dev
```

2. Set up your environment:

```bash
cp .env.example .env
# Edit .env with your API keys and configuration
```

## Configuration

Create a `.env` file with the following settings:

### Required Configuration

```bash
# ===== AI Agent (REQUIRED for multi-turn conversations) =====
OPENAI_API_KEY=your_openai_api_key_here
AI_AGENT_MODEL=gpt-4o-mini

# ===== Mode Selection =====
ASYNC_MODE=true  # Optional - true for async (faster), false for sync
LOCAL_MODE=false  # false for Telegram, true for local CLI

# ===== Telegram Client API (Required for Telegram mode) =====
TELEGRAM_API_ID=your_api_id_from_my_telegram_org
TELEGRAM_API_HASH=your_api_hash_from_my_telegram_org
TELEGRAM_PHONE=+1234567890
OPENCLAW_BOT_USERNAME=your_bot_username
```

### Optional Configuration

```bash
# ===== Conversation Settings =====
MAX_CONVERSATION_TURNS=10
CONVERSATION_TIMEOUT=300.0

# ===== Logging =====
LOG_LEVEL=INFO
DEBUG_MODE=false
```

## Usage

### Using `just` (Recommended)

```bash
# List available commands
just

# Authenticate with Telegram (one-time setup for Telegram mode)
just auth

# Run file benchmark (local mode)
just bench-file

# Run file benchmark (Telegram mode)
just bench-file-telegram

# Run all benchmarks with output
just bench-all-save results.json --telegram
just bench-all-save results.json --local

# Run smoke test
just smoke
```

### Using CLI Directly

```bash
# List available scenarios
uv run python cli.py --local list-scenarios

# Run file scenario (local mode, async for better performance)
uv run python cli.py --async --local benchmark-suite --scenario file

# Run file scenario (local mode, sync)
uv run python cli.py --local benchmark-suite --scenario file

# Run file scenario (Telegram mode, async)
uv run python cli.py --async benchmark-suite --scenario file

# Run file scenario (Telegram mode, sync)
uv run python cli.py benchmark-suite --scenario file

# Save results to file
uv run python cli.py --async benchmark-suite --scenario file --output results.json
```

## Architecture

### Multi-turn Conversation Flow

```
┌──────────────┐
│   User/CLI   │
└──────┬───────┘
       │
       ├─→ Creates BenchmarkAgent (OpenAI-powered)
       │
       ├─→ For each task:
       │   ┌───────────────────────────────────────┐
       │   │ AI Agent conducts conversation:       │
       │   │   Turn 1: Agent → Bot                 │
       │   │          Bot → Agent                  │
       │   │   Turn 2: Agent → Bot (based on Turn 1)
       │   │          Bot → Agent                  │
       │   │   ...                                 │
       │   │   Turn N: Task completion detected    │
       │   └───────────────────────────────────────┘
       │
       ├─→ Validates final bot response
       │
       └─→ Records:
           - Conversation turns (2-10 per task)
           - Full conversation history
           - Completion reason (goal_achieved/max_turns/timeout/error)
           - Total latency
           - Accuracy score
```

### Core Components

1. **benchmarks/ai_agent.py**: Pydantic AI agent for user simulation
   - `BenchmarkAgent`: Conducts multi-turn conversations
   - `ConversationResult`: Tracks conversation outcome
   - `ConversationTurn`: Individual message exchange

2. **benchmarks/base.py**: Benchmark framework
   - `ScenarioBase`: Abstract base for benchmark scenarios
   - `TaskResult`: Extended with conversation tracking
   - `BenchmarkTask`: Task definitions with validation

3. **benchmarks/scenarios/file_scenario.py**: File manipulation tests
   - File creation, CSV transformation, text extraction
   - Validates actual file system state

4. **cli.py**: Command-line interface
   - Creates AI agent with OpenAI API
   - Manages Telegram/local client
   - Exports results

5. **telegram_client.py**: Pyrogram-based Telegram client
   - User-based API (not bot API)
   - Async message handling
   - Response waiting with timeout

## Validation Approach

### Success Rate Determination

The benchmark uses a **two-phase validation approach**:

#### Phase 1: AI Agent Goal Detection (Conversation-level)
- The AI agent determines if the conversation successfully accomplished the task goal
- Based on bot responses and task completion indicators
- Marks conversation as `goal_achieved`, `max_turns`, `timeout`, or `error`
- **This only validates that the conversation appeared successful**

#### Phase 2: Task Validation Function (Accuracy-level)
- Each task has a validation function that checks the **actual result**
- **For local mode**: Validates files directly on local filesystem
- **For Telegram/remote mode**: MANUAL validation required on bot-side

### Remote vs Local Validation

**Local Mode** (`LOCAL_MODE=true`):
- ✅ Full automated validation
- Validates actual file creation, content, format
- Checks filesystem state directly
- Example: Verifies `/tmp/openclaw_benchmark/languages.md` exists and contains 3 languages

**Telegram/Remote Mode** (`LOCAL_MODE=false`):
- ⚠️ **Manual validation required on bot-side**
- AI agent can only verify conversation success
- **You must manually check files on the remote bot server**
- File validators currently check local paths (not applicable for remote)

### Current Limitation

When running in Telegram mode:
1. The AI agent conducts the conversation successfully ✅
2. The bot confirms task completion ✅
3. **But files are created on the REMOTE bot server** 🔴
4. **The benchmark cannot automatically validate remote files** 🔴

### Success Rate Interpretation

- **`success`**: Conversation completed AND validation passed
- **`accuracy_score`**: 0-100% based on validation criteria
- **For Telegram mode**: Both will be `False`/`0%` because validation can't access remote files
- **For Local mode**: Both reflect actual task completion

### Future Enhancement

To enable automated remote validation:
- Option 1: Bot exposes validation endpoints (e.g., `/benchmark_validate`)
- Option 2: Bot returns file contents in responses for validation
- Option 3: SSH-based remote file access (requires credentials)

## Benchmark Scenarios

The benchmark suite includes 6 scenarios, each testing different capabilities. All scenarios use **EASY** difficulty tasks for baseline capability assessment.

### 1. File Manipulation

Tests the bot's ability to create, read, transform, and extract data from files.

**Required Skills**: None (core tools only)

**Tasks:**
1. **File Creation** - Create a markdown file with a bullet list of 3 programming languages
2. **JSON to CSV Transformation** - Convert JSON data to CSV format with specific columns
3. **Text Extraction and Reporting** - Extract action items from notes and save to a file

**Validation**: Local filesystem checks (file existence, content, format)

---

### 2. Gmail Operations

Tests the bot's ability to send, read, and search emails.

**Required Skills**: `clawhub install gog`

**Setup Requirements**:
- Bot's Gmail account configured in OpenClaw
- Benchmark Gmail account with OAuth2 credentials (see `.env.example`)

**Tasks:**
1. **Send Email** - Compose and send an email to specified recipient
2. **Read Email** - Find and read specific email from inbox
3. **Search Email** - Search for emails matching criteria

**Validation**: Checks actual Gmail API for sent emails and inbox state

---

### 3. Web Search

Tests the bot's ability to search the web and retrieve information.

**Required Skills**: `clawhub install steipete/tavily`

**Setup Requirements**: Tavily API key (see `.env.example`)

**Tasks:**
1. **Simple Search** - Search for current information (e.g., "Who won the 2024 Super Bowl?")
2. **Fact Retrieval** - Find specific factual information
3. **Comparison** - Compare information from multiple sources

**Validation**: Checks response contains relevant keywords and information

---

### 4. Weather Information

Tests the bot's ability to retrieve and report weather data.

**Required Skills**: `clawhub install steipete/weather`

**Setup Requirements**: None (weather skill handles API access)

**Tasks:**
1. **Current Weather** - Get current weather for a specific city
2. **Weather Forecast** - Get multi-day weather forecast
3. **Weather Comparison** - Compare weather between two cities

**Validation**: Checks response contains city name and weather-related keywords

---

### 5. Content Summarization

Tests the bot's ability to summarize web pages, videos, and documents.

**Required Skills**: `clawhub install steipete/summarize`

**Setup Requirements**: None (summarize skill handles content fetching)

**Tasks:**
1. **URL Summary** - Summarize a web page (e.g., Wikipedia article)
2. **YouTube Summary** - Summarize a YouTube video
3. **Comparison Summary** - Compare content from two sources

**Validation**: Checks response contains summary keywords and sufficient content

---

### 6. GitHub Operations

Tests the bot's ability to interact with GitHub repositories, issues, and pull requests.

**Required Skills**: `clawhub install steipete/github`

**Setup Requirements**:
- Bot's GitHub account configured in OpenClaw
- Benchmark GitHub account with personal access token (see `.env.example`)
- Test repository for issue creation/management

**Tasks:**
1. **Issue Creation** - Create a new issue in test repository
2. **List Issues** - List all open issues in repository
3. **Repository Info** - Get repository metadata (description, stars, forks)

**Validation**: Checks actual GitHub API for created issues and repository data

## Example Results

```
============================================================
OpenClaw Benchmark Suite
Mode: async
Running 1 scenario(s): File Manipulation
============================================================

Multi-turn mode: max 10 turns, 300.0s timeout, model gpt-4o-mini

[1/1] Running scenario: File Manipulation
Description: Tests agent's ability to create, read, transform, and extract data from files

Task 1: File Creation - ✅ 2 turns, 10.13s, goal_achieved
Task 2: JSON to CSV   - ✅ 4 turns, 23.60s, goal_achieved
Task 3: Text Extract  - ✅ 6 turns, 35.50s, goal_achieved

------------------------------------------------------------
Scenario: File Manipulation
Duration: 69.24s
Average latency: 23.08s per task
------------------------------------------------------------
```

## AI Agent System Prompt

The AI agent is instructed to:
1. Send clear, concise messages to the bot
2. Follow the bot's instructions and respond appropriately
3. Ask clarifying questions if needed
4. Acknowledge when the task is complete
5. Be patient and helpful

The agent adapts its strategy based on bot responses and can conduct up to 10 turns per task.

## Testing

Run tests with uv:

```bash
# All tests
uv run pytest

# Verbose output
uv run pytest -v

# With coverage
uv run pytest --cov=. --cov-report=html
```

## Troubleshooting

### Missing OpenAI API Key

```
ERROR: OPENAI_API_KEY is required for multi-turn conversations.
Please set OPENAI_API_KEY in your .env file.
```

**Solution**: Add your OpenAI API key to `.env`:
```bash
OPENAI_API_KEY=sk-proj-...
```

### Performance Considerations

For best performance, use async mode with `--async` flag or set `ASYNC_MODE=true` in `.env`. Sync mode is also supported but may be slower as it uses `asyncio.run()` internally to wrap async operations.

### Telegram Authentication

For Telegram mode, you need to authenticate once:

```bash
just auth
# Or:
uv run python telegram_auth.py
```

This will:
1. Ask for your phone number
2. Send you a verification code
3. Save the session for future use

### Connection Errors

- Verify your API credentials are correct
- Check internet connectivity
- For Telegram: Ensure you've completed authentication

### Debug Mode

Enable detailed logging:

```bash
# In .env
DEBUG_MODE=true
LOG_LEVEL=DEBUG

# Or via CLI
uv run python cli.py -v --async benchmark-suite --scenario file
```

## Project Structure

```
opencalw-sandbox/
├── pyproject.toml              # Project dependencies
├── README.md                   # This file
├── .env.example                # Example configuration
├── justfile                    # Task runner commands
├── config.py                   # Configuration management
├── telegram_client.py          # Pyrogram Telegram client
├── local_client.py             # Local OpenClaw CLI client
├── cli.py                      # CLI interface
├── benchmarks/
│   ├── __init__.py
│   ├── base.py                 # Benchmark framework base
│   ├── ai_agent.py             # Pydantic AI agent
│   ├── skill_checker.py        # Skill availability checker
│   ├── scenarios/
│   │   ├── __init__.py         # Scenario registry
│   │   ├── file_scenario.py    # File manipulation tests
│   │   ├── gmail_scenario.py   # Email operations tests
│   │   ├── web_scenario.py     # Web search tests
│   │   ├── weather_scenario.py # Weather information tests
│   │   ├── summarize_scenario.py # Content summarization tests
│   │   └── github_scenario.py  # GitHub operations tests
│   ├── setup/
│   │   ├── file_setup.py       # File scenario setup
│   │   ├── gmail_setup.py      # Gmail API helper
│   │   └── github_setup.py     # GitHub API helper
│   └── validators/
│       ├── file_validator.py   # File validation logic
│       ├── gmail_validator.py  # Gmail validation logic
│       ├── web_validator.py    # Web search validation logic
│       ├── weather_validator.py # Weather validation logic
│       ├── summarize_validator.py # Summarize validation logic
│       └── github_validator.py # GitHub validation logic
└── tests/
    ├── conftest.py             # Pytest fixtures
    └── test_*.py               # Test files
```

## Future Enhancements

- **Remote validation**: SSH or API-based remote file validation
- **More scenarios**: Image generation, code analysis, database operations
- **Parallel execution**: Run multiple tasks concurrently
- **Advanced metrics**: Percentile analysis, token usage tracking
- **Result comparison**: Compare benchmark runs over time
- **Difficulty levels**: Add MEDIUM and HARD variants of existing tasks

## License

Part of the Sequrity project.
