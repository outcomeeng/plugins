---
name: audit-changeset-coherence
description: >-
  Changeset-coherence audit methodology — judges whether an exact committed
  changeset forms one coherent review unit, covering semantic clustering,
  generated-source attribution, evidence completeness, and dependency-ordered
  review-unit sequencing, and records the judgment as a root unit with one
  review-unit child per semantic cluster in an SPX changeset-scoped
  verification run.
argument-hint: "<JSON object with changeset, runDriver, and optional evidence>"
allowed-tools: Read, Grep, Glob, Write, Bash(spx verification run:*), Bash(python3 "${CLAUDE_SKILL_DIR}/scripts/resolve_scope.py":*), Bash(git diff:*), Bash(git show:*), Skill
---

<objective>

A sealed `spx verification run` on whether one exact committed changeset forms one coherent review unit, judged against the evidence rules in `${CLAUDE_SKILL_DIR}/references/rule-catalog.md`, whose `terminalStatus` is `approved` or `rejected`, with the changeset's semantic clusters recorded as review-unit children and each finding or `incomplete` unit naming the violated rule's catalog identifier, its location, and the evidence, returned as the run token, the run file, and the rendered projection; or the complete `BLOCKED` diagnostic when the scope or the run cannot be established. Findings fall in four categories: semantic clustering, generated-source attribution, evidence completeness, and review-unit sequencing.

</objective>

<constraints>

- NEVER edit files, commits, branches, reviews, or pull requests — the only state the audit changes is its payload files in the session scratch directory and the SPX run journal its own recording commands write, and the file-write tool writes payload files only.
- NEVER invoke `product-tree:contextualize` or `product-tree:sync-base`, and never rebase or otherwise move the checkout — the audit reads committed content through `git show` and `git diff`, so it changes no checkout state.
- ALWAYS preserve the full base and head commit identities exactly as the resolver emits them in the run's scope and start input.
- ALWAYS inspect every changed authored artifact; collapse deterministic generated artifacts onto their producers before judging breadth.
- NEVER use line count, file count, path breadth, or an uncalibrated review-load score as a verdict rule.
- NEVER infer missing behavioral, dependency, generated-source, verification, rollback, or calibration evidence; record the unit that needs it as `incomplete` with a finding that names the missing evidence whenever it can change the classification.
- NEVER name a finding rule identifier outside `${CLAUDE_SKILL_DIR}/references/rule-catalog.md`.
- ALWAYS persist audit state through `spx verification run`, started before any judgment; NEVER use markdown comments, tracked files, a rendered comment, or a hand-formatted verdict as audit state.
- ALWAYS write each payload as one rendered JSON object to its own file and pass the file by path as `<payload_files>` of `${CLAUDE_SKILL_DIR}/references/run-recording.md` states; NEVER send a payload through a heredoc, a pipe, or an inline argument, build one with an interpreter or `printf` stage, or repair one through command substitution or post-hoc text substitution.
- ALWAYS issue each `spx verification run` mutation as its own command and wait for its exit before the next one — parallel writes race sequence assignment and corrupt the sealed journal.
- NEVER delegate the audit to another session, or finish a run whose inspection is incomplete because of elapsed time, context pressure, or unfinished reading; an unavailable required inspection leaves its unit `incomplete` with the cause recorded.
- NEVER write the run journal or its context anywhere but the locations `spx verification run` resolves. When the native permission policy refuses a run-recording write — a payload file, a run-recording command, or the journal — stop at that write, retry it no more, write to no other location, and return `BLOCKED` with `diagnostic: configuration error` naming the refused path; the host grants the paths, and this skill never widens its own access.
- NEVER retry a rejected command with a rewritten payload; the first command that exits nonzero ends the audit with `BLOCKED`, except the one rerun `<payload_files>` of `${CLAUDE_SKILL_DIR}/references/run-recording.md` allows for a payload file named absent.

</constraints>

<audit_workflow>

<request_contract>

