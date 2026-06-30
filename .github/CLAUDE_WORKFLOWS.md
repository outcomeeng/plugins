# Claude Code GitHub Workflows

This repository uses reusable workflows from [outcomeeng/gh-actions](https://github.com/outcomeeng/gh-actions) for Claude Code integration and a local preview workflow for the shipped `review-changes` skill.

1. **`spec-tree.yml`** — `@spec-tree` mention handler. Wraps the generic `claude.yml` reusable with `use_project_plugins: true` so the methodology skills declared in `.claude/settings.json` (`/contextualizing`, `/authoring`, `/decomposing`, etc.) are installed for every mention.
2. **`spec-tree-review.yml`** — Automatic PR review on `opened` / `synchronize` / `reopened`. Wraps the generic `claude-code-review.yml` reusable while the hosted review integration is still upstream-owned.
3. **`review-changes-preview.yml`** — Automatic PR preview on `opened` / `synchronize` / `reopened`. Installs Claude Code and `spx`, loads `dist/claude/spec-tree`, invokes the shipped `review-changes` skill against the PR base/head range, and writes the sealed journal projection to the job summary.

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
      timeout_minutes: ${{ vars.CLAUDE_REVIEW_TIMEOUT_MINUTES || 15 }}
      # append_allow_list: "Read,Grep,Glob,Bash(git:*)"   # extends defaults
      # use_project_plugins: true                         # install plugins from .claude/settings.json
```

`spec-tree.yml` (the @-mention caller) accepts `trigger_phrase` (default `@spec-tree`), `concurrency_cancel`, `claude_args`, and `use_project_plugins` (defaults to `true`). See the inline comments in each workflow file for the full set and their trade-offs.

`review-changes-preview.yml` does not read repository-root review prompt files. The preview prompt lives inside `dist/claude/spec-tree/skills/review-changes/references/review-prompt.md`, generated from the authored skill source.

### Pinning

Both callers pin the upstream reusable by full commit SHA (not `@main`). The reusable's `validate-workflow` job compares the caller workflow file at the PR head against the file on the default branch; pinning by SHA ensures the composite actions the reusable checks out stay in lockstep with the workflow content. Update the pin by editing the `@<sha>` in both files when consuming a new upstream release.

## Authorization

Both workflows run only when the PR author or mention author has `admin`, `maintain`, or `write` permission on this repository, queried at runtime via the GitHub API. External contributors are rejected with a clear notice in the job log. The authorization model lives entirely inside the upstream reusables — these callers do not configure it.

## Reference

- Upstream workflow reusables: [`outcomeeng/gh-actions/.github/workflows/`](https://github.com/outcomeeng/gh-actions/tree/main/.github/workflows)
- Upstream caller examples: [`outcomeeng/gh-actions/examples/caller-workflows/`](https://github.com/outcomeeng/gh-actions/tree/main/examples/caller-workflows)
- Upstream README: [`outcomeeng/gh-actions#readme`](https://github.com/outcomeeng/gh-actions#readme)
