<objective>
Observed implementation-audit failures and their causes and prevention.
</objective>

<contents>
- `request_preparation`
- `concern_inventory`
- `language_ownership`
- `finding_persistence`
- `coverage_evidence`
- `serial_persistence`
- `payload_fields`
- `shell_quoting`
- `deterministic_boundary`
- `unblocked_stop`
- `unrecovered_truncation`
- `single_commit_subject`
- `finding_before_standards`
- `transcribed_inventory`
- `vacuous_reconciliation`
- `coverage_stated_as_findings`
- `language_probe_by_invocation`
- `empty_argument_taken_as_selector`

</contents>

<request_preparation>

**The request was empty or malformed**

What happened: Claude received no resolvable scope or run-driver identity.

Why it failed: Starting a verification run without the required selector fields creates durable audit state that cannot be tied to the intended scope.

How to avoid: Resolve the target and validate the internal identity before
`spx verification run start`; return the exact missing input or failed command
without a retry or substitute scope.

</request_preparation>

<concern_inventory>

**A missing concern skill appeared after one concern already ran**

What happened: Claude invoked one concern skill before validating that the complete `audit-{lang}-{code|tests|architecture}` trio existed for every language partition.

Why it failed: The coverage inventory belongs before concern dispatch, so a late missing-skill discovery can leave other concern results without a complete expected-unit classification.

How to avoid: Validate and record the complete concern-skill trio for every language partition before invoking any concern skill. Record an absent required skill as `missing-skill`, then finish and render the rejected run.

</concern_inventory>

<language_ownership>

**Every changed file extension became a required language partition**

What happened: Claude treated documentation and manifest suffixes as programming languages, required concern skills that do not exist, rejected the run before dispatch, and skipped an installed implementation-language concern trio.

Why it failed: Implementation-audit ownership comes from installed `code-{lang}` skill surfaces and their scope guidance, not from the set of suffixes present in a changeset. Artifact-specific auditors and whole-changeset review own files outside those programming-language surfaces.

How to avoid: Discover languages from installed `code-{lang}` skills, validate the required concern trio for every discovered language before dispatch, then let each complete concern trio claim applicable paths or return `NOT_APPLICABLE`; omit non-implementation artifacts from the coverage inventory.

</language_ownership>

<finding_persistence>

**A finding was reported only in prose**

What happened: Claude named a concern finding in text without recording it through `spx verification run finding add`.

Why it failed: Prose findings are not durable evidence and cannot appear in the rendered SPX projection.

How to avoid: Record every finding through `spx verification run finding add`; use the rendered projection as the inspection surface.

</finding_persistence>

<coverage_evidence>

**Coverage labels replaced concern execution**

What happened: Claude inspected changed files before opening the verification run, then emitted three scope rows labeled `audited` with generic partition subjects and no observable concern-skill results.

Why it failed: An `audited` label asserted completion without naming the inspected paths or preserving the concern invocation that produced the judgment. The sealed projection could not distinguish a completed concern audit from orchestration self-certification.

How to avoid: Start the run before project inspection and invoke each concern skill while the run is open. After a concern returns, record one accepted scope row per inspected path using the exact path in `subject` and `priorContext.changedFilePartition`, then record every finding with the accepted path-scoped `unitId`. Assign `coverageStatus: audited` only to those completed path-scoped rows; never emit custom concern-result fields.

</coverage_evidence>

<serial_persistence>

**Scope events were persisted concurrently**

What happened: Claude launched multiple `spx verification run scope add` commands at the same time. The sealed render carried duplicate sequence numbers and skipped the intervening sequence even though the terminal status was approved.

Why it failed: Concurrent mutations raced the journal's sequence assignment, so the rendered event prefix violated the strictly increasing, contiguous sequence contract.

How to avoid: Execute every state-changing `spx verification run` command serially and wait for its exit before issuing the next mutation for that run.

</serial_persistence>

<payload_fields>

**An implementation code scope used semantic aliases instead of SPX fields**

What happened: Claude submitted `id`, `subjectPaths`,
`expectedProducerIdentity`, and `executionProducerIdentity` for a code unit.
`spx verification run scope add` exited `1` with
`spx verification run scope add payload failed verification-type validation`,
then Claude returned only the command and dropped the run token, exit code, and
stderr.

Why it failed: The published scope contract requires `unitId`, one string
`subject`, nested `priorContext`, `expectedProducer`, and
`recordedByRunDriver`. A command-only fallback also discarded the
evidence needed to reproduce the rejected payload boundary.

How to avoid: Construct scope and finding payloads from the exact JSON contracts
in `<verification_run_contract>` and relay the complete blocked diagnostic from
`<verdict_format>` without reformatting or omission.