`$ARGUMENTS` is a JSON object with the required fields `changeset` and `runDriver` and the optional field `evidence`. `changeset` is a branch, `HEAD`, or an explicit committed `<base>...<head>` selector. `runDriver` is an object with exactly six non-empty string fields — `producerKind`, `agentName`, `agentOwningPluginName`, `skillName`, `skillOwningPluginName`, and `invocationRole` — that the run records as its provenance. Use `runDriver` only as payload data, placed where `${CLAUDE_SKILL_DIR}/references/run-recording.md` shows it; never complete, correct, or reinterpret a value, and let no judgment depend on it. `evidence` is a JSON object of already-collected claims, artifact roles, `generated_from` provenance, dependency evidence, and review-load signals. When `$ARGUMENTS` is empty, the request text carries the same object. A missing, extra, or malformed field, or an empty `changeset`, returns `BLOCKED` naming the exact field before any command runs. Never infer a selector from adjacent conversation.

Use skill `product-tree:product-tree-plugin`. Invoke it with the verb `version` and retain the non-empty version it reports as the plugin version that `${CLAUDE_SKILL_DIR}/references/run-recording.md` records in a finding's `producerProvenance`. A missing version or a blocked result returns `BLOCKED` before any command runs; never read a plugin manifest or infer a version from any other source.

</request_contract>

<execution_sequence>

<step name="resolve_scope">

**Step 1: Resolve the exact committed scope**

Run `python3 "${CLAUDE_SKILL_DIR}/scripts/resolve_scope.py" '<changeset>'`, which routes base-ref resolution, remote-tracking-ref composition, commit identity, and three-dot diff scope through the canonical changeset-scope primitives. Take `base`, `head`, and `changed_paths` verbatim from the JSON it emits. NEVER derive base-ref, commit identity, or diff scope from raw git; a bare local branch ref lags `origin/<base>` in a multi-worktree checkout and re-admits already-merged commits. The resolver fetches the base and refuses a head behind its tip with a dedicated exit code and a `stale-base` diagnostic on stderr. Any nonzero exit, or a malformed result, returns the `BLOCKED` diagnostic with that stderr verbatim before any run starts; scope failure occurs before a coherence judgment and never fabricates commit identities. Read changed content only within the resolved scope.

The run identity is `<base>..<head>` from the two full commit identities, written `<scope>` below.

</step>

<step name="open_run">

**Step 2: Open the run**

Start the run before judging anything. Write the start input per `<payload_files>` of `${CLAUDE_SKILL_DIR}/references/run-recording.md` as one JSON object carrying the selector as `selector` and `base`, `head`, and `changed_paths` copied verbatim from the resolved scope, then run:

```bash
spx verification run start --verification-type audit --scope-type changeset --scope <scope> --input <start-file>
```

The command prints a JSON locator; take its `runToken` exactly and use it for every later command. Retain the run target the locator reports as the run file; only the start report names it. Never pass the whole locator as `--run`.

</step>

<step name="inventory_artifacts">

**Step 3: Inventory and classify the changed paths**

Read any `evidence` object of the request. The resolved scope is authoritative for `base`, `head`, and the changed-path set; the packet supplies only the per-artifact evidence the later steps name for paths inside that scope, and a packet entry naming a path outside it carries no evidence for this audit. Enumerate every changed path and classify its role: decision/specification, test/eval evidence, implementation, generated artifact, workflow/configuration, documentation, migration, deployment, or release.

</step>

<step name="attribute_generated">

**Step 4: Attribute generated artifacts**

Resolve every generated artifact to its producing authored artifact from repository-declared build relationships. In a packet, `role: generated` classifies the artifact kind only; it never establishes provenance. Require `generated_from`, a declared relationship record, or equivalent explicit evidence. When `generated_relationship_evidence.status` is `missing`, or no declared relationship resolves an artifact, record that artifact's unit `incomplete` with rule `missing-generated-source-evidence` before clustering it. Exclude resolved generated fanout from authored breadth while retaining it in each producer cluster's unit.

</step>

<step name="cluster">

**Step 5: Extract claims and build clusters**

