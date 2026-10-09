---
name: audit-changeset-coherence
description: >-
  Changeset-coherence audit methodology — judges whether an exact committed
  changeset forms one coherent review unit, covering semantic clustering,
  generated-source attribution, evidence completeness, and dependency-ordered
  review-unit sequencing, and records the judgment through an SPX
  changeset-scoped verification run.
argument-hint: "<JSON object with target, runDriver, agentOwningPluginVersion, and optional evidence>"
allowed-tools: Read, Grep, Glob, Bash(python3 "${SKILL_DIR}/scripts/resolve_scope.py":*), Bash(git rev-parse:*), Bash(git diff:*), Bash(git show:*), Bash(git ls-tree:*), Bash(spx --version), Bash(spx verification run start:*), Bash(spx verification run status:*), Bash(spx verification run scope add:*), Bash(spx verification run finding add:*), Bash(spx verification run finish:*), Bash(spx verification run render:*), Bash(printf '%s\n':*)
---

<objective>

A sealed `spx verification run` on one exact committed changeset — terminal status `approved` when its authored artifacts form one review unit whose evidence is complete, or `rejected` with one `review-unit` child per semantic cluster, every unit whose evidence cannot be established recorded `incomplete`, and each finding naming the rule, its location, and the evidence — or a `BLOCKED` diagnostic naming the failed prerequisite or command.

</objective>

<constraints>

- Read-only on the subject: NEVER edit files, commits, branches, reviews, or pull requests, and NEVER commit, stash, rebase, or move the checkout. The audit's only state is its own SPX verification-run journal. The Step 2 resolver's fetch refreshes the remote-tracking base ref so the scope reads the current base and can refuse a stale head; it touches no working-tree file, local branch, or `HEAD`.
- NEVER run tests, evals, validation, linters, or any other deterministic verification inside the audit — coherence is judged by reading the committed changeset.
- ALWAYS read every subject and context file at the resolved `<head>` through `git show` or `git diff`, never from the working tree, so the judgment reads the committed changeset whatever the checkout holds.
- MUST preserve the resolved full base and head commit identities verbatim in the run's changeset scope and the root unit's subject.
- MUST account for every changed path exactly once; collapse each generated artifact onto its producing authored artifact before judging breadth.
- NEVER use line count, file count, path breadth, or an uncalibrated review-load score as a verdict rule.
- NEVER infer missing behavioral, dependency, generated-source, verification, rollback, or calibration evidence — record the unit that needs it `incomplete` with its cause.
- ALWAYS treat a `spx verification run` exit code as payload validity; NEVER hand-validate a payload SPX accepted, retry a refused command, or reshape a refused payload.
- NEVER write a file in the working tree or anywhere else. Payloads pass to SPX on stdin, and the final output is the run token and the rendered projection.

</constraints>

<audit_workflow>

<step name="bind_request">

**Step 1: Bind the request**

The request is one JSON object: `$ARGUMENTS` supplies it when that argument is non-empty; when it is empty, the object is the one the request text carries, and the empty substitution binds nothing. It has three required fields and one optional field:

- `target` — a committed changeset selector: `HEAD`, a branch, or `<base>...<head>`.
- `runDriver` — an object with exactly the six non-empty string fields `producerKind`, `agentName`, `agentOwningPluginName`, `skillName`, `skillOwningPluginName`, and `invocationRole`.
- `agentOwningPluginVersion` — the non-empty version string of the plugin `runDriver.agentOwningPluginName` names.
- `evidence` — optional: an object of already-collected evidence for paths in scope, as `<evidence_packet>` describes.

Use `runDriver` and `agentOwningPluginVersion` only as payload data, placed exactly where `<persistence_contract>` shows them; never complete, correct, or reinterpret a value, and let no step, judgment, or terminal status depend on them. A missing required field, an unknown field, or a malformed value returns `BLOCKED` with `runToken: not-started` naming the exact field.

