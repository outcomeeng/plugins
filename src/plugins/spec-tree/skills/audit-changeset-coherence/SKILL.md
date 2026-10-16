---
name: audit-changeset-coherence
description: >-
  Changeset-coherence audit methodology — judges whether an exact committed
  changeset forms one coherent review unit, covering semantic clustering,
  generated-source attribution, evidence completeness, and dependency-ordered
  review-unit sequencing, and records the judgment as one root unit and one
  review-unit child per semantic cluster in an SPX changeset-scoped
  verification run.
argument-hint: "<JSON object with target and runDriver>"
allowed-tools: Read, Grep, Glob, Write, Bash(python3 "${CLAUDE_SKILL_DIR}/scripts/resolve_scope.py":*), Bash(spx verification run:*), Bash(git diff:*), Bash(git show:*), {{! tool('use_skill') !}}
---

<objective>

A sealed `spx verification run` judging whether one exact committed changeset forms one reviewable semantic unit against the coherence model, with one root unit and one `review-unit` child per semantic cluster and findings drawn from its rule catalog — `split-required` or a `missing-*` evidence rule — returned as the run token, the run file, and the rendered projection, whose `terminalStatus` is `approved` or `rejected`; or the complete `BLOCKED` diagnostic when the scope cannot be resolved or the run cannot finish.

</objective>

<constraints>

- NEVER modify files, commits, branches, reviews, or pull requests — the only state the audit changes is its payload files in the session scratch directory and the SPX run journal its own recording commands write, and the file-write tool writes payload files only.
- NEVER invoke `/contextualize` or `/sync-base`: both can move the checkout, and this audit leaves the checkout unmoved.
- NEVER run tests, validation, linters, type-checkers, or other deterministic verification inside the audit — establish evidence by reading the committed content.
- ALWAYS preserve the full base and head commit identities exactly as the resolver reports them in the run scope, the start input, and every unit key.
- ALWAYS inspect every changed authored artifact, and collapse generated artifacts onto their producers before judging breadth.
- NEVER let line count, file count, path breadth, or a review-load measurement decide a verdict without semantic evidence.
- NEVER infer missing behavioral, dependency, generated-source, verification, rollback, or calibration evidence — record the unit that needs it as `incomplete` with its cause.
- ALWAYS draw each finding's `rule` from `<rule_catalog>` in `${CLAUDE_SKILL_DIR}/references/coherence-model.md` and carry the severity its row declares — a rule outside the catalog is a gap in the standard, never a finding.
- ALWAYS persist audit state through `spx verification run`, started before any judgment; NEVER use markdown comments, tracked files, or a hand-formatted verdict as audit state.
- ALWAYS write each payload as one rendered JSON object to its own file and pass the file by path as `<payload_files>` in `${CLAUDE_SKILL_DIR}/references/run-recording.md` states; NEVER send a payload through a heredoc, a pipe, or an inline argument, build one with an interpreter or `printf` stage, or repair one through command substitution or post-hoc text substitution.
- ALWAYS issue each `spx verification run` mutation as its own command and wait for its exit before the next one — parallel writes race sequence assignment and corrupt the sealed journal.
- NEVER retry a rejected command with a rewritten payload; the first command that exits nonzero ends the audit with `BLOCKED`.

</constraints>

<essential_principles>

**SEMANTIC EVIDENCE DECIDES, NEVER SIZE.**

A changeset is one reviewable unit when its authored artifacts realize one behavioral outcome, or inseparable semantic clusters with one verification story and one rollback story. A large changeset with one outcome approves; a small changeset with two independently mergeable outcomes rejects.

**SPLIT, NEVER GUESS.**

Two or more independently mergeable clusters reject the run with a dependency-ordered review-unit sequence that covers every cluster exactly once. Evidence that cannot be established rejects the run through an `incomplete` unit and never authorizes publication.

**BINARY OUTCOME.**

The run finishes `approved` or `rejected`. `approved` authorizes publication of the changeset as one review unit; `rejected` never does.

</essential_principles>

<audit_workflow>

<request_contract>

`$ARGUMENTS` supplies the request when non-empty; when it is empty, the request is the one the request text carries, and the empty substitution binds nothing. The request is a JSON object with exactly two fields. `target` is a committed changeset selector: `HEAD`, a branch, or a three-dot `<base>...<head>` range. `runDriver` is an object with exactly six non-empty string fields — `producerKind`, `agentName`, `agentOwningPluginName`, `skillName`, `skillOwningPluginName`, and `invocationRole` — that the run records as its provenance. Use `runDriver` only as payload data, placed where `<persistence_contract>` in `${CLAUDE_SKILL_DIR}/references/run-recording.md` shows it; never complete, correct, or reinterpret a value, and let no judgment depend on it. A missing or empty `target`, a missing, extra, or malformed `runDriver` field, or an unknown field returns `BLOCKED` with run token `not-started` naming the exact field before any command runs.

