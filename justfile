# Outcome Engineering Plugin Marketplace — use `just --list` to see commands

# Show available commands
help:
    @just --list

# Run deterministic [test] evidence
test *args:
    python3 -m outcomeeng.validation test -- {{args}}

# Run deterministic [test] evidence with verbose pytest output captured by the recipe runner
test-v *args:
    python3 -m outcomeeng.validation test -- -v {{args}}

# Run one [eval] suite using plugin_dir from eval.toml unless PLUGIN_DIR is set
eval eval_toml:
    #!/usr/bin/env bash
    set -euo pipefail
    plugin_dir="${PLUGIN_DIR:-$(uv run python -c 'import sys, tomllib; from pathlib import Path; data = tomllib.loads(Path(sys.argv[1]).read_text(encoding="utf-8")); print(data.get("plugin_dir", "dist/claude/spec-tree"))' "{{eval_toml}}")}"
    command=(uv run outcomeeng-evals run "{{eval_toml}}" --plugin-dir "$plugin_dir" --workers "${WORKERS:-1}" --max-budget-usd "${MAX_BUDGET_USD:-0.50}" --timeout-seconds "${TIMEOUT_SECONDS:-120}")
    printf 'Running:'
    printf ' %q' "${command[@]}"
    printf '\n'
    "${command[@]}"

# Run one [eval] case by id using plugin_dir from eval.toml unless PLUGIN_DIR is set
eval-case eval_toml case_id:
    #!/usr/bin/env bash
    set -euo pipefail
    plugin_dir="${PLUGIN_DIR:-$(uv run python -c 'import sys, tomllib; from pathlib import Path; data = tomllib.loads(Path(sys.argv[1]).read_text(encoding="utf-8")); print(data.get("plugin_dir", "dist/claude/spec-tree"))' "{{eval_toml}}")}"
    command=(uv run outcomeeng-evals run "{{eval_toml}}" --plugin-dir "$plugin_dir" --workers "${WORKERS:-1}" --max-budget-usd "${MAX_BUDGET_USD:-0.50}" --timeout-seconds "${TIMEOUT_SECONDS:-120}" --case-id "{{case_id}}")
    printf 'Running:'
    printf ' %q' "${command[@]}"
    printf '\n'
    "${command[@]}"

# Run every eval.toml under a node's evals/ directory serially
eval-node node_path:
    #!/usr/bin/env bash
    set -euo pipefail
    if [ ! -d "{{node_path}}/evals" ]; then
        echo "No evals directory found under {{node_path}}" >&2
        exit 1
    fi
    found=0
    while IFS= read -r eval_toml; do
        found=1
        just eval "$eval_toml"
    done < <(find "{{node_path}}/evals" -mindepth 2 -maxdepth 2 -name eval.toml -type f | sort)
    if [ "$found" -eq 0 ]; then
        echo "No eval.toml files found under {{node_path}}/evals" >&2
        exit 1
    fi

# Run deterministic validation only
validation:
    python3 -m outcomeeng.validation validation

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

# Regenerate root CLAUDE.md + AGENTS.md managed Spec Tree sections from rendered runtime templates
build-guides:
    uv run python -m outcomeeng.distribution.guide_diff --write

# Format Python files with ruff
fmt-python *args:
    uv run ruff format {{args}}

# Regenerate root CLAUDE.md + AGENTS.md managed Spec Tree sections and fail on drift (CI gate)
guide-check:
    uv run python -m outcomeeng.distribution.guide_diff

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

# Run validation, then test, through the signal-safe recipe orchestrator
check:
    python3 -m outcomeeng.validation check

# Install lefthook git hooks
hooks-install:
    lefthook install

# Run all pre-commit hooks on staged files
hooks-run:
    lefthook run pre-commit

# Validate SKILL.md frontmatter in the installed Claude cache and configured Codex marketplace source
check-installed marketplace="outcomeeng":
    #!/usr/bin/env bash
    set -euo pipefail
    claude_root=~/.claude/plugins/cache/{{marketplace}}
    codex_root=$(uv run python -m outcomeeng.distribution.marketplace_sources root {{marketplace}})
    claude_count=$(find "$claude_root" -name "SKILL.md" 2>/dev/null | wc -l | tr -d ' ')
    codex_count=$(find "$codex_root/dist/codex" -name "SKILL.md" 2>/dev/null | wc -l | tr -d ' ')
    echo "━━━ Claude Code install ($claude_count files) ━━━"
    if [ "$claude_count" -gt 0 ]; then
        find "$claude_root" -name "SKILL.md" -print0 | xargs -0 uv run python -m outcomeeng.validation.skill_frontmatter
    fi
    echo "━━━ Codex install ($codex_count files) ━━━"
    if [ "$codex_count" -gt 0 ]; then
        find "$codex_root/dist/codex" -name "SKILL.md" -print0 | xargs -0 uv run python -m outcomeeng.validation.skill_frontmatter
    fi
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
