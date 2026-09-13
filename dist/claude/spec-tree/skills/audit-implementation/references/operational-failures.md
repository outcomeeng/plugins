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