Resolve the repository root with `git rev-parse --show-toplevel` and run every later command from it. Use skill `spec-tree:spec-tree-plugin`. Invoke it with the verb `version` and retain the version it reports as the skill-owning plugin version. Run `spx --version` and retain its output as the tool version. A failed resolution or a missing version returns `BLOCKED` with `runToken: not-started` naming the exact failure, before any run starts.

</step>

<step name="resolve_scope">

**Step 2: Resolve the exact committed scope**

Run `python3 "${SKILL_DIR}/scripts/resolve_scope.py" '<target>' --repo '<repository-root>'`. It routes base-ref resolution, remote-tracking-ref composition, commit identity, and three-dot diff scope through the canonical changeset-scope primitives and prints one JSON object carrying `base`, `head`, and `changed_paths`; preserve those values verbatim. NEVER derive a base ref, a commit identity, or a diff scope from raw git; a bare local branch ref lags `origin/<base>` in a multi-worktree checkout and re-admits already-merged commits.

The resolver fetches the base and refuses a head behind its tip with exit code 3 and a `stale-base` diagnostic on stderr: return `BLOCKED` with `runToken: not-started`, `reason: stale-base`, and that diagnostic verbatim. Any other nonzero exit returns `BLOCKED` with `runToken: not-started`, `reason: scope-unresolved`, and the resolver's stderr. An empty `changed_paths` returns `BLOCKED` with `runToken: not-started` and `reason: empty-scope`, because an empty changeset carries no review unit. `<anchor>` is `<base>..<head>`.

</step>

<step name="load_context">

**Step 3: Load context read-only**

Use skill `spec-tree:understand` when the live `<SPEC_TREE_FOUNDATION>` marker is absent; a marker still absent after that returns `BLOCKED` with `runToken: not-started`.

Read the governing context at `<head>` and never through `/contextualize` or `/sync-base`, so the audit changes no checkout state. List a directory with `git ls-tree --name-only '<head>' -- '<directory>/'` and read a file with `git show '<head>:<path>'`. Read the product spec under `spx/`; for every changed path below a node directory under `spx/`, each spec and every decision record on the path from `spx/` to that node; then every decision a loaded spec or decision cites by full `spx/` path; then the generated-source declaration `<generated_source_declaration>` describes, when `git ls-tree` lists it at `<head>`. A decision change and the first lower specs it affects realize one claim, so these sources decide which clusters are inseparable. A spec missing on a loaded path, or a cited decision that does not exist, returns `BLOCKED` with `runToken: not-started` naming the missing file and, for a citation, the citing file.

</step>

<step name="open_run">

**Step 4: Open the run**

Pass the resolver's object — `base`, `head`, and `changed_paths` exactly as resolved — as the run input on stdin, in the transport form `<persistence_contract>` selects:

```bash
spx verification run start --verification-type audit --scope-type changeset --scope '<anchor>' --input stdin <<'SCOPE_INPUT'
<resolver-object-on-one-line>
SCOPE_INPUT
```

Capture the exact `runToken` and use it for every later command. Steps 5 through 7 record each unit and its findings as soon as that unit is judged, so the run shows each result before the next judgment begins.

</step>

<step name="classify_changeset">

**Step 5: Classify the changeset and record the root**

