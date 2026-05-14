# Outcome Engineering Plugin Marketplace — use `just --list` to see commands

# Show available commands
help:
    @just --list

# Run Python tests
test *args:
    uv run python -m pytest {{args}}

# Run Python tests with verbose output
test-v *args:
    uv run python -m pytest -v {{args}}

# Run TypeScript tests via vitest
test-ts *args:
    pnpm test {{args}}

# Check plugin and marketplace manifests
check-manifests:
    uv run python -m outcomeeng.scripts.validate_plugins .

# Check SKILL.md frontmatter in all skills
check-skills:
    find plugins -name "SKILL.md" -exec uv run python -m outcomeeng.scripts.validate_skill_frontmatter {} +

# Regenerate the plugin catalog in README.md from manifests and frontmatter
docs:
    uv run python -m outcomeeng.scripts.generate_plugin_catalog --write

# Verify the README.md plugin catalog matches the source manifests (CI-friendly)
docs-check:
    uv run python -m outcomeeng.scripts.generate_plugin_catalog --check

# Format with dprint
fmt *args:
    dprint fmt {{args}}

# Check formatting without modifying (CI-friendly)
fmt-check:
    dprint check

# Run all checks with timing summary (signal-safe Python orchestrator)
check:
    uv run python -m outcomeeng.scripts.check

# Install lefthook git hooks
hooks-install:
    lefthook install

# Run all pre-commit hooks on staged files
hooks-run:
    lefthook run pre-commit

# Validate SKILL.md frontmatter in installed Claude and Codex marketplace caches
check-installed marketplace="outcomeeng":
    #!/usr/bin/env bash
    set -euo pipefail
    claude_files=$(find ~/.claude/plugins/cache/{{marketplace}} -name "SKILL.md")
    codex_files=$(find ~/.codex/.tmp/marketplaces/{{marketplace}} -name "SKILL.md")
    claude_count=$(echo "$claude_files" | grep -c . || true)
    codex_count=$(echo "$codex_files" | grep -c . || true)
    echo "━━━ Claude Code install ($claude_count files) ━━━"
    echo "$claude_files" | xargs uv run python -m outcomeeng.scripts.validate_skill_frontmatter
    echo "━━━ Codex install ($codex_count files) ━━━"
    echo "$codex_files" | xargs uv run python -m outcomeeng.scripts.validate_skill_frontmatter
    echo "✔ installed skills valid"

# Refresh local Claude and Codex marketplace installs after plugin distribution changes
sync-marketplace base_ref="":
    #!/usr/bin/env bash
    set -euo pipefail
    for tool in claude codex uv; do
        if ! command -v "$tool" >/dev/null 2>&1; then
            echo "Missing required tool: $tool" >&2
            exit 1
        fi
    done
    if [[ -n "{{base_ref}}" ]]; then
        changed_paths="$(git diff --name-only "{{base_ref}}" HEAD -- plugins .claude-plugin .agents/plugins)"
        if [[ -z "$changed_paths" ]]; then
            echo "No plugin distribution changes since {{base_ref}}; skipping marketplace sync"
            exit 0
        fi
    fi
    claude plugin marketplace update outcomeeng
    uv run python -m outcomeeng.scripts.preserve_codex_plugin_cache outcomeeng
    uv run python -m outcomeeng.scripts.validate_install
    just check-installed

# Push directly, then sync local marketplace installs only when plugin distribution changed
push-marketplace *push_args:
    #!/usr/bin/env bash
    set -euo pipefail
    for tool in git claude codex uv; do
        if ! command -v "$tool" >/dev/null 2>&1; then
            echo "Missing required tool: $tool" >&2
            exit 1
        fi
    done
    before_ref="$(git rev-parse @{upstream} 2>/dev/null || true)"
    git push {{push_args}}
    if [[ -n "$before_ref" ]]; then
        just sync-marketplace "$before_ref"
    else
        just sync-marketplace
    fi

# Remove __pycache__, .pytest_cache, and other generated files
clean:
    find . -type f -name '.DS_Store' -delete 2>/dev/null || true
    find . -path '*/__pycache__/*.pyc' -delete 2>/dev/null || true
    find . -type d -name "__pycache__" -empty -delete 2>/dev/null || true
    find . -path '*/.pytest_cache/*' -delete 2>/dev/null || true
    find . -type d -name ".pytest_cache" -empty -delete 2>/dev/null || true
    @echo "Cleaned __pycache__ and .pytest_cache"
