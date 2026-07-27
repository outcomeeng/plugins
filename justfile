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
    model="${EVAL_MODEL:-$(uv run python -c 'import sys, tomllib; from pathlib import Path; from outcomeeng_evals.definition import DEFAULT_MODEL; data = tomllib.loads(Path(sys.argv[1]).read_text(encoding="utf-8")); print(data.get("model", DEFAULT_MODEL))' "{{eval_toml}}")}"
    workers="${WORKERS:-$(uv run python -c 'from outcomeeng_evals.ci_execution import DEFAULT_CI_WORKERS; print(DEFAULT_CI_WORKERS)')}"
    max_budget_usd="${MAX_BUDGET_USD:-$(uv run python -c 'from outcomeeng_evals.ci_execution import DEFAULT_CI_MAX_BUDGET_USD; print(DEFAULT_CI_MAX_BUDGET_USD)')}"
    timeout_seconds="${TIMEOUT_SECONDS:-$(uv run python -c 'from outcomeeng_evals.ci_execution import DEFAULT_CI_TIMEOUT_SECONDS; print(DEFAULT_CI_TIMEOUT_SECONDS)')}"
    command=(uv run outcomeeng-evals run "{{eval_toml}}" --plugin-dir "$plugin_dir" --workers "$workers" --max-budget-usd "$max_budget_usd" --model "$model" --timeout-seconds "$timeout_seconds")
    printf 'Running:'
    printf ' %q' "${command[@]}"
    printf '\n'
    "${command[@]}"

# Run one [eval] case by id using plugin_dir from eval.toml unless PLUGIN_DIR is set
eval-case eval_toml case_id:
    #!/usr/bin/env bash
    set -euo pipefail
    plugin_dir="${PLUGIN_DIR:-$(uv run python -c 'import sys, tomllib; from pathlib import Path; data = tomllib.loads(Path(sys.argv[1]).read_text(encoding="utf-8")); print(data.get("plugin_dir", "dist/claude/spec-tree"))' "{{eval_toml}}")}"
    model="${EVAL_MODEL:-$(uv run python -c 'import sys, tomllib; from pathlib import Path; from outcomeeng_evals.definition import DEFAULT_MODEL; data = tomllib.loads(Path(sys.argv[1]).read_text(encoding="utf-8")); print(data.get("model", DEFAULT_MODEL))' "{{eval_toml}}")}"
    workers="${WORKERS:-$(uv run python -c 'from outcomeeng_evals.ci_execution import DEFAULT_CI_WORKERS; print(DEFAULT_CI_WORKERS)')}"
    max_budget_usd="${MAX_BUDGET_USD:-$(uv run python -c 'from outcomeeng_evals.ci_execution import DEFAULT_CI_MAX_BUDGET_USD; print(DEFAULT_CI_MAX_BUDGET_USD)')}"
    timeout_seconds="${TIMEOUT_SECONDS:-$(uv run python -c 'from outcomeeng_evals.ci_execution import DEFAULT_CI_TIMEOUT_SECONDS; print(DEFAULT_CI_TIMEOUT_SECONDS)')}"
    command=(uv run outcomeeng-evals run "{{eval_toml}}" --plugin-dir "$plugin_dir" --workers "$workers" --max-budget-usd "$max_budget_usd" --model "$model" --timeout-seconds "$timeout_seconds" --case-id "{{case_id}}")
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

# Materialize producer-derived eval prompts under a root directory
eval-materialize-prompts root:
    uv run outcomeeng-evals materialize-prompts "{{root}}" --repo-root .

# Check producer-derived eval prompts under a root directory for drift
eval-materialize-prompts-check root:
    uv run outcomeeng-evals materialize-prompts "{{root}}" --repo-root . --check

# Regenerate the eval CI workflow's trigger paths from the eval definitions
build-eval-triggers:
    uv run outcomeeng-evals materialize-ci-triggers spx --workflow .github/workflows/spec-tree-evals.yml --repo-root .

# Check the eval CI workflow's trigger paths for drift
eval-triggers-check:
    uv run outcomeeng-evals materialize-ci-triggers spx --workflow .github/workflows/spec-tree-evals.yml --repo-root . --check

# Run deterministic validation only
validation:
    python3 -m outcomeeng.validation validation

# Check plugin and marketplace manifests
check-manifests:
    uv run python -m outcomeeng.validation.plugins .

# Check skill Markdown formatting and SKILL.md frontmatter
check-skills:
    dprint check --config dprint.jsonc "src/plugins/**/skills/**/*.md" "src/templates/**/*.md" "dist/claude/**/skills/**/*.md" "dist/codex/**/skills/**/*.md"
    # src/templates is formatted but not frontmatter-validated: an unrendered
    # template carries build tokens in place of values, so only its per-plugin
    # renders under dist/ are real skill frontmatter.
    find src/plugins dist/claude dist/codex -name "SKILL.md" -exec uv run python -m outcomeeng.validation.skill_frontmatter {} +

# Regenerate committed runtime plugin trees
build-skills:
    # --no-cache: build the wheel from this worktree's own source, not a stale cross-worktree cached wheel.
    uv run --no-cache python -m outcomeeng.distribution.build src dist

# Place every plugin's agent definitions into this checkout, through the same
# shipped lifecycle-skill script a consumer runs, so the repo dogfoods its own
# distribution rather than writing the directory by a private path.
place-agents:
    #!/usr/bin/env bash
    set -euo pipefail
    for skill in dist/codex/*/skills/*-plugin; do
        python3 "${skill}/scripts/place_agents.py" --checkout .
    done

# Fail when the committed checkout agent directory differs from what the
# shipped lifecycle skills would place.
place-agents-check:
    #!/usr/bin/env bash
    set -euo pipefail
    status=0
    for skill in dist/codex/*/skills/*-plugin; do
        python3 "${skill}/scripts/place_agents.py" --checkout . --check || status=1
    done
    if [ "${status}" -ne 0 ]; then
        echo "error: .codex/agents differs from the shipped definitions; run 'just place-agents'" >&2
        exit 1
    fi

# Regenerate root CLAUDE.md + AGENTS.md managed Spec Tree instruction blocks from rendered harness templates
build-instructions:
    uv run python -m outcomeeng.distribution.instruction_block --write

# Format Python files with ruff
fmt-python *args:
    uv run ruff format {{args}}

# Regenerate root CLAUDE.md + AGENTS.md managed Spec Tree instruction blocks and fail on drift (CI gate)
instructions-check:
    uv run python -m outcomeeng.distribution.instruction_block

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

# Run selected local gate steps through the signal-safe recipe orchestrator
check:
    python3 -m outcomeeng.validation check

# Run validation, then test, through the signal-safe recipe orchestrator
check-full:
    python3 -m outcomeeng.validation check-full

# Install lefthook git hooks
hooks-install:
    lefthook install

# Run all pre-commit hooks on staged files
hooks-run:
    lefthook run pre-commit

# Install every committed marketplace plugin into selected persistent agent state
install-marketplace *install_args:
    uv run python -m outcomeeng.distribution.installation {{install_args}}

# Verify installation with real agent CLIs in disposable homes
verify-marketplace-installation:
    just test spx/32-distribution.enabler/21-installation.enabler/21-repository-installation.enabler/tests/test_repository_installation.scenario.l2.py

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
# Use when `just check-full` reports a broken uv environment (stale .venv after a Python upgrade)
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
        echo "✔ uv environment healthy — outcomeeng importable. Run 'just check-full' to verify the full gate."
    else
        echo "✗ outcomeeng still not importable after reset — inspect the 'uv sync' output above."
        exit 1
    fi
