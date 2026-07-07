# Claude Code GitHub Workflows

This repository uses reusable workflows from [outcomeeng/gh-actions](https://github.com/outcomeeng/gh-actions) for Claude Code integration. The two active callers under `.github/workflows/` are beta-test consumers of the templates from `outcomeeng/gh-actions/examples/caller-workflows/`, pinned to `@main` with an explicit `# BETA TESTER:` marker:

1. **`spec-tree.yml`** — `@spec-tree` mention handler. Wraps the generic `claude.yml` reusable. `use_project_plugins` is controlled by `vars.SPEC_TREE_USE_PROJECT_PLUGINS == 'true'`, so the methodology skills declared in `.claude/settings.json` are installed only when the repository variable opts in.
2. **`spec-tree-review.yml`** — Automatic PR review on `opened` / `synchronize` / `reopened`. Wraps the `spec-tree-review.yml` reusable, which uses the shipped `review-changes` prompt and the findings-only `blocking` / `debt` taxonomy governed in the spec-tree plugin.

A separate `distribute-skills.yml` workflow handles plugin distribution and is unrelated to the Claude callers.

The generic `claude.yml` and `claude-code-review.yml` callers are deliberately absent from `.github/workflows/`. Keeping them active alongside the spec-tree callers would run multiple agent workflows on the same issue and pull-request events, spending tokens without adding a distinct product signal. If a copy is needed for reference, keep it outside the active workflow directory or disable it before merge.

## Configuration

### Secrets

Add `CLAUDE_CODE_OAUTH_TOKEN` to repository secrets (Settings → Secrets and variables → Actions → Secrets).

### Customization

Edit the `with:` block in either caller. The inputs that matter most:

```yaml
jobs:
  spec-tree-review:
    uses: outcomeeng/gh-actions/.github/workflows/spec-tree-review.yml@<sha>
    secrets:
      CLAUDE_CODE_OAUTH_TOKEN: ${{ secrets.CLAUDE_CODE_OAUTH_TOKEN }}
    with:
      concurrency_cancel: true
      timeout_minutes: ${{ vars.SPEC_TREE_REVIEW_TIMEOUT_MINUTES || '30' }}
      # append_allow_list: "Read,Grep,Glob,Bash(git:*)"   # extends defaults
      # use_project_plugins: true                         # install plugins from .claude/settings.json
```

`spec-tree-review.yml` deliberately does not expose `custom_prompt` — the prompt is baked in. Call `outcomeeng/gh-actions/.github/workflows/claude-code-review.yml` directly when full prompt control is needed.

`spec-tree.yml` (the @-mention caller) accepts `trigger_phrase` (default `@spec-tree`), `concurrency_cancel`, `claude_args`, and `use_project_plugins` (default disabled unless `vars.SPEC_TREE_USE_PROJECT_PLUGINS == 'true'`). See the inline comments in each workflow file for the full set and their trade-offs.

### Pinning

This repository intentionally uses the `outcomeeng/gh-actions` beta-tester exception: both active callers track `@main` so upstream reusable changes are exercised here before production consumers receive a SHA-pinned release update. The trade-off is explicit in each workflow file with the `# BETA TESTER:` marker required by the upstream README's Security section.

Production consumers should pin the upstream reusable by full commit SHA with a trailing tracked-branch comment. Renovate can advance SHA-pinned callers; it cannot advance this repo's `@main` beta references, which is the intended beta behavior. Pin both callers back to full SHAs when this repository graduates from beta-tester usage to production-caller usage.

## Authorization

Both workflows run only when the PR author or mention author has `admin`, `maintain`, or `write` permission on this repository, queried at runtime via the GitHub API. External contributors are rejected with a clear notice in the job log. The authorization model lives entirely inside the upstream reusables — these callers do not configure it.

## Reference

- Upstream workflow reusables: [`outcomeeng/gh-actions/.github/workflows/`](https://github.com/outcomeeng/gh-actions/tree/main/.github/workflows)
- Upstream caller examples: [`outcomeeng/gh-actions/examples/caller-workflows/`](https://github.com/outcomeeng/gh-actions/tree/main/examples/caller-workflows)
- Upstream README: [`outcomeeng/gh-actions#readme`](https://github.com/outcomeeng/gh-actions#readme)
