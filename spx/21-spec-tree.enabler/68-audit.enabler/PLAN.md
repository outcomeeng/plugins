# Plan: audit verification-run migration

The audit surface uses the published `spx verification run` lifecycle. The
target surface is declared by `spx/21-spec-tree.enabler/17-audit.adr.md`: one
spec-tree-owned
`implementation-auditor` wrapper agent composes `audit-{lang}-code`,
`audit-{lang}-tests`, and `audit-{lang}-architecture` skills inside one isolated
verifier context, then records one audit verification run. Language plugins ship
skills only; they do not ship language-specific auditor agents.

## First PR: implementation audit contract through `spx verification run`

### Observable path

Actor: an operator in this plugin checkout dispatches an implementation audit for
an implementation scope whose language concerns are supplied by installed
language plugins.

Invocation: the main conversation commits a deterministic-passing local
checkpoint, then dispatches `implementation-auditor` with that exact changeset
scope. An explicit live-file scope is advisory and cannot satisfy a gate. The
wrapper starts `spx verification run start --verification-type
audit --scope-type changeset --scope <base>..<head>`, records inspected scope
with `spx verification run scope add`, records findings with `spx verification
run finding add`, finishes with `spx verification run finish`, and renders the
projection with `spx verification run render`.

Behavior: the wrapper prompt remains policy-thin and invokes `spec-tree:audit`;
the `spec-tree:audit` prompt contract requires partitioning the caller's scope by
language and concern, validating that each language partition has
`audit-{lang}-code`, `audit-{lang}-tests`, and `audit-{lang}-architecture`,
recording planned or classified coverage units through `spx verification run
scope add`, recording findings through `spx verification run finding add`, and
relaying the rendered projection. The same PR also renames the TypeScript and
Rust implementation-code skills to `audit-typescript-code` and
`audit-rust-code` so every shipped language plugin satisfies
`spx/21-spec-tree.enabler/17-audit.adr.md`. No deterministic validation, test, or
eval command runs inside the audit.

Persisted result: one `verificationType=audit`, `scopeType=changeset` run whose
scope payload declares required audit units and whose finding payloads carry
stable producer identity plus producer provenance. Producer identity uses plugin,
skill, audit class, language, and concern for convergence; producer provenance
records the owning plugin version for debugging without making the same finding
look new after a version bump.

Inspection surface: `spx verification run render --verification-type audit
--scope-type changeset --scope <base>..<head> --run <token>` shows the terminal
projection and authoritative finding count. `spx verification run status` and
`spx verification run input` are available for resumability and audit input
inspection.

Failure behavior: a missing required concern skill, unsupported implementation
file, rejected SPX payload, or missing required audit unit rejects the audit run
through recorded coverage status rather than a prose fallback. The wrapper does
not continue after detecting an absent required skill.

Verification before PR merge:

- Advance `REQUIRED_SPX_VERSION` in `outcomeeng/validation/spx_version.py` and
  `SPX_VERSION` in `.github/workflows/check.yml` to published `@outcomeeng/spx`
  `0.6.13` or newer before any shipped skill depends on `spx verification run`.
- Update `spx/21-spec-tree.enabler/68-audit.enabler/audit.md` to the
  `spx verification run` contract so the first implementation slice aligns with
  `spx/21-spec-tree.enabler/17-audit.adr.md`.
- Ensure the implementation-code skills use `audit-python-code`,
  `audit-typescript-code`, and `audit-rust-code`; update every same-PR reference
  that would otherwise route to a retired skill name, and do not leave aliases.
- Add `src/plugins/spec-tree/agents/implementation-auditor.md` as the thin
  wrapper surface and remove retired implementation-audit wrapper routing so the
  first smoke path has one implementation entrypoint.
- Update the Codex and Claude instruction-block audit invocation contract for
  `implementation-auditor`: exact `agent_type`, concrete scope in `message`, no
  caller-selected output shape, blocked-result rule, and final result read from
  the SPX verification-run projection.
- Run `just build-skills`, `just check-skills`, `just docs-check`, `spx validation
  markdown`, `spx spec status --format json`, and the focused audit-node tests.
  After editing `SKILL.md` or agent files, run the develop-owned skill and
  subagent audit gates on the changed authored sources.

### Dependency-order check

This slice is runnable because the published SPX audit lifecycle accepts
implementation-audit payloads and the shipped wrapper and skill prompt contracts
route all audit state through that lifecycle. The version-floor bump, wrapper
rename, cross-language code-skill rename, instruction-block routing, and audit
spec cleanup are included only because the path cannot run correctly without
them.

## Later slices

- Add executable agent/eval coverage for representative implementation-auditor
  runs over one-language, multi-language, and unsupported-file scopes once the
  agentic runner can be exercised deterministically.
- Generalize the implementation-auditor partitioning and coverage inventory for
  several files, several languages, and changesets containing unsupported files.
- Move remaining audit run-set convergence onto SPX prior-context restoration
  once the plugin smoke path proves the single-run lifecycle.
- Reconcile artifact-type auditors (`adr-auditor`, `pdr-auditor`,
  `spec-auditor`, `test-evidence-auditor`, `eval-evidence-auditor`) with the
  same `spx verification run` contract after implementation audit is runnable.

## Governing context

- `spx/15-audit-result-delivery.pdr.md`: audit progress and findings are visible
  during the run on local and pull-request surfaces.
- `spx/21-spec-tree.enabler/16-verification.enabler/13-run-journal.adr.md`:
  agentic verification uses one append-only run source of truth and projection
  surfaces.
- `spx/21-spec-tree.enabler/17-audit.adr.md`: audit-specific wrapper, language
  skill naming, composition, and no-language-agent-fleet rules.
- `spx/31-outcomeeng.enabler/31-verification.enabler/14-verification.pdr.md`:
  deterministic validation, test, and eval stay outside the dispatched audit.
- Root guide published-floor rule: shipped skills may depend on `spx
  verification run` only after the repository floor and CI pin reach the
  published SPX release carrying it.
