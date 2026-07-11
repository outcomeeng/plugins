# Plan: retire `spx/EXCLUDE`

`spx/EXCLUDE` is superseded by the committed per-node `spx.status.json` claim. It predates a committed per-node status baseline and now carries nothing the claim does not.

This work is **blocked on the `spx` CLI** adopting the claim-and-reproduction model, so this note records the plan and its gate; it is not yet actionable in this repository.

## Model (the target)

`spx.status.json` holds committed *claims* of verification outcomes per node, per mechanism (test/eval/audit). Raw evidence (test runs, eval runs, audit verification runs) is uncommitted.

- `spx spec status --update` reads only *available* local evidence and folds it into the committed claims; absence of evidence leaves a claim unchanged. It never runs verification.
- A committed claim can be `passed`, `failed`, or `not-run` at rest. `failed` is legitimate: an agent who breaks tests and ends the session commits a `failing` claim.
- CI is the reproduction authority: it always runs validation and reproduces claimed-passing tests, and refutes any passing claim it cannot reproduce (catching regressions the local agent missed). It does not run verification for a claim that does not exist.
- State derives from the claim: no references → `declared`; references with a not-run claim → `specified`; passed claim → `passing`; failed or refuted claim → `failing`.

`spx/EXCLUDE` is subsumed: "no passing claim ⇒ not run" is the automatic exclusion. Tests + validation carry the removal; eval/audit reproduction is deferred (their use is localized, so a stale eval/audit claim has contained blast radius).

## This repository is not yet adopting the baseline

`spx.status.json` files are intentionally **not** committed here yet. `spx/EXCLUDE` remains live until the gate below is met. Do not commit generated `spx.status.json` files as part of unrelated work.

## Gate — start only when all hold

1. The `spx` CLI ships the claim-and-reproduction model. Filed as a follow-up in the `outcomeeng/spx` session queue: `2026-07-05_19-20-16` (goal, code delta, and open design decisions are captured there).
2. An `@outcomeeng/spx` release carrying it is published to npm.
3. `REQUIRED_SPX_VERSION` (`outcomeeng/validation/spx_version.py`) and `SPX_VERSION` (`.github/workflows/check.yml`) are advanced to that published release.

## Worklist (re-derive exact edits against current `main` — the tree is being restructured)

Product specs (`/contextualize` the node, then edit):

- `spx/21-spec-tree.enabler/65-apply.enabler/apply.md` — work queue derives from `spx spec status` (specified nodes), not the `spx/EXCLUDE` fallback.
- `spx/21-spec-tree.enabler/76-sessions.enabler/sessions.md` — continuation/closure signal: "a `spx/EXCLUDE` entry" → "a `specified` node".
- `spx/15-validation.enabler/32-reference-portability.enabler/reference-portability.md` — drop `spx/EXCLUDE` from the universal-path example set once the file is removed.

Authored skills + methodology under `src/plugins/` (run `instructions:skill-auditor` after):

- `spec-tree/skills/understand/references/excluded-nodes.md` — replace with a "specified via committed `spx.status.json`" reference.
- `spec-tree/skills/understand/references/durable-map.md` and `imperfection-protocol.md`; `understand/SKILL.md` reference list.
- `spec-tree/skills/{apply,author,test,handoff,manage-github-pr,merging-standards}` and `handoff/workflows/02-reflect.md`.
- `typescript/skills/test-typescript/SKILL.md`; sweep `methodology/skills/skill-structure.md`.

Migration:

- Convert `spx/EXCLUDE` (17 entries as of this note) to committed `spx.status.json` claims per the shipped migration, then delete `spx/EXCLUDE`.

Not required for removal (deferred): per-mechanism available-evidence readers for eval and audit, and a cost-reward CI reproduction policy.