1. Enumerate every changed path from the run input and classify its role: decision or specification, test or eval evidence, implementation, generated artifact, workflow or configuration, documentation, migration, deployment, or release. A packet artifact's `role` sets its role verbatim, and `generated` marks a generated artifact; otherwise a path the declaration classifies as generated is generated and every other path is authored. Read each changed artifact with `git diff '<base>...<head>' -- '<path>'` and `git show '<head>:<path>'`.
2. Resolve every generated artifact to its producer through its packet `generated_from` path or the declaration rule in `<generated_source_declaration>`. `role: generated` classifies the artifact kind only and never establishes provenance. NEVER infer a producer from path similarity, artifact count, or the presence of only one authored artifact. A generated artifact neither source attributes, and every generated artifact when the packet's `generated_relationship_evidence.status` is `missing`, is a `missing-generated-source-evidence` cause on its artifact unit.
3. Take each authored artifact's behavioral claims from the packet as `<evidence_packet>` states when the request carries one; otherwise extract them from the changed declarations and the observable implementation and evidence. Commit messages are supporting evidence only and never override changed artifacts. An authored artifact whose claim cannot be established is a `missing-behavioral-claim-evidence` cause on its artifact unit and joins no cluster.
4. Build the smallest semantic clusters whose authored artifacts realize one claim, and place each attributed generated artifact in its producer's cluster. Collapse dependency cycles, and clusters that cannot be verified or rolled back separately, into one inseparable cluster. Every cluster surviving the collapse is independently mergeable. A cluster's outcome is its claim, verbatim; a collapsed cluster's outcome is its claims sorted lexicographically and joined by a semicolon and one space. When no cluster forms, that is a `no-review-unit` cause on the root: no authored artifact in scope realizes an established claim.
5. With two or more clusters, establish the dependency edges between them. When the request carries a packet, its `dependencies` is the only dependency evidence: each entry `{"from_claim": A, "to_claim": B}` states that the cluster whose outcome contains claim A depends on, and merges after, the cluster whose outcome contains claim B; an explicit empty array establishes that no dependency exists, and an absent key or a `null` value is a `missing-dependency-evidence` cause on the root. When the request carries no packet, a cluster depends on another exactly when one of its authored artifacts at `<head>` imports, links, invokes, or cites by path an artifact the other cluster holds. An edge naming a claim no cluster realizes is a `missing-dependency-evidence` cause on the root. Order the clusters topologically, breaking ties by the lexicographically first authored path, and number them `cluster-1`, `cluster-2`, and so on in that order.
6. Take the review-load signals from the packet's `review_load.signals` object, one signal per key with its value, and the baseline from `review_load.repository_baseline_available`. Without a packet `review_load`, there is no signal and the baseline is `false`. A signal never decides a cluster, an edge, or the terminal status, with one exception: a signal whose value is an object carrying `requires_calibration: true`, while the baseline is `false`, is a `missing-calibration-evidence` cause on the root naming that signal.

Record the root unit — `incomplete` when item 4, item 5, or item 6 of this step raised a root cause, `audited` otherwise — then each root cause as a finding, then one review-load unit per signal and one for the baseline.

</step>

<step name="record_clusters">

**Step 6: Judge and record each cluster**

For each cluster in order, establish its verification story — the evidence that verifies its claim — and its rollback story — the artifacts or operations that reverse it. When the request carries a packet, the packet is the only story evidence: the verification story is the `artifacts` of every `verification_evidence` entry whose `claim` the cluster's outcome contains, plus the path of every packet artifact whose `verifies` lists such a claim, and the rollback story is the `artifacts` of every matching `rollback_evidence` entry, so a packet that omits either key leaves that story empty. When the request carries no packet, read from the changeset at `<head>`: the verification story is every `[test]`, `[eval]`, or `[probe]` evidence path a loaded spec links from an assertion stating the claim, and the rollback story is the cluster's authored paths plus every migration, deployment, or release operation the changeset names for reversing them. A story entry is one repository-relative path verbatim or, for a rollback operation no artifact carries, the operation string verbatim; each story lists its entries deduplicated and sorted lexicographically. An empty verification story is a `missing-verification-evidence` cause, and an empty rollback story a `missing-rollback-evidence` cause, each on the cluster's review unit.

Record the cluster's `review-unit` unit — `incomplete` when it carries a cause, `audited` otherwise — then each of its causes as a finding, then one artifact unit per authored artifact and generated artifact in the cluster, then one story unit per verification-story entry and per rollback-story entry.

</step>

<step name="record_unclustered">