</payload_fields>

<shell_quoting>

**An unquoted idempotency key split the command**

What happened: Claude passed
`--idempotency-key implementation:<lang>:tests:reports/audit report` without
quotes. The shell split the key at the space, so `spx` received a truncated key
and a stray argument.

Why it failed: An unquoted argument reaches the shell before `spx` sees it, so
any shell metacharacter the key carries — including one inside the subject path
of an otherwise correctly formatted key — becomes syntax rather than key text.
A subject path carrying `|` yields a different symptom: the shell runs the
fragment after it as a command, reporting `command not found` when the fragment
carries no slash and the `PATH` lookup fails, `No such file or directory` when a
slash-bearing fragment names nothing, and `Permission denied` when it names an
existing non-executable file. Each symptom names a path fragment, which reads as
a file problem rather than the quoting defect it is.

How to avoid: Pass every key as one single-quoted argument,
`--idempotency-key '<stable-scope-key>'`, per `<verification_run_contract>`.

</shell_quoting>

<deterministic_boundary>

**Deterministic verification ran inside the audit**

What happened: Claude ran validation, tests, or evals during implementation-audit orchestration.

Why it failed: This orchestration composes agentic concern audits only; running deterministic verification changes the audit boundary.

How to avoid: Stop and return the boundary failure with the deterministic command that was attempted.

</deterministic_boundary>

<unblocked_stop>

**A run sealed with required coverage uncovered and no blocker**

What happened: Claude ended two audit attempts over one 48-path changeset with
the inspection unfinished. The second attempt recorded required `incomplete`
coverage for code, tests, and architecture, sealed `rejected` with zero
findings, and reported "No external or tool condition blocks completion" before
finishing.

Why it failed: `incomplete` was a finishable state for a required unit, so
`finish` was reachable from Claude deciding to stop. A sealed `rejected` run
with no findings is indistinguishable at the projection from a completed audit
that found a coverage gap, so the gate consumed a giving-up as a verdict.

How to avoid: A required unit reaches only `audited`, `not-applicable`,
`missing-skill`, or `unsupported`. When none is reachable, return the
`<verdict_format>` blocked diagnostic naming the concrete failed operation or
absent prerequisite. Remaining work, elapsed time, context pressure, and
unfinished reading are never that cause.

</unblocked_stop>

<unrecovered_truncation>

**A truncated bulk read became missing coverage**

What happened: Claude read many source files in one call, the output truncated,
and no later read recovered the omitted content. The units covering those paths
never reached a final status.

Why it failed: A read boundary was converted into a coverage conclusion. The
files were present and readable; only the single oversized call failed.

How to avoid: Read subject bodies one at a time, and re-issue a truncated or
partial read in bounded ranges until the body is complete. An unrecovered read
is never coverage evidence.

</unrecovered_truncation>

<single_commit_subject>

**One commit's patch stood in for the changeset**

What happened: Claude inspected the latest commit's patch instead of the
resolved `base..head` range, so the subject was a fraction of the changeset the
run had already scoped.

Why it failed: The run's scope identity and the inspected content disagreed. The
projection reported coverage over a scope Claude never read.

How to avoid: Derive every subject body from the resolved `base` and `head`
retained at stage 1 of `<execution_sequence>`. Read a committed body with
`git show '{head}:{path}'`, never from a single commit's patch.

</single_commit_subject>

<finding_before_standards>

**A finding was raised before its governing standards were read**

What happened: Claude rejected a generated-value binding as invalid test
evidence before reading the applicable test standards and the audited
repository's `spx/local/` overlay. Both permit the pattern, and the overlay
documents the exact form observed. Claude withdrew the finding after reading
them.

Why it failed: The judgment ran against remembered rules rather than the
repository's declared ones. A finding raised that way costs the audited work a
repair round for a defect that does not exist.

How to avoid: Load each concern's governing standards and the audited
repository's declared `spx/local/` overlays at stage 3 of
`<execution_sequence>`, before any concern judgment. Withdraw a finding raised
before that load rather than recording it.

</finding_before_standards>

<transcribed_inventory>

**The resolved path inventory was corrupted by being retyped**

What happened: The resolver returned 48 changed paths for the audited head.
Claude read them out of the resolver's output and retyped them into the
`run start --input` payload, which reached the run carrying 47: two paths were
dropped and a third was replaced by a same-named file from a different
directory. Nothing later in the run referred to the resolver's output again, so
the substitution was invisible until the run was compared against a fresh
resolver invocation after it had sealed.

Why it failed: A changed-path set is longer than a response reproduces
reliably, and the paths in one repository differ by a single directory segment.
Retyping such a list is a transcription task, and the contract gave the
transcription no later referent that could contradict it.

