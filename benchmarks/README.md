# OpenClaw Benchmark Scenarios

This directory contains benchmark scenarios for testing OpenClaw bot capabilities across different domains.

## Available Scenarios

### 1. File Manipulation (`file`)

Tests the bot's ability to create, read, transform, and extract data from files.

**Required Skills**: None (uses built-in read/write/exec tools only)

**Setup Required**: None - automatically creates a temporary workspace

**Tasks**:
1. **File Organization** (Medium): Read JSON data and create directory structure with profile files
2. **File Modification** (Medium): Count action items from notes and update profile files
3. **File Consolidation** (Hard): Aggregate data from multiple files into sorted CSV

**Run**:
```bash
uv run python cli.py benchmark-suite --scenario file
```

---

### 2. Gmail Email (`gmail`)

Tests the bot's ability to search, send, and parse emails via Gmail.

**Required Skills**: `gog`

**Setup Required**: ⚠️ **TWO Gmail accounts needed**

#### Gmail Setup Instructions

You need **two separate Gmail accounts**:

1. **Bot's Gmail Account** (e.g., `openclaw-bot@gmail.com`)
   - Configure in OpenClaw bot: `clawhub install gog`
   - Follow prompts to connect your Gmail account
   - Bot will read and send emails from this account

2. **Benchmark Gmail Account** (e.g., `openclaw-benchmark@gmail.com`)
   - Separate account for benchmark validation
   - You'll need OAuth2 credentials for THIS account

#### Getting OAuth2 Credentials

**Option A: Using OAuth Playground (Recommended)**