**Step 7: Record unclustered artifacts and the split**

Record one artifact unit under the root for every changed path no cluster holds — `incomplete` with its cause as a finding when Step 5 item 2 or item 3 raised one on it, `audited` when it is an attributed generated artifact whose producer no cluster holds, because that producer is unclustered or lies outside the changeset.

When two or more clusters exist and no unit is `incomplete`, record one `split-required` finding on the root whose evidence carries the cluster detail and the dependency-ordered review-unit sequence `<persistence_contract>` defines. When any unit is `incomplete`, record no `split-required` finding: the missing evidence can change cluster membership, order, or mergeability, so no sequence is defensible.

</step>

<step name="reconcile_and_finish">

**Step 8: Reconcile**

Read `spx verification run status` with the same type, scope, and token. Require exactly one root unit, one review-load unit per signal plus the baseline unit, one `review-unit` unit per cluster, one artifact unit per changed path, one story unit per story entry, and an accepted unit for every finding; record any missing unit or finding and read the status again.

**Step 9: Finish and render**

Derive `approved` only when exactly one `review-unit` unit exists, every unit is `audited`, and no finding exists; derive `rejected` otherwise. Run `spx verification run finish` with the same type, scope, and token and `--terminal-status '<approved-or-rejected>'`, then `spx verification run render` with the same type, scope, and token, and return the token and the rendered projection unchanged. The terminal status is the audit's publication-authorization judgment: `approved` finds the changeset publishable as one review unit, and `rejected` finds that it is not.

</step>

<evidence_packet>

The optional `evidence` object carries already-collected evidence:

| Key                                      | Shape                                                                                                                                   |
| ---------------------------------------- | --------------------------------------------------------------------------------------------------------------------------------------- |
| `artifacts`                              | array of `{path, role, claims, verifies, generated_from}`: `claims` and `verifies` are arrays of claim strings, `generated_from` a path |
| `verification_evidence`                  | array of `{claim, artifacts}`, `artifacts` an array of paths                                                                            |
| `rollback_evidence`                      | array of `{claim, artifacts}`, `artifacts` an array of paths or operation strings                                                       |
| `dependencies`                           | array of `{from_claim, to_claim}`, or `null` for unavailable dependency evidence                                                        |
| `generated_relationship_evidence.status` | `missing` when the generated-source relationships could not be collected                                                                |
| `review_load`                            | `{repository_baseline_available, signals}`: a boolean, and an object mapping each signal name to a scalar or an object value            |

When the request carries a packet, an authored artifact's claims come from its packet `claims` alone, so an authored artifact the packet does not list, or lists without `claims`, has no established claim. The resolved scope from Step 2 is authoritative for `base`, `head`, and the changed paths: a packet `scope` is ignored, and a packet entry naming a path outside that scope carries no evidence for this run. Preserve packet claims, paths, evidence paths, dependencies, and review-load signals verbatim, sorting claim and path arrays lexicographically.

</evidence_packet>

<generated_source_declaration>

A repository declares its generated artifacts in `spx/local/generated-sources.toml`, a TOML file of `[[relation]]` tables. Each relation carries `outputs`, `sources`, and `generator`: `sources` and `generator` are arrays of path globs, and each `outputs` entry is either a path glob naming whole generated files or a table `{file, begin, end}` naming a generated region of an authored file, spanning each line that starts with `begin` through the next line that starts with `end`, inclusive.

- A changed path matching a whole-file output glob is generated. A changed path holding a declared region is generated only when every changed hunk lies inside such a region, and authored otherwise.
- A generated path's producer is the relation's changed `sources` and `generator` paths in scope. When they all sit in one cluster, the generated path joins it. When they span clusters, it joins the cluster holding the changed source whose path, with the source glob's fixed prefix before its first wildcard replaced by the output glob's fixed prefix, equals the generated path; when no such single source exists, the generated path is unattributed. When no source or generator path is in scope, the producer lies outside the changeset.
- A repository without that file declares no relation, and only a packet `generated_from` path attributes a generated artifact.