How to avoid: Pipe the resolver's output into `run start --input stdin` with
`--audit-input` carrying only the short invocation-supplied values, per
`<verification_run_contract>`. Never read `changed_paths` out of the resolver's
output and re-emit them into a payload.

</transcribed_inventory>

<vacuous_reconciliation>

**A narrowed plan reconciled with itself and sealed an approved run**

What happened: Claude narrowed coverage to four paths of the resolved
changeset, planned four units, recorded four units, confirmed at stage 7 that
every planned unit carried a final status, and sealed the run `approved` with
zero findings. Its own postmortem confirmed it had preserved no other inspected
path. The projection reads as a complete approval of a changeset it never
inspected.

Why it failed: Reconciling recorded units against the run's own plan tests
internal consistency, never correspondence to the changeset. A plan narrowed
before enumeration reconciles perfectly, so the check that was meant to prevent
a partial seal certified one instead.

How to avoid: Reconcile at stage 7 with the bundled reconciler, whose referent
is the run's own sealed start inventory rather than the plan. Its exit code is
the verdict: exit 1 naming only unaccounted paths returns the run to
inspection; exit 1 naming drift, an unexpected subject, or a non-final
required unit returns the blocked diagnostic whatever else it names, because
no inspection changes what the selector resolves to and the append-only run
revises neither an accepted subject nor an accepted status; and only its zero
exit reaches `finish`.

</vacuous_reconciliation>

<coverage_stated_as_findings>

**A run recorded a unit only where it found something, then let the rejection end it**

What happened: Claude started the run with the complete 48-path inventory
piped in, loaded all three concern skills for the recognized language, and read
fourteen subject bodies. It then recorded two scope units — both `code`, both
for paths carrying its one finding — added that finding, and finished
`rejected`. Twelve inspected paths, every `tests` unit, and every
`architecture` unit went unrecorded. The stage 7 reconciliation never ran.

Why it failed: Two failures compose. Scope rows were treated as anchors a
finding needs rather than as the evidence that an inspection happened, so a path
inspected and found clean produced no row at all. The early `rejected` verdict
then read as settled — the run's outcome could not change — which made the
remaining concerns look like work with no consequence. Both are invisible in the
sealed projection unless a reader compares its subjects against its inventory,
and the run driver comparing against its own recollection has nothing to
contradict it.

How to avoid: Persist a concern's complete claimed-path coverage before any of
its findings, so a row exists for every inspected path whether or not it carries
one. Treat `rejected` as a verdict about what was inspected, never as permission
to stop: the remaining concerns and every unclaimed resolved path are recorded
before `finish`. Then run the stage 7 reconciler, which fails on exactly this
shape by naming the paths the run left unaccounted.

</coverage_stated_as_findings>

<language_probe_by_invocation>

**Languages were discovered by invoking skills that did not exist**

What happened: A run on a TypeScript changeset loaded the complete TypeScript
trio, then invoked `python:audit-python-code` and `rust:audit-rust-code` "to
probe whether the python and rust concern trios are loadable", received
`Unknown skill` for both, and read the two errors as evidence that no other
language was installed.

Why it failed: The skill named installed `code-{lang}` skills as the discovery
source but never said how to read that inventory, so the run driver fell back
to trial invocation. A failed invocation is one step from a manufactured
`missing-skill` unit: a run that records those errors as coverage seals
`rejected` for two languages the changeset never touched, and the language set
the run records becomes the driver's guess rather than the installed surface.
The run avoided that outcome by prose judgment alone.

How to avoid: Read the installed skill inventory this context already carries
for `code-{lang}` names; a name absent from it is a language that is not
installed. Invoke a concern skill only as dispatch to a discovered language.

</language_probe_by_invocation>

<empty_argument_taken_as_selector>

**A preloaded skill's empty argument was read as the target**

What happened: A request carried `HEAD` as its text while the harness had
preloaded this skill with `$ARGUMENTS` substituted empty. The run bound the
empty substitution, returned `BLOCKED` with `runToken: not-started` naming an
absent selector, and never read the request text that carried it. Three runs
on the identical input shape bound the request text and proceeded; nothing in
the contract said which source was the selector.

Why it failed: The request contract named `$ARGUMENTS` as the only selector
source. A harness that preloads the skill renders that argument before any
request exists, so it is empty there, and a driver that takes it literally
reports its own launch mechanics as a request error.

How to avoid: Bind the selector from `$ARGUMENTS` when it is non-empty and
from the request text when it is empty; an empty substitution binds nothing,
and only a request with no selector is the missing-input case.

</empty_argument_taken_as_selector>