1. Go to [Google Cloud Console](https://console.cloud.google.com/)
   - Create a new project or select existing one
   - Enable **Gmail API**
   - Create OAuth2 credentials (Desktop app type)
   - Note your **Client ID** and **Client Secret**

2. Go to [OAuth 2.0 Playground](https://developers.google.com/oauthplayground/)
   - Click ⚙️ → Check "Use your own OAuth credentials"
   - Enter your Client ID and Client Secret
   - Select Gmail API scopes:
     - `https://www.googleapis.com/auth/gmail.readonly`
     - `https://www.googleapis.com/auth/gmail.send`
     - `https://www.googleapis.com/auth/gmail.modify`
   - Click "Authorize APIs" and sign in with your **benchmark Gmail account**
   - Exchange authorization code for tokens
   - Copy the **refresh_token**

**Option B: Using Helper Script**

```bash
# Install dependencies
pip install google-auth-oauthlib google-auth-httplib2

# Run the helper script
python tools/get_gmail_token.py

# Follow prompts to get your credentials
```

#### Configuration

Add to your `.env` file:

```bash
# OAuth2 credentials for BENCHMARK Gmail account
GOOGLE_CLIENT_ID=your_benchmark_gmail_client_id
GOOGLE_CLIENT_SECRET=your_benchmark_gmail_secret
GOOGLE_REFRESH_TOKEN=your_benchmark_gmail_refresh_token

# The two Gmail addresses
GMAIL_BENCHMARK_EMAIL=openclaw-benchmark@gmail.com  # Account with OAuth2 credentials
GMAIL_BOT_EMAIL=openclaw-bot@gmail.com              # Bot's Gmail account
```

**Tasks**:
1. **Email Search** (Easy): Find email by subject in inbox
2. **Email Send** (Medium): Send email to benchmark account
3. **Email Data Extraction** (Hard): Parse structured data from email

**How It Works**:
- Benchmark sends test emails TO bot's inbox
- Bot searches, reads, and parses emails
- Bot sends email TO benchmark account
- Validation checks benchmark's inbox for bot's email

**Run**:
```bash
# Using just (recommended)
just bench gmail

# Or directly with Python
uv run python cli.py --async benchmark-suite --scenario gmail
```

**Note**: The `--async` flag is required for multi-turn conversations to work properly.

---

### 3. Web Search (`web`)

Tests the bot's ability to search the web for information and extract relevant data using Tavily.

**Required Skills**: `tavily-search`

**Setup Required**: Tavily API key

#### Tavily Setup Instructions

1. **Get Tavily API Key**
   - Visit [https://tavily.com](https://tavily.com)
   - Sign up for an account
   - Generate an API key from your dashboard

2. **Install Tavily Skill in Bot**
   ```bash
   clawhub install tavily-search
   ```
   - Follow prompts to connect your Tavily API key

3. **Configure Benchmark** (Optional)

   Add to your `.env` file (only needed if benchmark requires direct API access):
   ```bash
   TAVILY_API_KEY=your_tavily_api_key_here
   ```

**Tasks**:
1. **Factual Web Search** (Easy): Search for well-known facts (e.g., Python creation date)
2. **Comparison Research** (Medium): Compare two technologies with key differences
3. **Current Events Research** (Hard): Research recent developments with specific details

**How It Works**:
- Bot receives search queries about various topics
- Bot uses Tavily to search the web
- Bot extracts and reports relevant information
- Validation checks for expected facts, keywords, and topics

**Run**:
```bash
# Using just (recommended)
just bench web

# Or directly with Python
uv run python cli.py --async benchmark-suite --scenario web
```

**Note**: The `--async` flag is required for multi-turn conversations to work properly.

---

## Running Benchmarks

### List Available Scenarios

```bash
uv run python cli.py list-scenarios
```

### Run a Specific Scenario

```bash
# Using just (recommended)
just bench <scenario_name>

# Or directly with Python (requires --async for multi-turn)
uv run python cli.py --async benchmark-suite --scenario <scenario_name>
```

### Run All Scenarios

```bash
# Using just (recommended)
just bench all

# Or directly with Python
uv run python cli.py --async benchmark-suite --scenario all
```

### Options

- `--async`: Enable async mode (REQUIRED for multi-turn conversations)
- `--skip-missing`: Skip scenarios with missing skills (default: false)
- `--output <path>`: Export results to markdown file
- `--mode <local|telegram>`: Choose mode (just command only)

---

## Benchmark Architecture

### Components

```
benchmarks/
├── base.py              # Base classes for scenarios and tasks
├── ai_agent.py          # AI agent for simulating user conversations
├── skill_checker.py     # Utilities for checking available skills
├── scenarios/           # Scenario implementations
│   ├── file_scenario.py
│   ├── gmail_scenario.py
│   └── ...
├── validators/          # Task validators
│   ├── file_validator.py
│   ├── gmail_validator.py
│   └── ...
├── setup/              # Setup helpers for scenarios
│   ├── file_setup.py
│   ├── gmail_setup.py
│   └── ...
└── README.md           # This file
```

### How Benchmarks Work

1. **Pre-check**: Verify required skills are installed and APIs are accessible
2. **Setup**: Create test data (files, emails, etc.)
3. **Execution**: AI agent has multi-turn conversation with bot to complete tasks
4. **Validation**: Validate bot's actions (binary scoring: 0% or 100% per task)
5. **Cleanup**: Remove test data

### Adding New Scenarios

1. Create scenario class in `benchmarks/scenarios/`
2. Create validators in `benchmarks/validators/`
3. Create setup helpers in `benchmarks/setup/` (if needed)
4. Register in `benchmarks/scenarios/__init__.py`
5. Update this README with setup instructions

---

## Scoring

All tasks use **binary scoring**:
- **100%**: Task completed successfully
- **0%**: Task failed

**Overall scenario score** = Average of all task scores

---

## Common Issues

### "Skill not installed" error

Install the required skill:
```bash
clawhub install <skill_name>

# For Gmail scenario specifically:
clawhub install gog
```

### "Cannot access API" error

- Check your API credentials in `.env`
- Verify the API is enabled in your cloud console
- Ensure OAuth2 tokens haven't expired

### File scenario fails

- Check workspace permissions
- Ensure the bot can read/write to `/tmp/opencalw_benchmark/`

### Gmail scenario fails

- Verify you're using **two different Gmail accounts**
- Ensure OAuth2 credentials are for the **benchmark account**, not bot's account
- Check that both emails are correctly configured in `.env`
- Wait a few seconds for emails to propagate through Gmail

---

## Configuration Reference

See `.env.example` for all configuration options.

Key settings:
- `AI_AGENT_MODEL`: OpenAI model for user simulation (default: `gpt-4o-mini`)
- `MAX_CONVERSATION_TURNS`: Maximum turns per task (default: 10)
- `CONVERSATION_TIMEOUT`: Maximum time per conversation (default: 300s)

---

## Local vs Telegram Mode

**Local Mode** (`LOCAL_MODE=true`):
- Bot runs on your machine via `openclaw agent`
- Skill detection available
- File operations are local

**Telegram Mode** (`LOCAL_MODE=false`):
- Bot runs remotely via Telegram
- Skill detection unavailable (all scenarios run)
- May require remote setup for file operations

---

## Support

For issues or questions:
- Check [OpenClaw Documentation](https://docs.openclaw.ai/)
- Report bugs at: https://github.com/anthropics/claude-code/issues
