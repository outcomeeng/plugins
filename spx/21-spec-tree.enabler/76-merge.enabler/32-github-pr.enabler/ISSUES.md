# Issues: GitHub PR Transport

## 1. Eval implementation absent for PR orchestration scenarios (FOLLOW-UP)

`github-pr.md` defines the eval coverage model for the argument,
existing-changeset, clean-tree interview, and existing open-PR modes. The node
does not carry co-located eval implementations for those cases, so the scenario
assertions rely on `[audit]` evidence.
`[audit]` fits LLM-driven orchestration behavior that no finite automated test
falsifies, but it leaves a structural regression (for example the skill body
losing its `<mode_detection>` block) undetected by the deterministic gate.
Packaging, frontmatter intent, and closeout semantics use `[audit]`; deterministic
tests do not parse skill Markdown as a proxy for LLM-driven orchestration behavior.

The eval lane can add scenarios mirroring the gate evals under
`spx/21-spec-tree.enabler/76-merge.enabler`:

- Add an `evals/<mode-slug>/` directory per mode with `eval.toml`,
  `cases.jsonl`, and `prompt.md` exercising mode detection from arguments
  and git state, the existing-open-PR route, and the interview-first proposal
  boundary. The interview-first boundary is the case where this transport is
  already selected — `/merge` chose GitHub-PR, or `/manage-github-pr` was invoked directly —
  and the working tree is clean; transport selection is complete at that point,
  so the `/manage-github-pr` eval scope never covers transport-selection logic (that is
  `/merge`'s, declared in `merging.md`).
- Run them in the canonical CI execution surface and commit `history.jsonl`.

Surfaced by the local `changes-reviewer` on `feat/pr-skill`.

## The non-interactive git guard sits on the command that cannot prompt

`GIT_TERMINAL_PROMPT=0` guards `gh pr create` in `src/plugins/spec-tree/skills/open-pr/SKILL.md` (lines 87 and 116). `gh` authenticates through its own stored credential against the GitHub API, so the variable has little to act on there. The `git push` the skill runs immediately before is the command that blocks an unattended run on a credential or host-key prompt, and it carries no guard.

Moving the guard is not a text edit. The skill declares narrow prefix-matched grants (`Bash(gh pr create:*)`, `Bash(git push:*)`, `Bash(git push -u origin HEAD:refs/heads/*)`), and an `ENV=value` prefix changes the command string the grant matches. Whether Claude Code's matcher tolerates an environment-variable prefix decides between three fixes: move the variable, drop it, or reach non-interactivity through `git -c` configuration.

**Settlement condition.** The matcher's treatment of an environment-variable prefix is established, and one fix applies across this skill and `src/plugins/contribute/skills/open-upstream-pr/SKILL.md` in the same change, with each plugin gated by `instructions:skill-auditor`. `spx/43-instructions.enabler/21-skills.enabler/ISSUES.md` records the adjacent question about a skill-directory token in a grant.

**Evidence.** The pattern predates the changeset that found it and is identical in both plugins; fixing it inside one plugin's changeset would leave the marketplace holding two spellings of the same convention.