Use skill `spec-tree:spec-tree-plugin`. Invoke it with the verb `version` and retain the non-empty version it reports as the plugin version that the finding payload of `${CLAUDE_SKILL_DIR}/references/run-recording.md` records in `producerProvenance`. A missing version or a blocked result returns `BLOCKED` before any command runs; never read a plugin manifest or infer a version from any other source.

</request_contract>

<step name="resolve_scope">

**Step 1: Resolve the committed scope and load the foundation**

Run `python3 "${CLAUDE_SKILL_DIR}/scripts/resolve_scope.py" "<target>"`, which routes base-ref resolution, remote-tracking-ref composition, commit identity, and three-dot diff scope through the canonical changeset-scope primitives. Retain its `base`, `head`, and `changed_paths` verbatim. NEVER derive a base ref, commit identity, or diff scope from raw git: a bare local branch ref lags `origin/<base>` in a multi-worktree checkout and re-admits already-merged commits.

The resolver fetches the base and refuses a head behind its tip with a dedicated nonzero exit code and a `stale-base` diagnostic on stderr. That refusal and every other nonzero exit return `BLOCKED` with run token `not-started`, the resolver command, its exit code, and its stderr verbatim, before any subject is read and with no run started. Never fabricate commit identities or a replacement scope.

When the live `<SPEC_TREE_FOUNDATION>` marker is absent: Use skill `spec-tree:understand`. Do not proceed without it: a failed load returns `BLOCKED` with run token `not-started`, the load as the command, and the failure as stderr, so no changed path is read and no run starts.

</step>

<step name="open_run">

**Step 2: Open the run**

Start the run before judging anything. Write the scope as one JSON object with `base`, `head`, and `changed_paths` copied verbatim from the resolver output, with the file-write tool to a start-input file in the scratch directory, then:

```bash
spx verification run start --verification-type audit --scope-type changeset --scope <base>..<head> --input '<start-input-file>'
```

The command prints a JSON locator; take its `runToken` exactly and use it for every later command. Retain the run target the locator reports as the run file; only the start report names it. Never pass the whole locator as `--run`.

</step>

<step name="classify_artifacts">

**Step 3: Classify every changed path**

Read the coherence model before judging: `${CLAUDE_SKILL_DIR}/references/coherence-model.md`

Enumerate every path in `changed_paths` and classify its role as `<artifact_roles>` states. Read changed content within the resolved scope with `git diff`, `git show`, and `Read`; a path outside the resolved scope carries no evidence for this audit.

Resolve every generated artifact to its producing authored artifact from the build relationships the repository declares, and collapse it onto that producer. An artifact whose producer the repository's declarations leave unestablished is unresolved, and the cluster it belongs to is undecidable until it resolves.

</step>

<step name="cluster">

**Step 4: Build the semantic clusters**

Extract behavioral claims from the changed declarations and the observable behavior of the changed implementation and evidence. Build the smallest clusters whose artifacts realize one claim, and establish each cluster's facts as `<semantic_clusters>` states.

Fuse every dependency cycle and every set of clusters that cannot be verified or rolled back separately into one inseparable cluster, then order the survivors as `<review_units>` states. Establish each cluster's review-load signals after collapse and record them on its cluster line, to raise scrutiny only.

</step>

<step name="judge">

**Step 5: Judge the changeset**

- One surviving cluster: the changeset is one reviewable semantic unit and raises no `split-required` finding.
- Two or more surviving clusters: the changeset raises one `split-required` finding on the root, carrying the review-unit sequence as `<persistence_contract>` shapes it.
- A unit whose behavioral claim, dependency, generated-source, verification, rollback, or calibration evidence cannot be established is `incomplete`, and the unit carries the matching `missing-*` finding naming the cause. An empty rollback story for any cluster is `missing-rollback-evidence` before approval is considered. A repository baseline for review load may be absent when the semantic evidence is otherwise complete; `missing-calibration-evidence` applies only where a repository-specific signal requires that baseline.
- Two or more clusters with a dependency set that is not established raise `missing-dependency-evidence`; an established empty set is an established absence of any dependency.

