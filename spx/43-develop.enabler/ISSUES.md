# Issues: Develop Plugin

## 1. Named-subject convention has drifted across marketplace skills (OPEN)

The `develop` plugin's `standardizing-agent-prompts` `<voice>` rule requires authored skill
content to drop the subject (imperative mood) by default and name **"Claude"** for behavioral
claims, tendencies, and failure modes. **"the agent"**, **"an agent"**, **"the model"**, and
**"you"** are banned subjects. The build ships authored content verbatim to both runtimes (no
identity substitution today), so the authored canon is always "Claude"; other-agent targeting is
a downstream replacement step.

This convention has drifted: ~37 executing-instance "the agent" / "an agent" sites remain across
12 skills (counts from a `git grep` survey on 2026-06-12, excluding legitimate uses —
`agentic`/`agent review` domain terms, named subagents like `changes-reviewer agent`, and
`agent definition`/`agent prompt` references):

| Skill                                    | Sites |
| ---------------------------------------- | ----- |
| `spec-tree/skills/standardizing-merging` | 9     |
| `spec-tree/skills/auditing`              | 5     |
| `spec-tree/skills/reviewing-changes`     | 4     |
| `develop/skills/auditing-skills`         | 4     |
| `spec-tree/skills/github-actions`        | 3     |
| `spec-tree/skills/decomposing`           | 3     |
| `spec-tree/skills/understanding`         | 2     |
| `develop/skills/standardizing-skills`    | 2     |
| `excalidraw*/skills/excalidrawing`       | 2     |
| `spec-tree/skills/managing-pr`           | 1     |
| `develop/skills/auditing-commands`       | 1     |
| `spec-tree/skills/applying`              | 1     |

The "the model" / standalone "you" survey is noisier — most hits are legitimate (domain/data
models in `architecting-python`, reader-addressing "you" in the prose skills) and must be
classified per-site, not bulk-replaced.

**Required handling (fresh-effort sweep PR):**

- Per site, apply the `<voice>` rule by judgment: **imperative** (drop the subject) for an
  instruction, **"Claude"** for a behavioral claim / failure mode. Not a blind `sed`.
- Exclude legitimate uses: `agentic`, `agent review`/`[audit]`, named subagents
  (`changes-reviewer`/`applier`/`*-auditor`/`pr-reviewer` agent), `agent definition`/`agent prompt`.
- Run `develop:skill-auditor` (`/auditing-skills`) on each changed skill to confirm conformance —
  it is the only gate that loads `standardizing-agent-prompts`.
- `standardizing-merging`, `managing-pr`, and `reviewing-changes` are live PR-flow skills; edit them
  deliberately (a session that ships via `/pr` is exercising them concurrently).

Surfaced 2026-06-12 while correcting a named-subject regression introduced in PR #169 and fixed in
PR #171 (`understanding` skill); the broader drift was deferred to a dedicated sweep.
