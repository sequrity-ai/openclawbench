# OpenClaw Benchmark Suite - Justfile
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
    @echo "Authentication reset. Run 'just auth' to re-authenticate."

# Global settings (override on command line: just mode=daytona bench file)
mode := "local"
difficulty := "all"
output := ""

# Run benchmark scenario (Harbor-native task runner)
# Scenarios: file, weather, web, summarize, gmail, github, compound, all
# Usage: just bench file                                   (local mode, default)
#        just mode=daytona bench file                      (Daytona sandbox mode)
#        just difficulty=easy bench file                   (filter by difficulty)
#        just bench all                                    (all scenarios)
#        just output=results.json bench file               (export results)
#        just mode=daytona difficulty=easy bench file      (combine options)
# Logs are automatically saved to logs/bench_<scenario>_<timestamp>.log
bench scenario="file":
    #!/usr/bin/env bash
    mkdir -p logs
    log_file="logs/bench_{{scenario}}_$(date +%Y%m%d_%H%M%S).log"
    echo "Logging to $log_file"
    output_flag=""
    if [ -n "{{output}}" ]; then
        output_flag="--output {{output}}"
    fi
    difficulty_flag=""
    if [ "{{difficulty}}" != "all" ]; then
        difficulty_flag="--difficulty {{difficulty}}"
    fi
    if [ "{{mode}}" = "local" ] || [ "{{mode}}" = "daytona" ]; then
        uv run python run.py --scenario {{scenario}} --backend {{mode}} $difficulty_flag $output_flag 2>&1 | tee "$log_file"
    elif [ "{{mode}}" = "telegram" ]; then
        uv run python cli.py --async benchmark-suite --scenario {{scenario}} $output_flag 2>&1 | tee "$log_file"
    else
        echo "Error: mode must be 'local', 'daytona', or 'telegram'"
        exit 1
    fi

# Run a single task by path
# Usage: just run-task tasks/file/file-organization
#        just mode=daytona run-task tasks/file/file-organization
run-task path:
    #!/usr/bin/env bash
    mkdir -p logs
    log_file="logs/task_$(basename {{path}})_$(date +%Y%m%d_%H%M%S).log"
    echo "Logging to $log_file"
    uv run python run.py --task {{path}} --backend {{mode}} 2>&1 | tee "$log_file"

# Verify reference solutions pass all tests
# Usage: just verify                    (all tasks)
#        just verify file               (file tasks only)
verify scenario="all":
    #!/usr/bin/env bash
    uv run python run.py --scenario {{scenario}} --verify-only

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
        "Total Tasks: \(.summary.total_tasks)",
        "Tasks Passed: \(.summary.tasks_passed)",
        "Overall Accuracy: \(.summary.overall_accuracy | round)%",
        "Average Latency: \(.summary.average_latency | round)s",
        "Total Tokens: \(.summary.total_tokens)",
        "",
        "Tasks:",
        (.task_results[] | "  \(if .success then "PASS" else "FAIL" end): \(.task_name) (\(.scenario)) - \(.latency | round)s")
    ' {{results}}

# Analyze sweep log file and generate summary tables
# Usage: just analyze                          (uses latest sweep log)
#        just analyze logs/sweep_20250101.log  (specific log file)
analyze logfile="":
    #!/usr/bin/env bash
    if [ -z "{{logfile}}" ]; then
        uv run python scripts/analyze_sweep.py
    else
        if [ ! -f "{{logfile}}" ]; then
            echo "Error: {{logfile}} not found"
            exit 1
        fi
        uv run python scripts/analyze_sweep.py {{logfile}}
    fi

# List recent benchmark log files
logs:
    @ls -lt logs/bench_*.log logs/task_*.log 2>/dev/null | head -20 || echo "No log files found in logs/"

# List all available tasks
list-tasks:
    @uv run python run.py --list

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
    @echo "Benchmark logs removed."

# Clean up benchmark workspace
clean-workspace:
    rm -rf /tmp/openclaw_benchmark

# Full clean (includes dependencies and logs)
clean-all: clean clean-workspace clean-logs
    rm -rf .venv
    rm -rf uv.lock

# Development mode: format, lint, test
dev: format lint test
    @echo "\nAll checks passed!"

# CI mode: check formatting, lint, test with coverage
ci: format-check lint test-cov
    @echo "\nCI checks complete!"

# Show project info
info:
    @echo "=== OpenClaw Benchmark Suite ==="
    @echo "Version: 0.2.0"
    @echo "Python: $(python3 --version)"
    @echo "Location: $(pwd)"
    @echo ""
    @echo "Quick commands:"
    @echo "  just bench file                        - Run file benchmark (local)"
    @echo "  just bench file mode=daytona            - Run in Daytona sandbox"
    @echo "  just bench file difficulty=easy          - Run easy tasks only"
    @echo "  just bench all                          - Run all benchmarks"
    @echo "  just run-task tasks/file/file-organization  - Run a single task"
    @echo "  just verify                             - Verify reference solutions"
    @echo "  just list-tasks                         - List all available tasks"
    @echo "  just logs                               - List recent run logs"
    @echo "  just analyze                            - Analyze latest sweep log"
    @echo "  just evaluate results.json              - Evaluate benchmark results"
    @echo ""
    @echo "Run 'just' to see all commands"
