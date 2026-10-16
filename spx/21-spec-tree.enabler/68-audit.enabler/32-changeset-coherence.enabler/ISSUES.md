# Issues: Changeset Coherence

## Scope-resolver extraction awaits a published SPX CLI capability

`src/plugins/spec-tree/skills/audit-changeset-coherence/scripts/resolve_scope.py`
is the CLI entrypoint for the shared `resolve_committed_scope` provider in
`src/plugins/spec-tree/skills/scope-changeset/scripts/changeset_scope.py`.
It emits base and head commit identity plus the changed-file set as one JSON
object so the audit resolves its own scope. The entrypoint and provider each
exceed fifty lines. Past fifty lines
[`spx/12-shipped-scripting.adr.md`](spx/12-shipped-scripting.adr.md) makes a shipped script debt whose logic moves
into the SPX CLI once the script proves its value; the resolver has proven its
value in use, so extraction is what it owes.

The extraction is a cross-repo port into `@outcomeeng/spx`, a separate product,
and the plugins product may depend on the resulting capability only once it is
published to npm and `REQUIRED_SPX_VERSION` advances to it. That sequencing puts
the fix outside any changeset confined to this repository.

**Resolution shape**: the resolver already routes its derivation through the
shared changeset primitives tracked in
`spx/21-spec-tree.enabler/14-version-control.enabler/15-changeset-scope.enabler/ISSUES.md`,
so it extracts with them — port both, publish, advance the floor, and reduce the
shipped skill to its instruction with no script. Preserve the caller-independent
scope resolution across the move: the audit names no caller and stays invocable
on its own. Revisit when the capability publishes.

## The configured coherence auditor has no authorized caller or execution record

The configured-agent audit of
`src/plugins/spec-tree/agents/changeset-coherence-auditor.md` during Change #76
found no owning skill that explicitly launches the exact role with a target-only
prompt and no retained native-loading plus minimal isolated invocation result.
The node currently says `/audit-changeset-coherence` names no caller and stays
invocable on its own, while the root invocation policy requires an active skill
to select a configured role. That conflict leaves the agent definition without
an authorized launch path even though its capability boundary and thin wrapper
shape audit cleanly.

**Required handling**: decide whether the Author's governing workflow names and
launches this role or whether the configured agent is removed and the audit is
reached through another declared surface. Update the node, caller, and wrapper
together, then retain the emitted native definition and one target-only isolated
result.

**Evidence**: final `instructions:subagent-auditor` findings `f-001` and
`f-002` against
`src/plugins/spec-tree/agents/changeset-coherence-auditor.md` on Change #76
head `843ddd709b058970d414ec755cc10121ff6bb5ff`. The same audit approved the
corrected least-privilege tool and profile configuration.

**Release acceptance and invocation evidence.** The tree retains no native-loading
record and no minimal isolated execution of the emitted definition for either
harness's Standard profile, as property 3 of
[`spx/15-subagent-execution.pdr.md`](spx/15-subagent-execution.pdr.md) requires.
The gap is the one the `adr-auditor` entry in
`spx/21-spec-tree.enabler/32-decisions.enabler/21-adr-auditing.enabler/ISSUES.md`
records, and it holds for every marketplace definition: the decision binds
acceptance to profiles, and no definition's tool grant or sandbox changes the
Standard profile it selects.

**Impact**: nothing in the tree shows the emitted `changeset-coherence-auditor`
definitions loading natively and returning a run token and projection on either
harness, so each `subagent-auditor` run on the definition files the finding again.

**Settlement condition**: the release retains passing Standard-profile acceptance
rows for both harnesses at a location `/audit-subagent` reads, or the subagent
standards accept the harness's profile acceptance as a definition's invocation
evidence, which <https://github.com/outcomeeng/changes/issues/118> carries; then
one `subagent-auditor` run on the definition raises no `release_acceptance_evidence`
finding.

**Evidence**: two `instructions:subagent-auditor` runs on
`src/plugins/spec-tree/agents/changeset-coherence-auditor.md` under outcomeeng/changes#513.
Run `2026-10-16_19-39-21-548-906835a64c26` at head
`06d6e1e18e8a4485cb29c6e171ec73bed7d9669c` sealed `rejected`; it raised the
blocking rule `release_acceptance_evidence` and the blocking rule
`execution_boundary_mismatch`, which the amended wrapper assertion in commit
`d92f6f73b0a17127c8840078370fef38d072e02b` resolved. Run
`2026-10-16_19-59-29-460-b8a7ac7b6830` at that head sealed `approved` and filed
`instructions:subagent:definition:src/plugins/spec-tree/agents/changeset-coherence-auditor.md:release_acceptance_evidence`
against this entry, with `baseRefEvidence`
`184cc92eae6e896050a7cc991f63ce953b236ccd..d92f6f73b0a17127c8840078370fef38d072e02b`. The Plugins Maintainer's
disposition of this class for the Change's rewritten wrapper definitions
(outcomeeng/changes#513, comment 6221945881, item 4) leaves no repair in the
changeset.

## An approved run records no cluster facts

The assertion of
[`spx/21-spec-tree.enabler/68-audit.enabler/32-changeset-coherence.enabler/changeset-coherence.md`](spx/21-spec-tree.enabler/68-audit.enabler/32-changeset-coherence.enabler/changeset-coherence.md)
that the audit records its semantic clusters and the facts about them in its sealed
run's units stands as declared. The `spx verification run` unit payload has no field that
carries cluster facts, so an approved run records none.

**Impact**: the declaration leads the toolchain; the sealed record of an approved
run omits the cluster facts the assertion states.

**Settlement condition**: an `@outcomeeng/spx` release whose unit payload carries
the cluster facts is published, the repository floor advances to it, and the audit
records them on an approved run.

**Evidence**: ruling of the Plugins Maintainer on outcomeeng/changes#513 (comment
6223578521, item 2). The node is `spec`-malleable, so its declaration may lead its
implementation.

## The compliance section holds eleven assertions

The Compliance section holds eleven assertions, above the guideline of about seven for a decomposition candidate. The node stays whole: one `PROVIDES` statement covers every assertion, and the verdict states, the cluster partition, the collapse ordering, the evidence boundaries and the structured projection are one classification contract that the eval suite scores as one producer. Splitting them yields children whose assertions cannot be verified apart. A Verifier skips this decomposition signal.

**Revisit condition.** The node gains an assertion outside the classification contract, or the persistence migration lands and the projection contract separates from the classification contract.

## The node names no declared generated-source relationship

`changeset-coherence.md` and the shipped `src/plugins/spec-tree/skills/audit-changeset-coherence/SKILL.md` require declared generated-source relationship evidence without naming `spx/local/generated-sources.toml` or citing [`spx/31-outcomeeng.enabler/31-verification.enabler/15-generated-attribution.pdr.md`](spx/31-outcomeeng.enabler/31-verification.enabler/15-generated-attribution.pdr.md). The entry in `spx/31-outcomeeng.enabler/31-verification.enabler/ISSUES.md` carries the settlement condition.
