# Issues

## Implementation audit cannot dispatch its selected concern skills

The isolated implementation-auditor run
`2026-09-17_19-03-14-472-e7a80b7b7f6b` resolved Change #76 at committed
head `13c2655df40c2a17041dd36d7b94e546e1179380`, started its verification
run, and reached the required `audit-{lang}-{code|tests|architecture}`
dispatch. The configured verifier context exposed no skill-invocation surface,
so the run returned `BLOCKED` before any concern verdict.

The run supplies no implementation-audit approval. Resume the gate from a
fresh configured-agent registry that contains the Change #76 execution-policy
repair, then dispatch once against the exact current committed head. Keep the
failed run token as the reproduction record; never reinterpret it as a
verdict or retry the same failed launch.

## Configured Codex verifier selected Xcode Python 3.9

The Change #76 composition probe on subject
`759e3abccc5f90b0cbc18a284557caeb9d07766e`, using Change #86 adapter commit
`04ef3aa632ba7e4b6ce450c013a00de0cc916347`, installed the generated
`spec-tree_implementation-auditor`, launched exactly one isolated child, and
observed that child read the installed `spec-tree:audit-implementation` skill.
The child then invoked the skill's `resolve_scope.py` through `python3`.

Inside the configured child, `python3` resolved to Xcode Python 3.9 at
`/Applications/Xcode.app/Contents/Developer/Library/Frameworks/Python3.framework/Versions/3.9/`.
Importing `enum.StrEnum` failed before the child could start an SPX run, select
any concern skill, or produce an implementation-audit projection. The probe's
terminal result records `runToken: not-started` and exit code 1. The attested
run and scrubbed artifacts are retained in
`probes/codex-skill-composition/2026-09-17-759e3abcc/`.

Settlement requires the isolated Codex probe environment to expose the
repository's supported managed Python window to configured children, followed
by a fresh attested run on a new committed subject. The failed one-shot run is
never retried or reinterpreted as approval.
