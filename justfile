# Outcome Engineering Plugin Marketplace — use `just --list` to see commands

# Show available commands
help:
    @just --list

# Run all tests
test *args:
    uv run python -m pytest {{args}}

# Run tests with verbose output
test-v *args:
    uv run python -m pytest -v {{args}}

# Check plugin and marketplace manifests
check-manifests:
    uv run python -m outcomeeng.scripts.validate_plugins .

# Check SKILL.md frontmatter in all skills
check-skills:
    find plugins -name "SKILL.md" -exec uv run python -m outcomeeng.scripts.validate_skill_frontmatter {} +

# Format with dprint
fmt *args:
    dprint fmt {{args}}

# Check formatting without modifying (CI-friendly)
fmt-check:
    dprint check

# Run all checks with timing summary
check:
    #!/usr/bin/env bash
    set -e
    declare -a labels=()
    declare -a times=()
    total_start=$SECONDS
    step() {
        local label="$1"; shift
        local start=$SECONDS
        echo "━━━ $label ━━━"
        "$@"
        local elapsed=$((SECONDS - start))
        labels+=("$label")
        times+=("$elapsed")
    }
    step "manifests"       uv run python -m outcomeeng.scripts.validate_plugins .
    step "skills"          find plugins -name "SKILL.md" -exec uv run python -m outcomeeng.scripts.validate_skill_frontmatter {} +
    step "fmt-check"       dprint check
    step "pytest"          uv run python -m pytest -v
    total=$((SECONDS - total_start))
    echo ""
    echo "━━━ Timing Summary ━━━"
    for i in "${!labels[@]}"; do
        printf "  %-20s %3ds\n" "${labels[$i]}" "${times[$i]}"
    done
    echo "  ────────────────────────"
    printf "  %-20s %3ds\n" "TOTAL" "$total"

# Install lefthook git hooks
hooks-install:
    lefthook install

# Run all pre-commit hooks on staged files
hooks-run:
    lefthook run pre-commit

# Remove __pycache__, .pytest_cache, and other generated files
clean:
    find . -type f -name '.DS_Store' -delete 2>/dev/null || true
    find . -path '*/__pycache__/*.pyc' -delete 2>/dev/null || true
    find . -type d -name "__pycache__" -empty -delete 2>/dev/null || true
    find . -path '*/.pytest_cache/*' -delete 2>/dev/null || true
    find . -type d -name ".pytest_cache" -empty -delete 2>/dev/null || true
    @echo "Cleaned __pycache__ and .pytest_cache"