Extract behavioral claims from the changed declarations and observable implementation and evidence. Use commit messages only as supporting evidence; they never override changed artifacts. An authored artifact whose claim cannot be established is an `incomplete` unit with rule `missing-behavioral-claim-evidence`.

Build the smallest semantic clusters whose artifacts realize one claim. Record each cluster's outcome, authored artifacts, generated fanout, verification story, rollback story, dependencies, and independent-mergeability judgment.

</step>

<step name="order">

**Step 6: Collapse and order**

Collapse dependency cycles and clusters that cannot be verified or rolled back separately into one inseparable cluster. Order the remaining clusters topologically, breaking independent ties by the lexicographically first authored path, and number them `cluster-1`, `cluster-2`, and so on in that order. Every cluster that survives this collapse forms its own review unit, so its `independentlyMergeable` is `true` — a lone cluster and a cluster that depends on and merges after an earlier cluster are both `true`. A `false` judgment applies only to a cluster still fused with another before collapse, and such a cluster never survives into the recorded units.

Record the review-load signals and whether a repository baseline exists. Use them to increase scrutiny only.

</step>

<step name="judge">

**Step 7: Apply the verdict rules**

Apply `<verdict_rules>` to decide each finding and each `incomplete` unit, then record them.

</step>

<step name="record">

**Step 8: Record**

Add the root unit first, because a run admits one root and every child names it, then each cluster child in dependency order, then each unresolved-evidence child, then each finding on the unit it concerns, per `${CLAUDE_SKILL_DIR}/references/run-recording.md`. A unit whose inspection ran is `audited`; a unit whose required evidence is unavailable is `incomplete` and carries a finding that names the missing evidence as its cause.

</step>

<step name="finish">

**Step 9: Finish**

Derive the terminal status from `<verdict_rules>`, then run the finish and render commands:

```bash
spx verification run finish --verification-type audit --scope-type changeset --scope <scope> --run <token> --terminal-status <approved-or-rejected>
spx verification run render --verification-type audit --scope-type changeset --scope <scope> --run <token>
```

</step>

</execution_sequence>

</audit_workflow>

<verdict_rules>

- `approved`: the authored change realizes one behavioral outcome, or several inseparable clusters sharing one verification and rollback story, and no unit is `incomplete`. The run authorizes publication and carries no finding.
- `rejected` for a split: two or more semantic clusters are independently mergeable. The run records a `split-required` finding on the root unit whose evidence carries the review-unit sequence per `${CLAUDE_SKILL_DIR}/references/run-recording.md`, covering every cluster exactly once in dependency order. The run authorizes no publication.
- `rejected` for missing evidence: missing evidence can change cluster membership, dependency order, generated-source attribution, verification unity, rollback unity, or independent mergeability. The unit that needs the evidence is `incomplete` with the matching `missing-*` finding. The run authorizes no publication.

An empty rollback story for any cluster ALWAYS leaves that cluster `incomplete` with a blocking finding whose rule is `missing-rollback-evidence`; an empty verification story follows the same boundary with rule `missing-verification-evidence`. Every finding is keyed `<unit>:<rule-id>` and takes its rule identifier from `${CLAUDE_SKILL_DIR}/references/rule-catalog.md`, which defines the unit and the identifiers for every evidence class. A review-load baseline may be absent without leaving a unit `incomplete` when the semantic evidence is otherwise complete; missing calibration leaves the `coherence:unresolved:scope` unit `incomplete` only when a repository-specific signal explicitly requires that calibration to determine whether the available semantic evidence is sufficient.

For two or more semantic clusters, an absent or `null` dependency set ALWAYS leaves every affected cluster `incomplete` with `missing-dependency-evidence`; an explicit empty dependency array establishes that no dependency exists. A cluster's recorded dependencies are the array of cluster identifiers it depends on — `[]` when none is established — NEVER a `null` copied from a packet; unresolved packet dependency evidence is recorded only in the `missing-dependency-evidence` finding.