</step>

<step name="record">

**Step 6: Record**

Read `${CLAUDE_SKILL_DIR}/references/run-recording.md` before the first `scope add`; its `<persistence_contract>` gives the unit identities and payloads and its `<payload_files>` gives how each payload reaches a command. Add the root unit first, because a run admits one root and every review unit names it, then one review unit per surviving cluster in review-unit order, then each finding on the unit its catalog row names. A review unit whose inspection was completed is `audited`; a unit that needs evidence the committed content does not establish is `incomplete`.

</step>

<step name="finish">

**Step 7: Finish and render**

Derive `rejected` when any finding is recorded, any unit is `incomplete`, or two or more review units are recorded, and `approved` otherwise. Run the finish and render commands with the scope Step 2 started:

```bash
spx verification run finish --verification-type audit --scope-type changeset --scope <base>..<head> --run <token> --terminal-status <approved-or-rejected>
spx verification run render --verification-type audit --scope-type changeset --scope <base>..<head> --run <token>
```

</step>

</audit_workflow>

<verdict_format>

Return the run token, the run file, and the unchanged `spx verification run render` output; its `terminalStatus` is authoritative. Add no `APPROVED`, `REJECTED`, or `UNKNOWN` envelope, no JSON verdict, and no restated findings.

When a command exits nonzero or a prerequisite is absent, return:

```text
BLOCKED
runToken: <exact-token-if-start-succeeded-or-not-started>
command: <exact-command-attempted>
payloadSource: <payload-file-path|none>
payloadKey: <unitId-or-finding-idempotency-key-or-none>
exitCode: <exact-exit-code-or-none>
stderr: <exact-stderr-or-none>
```

</verdict_format>

<failure_modes>

**Failure 1: Missing rollback evidence received approval.**

What happened: Claude classified a migration changeset as coherent even though it carried no rollback artifact or operation.

Why it failed: The general missing-evidence rule did not make an empty rollback story an explicit terminal boundary, so semantic cohesion overshadowed reversibility.

How to avoid: Record the review unit `incomplete` with `missing-rollback-evidence` before considering approval, so the run finishes `rejected`.

**Failure 2: Unresolved scope was forced into a verdict.**

What happened: Claude was instructed to return an undecided verdict for an unresolved scope while the verdict still required full base and head commit identities.

Why it failed: Scope resolution failure occurs before an exact changeset exists, so a verdict would require fabricated identities.

How to avoid: Return `BLOCKED` with run token `not-started` and the resolver's diagnostic, and start a run only after both full commit identities resolve.

**Failure 3: Unavailable dependency evidence was treated as no dependency.**

What happened: Claude rejected two independently understandable clusters and ordered them as unrelated review units although nothing in the committed content established whether one depended on the other.

Why it failed: Claude collapsed "dependency evidence unavailable" into "dependency evidence establishes no relationships," producing a split without a defensible order.

How to avoid: Distinguish an established absence of dependency from unavailable evidence, and record `missing-dependency-evidence` on the unit whenever the unavailable evidence can change a multi-cluster classification or order.

**Failure 4: A generated artifact was attached by proximity.**

What happened: Claude attached one generated artifact to the only authored artifact and approved the changeset although no repository relationship established that producer.

Why it failed: Artifact count and nearby paths were treated as provenance, inventing the relationship the audit was required to verify.

How to avoid: Require a repository-declared generated-source relationship and record `missing-generated-source-evidence` when attribution cannot be established.

</failure_modes>

<success_criteria>

- Every changed authored artifact belongs to exactly one cluster and every generated artifact shares the cluster of its established producer, so none is counted twice or omitted.
- Every recorded finding names one catalog identifier and sits on the unit its catalog row names, and every `incomplete` unit carries its cause.
- Every `split-required` finding carries a review-unit sequence that covers every cluster exactly once and references only earlier review units.
- No size measurement acts as a verdict rule, and the terminal status follows semantic cohesion, verification unity, rollback unity, and independent mergeability.
- The checkout the audit judged is the checkout it started on and left, so the verdict describes one head.
- The same committed scope and repository evidence yield the same cluster identities, ordering, unit keys, and terminal status.

</success_criteria>

<reference_guides>

- `${CLAUDE_SKILL_DIR}/references/coherence-model.md` — artifact roles, semantic clusters, review units, evidence classes, and the rule catalog.
- `${CLAUDE_SKILL_DIR}/references/run-recording.md` — unit identities, payload schemas, and payload-file rules for the run.

</reference_guides>