</generated_source_declaration>

<persistence_contract>

Units record in the order Steps 5 through 7 state. Every unit carries `auditClass: changeset` and `coverageRequirement: required`, and every unit except the root carries `parentUnitId`.

| Unit        | `auditKind`   | `unitId`                                | Parent           | `subject`                      | `priorContext.concernPartition`          | `coverageStatus`          |
| ----------- | ------------- | --------------------------------------- | ---------------- | ------------------------------ | ---------------------------------------- | ------------------------- |
| Root        | `coherence`   | `coherence:root:<anchor>`               | —                | `<anchor>`                     | `coherence`                              | `audited` or `incomplete` |
| Review load | `coherence`   | `coherence:review-load:<signal>`        | root             | `<signal>=<value>`             | `review-load`                            | `audited`                 |
| Review unit | `review-unit` | `coherence:cluster-<n>:<anchor>`        | root             | the cluster's outcome          | `review-unit`                            | `audited` or `incomplete` |
| Artifact    | `coherence`   | `coherence:artifact:<path>`             | cluster, or root | `<path>`                       | `authored` or `generated`                | `audited` or `incomplete` |
| Story       | `coherence`   | `coherence:cluster-<n>:<story>:<entry>` | cluster          | the evidence path or operation | `verification-story` or `rollback-story` | `audited`                 |

The baseline unit is the review-load unit whose `<signal>` is `repository-baseline` and whose value is `true` or `false`. `<signal>` is a `review_load.signals` key and `<value>` its value written as JSON. `<story>` is `verification` or `rollback`, and `<entry>` is the story entry Step 6 defines, which is also the story unit's subject. `priorContext.changedFilePartition` is `<path>` for an artifact unit and `<anchor>` for every other unit. Every unit's expected producer has `producerKind: skill`, the `runDriver`'s `agentName` and `agentOwningPluginName`, `skillName: audit-changeset-coherence`, `skillOwningPluginName: spec-tree`, and `invocationRole: leaf-skill`. `recordedByRunDriver` carries the `runDriver` object unchanged. `producerProvenance` carries the request's `agentOwningPluginVersion`, the `spec-tree` version from Step 1 as `skillOwningPluginVersion`, and the exact `spx --version` output as `toolVersion`.

These objects are the sanctioned SPX audit payload schema for this auditor; SPX drops any field outside them, so use their fields exactly, never derive a replacement schema from command help, and never alter a refused payload by guesswork:

```json
{
  "unitId": "<unit-key>",
  "parentUnitId": "<parent-unit-key-for-a-non-root-unit-only>",
  "auditClass": "changeset",
  "auditKind": "<coherence-or-review-unit>",
  "subject": "<subject>",
  "coverageRequirement": "required",
  "coverageStatus": "<audited-or-incomplete>",
  "priorContext": {
    "changedFilePartition": "<path-or-anchor>",
    "concernPartition": "<concern-partition>"
  },
  "expectedProducer": {
    "producerKind": "skill",
    "agentName": "<supplied-agent-name>",
    "agentOwningPluginName": "<supplied-agent-owning-plugin>",
    "skillName": "audit-changeset-coherence",
    "skillOwningPluginName": "spec-tree",
    "invocationRole": "leaf-skill"
  },
  "recordedByRunDriver": "<the runDriver object, repeated exactly>",
  "producerProvenance": {
    "agentOwningPluginVersion": "<agent-owning-plugin-version>",
    "skillOwningPluginVersion": "<spec-tree-plugin-version>",
    "toolVersion": "<exact-spx-version>"
  }
}
```

A finding copies its unit's `expectedProducer` as `producerIdentity` and its unit's complete `producerProvenance`. Every finding is `blocking` and rejects the run. Each rule records against one unit:

