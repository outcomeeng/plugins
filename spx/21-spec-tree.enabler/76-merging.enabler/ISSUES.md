# Issues — Merging

Known follow-ups for the merging node. Coordination note; not spec truth.

## Transport-selection status message exposes classifier internals

`/merge` can report the selected transport with raw classifier counts and a mechanical delegation sentence:

```text
Transport selected: GitHub PR, because the classification has 2 changed files and 2 non-coordination-note files. I'm delegating to /manage-github-pr, which owns branch creation, commit, PR opening, checks, review, and merge.
```

The status is technically traceable to the transport-selection policy in `spx/21-spec-tree.enabler/76-merging.enabler/merging.md`, but it is the wrong operator surface. It leaks count-level classifier implementation detail, over-narrates delegation, and reads as a handoff rather than a lifecycle step the merge skill continues to own. A future merging-skill change should adjust the `/merge` transport-selection wording and eval expectations so the message names the selected transport and the policy reason at the user-facing level: coordination-note-only changes use direct-push, overlay-declared transport wins, otherwise GitHub PR. The message should avoid raw changed-file counts unless the count is itself the decision boundary the operator needs to inspect.

## Generated instruction-block lifecycle vocabulary window

`spx/15-merging.pdr.md` declares four readiness gates and the lifecycle `VERIFY -> PREVIEW -> MERGE -> DEPLOY -> RELEASE -> CLOSE`, while the generated instruction blocks still teach the installed `merging-standards` vocabulary until the shared methodology PR updates `src/plugins/spec-tree/skills/merging-standards/SKILL.md` and regenerates instruction-block output.

Required handling:

- Update `src/plugins/spec-tree/skills/merging-standards/SKILL.md` in the shared methodology PR.
- Run `just build-skills` and `just build-instructions`.
- Verify the generated instruction blocks in root `CLAUDE.md` and `AGENTS.md` no longer teach the old three-gate or production-readiness lifecycle.

## Merge lifecycle eval suites are prompt-only simulations

`eval-evidence-auditor` runs `019f4219-ac8e-7b92-96db-fefd48bf8b41` and
`019f421a-01ad-7ac0-b1f8-abc05f458dc7` reported that the
`local-completion-boundary` and `transport-selection` eval suites do not prove
the producing merge lifecycle behavior:

- `local-completion-boundary` simulates status assessment in
  [`prompt.md`](evals/local-completion-boundary/prompt.md); replacing
  [`src/plugins/spec-tree/skills/merge/SKILL.md`](../../../src/plugins/spec-tree/skills/merge/SKILL.md)
  or [`spx/local/merging.md`](../../local/merging.md) would not change the
  evaluated behavior.
- `local-completion-boundary` covers the local-stop/local-pause branch, but not
  continuation through default-branch merge, declared deploy/release phases, and
  closeout.
- `transport-selection` grades a static prompt/case model without materializing
  or directly invoking
  [`src/plugins/spec-tree/skills/merge/SKILL.md`](../../../src/plugins/spec-tree/skills/merge/SKILL.md).
- Both suites hard-code the policy in the prompt, so the grader can keep passing
  after the producer changes.

Revisit condition: run `/apply` on
`spx/21-spec-tree.enabler/76-merging.enabler` to convert
`evals/local-completion-boundary` and `evals/transport-selection` to
producer-coupled evals, or reclassify/remove the `[eval]` assertions they no
longer support. Rerun `eval-evidence-auditor` over the repaired eval artifacts.

### PR-lifecycle skills carry no eval trigger

`transport-selection` does not own the `manage-github-pr` or `open-pr` skills.
Its `prompt.md` names `manage-github-pr` only as the literal `delegation_target`
string its own decision rule dictates, never loading that skill's content, and
`open-pr` appears in neither `prompt.md` nor `cases.jsonl`. Replacing either
skill's `SKILL.md` with unrelated text changes no case outcome, so a CI trigger
on those paths starts a job that cannot detect the change that started it.

Those four trigger paths therefore carry no `owned_paths` declaration and no
generated trigger entry. Declaring them would assert a producer coupling the
suite does not have — the `False` producer-coupling category in
`spx/13-infrastructure.enabler/25-eval-harness.enabler/57-producer-coupled-skill-evals.adr.md`.

Revisit condition: this resolves with the prompt-only simulation above. Once
`transport-selection` materializes its prompt from a declared `prompt_source`
producer, declare the producers the materialized prompt actually reads — then
the generator derives their trigger paths, and a mutation to those skills
genuinely changes a case outcome.
