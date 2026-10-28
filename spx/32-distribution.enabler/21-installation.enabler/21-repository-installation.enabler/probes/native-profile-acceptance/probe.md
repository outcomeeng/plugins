# Native profile acceptance

The protocol lives at `probes/native-profile-acceptance/probe.md`, the target of the assertion's `[probe]` tag. Working runs stay in an ignored `runs/` inside this directory; every attested run retains at least one inspectable artifact beside this file.

## Intent

Each subagent profile the marketplace ships — Standard, Strong, Executor and Fast — resolves to a native model and effort on Claude Code and on Codex. Reading the profile registry and the generated definitions does not show that each harness loads the definition natively and executes one isolated child under the configuration the registry names. This probe shows, for each of the eight `<harness>-<profile>` rows, a retained configuration artifact, a retained loading artifact, and a result artifact that records one native child invocation or the terminal condition that stopped the row.

The retained rows are the release acceptance of the profiles. A changed profile registry or a changed shipped subagent definition makes the rows stale until the protocol runs again.

## Environment and preconditions

- The native profile acceptance workflow exists at the subject commit on a branch the operator can dispatch, and it declares `workflow_dispatch` as its only trigger.
- The repository secrets the workflow reads are set by the operator: the Claude Code credential, and the Codex credential with the explicit authentication mode the workflow selects. The Author sets no secret.
- The operator has approved the run and its spend before the dispatch.
- The Author holds write access to the repository and an authenticated `gh` command-line tool.
- The working tree at the subject commit is clean, and the generated trees match their authored sources.

## Protocol

1. Record the subject commit, the workflow file path, and the profile registry the workflow runs against.
2. Dispatch the native profile acceptance workflow at the subject commit on a hosted runner, and record the run identifier and the run URL.
3. Wait for the run to finish. A run that stops before it uploads its artifact is a failed attempt: record its terminal condition and repeat from step 2 only when the operator approves another run.
4. Download the workflow's uploaded artifact into a new, empty directory outside the repository.
5. Confirm that the `profiles` directory of the artifact holds one directory for each of the eight rows, named by the row's identifier — Claude Code and Codex, each with the Standard, Strong, Executor and Fast profiles — and that each holds a configuration artifact, a `loading.json` and a `result.json`.
6. Copy each row's directory from the artifact's `profiles` directory into this probe directory under `profiles/<row identifier>/`, unchanged.
7. Copy each of the four auditor-dispatch rows from the artifact's `auditors` directory — `skill-auditor` and `subagent-auditor` on each of Claude Code and Codex — unchanged into the `probes/native-auditor-dispatch/` directory beside the native-dispatch assertion in `spx/43-instructions.enabler/instructions.md`, under `auditors/<row identifier>/`.
8. Read each of the eight profile rows' artifacts: from the loading artifact, whether the native definition was materialized and discovered; from the result artifact, the terminal condition, the child invocation, and, for Codex, the recorded role, model, effort and completion of the sole child. Judge each row against the configuration its configuration artifact records.
9. Under Attested run, list the run identifier, the subject commit, the date, one observation per row, and a link to every retained artifact.
10. Under Verdict, name each row `passed` or `failed`. A row whose result artifact is missing, unparseable, or records a terminal condition other than one completed native child invocation is `failed`, and the verdict names it.

## Attested run

- Date:
- Subject commit:
- Workflow run:
- Observations:
- Artifacts:

## Verdict

## Limitations

- Each row makes one minimal child invocation; judgment quality of a profile over a large or adversarial task stays unexercised.
- The Codex record carries the configuration the child recorded; it is not per-turn execution telemetry.
- Evidence for one harness establishes no execution claim for the other.
- A change to the profile registry, to a shipped subagent definition, or to the native profile acceptance workflow makes the retained rows stale until the protocol runs again on the new commit.
- The protocol depends on credentials only the operator sets; a missing or invalid credential stops every row of its harness and the verdict records that condition.
