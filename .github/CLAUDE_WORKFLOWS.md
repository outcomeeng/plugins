# Claude Code GitHub Workflows

This repository uses reusable workflows from [outcomeeng/gh-actions](https://github.com/outcomeeng/gh-actions) for Claude Code integration. The two active callers under `.github/workflows/` are release-lane consumers of the templates from `outcomeeng/gh-actions/examples/caller-workflows/`, pinned by full commit SHA with a trailing `# main` tracked-branch comment:

1. **`spec-tree.yml`** — `@spec-tree` mention handler. Wraps the generic `claude.yml` reusable. `use_project_plugins` is controlled by `vars.SPEC_TREE_USE_PROJECT_PLUGINS == 'true'`, so the methodology skills declared in `.claude/settings.json` are installed only when the repository variable opts in.
2. **`spec-tree-review.yml`** — Automatic PR review on `opened` / `synchronize` / `reopened`. Wraps the `spec-tree-review.yml` reusable, which uses the shipped `review-changes` prompt and the findings-only `blocking` / `debt` taxonomy governed in the spec-tree plugin.

A separate `distribute-skills.yml` workflow handles plugin distribution and is unrelated to the Claude callers.

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

Both callers pin the upstream reusable by full commit SHA (not `@main`). The reusable's `validate-workflow` job compares the caller workflow file at the PR head against the file on the default branch; pinning by SHA ensures the composite actions the reusable checks out stay in lockstep with the workflow content. Update the pin by editing the `@<sha>` in both files when consuming a new upstream release.

Routine release-lane updates come from Renovate. `renovate.json` extends `github>outcomeeng/gh-actions//renovate-presets/gh-actions-consumer`, which keeps `outcomeeng/gh-actions` reusable workflow references SHA-pinned and grouped. The trailing `# main` comment on each `uses:` line is the tracked branch Renovate advances.

## Authorization

Both workflows run only when the PR author or mention author has `admin`, `maintain`, or `write` permission on this repository, queried at runtime via the GitHub API. External contributors are rejected with a clear notice in the job log. The authorization model lives entirely inside the upstream reusables — these callers do not configure it.

## Reference

- Upstream workflow reusables: [`outcomeeng/gh-actions/.github/workflows/`](https://github.com/outcomeeng/gh-actions/tree/main/.github/workflows)
- Upstream caller examples: [`outcomeeng/gh-actions/examples/caller-workflows/`](https://github.com/outcomeeng/gh-actions/tree/main/examples/caller-workflows)
- Upstream README: [`outcomeeng/gh-actions#readme`](https://github.com/outcomeeng/gh-actions#readme)