| Rule                                | Unit        | `location`                        |
| ----------------------------------- | ----------- | --------------------------------- |
| `missing-dependency-evidence`       | root        | `<anchor>`                        |
| `missing-calibration-evidence`      | root        | `<anchor>`                        |
| `no-review-unit`                    | root        | `<anchor>`                        |
| `split-required`                    | root        | `<anchor>`                        |
| `missing-verification-evidence`     | review unit | the cluster's first authored path |
| `missing-rollback-evidence`         | review unit | the cluster's first authored path |
| `missing-behavioral-claim-evidence` | artifact    | `<path>`                          |
| `missing-generated-source-evidence` | artifact    | `<path>`                          |

`message` names the rule's subject and the missing or violated property. For every rule except `split-required`, `evidence.observed` states what the changeset carries and `evidence.expected` the evidence the judgment requires. A `split-required` finding's `evidence.observed` is one JSON text, encoded as a JSON string, of the cluster array — each cluster's `id`, `outcome`, `authored_artifacts`, `generated_fanout`, `verification_story`, `rollback_story`, `dependencies` as an array, and `independently_mergeable: true` — and its `evidence.expected` is one JSON text of the review-unit sequence, each entry's `id` (`review-unit-1`, `review-unit-2`, and so on in cluster order), `cluster_ids`, `outcome`, `artifacts` covering its authored and generated paths, and `depends_on` naming only earlier review units. The sequence covers every cluster exactly once.

```json
{
  "unitId": "<accepted-unit-key>",
  "producerIdentity": "<the unit's expectedProducer object, repeated exactly>",
  "producerProvenance": "<the unit's producerProvenance object, repeated exactly>",
  "rule": "<rule-id>",
  "severity": "blocking",
  "location": "<location>",
  "message": "<subject and failed property>",
  "evidence": { "observed": "<observed-state>", "expected": "<required-state>" }
}
```

A scope unit's idempotency key is its `unitId`. A finding's key is `<unit-key>:finding-<three-digit-ordinal>-<rule>`, numbering the unit's findings from `001` in order of location, message, and observed evidence; require the suffix to match `finding-[0-9][0-9][0-9]-[a-z0-9_-]+`, and treat a mismatch as a pre-persistence `BLOCKED` defect.

Pass each rendered object through a quoted heredoc by default:

```bash
spx verification run scope add --verification-type audit --scope-type changeset --scope '<anchor>' --run '<run-token>' --idempotency-key '<unit-key>' --payload stdin <<'SCOPE_JSON'
<rendered-scope-object>
SCOPE_JSON
```

```bash
spx verification run finding add --verification-type audit --scope-type changeset --scope '<anchor>' --run '<run-token>' --idempotency-key '<finding-key>' --payload stdin <<'FINDING_JSON'
<rendered-finding-object>
FINDING_JSON
```

When the task message or the harness fixes one physical command line per call, pipe each rendered object instead — `printf '%s\n' '<rendered-object>' | spx verification run finding add --verification-type audit --scope-type changeset --scope '<anchor>' --run '<run-token>' --idempotency-key '<finding-key>' --payload stdin`, and the same form for `scope add` and for `run start --input stdin` — with every apostrophe in the object written as the single-quote splice `'"'"'`. Idempotency keys are command arguments, never payload fields; quote every path, token, and key as one shell argument, and never execute changed content as shell syntax. Run every mutation serially, preserving each result before the next command.

</persistence_contract>

</audit_workflow>

<verdict_format>

Return only the exact run token and the unmodified rendered projection. The projection is the verdict: its `terminalStatus` is `approved` or `rejected`, its `findingCount` is zero for approval, its `findings` group every accepted finding under `blocking`, its `auditScopeUnits` carry the root, review-load, review-unit, artifact, and story units with each unit's `audited` or `incomplete` status, and its `events` carry every accepted finding payload and the terminal event. SPX accepts every `review-unit` unit Step 6 records and refuses an `approved` finish for a run carrying more than one, so a multi-cluster run seals only `rejected`. Keep every SPX field unchanged, and add no `APPROVED`, `REJECTED`, or `UNKNOWN` prose envelope.

