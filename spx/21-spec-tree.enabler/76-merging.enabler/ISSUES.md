# Issues — Merging

Known follow-ups for the merging node. Coordination note; not spec truth.

## Transport-selection status message exposes classifier internals

`/merge` can report the selected transport with raw classifier counts and a mechanical delegation sentence:

```text
Transport selected: GitHub PR, because the classification has 2 changed files and 2 non-coordination-note files. I'm delegating to /manage-github-pr, which owns branch creation, commit, PR opening, checks, review, and merge.
```

The status is technically traceable to the transport-selection policy in `spx/21-spec-tree.enabler/76-merging.enabler/merging.md`, but it is the wrong operator surface. It leaks count-level classifier implementation detail, over-narrates delegation, and reads as a handoff rather than a lifecycle step the merge skill continues to own. A future merging-skill change should adjust the `/merge` transport-selection wording and eval expectations so the message names the selected transport and the policy reason at the user-facing level: coordination-note-only changes use direct-push, overlay-declared transport wins, otherwise GitHub PR. The message should avoid raw changed-file counts unless the count is itself the decision boundary the operator needs to inspect.

## Deploy/release mapping assertions await lower-layer evidence

`spx/15-merging.pdr.md` and `spx/21-spec-tree.enabler/76-merging.enabler/merging.md` declare `DEPLOYMENT_READINESS` and `RELEASE_READINESS` mapping behavior before the implementation and tests exist. The two mapping assertions in `spx/21-spec-tree.enabler/76-merging.enabler/merging.md` intentionally carry no `[test]` marker in the decision PR because `spx/21-spec-tree.enabler/76-merging.enabler/tests/test_merge_gate_policy.mapping.l1.py` still verifies the installed production-readiness helper.

Required handling:

- Implement the deploy/release mapping helper behavior in the transport implementation slice.
- Add the planned mapping tests named in `spx/21-spec-tree.enabler/76-merging.enabler/PLAN.md`.
- Attach `[test](tests/test_merge_gate_policy.mapping.l1.py)` evidence to the deploy and release mapping assertions only in the same changeset that adds the tests.

## Generated guide lifecycle vocabulary window

`spx/15-merging.pdr.md` declares four readiness gates and the lifecycle `VERIFY -> PREVIEW -> MERGE -> DEPLOY -> RELEASE -> CLOSE`, while the generated guides still teach the installed `merging-standards` vocabulary until the shared methodology PR updates `src/plugins/spec-tree/skills/merging-standards/SKILL.md` and regenerates guide output.

Required handling:

- Update `src/plugins/spec-tree/skills/merging-standards/SKILL.md` in the shared methodology PR.
- Run `just build-skills` and `just build-guides`.
- Verify generated `spx/CLAUDE.md` and `spx/AGENTS.md` no longer teach the old three-gate or production-readiness lifecycle.
