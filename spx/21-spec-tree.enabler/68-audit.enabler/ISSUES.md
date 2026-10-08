# Issues - Audit

Known follow-ups for the audit node. Coordination note; not spec truth.

## Compliance-lane tests read as `assert harness_call()`

`spec-tree:test-evidence-standards` `<predicate_seam>` and
`python:python-test-standards` `<predicate_and_oracle_litmus>` reject a test whose
body is a bare `assert helper(...)`: the harness computes the verdict, no
behavioral predicate is visible in the executed test, a failure reports only
`assert False` with no observed-versus-expected diagnostic, and inverting the
claim requires editing the harness rather than the test.

The scenario lane of this node is converted — `observe_implementation_audit_lifecycle`
and `observe_mismatched_terminal_status_finish` expose observations, and
`tests/test_implementation_audit_contract.scenario.l3.py` owns every predicate.
The compliance lane still carries the rejected shape:

- `spx/21-spec-tree.enabler/68-audit.enabler/tests/test_implementation_audit_contract.compliance.l1.py` — 16 functions
- `spx/21-spec-tree.enabler/68-audit.enabler/21-state-surface.enabler/tests/test_implementation_audit_runtime.compliance.l1.py`
- `spx/21-spec-tree.enabler/16-verification.enabler/15-verdict-toolchain.enabler/tests/test_verification_run_payload_contract.compliance.l1.py`

**Why this is a separate larger concern.** Each of those functions backs a
different compliance assertion, and the harness functions behind them return a
boolean derived from a distinct check — surface validation, filename rejection,
payload rejection, trio completeness. Converting them is not one mechanical
rename: every function needs its own observation shape designed against the
assertion it backs, and the surrounding assertions in three nodes across two
subtrees are re-audited against those shapes. The scenario-lane conversion
landed with the finding that surfaced it because that lane's evidence was
already being changed; the compliance lane is untouched by that change.

**Resolution shape**: convert one compliance file at a time, designing each
harness function's observation from the assertion it backs, and gate each file
with `spec-tree:test-evidence-auditor` before moving to the next.

**Evidence.** Surfaced by `spec-tree:test-evidence-auditor` on the
implementation-audit idempotency-key changeset, which audited the scenario
assertion and named the same defect class in the other two functions of that
file. Raised again as four `REJECT` findings (predicate-ownership, eleven
functions across the trio, wrapper, and retired-name assertions) on the
coverage-accounting changeset, which touches neither the compliance file nor
its harness; deferred there for the reason above.

## `check_wrapper_surface` acceptance boundary has no fixture evidence

`outcomeeng/validation/audit_artifacts.py` `check_wrapper_surface` scopes its
`language_names` predicate to `implementation_languages(surface)` so that an
artifact-type auditor sharing its owning plugin's name — a craft plugin's
`{plugin}-auditor`, such as `prose-auditor` — passes while every
per-programming-language wrapper filename stays rejected. The rejection side is
fixture-backed (`audit_contract_rejects_language_specific_wrapper`,
`audit_contract_rejects_unrecognized_language_specific_wrapper`); the acceptance
side is evidenced only by the live repository surface passing after
`prose-auditor` was added.

**Resolution shape**: add a violating/passing fixture pair to
`outcomeeng_testing/harnesses/audit_verification_run_contract.py` — violating: a
genuine per-programming-language wrapper such as `python-auditor`; passing: a
non-language plugin's `{plugin}-auditor` colliding by name — and assert both
through `check_wrapper_surface`.

