# OpenClaw Telegram Benchmark Client - Justfile
# Run `just` or `just --list` to see available commands

# Default recipe - show help
default:
    @just --list

# Install dependencies with uv
install:
    uv sync

# Install with dev dependencies
install-dev:
    uv sync --group dev

# Run tests
test:
    uv run pytest -v

# Run tests with coverage
test-cov:
    uv run pytest --cov=. --cov-report=html --cov-report=term
    @echo "\nCoverage report generated in htmlcov/index.html"

# Run linter
lint:
    uv run ruff check .

# Format code
format:
    uv run ruff format .

# Check formatting without making changes
format-check:
    uv run ruff format --check .

# Authenticate with Telegram (run once before using Telegram mode)
auth:
    uv run python telegram_auth.py

# Reset Telegram authentication (delete session file)
auth-reset:
    @rm -f *.session
    @echo "✓ Authentication reset. Run 'just auth' to re-authenticate."

# Run benchmark scenario (setup is automatic)
# Scenarios: file, weather, web, summarize, gmail, github, compound, all
# Usage: just bench file                                             (Telegram mode, default)
#        just bench file model="anthropic/claude-opus-4-5"          (Switch bot model first)
#        just bench file mode=local                                  (Local mode)
#        just bench all mode=telegram                                (All scenarios)
#        just bench compound                                         (Multi-skill compound scenario)
# Logs are automatically saved to logs/bench_<scenario>_<timestamp>.log
bench scenario="file" mode="telegram" output="" model="":
    #!/usr/bin/env bash
    mkdir -p logs
    log_file="logs/bench_{{scenario}}_$(date +%Y%m%d_%H%M%S).log"
    echo "Logging to $log_file"
    bot_model_flag=""
    if [ -n "{{model}}" ]; then
        bot_model_flag="--bot-model {{model}}"
    fi
    if [ "{{mode}}" = "local" ]; then
        if [ -z "{{output}}" ]; then
            uv run python cli.py --async --local benchmark-suite --scenario {{scenario}} $bot_model_flag 2>&1 | tee "$log_file"
        else
            uv run python cli.py --async --local benchmark-suite --scenario {{scenario}} $bot_model_flag --output {{output}} 2>&1 | tee "$log_file"
        fi
    elif [ "{{mode}}" = "telegram" ]; then
        if [ -z "{{output}}" ]; then
            uv run python cli.py --async benchmark-suite --scenario {{scenario}} $bot_model_flag 2>&1 | tee "$log_file"
        else
            uv run python cli.py --async benchmark-suite --scenario {{scenario}} $bot_model_flag --output {{output}} 2>&1 | tee "$log_file"
        fi
    else
        echo "Error: mode must be 'local' or 'telegram'"
        echo "Usage: just bench <scenario> [mode=local|telegram] [model=provider/model] [output=file]"
        exit 1
    fi

# Run model sweep: discover all models, run all scenarios for each
# Usage: just sweep                              (Telegram mode, default)
#        just sweep output=sweep_results.json    (with JSON export)
#        just sweep mode=local                   (Local mode - faster, no Telegram)
#        just sweep mode=local output=out.json   (Local mode with JSON export)
sweep output="" mode="telegram":
    #!/usr/bin/env bash
    mkdir -p logs
    log_file="logs/sweep_$(date +%Y%m%d_%H%M%S).log"
    echo "Logging to $log_file"
    if [ "{{mode}}" = "local" ]; then
        local_flag="--local"
    elif [ "{{mode}}" = "telegram" ]; then
        local_flag=""
    else
        echo "Error: mode must be 'local' or 'telegram'"
        echo "Usage: just sweep [mode=local|telegram] [output=file]"
        exit 1
    fi
    if [ -z "{{output}}" ]; then
        uv run python cli.py --async $local_flag benchmark-sweep 2>&1 | tee "$log_file"
    else
        uv run python cli.py --async $local_flag benchmark-sweep --output {{output}} 2>&1 | tee "$log_file"
    fi

# Evaluate benchmark results from JSON file
# Usage: just evaluate results.json
evaluate results="benchmark_results.json":
    #!/usr/bin/env bash
    if [ ! -f "{{results}}" ]; then
        echo "Error: {{results}} not found"
        exit 1
    fi
    echo "=== Benchmark Evaluation Report ==="
    jq -r '
        "Total Scenarios: \(.summary.total_scenarios)",
        "Total Tasks: \(.summary.total_tasks)",
        "Tasks Passed: \(.summary.tasks_passed)",
        "Overall Accuracy: \(.summary.overall_accuracy | round)%",
        "",
        "Scenarios:",
        (.scenarios[] | "  - \(.scenario_name): \(.task_results | map(select(.success)) | length)/\(.task_results | length) tasks passed, \(.average_accuracy | round)% accuracy")
    ' {{results}}

# List recent benchmark log files
logs:
    @ls -lt logs/bench_*.log 2>/dev/null | head -20 || echo "No log files found in logs/"

# Clean up test artifacts
clean:
    rm -rf .pytest_cache
    rm -rf htmlcov
    rm -rf .coverage
    rm -rf __pycache__
    find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
    find . -type f -name "*.pyc" -delete
    rm -f benchmark_*.json benchmark_*.md *_results.json *_results.md

# Clean up benchmark logs
clean-logs:
    rm -rf logs/
    @echo "✓ Benchmark logs removed."

# Clean up benchmark workspace
clean-workspace:
    rm -rf /tmp/openclaw_benchmark

# Full clean (includes dependencies and logs)
clean-all: clean clean-workspace clean-logs
    rm -rf .venv
    rm -rf uv.lock

# Development mode: format, lint, test
dev: format lint test
    @echo "\n✓ All checks passed!"

# CI mode: check formatting, lint, test with coverage
ci: format-check lint test-cov
    @echo "\n✓ CI checks complete!"

# Show project info
info:
    @echo "=== OpenClaw Telegram Benchmark Client ==="
    @echo "Version: 0.1.0"
    @echo "Python: $(python3 --version)"
    @echo "Location: $(pwd)"
    @echo ""
    @echo "Quick commands:"
    @echo "  just bench file                                  - Run file benchmark (Telegram)"
    @echo "  just bench file model=anthropic/claude-opus-4-5 - Run with bot model switch"
    @echo "  just bench weather           - Run weather benchmark"
    @echo "  just bench web               - Run web search benchmark"
    @echo "  just bench summarize         - Run summarize benchmark"
    @echo "  just bench gmail             - Run Gmail benchmark"
    @echo "  just bench github            - Run GitHub benchmark"
    @echo "  just bench compound          - Run compound multi-skill benchmark"
    @echo "  just bench all               - Run all benchmarks"
    @echo "  just bench file mode=local   - Run file benchmark (local mode)"
    @echo "  just logs                    - List recent run logs (logs/bench_*.log)"
    @echo "  just evaluate results.json   - Evaluate benchmark results"
    @echo "  just auth                    - Authenticate with Telegram"
    @echo ""
    @echo "Run 'just' to see all commands"