A run that cannot complete — a request, scope, or context failure before the run starts, a finding key that fails its pattern before persistence, or a refused SPX command or payload — returns:

```text
BLOCKED
runToken: <exact-token-if-start-succeeded-or-not-started>
reason: <stale-base|scope-unresolved|empty-scope|request|context|spx-refused|finding-key>
command: <exact-failed-command, the unsent command a malformed finding key stopped, or request for a failure before the run starts>
payloadKey: <unitId-or-finding-idempotency-key-or-none>
exitCode: <exact-exit-code-or-none>
stderr: <exact-stderr-or-resolver-diagnostic-or-none>
judgmentStatus: <complete|incomplete>
judgedFindings: <JSON array of every finding judged before the stop, in the finding-payload shape>
```

</verdict_format>

<failure_modes>

**Failure 1: Missing rollback evidence received approval.**

What happened: Claude classified a migration packet as coherent even though the packet contained no rollback evidence.

Why it failed: The general missing-evidence rule did not make an empty rollback story an explicit terminal boundary, so semantic cohesion overshadowed reversibility.

How to avoid: Take a packet's stories from the packet alone, so a packet without rollback evidence leaves the rollback story empty, and record every cluster with an empty rollback story as an `incomplete` review unit carrying `missing-rollback-evidence`, so the run seals `rejected`.

**Failure 2: Unresolved scope was forced into the verdict.**

What happened: Claude was instructed to judge an unresolved scope while the verdict required full base and head commit identities.

Why it failed: Scope resolution failure occurs before an exact changeset exists, so a verdict would require fabricated identities.

How to avoid: Return `BLOCKED` with `runToken: not-started` for a scope failure, and start the run only after both full commit identities resolve.

**Failure 3: A null dependency set was treated as an empty set.**

What happened: Claude split two independently understandable clusters and ordered them as unrelated review units even though the evidence packet supplied `dependencies: null`.

Why it failed: Claude collapsed "dependency evidence unavailable" into "dependency evidence establishes no relationships", producing a split without a defensible order.

How to avoid: When the request carries a packet, distinguish an absent or `null` dependency set from an explicit empty array, record the root `incomplete` with `missing-dependency-evidence`, and record no `split-required` finding.

**Failure 4: A generated artifact was attached by proximity.**

What happened: Claude attached one generated artifact to the only authored artifact and approved the changeset even though no repository relationship or `generated_from` field established that producer.

Why it failed: Artifact count and nearby paths were treated as provenance, inventing the relationship the audit was required to verify.

How to avoid: Require a declared generated-source relationship or `generated_from` field, and record an unattributed generated artifact as an `incomplete` artifact unit carrying `missing-generated-source-evidence`.

</failure_modes>

<success_criteria>

The verdict is sound when:

- Every changed path carries exactly one artifact unit: under the review unit of the one cluster that holds it, or under the root when no cluster holds it, in which case the unit is `incomplete` with its cause or is an attributed generated artifact whose producer no cluster holds.
- Every `rejected` run carries at least one finding or `incomplete` unit naming why: a run with no cluster carries `no-review-unit` on the root.
- The terminal status follows semantic cohesion, verification unity, rollback unity, and independent mergeability, with no size threshold acting as a verdict rule; it is `approved` only with exactly one review unit, every unit `audited`, and no finding.
- Every evidence gap is an `incomplete` unit carrying a finding that names the missing evidence, and every split carries a `split-required` finding whose sequence covers every cluster exactly once in dependency order.
- The run's changeset scope and root subject carry the resolved base and head commit identities verbatim.
- The same committed scope, repository evidence, evidence packet, and run-driver identity yield the same units, cluster numbering, finding keys, and terminal status.

</success_criteria>
