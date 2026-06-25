# Issues — Merging

Known follow-ups for the merging node. Coordination note; not spec truth.

## Transport-selection status message exposes classifier internals

`/merge` can report the selected transport with raw classifier counts and a mechanical delegation sentence:

```text
Transport selected: GitHub PR, because the classification has 2 changed files and 2 non-coordination-note files. I'm delegating to /manage-github-pr, which owns branch creation, commit, PR opening, checks, review, and merge.
```

The status is technically traceable to the transport-selection policy in `spx/21-spec-tree.enabler/76-merging.enabler/merging.md`, but it is the wrong operator surface. It leaks count-level classifier implementation detail, over-narrates delegation, and reads as a handoff rather than a lifecycle step the merge skill continues to own. A future merging-skill change should adjust the `/merge` transport-selection wording and eval expectations so the message names the selected transport and the policy reason at the user-facing level: coordination-note-only changes use direct-push, overlay-declared transport wins, otherwise GitHub PR. The message should avoid raw changed-file counts unless the count is itself the decision boundary the operator needs to inspect.

## Lifecycle skills use bare `$ARGUMENTS` instead of a declared `arguments` field

`develop:skill-auditor` flags `merge/SKILL.md` (and the same pattern in `manage-github-pr`, `pickup`, `handoff`, and `audit-skills`) for using the bare `$ARGUMENTS` token in the skill body, which `src/plugins/develop/skills/skill-standards/references/command-capabilities.md` forbids ("NEVER: copy a command's bare `$ARGUMENTS` / `$1` into a skill body — skills name arguments through the `arguments` field"). The deterministic `skill_frontmatter` validator does not catch it; only the agentic skill auditor does.

This is a genuinely separate, larger concern, not a piecemeal merge-skill fix:

- It spans five skills across three plugins/nodes (merging: `merge`, `manage-github-pr`; sessions: `pickup`, `handoff`; develop: `audit-skills`), four of which are outside any single merge-lifecycle changeset. `merge` also forwards its raw argument string to `/manage-github-pr` ("with `$ARGUMENTS` verbatim"), so the two are coupled.
- All five take a **free-form, multi-word instruction string** (or multiple session IDs), not a single positional token. The only skill that declares `arguments:` today (`audit-subagents`) uses it for a single-token path (`$subagent_path`). `command-capabilities.md` says named args "map to positions in order" and offers no pattern for capturing a whole rest-of-line instruction through one identifier — so naively declaring `arguments: instructions` and substituting `$instructions` risks capturing only the first whitespace-delimited token and breaking free-form capture.

Required handling (one coordinated change, not per-skill drips): decide whether `command-capabilities.md` needs an explicit free-form / rest-of-line exception that permits `$ARGUMENTS` for whole-string-instruction skills, or whether the `arguments` field can name a single greedy whole-string argument — then either amend the standard or migrate all five skills preserving whole-string capture, and re-audit each. Surfaced by `develop:skill-auditor` during the merge-overlay / assigned-CWD-discipline change (2026-06-24).