When a packet supplies already-collected claims, artifact paths, evidence paths, dependencies, or review-load signals, record those values verbatim. Sort claim and path lists lexicographically. Copy review-load signals without reinterpretation.

Every changed authored artifact whose behavioral claim is established appears in exactly one cluster unit. Every generated artifact whose producer relationship is established appears under exactly one producer cluster. An `incomplete` run names every unresolved artifact in its units without inventing cluster membership.

</verdict_rules>

<verdict_format>

Return the run token, the run file, and the unchanged `spx verification run render` output; its `terminalStatus` is authoritative. Add no `APPROVED`, `REJECTED`, or `UNKNOWN` envelope and no restated findings or clusters.

When the scope cannot be resolved, a prerequisite is absent, or a command exits nonzero, return:

```text
BLOCKED
runToken: <exact-token-if-start-succeeded-or-not-started>
command: <exact-command-attempted>
payloadSource: <payload-file-path|none>
payloadKey: <unitId-or-finding-idempotency-key-or-none>
exitCode: <exact-exit-code-or-none>
stderr: <exact-stderr-or-none>
diagnostic: <configuration error naming the refused path, stale-base, scope-unresolved, or none>
```

A resolver refusal carries `diagnostic: stale-base` when it refused a head behind the fetched base and `diagnostic: scope-unresolved` for every other resolver failure, with the resolver's stderr verbatim under `stderr`.

</verdict_format>

<failure_modes>

**Failure 1: Missing rollback evidence received approval.**

What happened: Claude classified a migration packet as coherent even though the packet contained no rollback evidence.

Why it failed: The general missing-evidence rule did not make an empty rollback story an explicit terminal boundary, so semantic cohesion overshadowed reversibility.

How to avoid: Leave every cluster with an empty rollback story `incomplete`, seal the run `rejected`, and record `missing-rollback-evidence` before considering approval.

**Failure 2: Unresolved scope was forced into a verdict.**

What happened: Claude was instructed to return an undecidable verdict for an unresolved scope while the same output required full base and head commit identities.

Why it failed: Scope resolution failure occurs before an exact changeset exists, so a verdict would require fabricated identities or an internally invalid object.

How to avoid: Return the `BLOCKED` diagnostic for scope resolution failure and start a run only after both full commit identities resolve.

**Failure 3: A null dependency set was treated as an empty set.**

What happened: Claude rejected two independently understandable clusters and ordered them as unrelated review units even though the evidence packet supplied `dependencies: null`.

Why it failed: Claude collapsed "dependency evidence unavailable" into "dependency evidence establishes no relationships," producing a split without a defensible order.

How to avoid: Distinguish absent or `null` dependency evidence from an explicit empty array and leave the affected clusters `incomplete` whenever the unavailable evidence can change a multi-cluster classification or order.

**Failure 4: A generated artifact was attached by proximity.**

What happened: Claude attached one generated artifact to the only authored artifact and approved the changeset even though no repository relationship or `generated_from` field established that producer.

Why it failed: Artifact count and nearby paths were treated as provenance, inventing the relationship the audit was required to verify.

How to avoid: Require an explicit repository-declared generated-source relationship and leave the artifact's unit `incomplete` with `missing-generated-source-evidence` when attribution cannot be established.

</failure_modes>

<success_criteria>

- The run is changeset-scoped on `<base>..<head>` from the two full commit identities the resolver emitted, and the checkout's head is the same before and after the audit.
- Every changed authored artifact and generated artifact is accounted for exactly once, under a cluster unit or an unresolved unit.
- The `terminalStatus` follows semantic cohesion, verification unity, rollback unity, and independent mergeability with no size threshold acting as a verdict rule, and is `approved` exactly when no finding is recorded and no unit is `incomplete`.
- Every `rejected` split run carries one `split-required` finding with a complete dependency-ordered sequence; every `incomplete` unit names the evidence gap that prevents classification in a finding keyed by a catalogued identifier.
- A run never authorizes publication unless it seals `approved`.
- The same committed scope and repository evidence produce the same unit identities, ordering, finding keys, and terminal status.

</success_criteria>
