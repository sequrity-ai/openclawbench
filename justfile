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
# Usage: just bench file                    (Telegram mode with remote validation, default)
#        just bench file --mode local       (Local mode)
#        just bench all --mode telegram     (All scenarios)
bench scenario="file" mode="telegram" output="":
    #!/usr/bin/env bash
    if [ "{{mode}}" = "local" ]; then
        if [ -z "{{output}}" ]; then
            uv run python cli.py --async --local benchmark-suite --scenario {{scenario}}
        else
            uv run python cli.py --async --local benchmark-suite --scenario {{scenario}} --output {{output}}
        fi
    elif [ "{{mode}}" = "telegram" ]; then
        if [ -z "{{output}}" ]; then
            uv run python cli.py --async benchmark-suite --scenario {{scenario}}
        else
            uv run python cli.py --async benchmark-suite --scenario {{scenario}} --output {{output}}
        fi
    else
        echo "Error: mode must be 'local' or 'telegram'"
        echo "Usage: just bench <scenario> --mode [local|telegram] [output_file]"
        exit 1
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

# Clean up test artifacts
clean:
    rm -rf .pytest_cache
    rm -rf htmlcov
    rm -rf .coverage
    rm -rf __pycache__
    find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
    find . -type f -name "*.pyc" -delete
    rm -f benchmark_*.json benchmark_*.md *_results.json *_results.md

# Clean up benchmark workspace
clean-workspace:
    rm -rf /tmp/openclaw_benchmark

# Full clean (includes dependencies)
clean-all: clean clean-workspace
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
    @echo "  just bench file              - Run file benchmark (Telegram + remote validation)"
    @echo "  just bench file --mode local - Run file benchmark (local mode)"
    @echo "  just bench all               - Run all benchmarks"
    @echo "  just evaluate results.json   - Evaluate benchmark results"
    @echo "  just auth                    - Authenticate with Telegram"
    @echo ""
    @echo "Run 'just' to see all commands"
