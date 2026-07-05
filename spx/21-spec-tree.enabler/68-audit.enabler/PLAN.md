# Plan: mirror the changeset-reviewer subagent-invocation contract onto the audit family

Apply to the audit surface the same Codex subagent-invocation transformation that
`spx/21-spec-tree.enabler/68-reviewing.enabler/21-reviewing-changes.enabler` and its
`changes-reviewer` agent received (landed in the `instruction-block.md` guide template). This is the
audit-family slice of the verification-skill migration owned by the SPX-journal-channel migration
work; it is blocked on the forthcoming `spx` sub-command that provides a cleaner audit surface than
today's `spx journal --type audit`.

## Blocked on

- The new `spx` sub-command (cleaner audit surface). Merged-to-spx-`main` is not "available" per the
  root guide's published-floor rule: the pin in `outcomeeng/validation/spx_version.py` and
  `.github/workflows/check.yml` must reach a published release carrying it first.

## Scope to transform

- `src/plugins/spec-tree/skills/understand/templates/instruction-block.md` — the `runtime:codex` audit
  invocation contract (currently only `changes-reviewer` carries the full contract).
- `src/plugins/spec-tree/agents/auditor.md` and `.../audit-orchestrator.md`.
- The artifact-type auditors `adr-auditor`, `pdr-auditor`, `spec-auditor`, `test-evidence-auditor`.

## Design conclusions from the assessment (not yet ratified)

- Pass `agent_type` as the exact name and put the concrete scope in `message`. Audit's scope is
  legitimately richer than the reviewer's single scope token: a git ref / diff range **or** an
  explicit file list (code audits) **or** a decision-file / node path (`pdr-auditor`, `spec-auditor`).
  Do not copy `changes-reviewer`'s "raw scope token only" rule verbatim.
- Give the audit family the reviewer's missing contracts: a Codex audit output contract (a successful
  audit final message is the journal-rendered verdict; do not accept a prose summary as the gate
  result), a blocked-result rule, and the explicit "never run `/audit` in the main thread" symmetry
  (already an `[audit]` rule in `spx/21-spec-tree.enabler/17-audit.adr.md`, weakly phrased in the guide).
- Place `audit-orchestrator` in the 30-minute wait tier (whole-changeset / cross-commit run set),
  alongside `changes-reviewer`; `auditor` and `spec-auditor` stay in the 10-minute per-file tier
  (already named in the guide).

## Open decision (resolve before writing the guide change)

Whether the audit `message` carries a caller-requested output shape.

- `spx/AGENTS.md` subagent-spawn guidance lists "requested output shape" as something to put in
  `message`.
- The `changes-reviewer` transformation went the other way — it forbids caller-side output steering
  because output shape is fixed and agent-owned.
- Recommendation: **drop** "requested output shape" from the audit `message` for symmetry, grounded in
  `spx/31-outcomeeng.enabler/31-verification.enabler/14-verification.pdr.md` property 2 (each output surface is a projection) and
  `spx/21-spec-tree.enabler/16-verification.enabler/13-run-journal.adr.md` (every output surface is a
  projection rendered from the journal event history). Keeping the literal `AGENTS.md` wording would
  reintroduce the steering the reviewer change removed.

## Governing context

- `spx/31-outcomeeng.enabler/31-verification.enabler/14-verification.pdr.md`, `spx/15-audit-result-delivery.pdr.md`,
  `spx/21-spec-tree.enabler/17-audit.adr.md`,
  `spx/21-spec-tree.enabler/16-verification.enabler/13-run-journal.adr.md`.
- Reference implementation to mirror: the `changes-reviewer` contract in the `instruction-block.md` guide
  template and `src/plugins/spec-tree/agents/changes-reviewer.md`.