**Evidence.** Surfaced by the changes reviewer on the prose router-surface
changeset (sealed review run `2026-08-05_21-08-16-860-5bf3b83599ce`, PR #501).

## `audit-implementation` documents contracts without one worked run

`src/plugins/spec-tree/skills/audit-implementation/SKILL.md` documents the
scope-unit JSON contract, the finding JSON contract, and nine failure modes, but
carries no end-to-end walkthrough: one real `$ARGUMENTS` block, the resulting run
token, one scope and one finding payload with concrete field values, and the
final `spx verification run render` output. `/audit-skill`
`references/operational-effectiveness-examples.md` recommends that shape so
Claude has a line-for-line comparison target for detecting a malformed payload or
a wrong terminal-status derivation before emitting it, rather than only the
abstract field-name contracts.

**Why this is a separate larger concern.** A truthful walkthrough carries real
values from a real run, and the two entries below record implementation-audit
runs as not yet reproducible for gating: mixed-changeset partitioning yields
different coverage projections across runs of the same branch, and the terminal
projection and event prefix can disagree on `sealed`. A walkthrough captured
before those settle would publish one arbitrary run's shape as the contract, and
a fabricated one would state values the CLI does not produce — both worse than
the abstract contracts the skill carries today. This is authoring against an
unstable surface, not a mechanical addition to a stable one.

**Resolution shape**: once mixed-changeset partitioning and the projection seal
agreement are settled, capture one single-language, single-finding audit run and
render its `$ARGUMENTS`, run token, payloads, and projection into an
`<examples>` section, then gate the change with the configured `skill-auditor`.

**Evidence.** Surfaced by `instructions:skill-auditor` (finding `f-007`,
`procedural_without_operational`) on the implementation-audit idempotency-key
changeset, alongside a bounded example-format finding that was fixed in that
same changeset.

## Implementation audit has incomplete mixed-changeset coverage

The implementation auditor has no skill covering workflow YAML, so a changeset
scope including `.github/workflows/*.yml` rejects audit setup with
`missing required skill: audit-yaml-kind`. `actionlint` covers workflow syntax,
and the changeset review gate owns full-diff review of that surface meanwhile.

Open decision: whether workflow YAML receives a dedicated YAML audit skill or
routes to a workflow-specific audit surface. Once decided,
`implementation-auditor` reports that coverage without requiring callers to
split YAML out of an otherwise valid changeset.

Two further gaps block a gating implementation audit:

- Mixed-changeset partitioning is not reproducible across verifier runs. The
  same branch yields different coverage projections — one run collecting
  unsupported files into a required `unsupported` unit and sealing `rejected`
  with zero findings, another recording no unsupported unit and sealing
  `approved`. Gating depends on how orchestration classifies supported language
  and artifact partitions, and on distinguishing files outside
  implementation-audit ownership from missing required implementation coverage.
- The verifier output contract needs one post-completion projection whose seal
  and event prefix agree; a terminal projection reporting `sealed: true`
  alongside an event projection reporting `sealed: false` and omitting the
  terminal event leaves no single authoritative read.

## SPX audit verification contract follow-ups

The plugin implementation-auditor model records implementation-audit coverage, findings, terminal state, and projections through `spx verification run`. The remaining issues live in the SPX verification-run contract rather than in plugin-side verdict scripts.

Open gaps:

- Audit scope payloads require stable producer identity and producer provenance for every unit, but `missing-skill`, `unsupported`, and `coverage-gap` units may have no executed leaf skill and sometimes no skill or plugin version. SPX should distinguish the run driver that recorded the unit from the expected producer that would have covered it, and make provenance optional when the expected producer is absent.
- The `coverage-gap` audit kind pairs only with an uncovered coverage status. `spx` 0.6.21 and 0.6.27 both accept `auditKind: "coverage-gap"` when the payload carries `coverageStatus: "skipped"` and reject it with `a coverage-gap unit carries an uncovered coverage status` when it carries `not-applicable` — so the kind is available and the constraint is on the status, not the kind. A required coverage-gap unit additionally forces the terminal rollup to `rejected`, which is why the accounting record for an unclaimed path is `optional` and `skipped`. An earlier reading of this boundary as a rejection of the kind itself is superseded by direct observation against both releases; the l3 lifecycle scenario now records the accounting record against the pinned floor release, so its acceptance there is test evidence rather than this note.
- Audit unit identity and subject normalization are not specified. SPX should define deterministic `unit_id` derivation, parent/child identity stability, and normalized subject shape so findings, coverage gaps, and prior-run context converge across repeated runs.
- Finding-key granularity is unspecified where the payload models a finer grain than the key. A finding payload carries `location`, so one concern can report two violations of the same rule at different locations within one subject, while the finding key is the unit key plus the rule alone — the second recording composes the first key, and the run counts one finding where the producer raised two. SPX should specify whether a finding's identity is one per subject and rule, with `location` describing the occurrence, or one per location, with a deterministic location component in the key; the plugin contract then follows that decision rather than choosing a key shape the CLI may not honor. **Why this is a separate larger concern.** The choice is the same identity specification the entry above defers to SPX, and adding a location segment now would publish a key shape the CLI has not agreed to, so a run recorded against it could stop converging with prior-run context. Surfaced by the pull-request reviewer on the idempotency-key changeset, which disambiguated the key across subjects and left this narrower collision open.
- Audit class/kind validation needs a compatibility matrix for `instructions`, `spec`, and `implementation` classes so impossible combinations such as an implementation audit of `skill` or an instructions audit of `code` are rejected by schema validation.
- Audit terminal rollup is planned, but the public `finish` contract still speaks as caller-supplied terminal status. SPX should decide whether audit `finish` derives status without a caller value or validates a supplied value against the derived rollup, and specify the rejected mismatch behavior.
- Prior-run selection must distinguish gating runs over committed heads from advisory runs over live modified or untracked files. The run-set selector should expose run purpose directly rather than infer authority from scope payload prose.
- Finding severity vocabulary is not reconciled across the artifact-type audit skills. `audit-adr` emits the audit-run severities `blocking`/`debt`; `audit-pdr`, `audit-tests`, `audit-specs`, and `audit-eval-evidence` emit `REJECT`/`WARNING`/`INFO`. The governing authority conflicts: `/merging-standards` `<review_classification>` mandates `BLOCKING`/`DEBT` and forbids severity-rank labels, while its `<auditor_verdicts>` references a `REJECT` finding. SPX should define the single canonical finding-severity enum for audit-run verdicts, after which the four non-`blocking`/`debt` skills reconcile to it in one pass — a sub-task of the verification-run migration (`outcomeeng/changes#327`), not independent work, because that migration rewrites the same skills.

## The completion contract's behavioral claim carries no eval evidence

The node asserts the implementation-audit completion contract as five `[audit]`
assertions whose subject is the shipped `spec-tree:audit-implementation` prompt.
They state what the contract requires; they establish nothing about how a run
behaves.

`/verify` `<classify-subject>` routes the behavioral claim elsewhere: an
implementation-audit run is an LLM-driven producer emitting a structured verdict,
which resolves to `[eval]`, and reading authored text proves only that the text
was authored. The behavioral assertion — a run finishes only when every required
unit carries a final status, or returns the blocked diagnostic naming a concrete
failed operation or absent prerequisite — is therefore `capability-required`,
with its `[eval]` shape preserved and no evidence path written, because
`just eval-links` fails the gate on a dangling link.

**Why this is a separate larger concern.** The two entries above record the eval
surface as unstable: mixed-changeset partitioning yields different coverage
projections across runs of the same branch, and a terminal projection can report
`sealed: true` beside an event projection reporting `sealed: false`. A case set
captured against that surface would pin one arbitrary run's shape as the
contract.

**Resolution shape**: author the `[eval]` assertion and its cases once the
partitioning and seal-agreement entries above settle, scoping the cases to the
terminal contract rather than to partitioning. Tracked as a Change deriving from
the one that added the `[audit]` assertions.

**Evidence.** `/verify` classification during the interview that scoped those
five assertions; the operator accepted `[audit]`-only with the gap recorded here.

## The audit-skill file inventory is enforced but undocumented

`outcomeeng/validation/audit_artifacts.py` enforces an exact file inventory for
each `audit-*` skill directory. For `audit-implementation` the permitted set is
`SKILL.md`, `references/`, `references/operational-failures.md`, `scripts/`, and
`scripts/resolve_scope.py`. Adding any further bundled file — a `templates/`
directory carrying the scope-unit and finding payload shapes, for instance —
fails the pre-commit hook with an `expected ... found ...` diff naming the new
paths.

The constraint is real and serves the assertions that keep plugin-side audit
machinery out of the skill. No spec assertion, decision, or skill-authoring
overlay states it, so an author reaches it only by having a commit rejected, and
`/skill-standards` `<progressive_disclosure>` actively suggests the bundled-file
shapes the validator forbids here.

**Resolution shape**: declare the inventory constraint where an author reads it
before authoring — a compliance assertion on this node naming the validator as
its enforcement, and a line in `spx/local/skills.md` for the authoring surface —
or widen the validator to a category rule that admits inert data files while
still rejecting executable audit machinery.

The constraint now also blocks the standard remedy for the skill's size.
`SKILL.md` stands at 499 of the 500-line ceiling `/skill-standards` sets, and
the content that would move — the scope and finding payload contracts — has
nowhere to go, because `references/operational-failures.md` is the only
reference file the inventory admits. The next necessary addition crosses the
ceiling with no sanctioned extraction available, so widening the validator is
the move that unblocks both this entry and the ceiling.

**Evidence.** The pre-commit hook rejected a `templates/` directory carrying the
two payload shapes during the completion-contract repair; the extraction was
withdrawn and the payloads stay inline in `SKILL.md`. The ceiling pressure was
surfaced by `instructions:skill-auditor` on the coverage-accounting repair.

## The run driver reports inconsistent provenance for its own plugin version

Two sealed implementation-audit runs recorded minutes apart, from the same agent
on the same machine against the same installed plugin set, carry different
`producerProvenance.agentOwningPluginVersion` values: `0.92.8` in run
`2026-09-14_20-51-24-761-379222378048` and `0.85.0` in run
`2026-09-14_20-56-49-016-d65f8206db75`. The co-recorded
`skillOwningPluginVersion` and `toolVersion` agree across both runs.

Both values cannot describe the same environment, so at least one sealed record
carries false provenance. The skill supplies this value; SPX records what it is
given.

Neither verdict is affected, and finding convergence keys on content and stable
producer identity rather than plugin version, so no downstream read breaks. The
defect is that a durable, sealed audit record states a version the environment
did not run.

**Resolution shape**: establish where the run driver reads its own owning-plugin
version, and derive it from one source that cannot disagree across runs — the
installed plugin manifest the skill was loaded from. Until then, treat
`agentOwningPluginVersion` in sealed audit records as unreliable for run
comparison.

**Evidence.** The two run tokens above, recorded during the completion-contract
repair.

## The scope resolver crossed the shipped-script size threshold

`src/plugins/spec-tree/skills/audit-implementation/scripts/resolve_scope.py` is
268 lines. [`spx/12-shipped-scripting.adr.md`](spx/12-shipped-scripting.adr.md) holds that a generic shipped script
beyond fifty lines is debt awaiting extraction into the SPX CLI once it proves
its value.

Two mechanizations carried it past the threshold, both closing a hole that
prose alone had failed to close twice. `--audit-input` merges the invocation's
short context values beneath the git-resolved scope, so the changed-path set
reaches `spx verification run start` through a pipe instead of being retyped.
`--reconcile-run` reads a run's sealed start inventory and its recorded scope
units back through `spx verification run input` and `render`, and returns an
exit code for whether the recorded subjects account for that inventory.

Neither is agent-specific, and SPX owns both sides: it already returns
`resolvedScope` from `start`, and it holds both the sealed inventory and the
recorded units at `finish`. The end state is SPX resolving the scope from a
selector at `start` and refusing to seal a changeset audit whose required units
do not account for that run's own inventory — at which point the skill passes a
selector, the reconciler becomes a `finish` precondition no caller can skip, and
this script disappears. Until then the reconciler is advisory: a caller that
never runs it can still seal a partial inspection, which is why the same check
must reach `finish` itself.

**Resolution shape**: fold scope resolution, run-input composition, and
inventory reconciliation into the SPX `verification run` contract, then remove
the bundled script. Filed as the SPX-side Change; the audit-payload schema work
carries it.

**Evidence.** The resolver grew from 48 to 61 lines closing the
transcribed-inventory hole, then to 268 closing the coverage-accounting hole,
both recorded against `outcomeeng/changes#47`.

## The skill's payload templates and the contract module declare the same shapes twice

`src/plugins/spec-tree/skills/audit-implementation/SKILL.md` carries the scope
and finding payload shapes as prose templates, and
`outcomeeng/validation/implementation_audit_contract.py` builds the same
shapes for the l3 lifecycle evidence. No build derives one from the other, so
drift between them is invisible to the evidence.

**Resolution shape**: render the shipped templates from the contract module at
build time, the way the diagnose manifest and the language registry are
rendered; tracked with <https://github.com/outcomeeng/changes/issues/64>,
which introduces build-time rendering into this skill.

**Evidence.** `INFO` finding (source-ownership) from
`spec-tree:test-evidence-auditor` on the coverage-accounting changeset.

## The selector argument is captured as `$ARGUMENTS` rather than a named argument

The skill accepts one stable token — `HEAD`, a branch, `base...head`, or
`worktree:selector` — through whole-string `$ARGUMENTS`. `/skill-standards`
prefers a named `arguments: selector` for a stable single token. The change
depends on the pending Codex argument-rendering audit recorded in
`spx/18-plugin-build.enabler/ISSUES.md`, so it waits for that outcome rather
than changing the capture form blind.

**Evidence.** `WARNING` (argument capture style) from
`instructions:skill-auditor` on the coverage-accounting changeset, three
rounds running.

## The implementation-auditor wrapper lacks a successful exact-role invocation

The configured-agent audit of
`src/plugins/spec-tree/agents/implementation-auditor.md` during Change #76
approved the wrapper's profile, capability, thin-delegation, and result-contract
shape, then rejected its execution evidence. The retained Codex composition
probe ended before a child session started, and later commits changed the
generated definition, so no successful minimal isolated invocation exists for
the current emitted role.

**Settlement condition**: one retained minimal isolated invocation of the
exact emitted role that starts a child session and returns the terminal
`spx verification run` result. A loader or authentication failure remains a
failed invocation rather than approval evidence.

**Evidence**: `instructions:subagent-auditor` finding `f-001` against
`src/plugins/spec-tree/agents/implementation-auditor.md` on Change #76 head
`843ddd709b058970d414ec755cc10121ff6bb5ff`.

## The implementation-auditor has no executable agent or eval coverage

The audit surface uses the published `spx verification run` lifecycle, and [`spx/21-spec-tree.enabler/17-audit.adr.md`](spx/21-spec-tree.enabler/17-audit.adr.md) declares the target surface: one spec-tree-owned `implementation-auditor` wrapper agent composes the `audit-{lang}-code`, `audit-{lang}-tests` and `audit-{lang}-architecture` skills inside one isolated verifier context and records one audit verification run. Language plugins ship skills only. No executable agent or eval covers representative implementation-auditor runs over a one-language, a multi-language and an unsupported-file scope.

**Settlement condition.** Agent or eval coverage exists for those three scopes, once the agentic runner can be exercised deterministically.

## Audit run-set convergence does not use SPX prior-context restoration

Remaining audit run-set convergence moves onto SPX prior-context restoration once the plugin smoke path proves the single-run lifecycle.

**Settlement condition.** The audit skills restore prior context through `spx verification run` and carry no convergence mechanism of their own. `outcomeeng/changes#327` carries the artifact-type auditors' move onto the same contract.

## The audit-runtime-evidence branch is unpartitioned

`origin/work/audit-runtime-evidence` changed 59 paths across implementation-audit contracts, Python authoring guidance, distribution code and repository configuration when it was recorded. It is unpartitioned and unpublished, so its implementation-auditor run contract, coverage inventory, wrapper configuration, audit declarations and co-located tests share one history with Python authoring and distribution changes that belong to other nodes.

**Settlement condition.** The branch is replaced by the audit pull request, one implementation-audit behavior with one verification story and one rollback story, and its other changes go to their owning nodes. This is one merge cycle of the aggregate that `spx/21-spec-tree.enabler/65-apply.enabler/ISSUES.md` records.

## An implementation audit and a changeset review read one shipped executable to opposite verdicts

The audit side of the divergence between `spec-tree:implementation-auditor` run `2026-09-22_20-40-39-797-98d0f564dc05`, which approved `src/plugins/coding-agents/skills/orchestrate-officers/scripts/derive_ledger.py`, and `spec-tree:changes-reviewer` run `2026-09-22_20-40-26-221-404eea4ba809`, which rejected it by executing it. An audit that reads code approves a contract violation that executing the code exposes.

**Settlement condition.** A decision states whether an implementation audit of a shipped executable executes it. The full entry is in `spx/31-outcomeeng.enabler/31-verification.enabler/ISSUES.md`.

## Stage 7 of the implementation audit routes no stale-base exit from the reconciler

**Evidence.** `src/plugins/spec-tree/skills/audit-implementation/SKILL.md` stage 7 routes the reconciler's exits 0, 1 and 2. The reconciler re-resolves the selector through the changeset-scope provider, which exits 3 with a `stale-base` diagnostic when the base advanced during the run. `instructions:skill-auditor` reported the missing route as a warning (`unhandled_command_outcome`) on the registry-selection changeset.

**Impact.** A run whose base moves between `start` and stage 7 has no stated outcome, so the run driver improvises between a blocked diagnostic and a new run.

**Settlement condition.** Stage 7 states that exit 3 returns the blocked diagnostic carrying the reconciler's stale-base stderr, and a test pins the routing.

## The implementation audit chooses its stdin command form by the kind of caller

**Evidence.** `src/plugins/spec-tree/skills/audit-implementation/SKILL.md` selects the quoted heredoc for interactive sessions and the one-line `printf` pipe for programmatic runners, as [`spx/15-agent-tools.pdr.md`](spx/15-agent-tools.pdr.md) requires of tool guidance. `instructions:skill-auditor` reported the caller-dependent branch as a warning (`caller_independence`) on the registry-selection changeset.

**Impact.** `/skill-standards` `<skill_organization>` holds that a skill never branches on its invocation context, so the two decisions disagree and each audit of the skill raises the conflict again.

**Settlement condition.** The two sources agree on one form: either `/skill-standards` admits harness-scoped command forms, or the skill states one form that holds in both environments.

## The implementation audit requires its caller's identity

**Evidence.** `src/plugins/spec-tree/skills/audit-implementation/SKILL.md` requires the six run-driver producer fields in the invocation context, returns `BLOCKED` with `runToken: not-started` when they are absent, and writes them into every scope payload as `recordedByRunDriver`. `instructions:skill-auditor` rejected the dependency (`caller_independence`) on the registry-selection changeset. [`spx/21-spec-tree.enabler/17-audit.adr.md`](spx/21-spec-tree.enabler/17-audit.adr.md) decides that the `implementation-auditor` supplies its identity as explicit request data.

**Impact.** A direct `/audit-implementation HEAD` invocation without injected identity always returns `BLOCKED`, so the skill is not independently invocable, and the standard and the decision contradict each other.

**Settlement condition.** The contradiction is settled in the governing layer: either the decision and the SPX run contract make the run-driver identity optional and derived, or `/skill-standards` admits a declared request-data input from the wrapper agent.

## The implementation audit skill carries standards warnings on unedited text

**Evidence.** `instructions:skill-auditor` reported, on `src/plugins/spec-tree/skills/audit-implementation` during the registry-selection changeset, four warnings on text that changeset left alone:

- `<failure_modes>` loads the failure reference only after a failure, so the preventive records (`finding_before_standards`, `transcribed_inventory`, `coverage_stated_as_findings`) reach Claude too late (`failure-modes-load-trigger`).
- `allowed-tools` grants `Bash(spx verification run:*)`, which covers the state-changing `start`, `scope add`, `finding add` and `finish` subcommands, while `/skill-standards` limits audit skills to read-only Bash verbs; the skill never says why persisting the verdict is the audit's output and not a modification (`audit-read-only-allowed-tools`).
- The skill composes a concern skill whose name it reads from the registry selection at run time, while `/skill-standards` requires a parent to name the exact installed skill it composes; the `concern` contract filter contains the dispatch and the skill states the exception (`skill-tool-composition`).
- `resolve_scope.py` builds paths into the `scope-changeset` and `select-artifacts` provider skills, which `/skill-standards` command-capabilities reads as a cross-skill file reference, while [`spx/13-plugin-and-runtime-conventions.adr.md`](spx/13-plugin-and-runtime-conventions.adr.md) decides that a consumer script reaches a provider by a `__file__`-relative import (`cross-skill-file-reference`).

**Impact.** Each audit of the skill raises these warnings again, and the last two record conflicts between the skill standard and the decision.

**Settlement condition.** The failure-reference trigger names the preventive records, the skill states that journal writes through SPX are the audit's output, the standard recognizes composition of a registry-selected skill, and the standard and the decision agree on how a consumer script reaches a provider skill.

## Two compliance tests of this node back no assertion and the lifecycle harness chooses the terminal status

**Evidence.** `spec-tree:test-evidence-auditor` on this node reported two warnings on evidence the registry-selection changeset left alone. `test_implementation_audit_unit_ids_are_subject_specific` and `test_implementation_audit_payloads_reject_empty_subject` in `spx/21-spec-tree.enabler/68-audit.enabler/tests/test_implementation_audit_contract.compliance.l1.py` link to no compliance assertion of this spec (`alignment`). `observe_implementation_audit_lifecycle` in `outcomeeng_testing/harnesses/audit_verification_run_contract.py` picks the terminal status it submits to `finish`, so a reader cannot see from the linked l3 test which status the scenario submits (`test-owned data`). The same audit reported the `assert harness()` shape recorded in the first entry of this note as four rejected findings on the trio, wrapper, retired-wrapper and retired-skill assertions.

**Impact.** Evidence without an owning assertion proves a claim no one declared, and the hidden status choice leaves the scenario's case outside its test.

**Settlement condition.** Each of the two compliance tests backs a declared assertion on the node that owns unit identity, or moves there, and the lifecycle test submits the terminal status at its own call site.

## The accounting record that names an artifact-type audit skill has no lifecycle evidence

**Evidence.** `implementation_audit_accounting_payload` in `outcomeeng/validation/implementation_audit_contract.py` accepts a registered kind and an artifact-type audit skill, and `src/plugins/spec-tree/skills/audit-implementation/SKILL.md` prescribes the record that carries them. The lifecycle scenario of this node records only an accounting unit for a path no registered artifact matches, so no executed run seals a unit whose `expectedProducer` names an artifact-type skill.

**Impact.** The unit key and the producer shape of that record rest on the skill text and the payload builder alone.

**Settlement condition.** A scenario of this node records the accounting unit for a path the registry selects an artifact-type audit skill for, and asserts the sealed projection carries that kind in the unit key and that skill as its expected producer.
