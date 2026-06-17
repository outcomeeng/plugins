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

# Check plugin and marketplace manifests
check-manifests:
    uv run python -m outcomeeng.validation.plugins .

# Check SKILL.md frontmatter in all skills
check-skills:
    find src/plugins dist/claude dist/codex -name "SKILL.md" -exec uv run python -m outcomeeng.validation.skill_frontmatter {} +

# Regenerate committed runtime plugin trees
build-skills:
    # --no-cache: build the wheel from this worktree's own source, not a stale cross-worktree cached wheel.
    uv run --no-cache python -m outcomeeng.distribution.build src dist

# Regenerate the plugin catalog in README.md from manifests and frontmatter
docs:
    uv run python -m outcomeeng.catalog.plugin_catalog --write

# Verify the README.md plugin catalog matches the source manifests (CI-friendly)
docs-check:
    uv run python -m outcomeeng.catalog.plugin_catalog --check

# Format with dprint
fmt *args:
    dprint fmt {{args}}

# Check formatting without modifying (CI-friendly)
fmt-check:
    dprint check

# Run all checks with timing summary (signal-safe Python orchestrator)
check:
    #!/usr/bin/env bash
    set -euo pipefail
    # Preflight: a healthy uv environment must import the toolchain before the gate
    # runs. A stale .venv — most often one built on a Python the system no longer
    # provides after an upgrade — makes every `uv run` step fail with an opaque
    # error. Catch that here and point at the hard reset instead.
    if ! uv_err="$(uv run python -c 'import outcomeeng' 2>&1)"; then
        echo "✗ uv environment is broken: 'uv run python -c \"import outcomeeng\"' failed."
        echo "$uv_err" | sed 's/^/    /'
        echo ""
        echo "  The .venv is likely stale or built on a Python that is no longer"
        echo "  available (e.g. after a system Python upgrade). Hard-reset it with:"
        echo ""
        echo "      just reset-uv"
        echo ""
        exit 1
    fi
    uv run python -m outcomeeng.validation

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
    echo "$claude_files" | xargs uv run python -m outcomeeng.validation.skill_frontmatter
    echo "━━━ Codex install ($codex_count files) ━━━"
    echo "$codex_files" | xargs uv run python -m outcomeeng.validation.skill_frontmatter
    echo "✔ installed skills valid"

# Refresh local Claude and Codex marketplace installs after plugin distribution changes
sync-marketplace base_ref="":
    uv run python -m outcomeeng.distribution.sync {{base_ref}}

# Push directly, then sync local marketplace installs only when plugin distribution changed
push-marketplace *push_args:
    uv run python -m outcomeeng.distribution.push {{push_args}}

# Bump the manifest version of every plugin with changes under src/plugins/<name>/** since base_ref
# Segment defaults to per-plugin auto-detection; pass an explicit segment to override every changed plugin.
bump base_ref="origin/main" segment="":
    uv run python -m outcomeeng.distribution.bump {{ if segment != "" { "--segment " + segment } else { "" } }} {{base_ref}}

# Preview what `just bump` would write without touching any manifest
bump-dry base_ref="origin/main" segment="":
    uv run python -m outcomeeng.distribution.bump --dry-run {{ if segment != "" { "--segment " + segment } else { "" } }} {{base_ref}}

# Exit non-zero if any changed plugin still needs a bump (CI-friendly)
bump-check base_ref="origin/main":
    uv run python -m outcomeeng.distribution.bump --check {{base_ref}}

# Remove every gitignored file and directory (git clean -fdX semantics)
clean:
    uv run python -m outcomeeng.hygiene.clean

# Hard-reset the uv environment: remove .venv and Python tool caches, re-sync, verify
# Use when `just check` reports a broken uv environment (stale .venv after a Python upgrade)
reset-uv:
    #!/usr/bin/env bash
    set -euo pipefail
    echo "Removing .venv..."
    rm -rf .venv
    echo "Removing Python tool caches..."
    rm -rf .mypy_cache .ruff_cache .pytest_cache .hypothesis
    echo "Re-syncing dependencies with uv..."
    uv sync
    echo "Verifying environment..."
    if uv run python -c 'import outcomeeng' >/dev/null 2>&1; then
        echo "✔ uv environment healthy — outcomeeng importable. Run 'just check' to verify the gate."
    else
        echo "✗ outcomeeng still not importable after reset — inspect the 'uv sync' output above."
        exit 1
    fi
