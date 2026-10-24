<objective>

The long tail of operational failure modes of the implementation audit. A failed preparation, concern invocation, payload submission, or projection that matches one below keeps its exact diagnostic and takes no retry beyond the one absent-payload rerun the payload contract allows.

</objective>

<failure_modes>

**Failure 3: Every changed file extension became a required partition**

What happened: Claude treated documentation and manifest suffixes as programming languages, required concern skills that do not exist, rejected the run before dispatch, and skipped a selected concern skill.

Why it failed: Implementation-audit ownership comes from the registry selection the scope resolver recorded for each path, not from the set of suffixes present in a changeset. Artifact-type auditors and whole-changeset review own paths whose registered audit skill follows another contract and paths no registered artifact matches.

How to avoid: Read the selection from the run's sealed start input, validate each selected concern skill before dispatch, then let each concern skill claim applicable paths or return `NOT_APPLICABLE`; record every other path as an accounting unit, naming `<plugin>:<audit>` when the selection carries an artifact-type skill for it.

**Failure 4: A finding was reported only in prose**

What happened: Claude named a concern finding in text without recording it through `spx verification run finding add`.

Why it failed: Prose findings are not durable evidence and cannot appear in the rendered SPX projection.

How to avoid: Record every finding through `spx verification run finding add`; use the rendered projection as the inspection surface.

**Failure 6: Scope events were persisted concurrently**

What happened: Claude launched multiple `spx verification run scope add` commands at the same time. The sealed render carried duplicate sequence numbers and skipped the intervening sequence even though the terminal status was approved.

Why it failed: Concurrent mutations raced the journal's sequence assignment, so the rendered event prefix violated the strictly increasing, contiguous sequence contract.

How to avoid: Execute every state-changing `spx verification run` command serially and wait for its exit before issuing the next mutation for that run.

**Failure 7: An implementation code scope used semantic aliases instead of SPX fields**

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
in the payload contract and relay the complete blocked diagnostic from
`<verdict_format>` without reformatting or omission.

**Failure 8: An unquoted idempotency key split the command**

What happened: Claude passed
`--idempotency-key implementation:<kind>:tests:reports/audit report` without
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
`--idempotency-key '<stable-scope-key>'`, per the payload contract.

**Failure 9: Deterministic verification ran inside the audit**

What happened: Claude ran validation, tests, or evals during implementation-audit orchestration.

Why it failed: This orchestration composes agentic concern audits only; running deterministic verification changes the audit boundary.

How to avoid: Stop and return the boundary failure with the deterministic command that was attempted.

**Failure 11: A truncated bulk read became missing coverage**

What happened: Claude read many source files in one call, the output truncated,
and no later read recovered the omitted content. The units covering those paths
never reached a final status.

Why it failed: A read boundary was converted into a coverage conclusion. The
files were present and readable; only the single oversized call failed.

How to avoid: Read subject bodies one at a time, and re-issue a truncated or
partial read in bounded ranges until the body is complete. An unrecovered read
is never coverage evidence.

**Failure 12: One commit's patch stood in for the changeset**

What happened: Claude inspected the latest commit's patch instead of the
resolved `base..head` range, so the subject was a fraction of the changeset the
run had already scoped.

Why it failed: The run's scope identity and the inspected content disagreed. The
projection reported coverage over a scope Claude never read.

How to avoid: Derive every subject body from the resolved `base` and `head`
retained at stage 1 of `<execution_sequence>`. Read a committed body with
`git show '{head}:{path}'`, never from a single commit's patch.

**Failure 13: A finding was raised before its governing standards were read**

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

**Failure 14: The resolved path inventory was corrupted by being retyped**

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

How to avoid: Have the resolver write its output to a file and pass that file by
path to `run start --input`, with `--audit-input` carrying only the short
invocation-supplied values, per the run-start contract. Never read `changed_paths` out of the resolver's
output and re-emit them into a payload.

**Failure 17: Kinds were discovered by invoking skills that did not exist**

What happened: A run on a TypeScript changeset loaded the complete TypeScript concern skills, then invoked `python:audit-python-code` and `rust:audit-rust-code` "to probe whether the python and rust concern skills are loadable", received `Unknown skill` for both, and read the two errors as evidence that no other language was installed.

Why it failed: The run selected skills by trial invocation instead of reading the registry selection. A failed invocation is one step from a manufactured `missing-skill` unit: a run that records those errors as coverage seals `rejected` for two kinds the changeset never touched, and the kind set the run records becomes the driver's guess rather than the registry's selection.

How to avoid: Select skills only from `artifact_selection` in the run's sealed start input. Read the installed skill inventory this context already carries to decide whether a selected skill runs or is recorded as `missing-skill`. Invoke a concern skill only as dispatch to a selected artifact.

**Failure 18: A preloaded skill's empty argument was read as the target**

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

**Failure 19: A retyped payload path voided the run**

What happened: Claude wrote a scope payload with the file-write tool, then typed
the path into `scope add --payload` from memory. The typed scratch directory
differed from the reported one by a character, the command exited nonzero
naming the payload file as absent, and the run sealed no verdict.

Why it failed: A scratch directory name is long and differs from its neighbours
by a few characters, so retyping it is a transcription task with no later
referent to contradict it. The failure surfaced only at the command.

How to avoid: Copy the scratch directory the harness names into each payload
path character for character, and pass each scope-add and finding-add command
the path exactly as the file-write result reports it. Stop before the command
when the reported path lies outside that directory by whole path components,
naming the reported path. Rerun a scope-add or finding-add command once, with
the path copied from the file-write result, when its diagnostic names the
payload file as absent; on a second failure return the blocked diagnostic
naming the run token.

</failure_modes>
