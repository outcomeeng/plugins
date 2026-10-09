<!-- Generated from the complete producer at dist/codex/spec-tree/skills/audit-tests/SKILL.md. -->

The runner substitutes only the case's `input` object into `{input_json}`; grader expectations remain withheld from the producer. Apply the complete producer below to the supplied test-evidence package. The package's `language_composition` field is completed composition evidence governed by the producer's Step 3f input contract. Return only the producer's structured JSON verdict.

---
name: audit-tests
description: >-
  Test-evidence audit methodology — judges whether a spec node's tests, or a
  committed changeset's test evidence, provide behavior-coupled evidence their
  assertions are fulfilled, covering predicate ownership, source ownership,
  coupling, falsifiability, and full-chain coverage, and records the judgment
  through an SPX file- or changeset-scoped verification run.
argument-hint: "<JSON object with target, runDriver, and agentOwningPluginVersion>"
allowed-tools: Read, Grep, Glob, Bash(git rev-parse:*), Bash(git status --porcelain:*), Bash(realpath:*), Bash(spx --version), Bash(spx verification run start:*), Bash(spx verification run input:*), Bash(spx verification run status:*), Bash(spx verification run scope add:*), Bash(spx verification run finding add:*), Bash(spx verification run finish:*), Bash(spx verification run render:*), Bash(printf '%s\n':*)
---

<objective>

A sealed `spx verification run` on one spec node's `[test]` evidence or one committed changeset's test evidence — terminal status `approved` with no finding, or `rejected` with each finding naming the assertion or evidence artifact, the failed evidence property, the evidence, and the ownership target the remediation belongs to — or a `BLOCKED` diagnostic naming the failed prerequisite or command.

</objective>

<constraints>

- NEVER modify the tests under audit or any other file, and NEVER commit, stash, synchronize, rebase, create a branch, or move the checkout. The audit's own SPX verification-run journal is the only state it writes.
- NEVER run the project's coverage command, test command, linter, type-checker, or any other deterministic verification — the Author's agent session passes it on the changeset before dispatch, and CI re-runs it over the whole repository. Every Bash grant names an identity, path, worktree-status, or run-journal verb; none runs project verification, and no grant is added for parity with a composed skill.
- ALWAYS judge a node target's assertions from the spec content `spx verification run input` replays from the run, never from a separate read of the live spec. Step 9 compares the live spec with the retained input before the run finishes.
- ALWAYS complete the evidence-chain inventory of an assertion before recording its unit. An unresolved import, unread artifact, or unclassified role is an `incomplete-evidence-chain` finding; absence of an artifact is missing evidence, never permission to infer its contents.
- ALWAYS name the assertion or evidence artifact, the failed property, the evidence, and the remediation target in every finding.
- NEVER record a finding the evidence model does not support — drop an unbacked finding rather than reject the tests for it.
- ALWAYS treat a `spx verification run` exit code as payload validity; NEVER hand-validate a payload SPX accepted, retry a refused command, or reshape a refused payload.
- NEVER write a file. Payloads pass to SPX on stdin, and the final output is the run token and the rendered projection.

</constraints>

<essential_principles>

**PREDICATE AND OWNERSHIP SCREEN, THEN COUPLING.**

The linked test function or callback owns every predicate and assertion API call. Screen the full chain for verdict logic and classify each test-file binding by semantic choice before checking imports. A test that imports nothing from the codebase passes forever regardless of what any file contains.

**COMPLETE THE EVIDENCE CHAIN.**

Start from every linked test and recursively follow repository imports through test infrastructure before judging evidence. Four properties then hold in strict order: coupling (the test exercises codebase behavior, not authored prose), falsifiability (a named mutation breaks it), alignment (it exercises the asserted behavior), and coverage (it drives execution into the assertion-relevant path). A test missing any property has zero evidentiary value regardless of code quality.

**JUDGE COVERAGE BY READING.**

Establish coverage from a source trace into the assertion-relevant code path, never from a measured percentage.

**NO MECHANICAL SUBSTITUTES.**

Mocking patterns, skip patterns, and type annotations are linting concerns. The declaration screen is a read step: identify declarations in the test file, then judge ownership from their evidence role. Apply the literal rule by reading the test's literals against their sources.

**TEST FILES OWN PREDICATES AND NO INDEPENDENT DATA OR CONFIGURATION.**

Reject a harness, generator, fixture, controlled implementation, or recording collaborator that accepts an expected outcome, returns a verdict, calls an assertion API, or exposes matcher-shaped verdict methods. Classify bindings by what they choose: observation aliases, actual-result bindings, imported source-contract aliases, generated parameters, callback inputs, and resource handles are valid when they introduce no data or policy. NEVER reject a binding merely because it is a parameter, assignment, alias, or local expression. Reject bindings that choose cases, expectations, runner settings, property configuration, setup policy, reusable data, generator domains, fixture payloads, or verdict rules, and name the owner: source contract, spec-governed harness, spec-governed generator, inert whole-payload fixture, independent oracle, or curated eval case data.

</essential_principles>

<audit_workflow>

<step name="bind_request">

**Step 1: Bind the request**

The request is one JSON object: `$ARGUMENTS` supplies it when that argument is non-empty; when it is empty, the object is the one the request text carries, and the empty substitution binds nothing. It has exactly three fields:

- `target` — a spec node directory or its spec file, repository-relative, or a committed changeset selector: `HEAD`, a branch, or `base...head`.
- `runDriver` — an object with exactly the six non-empty string fields `producerKind`, `agentName`, `agentOwningPluginName`, `skillName`, `skillOwningPluginName`, and `invocationRole`.
- `agentOwningPluginVersion` — the non-empty version string of the plugin `runDriver.agentOwningPluginName` names.

Use `runDriver` and `agentOwningPluginVersion` only as payload data, placed exactly where `<persistence_contract>` shows them; never complete, correct, or reinterpret a value, and let no step, judgment, or terminal status depend on them. A missing, extra, or malformed field returns `BLOCKED` with `runToken: not-started` naming the exact field.

Resolve the repository root with `git rev-parse --show-toplevel` and run `realpath` separately on the root and on `target`. The target is a **node target** when it resolves beneath the root, by path-component boundary, to a directory below `spx/` whose name carries a node-kind suffix, or to the spec file directly inside such a directory; its spec, `<spec-path>`, is the directory's `{slug}.spec.md`, or the prior `{slug}.md` a 3.x-authored tree carries, as a normalized repository-relative path. A target directly under `spx/` is the product spec, which carries no `[test]` assertion: return `BLOCKED` with `runToken: not-started` naming `unsupported-target`. Every other target is a **changeset target**, passed unchanged as a selector to Step 3.

Use skill `spec-tree:spec-tree-plugin`. Invoke it with the verb `version` and retain the version it reports as the skill-owning plugin version. Run `spx --version` and retain its output as the tool version. A failed resolution, a node directory without its spec, or a missing version returns `BLOCKED` with `runToken: not-started` naming the exact failure, before any run starts.

</step>

<step name="load_standards">

**Step 2: Load the shared test-evidence standards**

Use skill `spec-tree:test-evidence-standards`. Apply its complete predicate-seam, semantic-binding, case-provenance, oracle-independence, assertion-type-litmus, mutation-litmus, and assertion-design-record rules. When it cannot load, return `BLOCKED` with `runToken: not-started` naming `test-standards-unavailable`, because `/test` and this audit judge from the same standards.

</step>

<step name="load_context">

**Step 3: Resolve the scope and load context**

Use skill `spec-tree:understand` when the live `<SPEC_TREE_FOUNDATION>` marker is absent; a marker still absent after that returns `BLOCKED` with `runToken: not-started`.

For a changeset target, Use skill `spec-tree:scope-changeset` with the selector and consume its `<COMMITTED_CHANGESET_SCOPE>` marker: `<base>`, `<head>`, and the changed paths. A stale-base refusal returns `BLOCKED` with `runToken: not-started` naming `stale-base` and carrying the provider's diagnostic; any other provider failure returns `BLOCKED` with that diagnostic. Require `<head>` to equal `git rev-parse HEAD` and `git status --porcelain` to print nothing, so every live read below reads the committed subject; otherwise return `BLOCKED` with `runToken: not-started` naming `uncommitted-subject`. The governing node of a changed path is the node containing the `spx/**/tests/` file that is that path or that names it in its evidence chain; several governing nodes are judged together in one run.

Load each governing node's context read-only, never invoking `/contextualize` or `/sync-base`, so the audit changes no checkout state: the product spec, then each spec and every decision record on the path from `spx/` to the node, then every decision a loaded spec or decision cites by full `spx/` path. A node target's own spec is excluded from this read; Step 4 replays it from the run. A spec missing on that path, or a cited decision that does not exist, returns `BLOCKED` with `runToken: not-started` naming the missing file and, for a citation, the citing file.

</step>

<step name="open_run">

**Step 4: Open the run and record the root**

For a node target, from the repository root:

```bash
spx verification run start --verification-type audit --scope-type file --scope '<spec-path>' --input '<spec-path>'
```

Read the retained input with `spx verification run input --verification-type audit --scope-type file --scope '<spec-path>' --run '<run-token>'`; its `content` is the one copy of the node spec this audit judges.

For a changeset target, pass the provider's scope object — `base`, `head`, and `changed_paths` exactly as the marker carries them — as the run input on stdin, in the transport form `<persistence_contract>` selects:

```bash
spx verification run start --verification-type audit --scope-type changeset --scope '<base>..<head>' --input stdin <<'SCOPE_INPUT'
<scope-object-on-one-line>
SCOPE_INPUT
```

Capture the exact `runToken` and use it for every later command. Record the root unit under `<persistence_contract>`. Steps 5 through 7 record each assertion's unit and findings as soon as that assertion is judged, then its language units, so the run shows each result before the next assertion is judged.

</step>

<step name="map_assertions">

**Step 5: Map assertions and evidence paths**

Read each governing spec's `## Assertions` — the replayed content for a node target, the committed spec for a changeset target. Only assertions carrying `[test]` evidence enter this audit; `[eval]`, `[probe]`, and `[audit]` evidence belongs to other verification workflows. Number the `[test]` assertions of each spec from `001` in document order. For each, extract the assertion text, the assertion type, the linked test path, and whether the linked file exists.

A node target audits every `[test]` assertion of its spec. A changeset target audits each `[test]` assertion whose linked test is a changed path or whose evidence chain, inventoried in Step 6, reaches one. A changed test or test-infrastructure path that no current `[test]` assertion links and no current evidence chain reaches is a **retired path**: record it as a `not-applicable` retired unit naming the reason, and never demand restoration of evidence a current spec no longer claims. A current `[test]` link to a missing file is a `missing-test-file` finding on that assertion's unit.

</step>

<step name="full_chain_ownership">

**Step 6: Judge each assertion's evidence chain**

For each in-scope assertion, judge in this order, then record its assertion unit and every finding against it.

**Inventory.** Starting from the linked test, follow each repository import recursively and inventory every artifact by path, role (`test`, `harness`, `generator`, `fixture`, `discovery`, or `production`), importing artifact, and inspection status. Read every resolved artifact. A fixture consumed only by path is inventoried, and so is every applicable discovery or module-resolution artifact — `conftest.py` or pytest configuration, Vitest configuration, `Cargo.toml`, `go.mod` — even when it produces no finding. An import that cannot be resolved is an `incomplete-evidence-chain` finding located at the unresolved path, never at the thin test file; continue every check the available artifacts support, and report a property whose required evidence is unavailable as missing evidence rather than inferring it.

**Testability.** Read the governed production source and identify the observable boundary, seam, or injection point through which a test can exercise the assertion-relevant behavior. When the source exposes none, record `untestable-source` located at the source file with remediation target `source-file`, naming the missing seam. Continue the remaining checks; the testability failure stands regardless of their results.

**Ownership.** Before coupling, enumerate every variable, constant, local function, fixture parameter, property-generated parameter, predicate, and assertion API call in the linked test, and classify its owner by reading its evidence role, never by a grep pattern or validation command. Resolve anything that looks like case data through the `/test-evidence-standards` per-assertion-type litmus first: a case the litmus assigns to the test is correctly owned there, and demanding that it move into a production module is source laundering.

| Binding or predicate role                                                                                                                       | Verdict                                            |
| ----------------------------------------------------------------------------------------------------------------------------------------------- | -------------------------------------------------- |
| Actual result, observation, resource handle, generated parameter, callback input, or imported-contract alias that introduces no choice          | Accept — assertion flow                            |
| Behavioral predicate or assertion API call in the linked test function or callback                                                              | Accept — test-owned predicate                      |
| Predicate, matcher, expected-value parameter, assertion call, or verdict helper in infrastructure                                               | `assertion-seam`, target `test-file`               |
| Runner settings, seed policy, retries, setup policy, or lifecycle policy                                                                        | `test-owned-configuration`                         |
| Test-invented case data, boundary bags, expected outputs, fixture contents, or generator domains the assertion type does not assign to the test | `test-owned-data`                                  |
| Source-owned singleton shape or vocabulary copied into the test                                                                                 | `source-ownership`, target `source-contract`       |
| Expected result derived from the production table, algorithm, parser, or branch logic that produces the actual result                           | `oracle-independence`, target `independent-oracle` |

Casing and syntax are never evidence: renaming `MAPPING_RUNS` to `mappingRuns` or receiving a value through a parameter does not change what the binding chooses. A property test whose imported harness or wrapper owns no seed policy and reports no seed or replay path on failure is `missing-property-seed-reporting`.

Apply the category checks to every imported test-infrastructure artifact; a value outside its category's allowed ownership is `source-ownership`:

| Artifact role | Allowed ownership                                                                      | `source-ownership` when it owns                                                                          |
| ------------- | -------------------------------------------------------------------------------------- | -------------------------------------------------------------------------------------------------------- |
| Harness       | Setup, teardown, cleanup, resource policy, access to real behavior, replay diagnostics | Protocol keys, command tokens, status values, expected outputs, arbitrary request payloads, domain truth |
| Generator     | Variable domains with meaningful variation and shrinking                               | Copied protocol vocabulary, constant-only domains, hand-picked expected outputs                          |
| Fixture       | Inert whole payload consumed by path or bytes                                          | Isolated tokens, values, expected outputs, executable exports                                            |
| Discovery     | Test collection and registration policy                                                | Fixture bodies, domain values, generated cases, hidden setup policy                                      |

Judge a source symbol the test cites by declared-contract ownership: does production consume, emit, publish, register, or serialize it against a declared schema? An absent in-repository caller opens that question rather than settling it, so inspect the declared surfaces the checkout carries — packaging entry points and export declarations, plugin and protocol implementations, registry and reflective lookups, generated use, and declared schemas — before reporting the symbol as laundered, and name the surfaces inspected. Report it when none requires the symbol; a consumer outside the checkout is not evidence this audit can gather. Every `source-ownership` finding locates the artifact that copied the value and names `source-contract` as its target, even when the copy sits in a harness, generator, fixture, or discovery file. Judge the `/test-evidence-standards` `<assertion_design_record>` as one unit through the steps that own its fields: assertion mapping in Step 5, production subject in testability, case provenance in `source-ownership`, oracle owner in `oracle-independence`, and the rejected mutation with its failure observation in falsifiability.

**Coupling.** Classify each import of the linked test: a test framework or a third-party library does not count; a codebase path counts. Zero codebase imports is `no-coupling`. Otherwise classify:

| Category           | Definition                                                                                        | Rule                                           |
| ------------------ | ------------------------------------------------------------------------------------------------- | ---------------------------------------------- |
| Direct             | Imports the module under test                                                                     | Proceed                                        |
| Indirect           | Imports a harness wrapping the module                                                             | Proceed — verify the harness has real coupling |
| Transitive         | Imports a consumer of the module                                                                  | Proceed — verify the test level matches        |
| Laundered indirect | Imports a test-infrastructure module that exists only to expose hardcoded values back to the test | `laundered-coupling`                           |
| False              | Imports the module but never calls assertion-relevant functions                                   | `false-coupling`                               |
| Partial            | Calls functions on wrong inputs or wrong code paths                                               | `partial-coupling`                             |
| Severed            | Imports the module and replaces its behavior with a mock, fake, stub, or monkeypatch              | `severed-coupling`                             |
| Prose-coupling     | Reads an authored prose or documentation body and asserts its content                             | `prose-coupling`                               |

Coupling means exercising executable behavior. A test that reads a skill body, spec body, prompt, or any other authored text and asserts its substrings is `prose-coupling`, directly or through a harness constant or reader function: its verification type belongs in `[eval]` or `[audit]`. Reading an authored source-code file for a structural lint that exercises a rule is not prose-coupling.

**Falsifiability.** For each codebase import, write down a concrete mutation to the imported module that would make this test fail, as `Module`, `Mutation`, and `Impact`. No nameable mutation is `unfalsifiable`. A test double is legitimate only under one of the seven `/test` Stage 5 exception cases with its matching double: failure simulation (stub returning errors), interaction protocols (spy recording calls), time and concurrency (fake clock), safety (stub that records), combinatorial cost (configurable fake), observability (spy recording details), contract probes (contract stub).

**Alignment.** Answer whether the test exercises the exact behavior the assertion describes, and whether the assertion could be unfulfilled while the test passes; the second answering yes is `misaligned`. Judge the test against the executable source contract: when production exports and uses a contract the test imports while exercising the behavior, a change to that contract is intentional behavior change, so name a mutation to the consuming behavior. NEVER require a test to parse spec or decision Markdown or copy a literal from that prose as its oracle. The test strategy must fit the assertion type — scenario example-based with concrete Given/When/Then inputs, mapping parameterized over the input set, property through a property-based framework, conformance through a tool or schema, compliance against violating cases — and a mismatch is `strategy-mismatch`.

**Coverage.** Read the production code the assertion governs and identify the assertion-relevant functions, branches, and lines; follow what the test calls into it; judge whether execution reaches those lines. A test that never reaches them is `no-coverage`, naming the unreached path traced from the code. A trivially total path the test obviously reaches is covered; its value comes from the other three properties.

</step>

<step name="compose_language">

**Step 7: Compose the language-specific test-evidence concerns**

Language-specific concerns are owned by the installed `audit-<lang>-tests` skills. Derive one partition per linked test path: take the installed `audit-<lang>-tests` skills from the skill listing in context, load each language's `<lang>-test-standards`, and read its filename instantiation of `<subject>.<evidence>.<level>[.<runner>]`; the text after the last closing bracket is the declared suffix, whether `.test.ts`, `.py`, or `_test.go`. Map every linked test whose filename ends in an installed plugin's declared suffix to that language, never from an extension list this skill carries. A suffix no installed plugin declares, or an ambiguous partition, is an `unsupported` language unit carrying the `unsupported-language` finding with target `language-partition`.

For each partition, Use skill `{lang}:audit-{lang}-tests` and pass the governing node path and that partition's linked test paths, adding retired paths of that language for a changeset target. When the skill is not installed, record each of that language's units as `missing-skill`, which rejects the run without a finding. Validate each returned result against the composed concern contract in `<verdict_format>` — row names, required finding fields, allowed statuses, and agreement between findings, row statuses, and the overall value — and accept no partial rows from a result that fails it: record `language-result-invalid` naming the failed check.

From a validated result, record one language unit per linked test path of that partition, then each finding: a `REJECT` finding as `blocking`, a `WARNING` as `debt`, and no `INFO` observation. A Gate 1 or Gate 2 finding records on the unit whose test path its `file` names, or on the partition's first language unit when its `file` names a shared artifact. A `NOT_APPLICABLE` result records each reported subject as a retired unit carrying the result's explanation. Language concerns reach the run only through the installed skill; never read a language plugin's `SKILL.md` from the checkout in its place.

</step>

<step name="reconcile_and_finish">

**Step 8: Reconcile**

Read `spx verification run status` with the same type, scope, and token. Require exactly one root unit, one unit per in-scope assertion, one language unit per linked test path and language, one retired unit per retired path, and an accepted unit for every finding; record any missing unit or finding and read the status again.

**Step 9: Finish and render**

For a node target, re-read the live spec and compare it with the retained input; a changed or missing file returns `BLOCKED` with the run preserved. For a changeset target, require `git rev-parse HEAD` to still equal `<head>`; a moved head returns `BLOCKED` with the run preserved.

Derive `approved` only when every unit is `audited` or `not-applicable` and no finding exists; derive `rejected` when any finding exists or any unit is `missing-skill` or `unsupported`. Then run `spx verification run finish` with the same type, scope, and token and `--terminal-status '<approved-or-rejected>'`, then `spx verification run render` with the same type, scope, and token, and return the token and the rendered projection unchanged.

</step>

<persistence_contract>

Units record in this order: the root, then for each assertion its assertion unit followed by its language units, with retired units after the assertion units of their governing node. `<anchor>` is `<spec-path>` for a node target and `<base>..<head>` for a changeset target. Every unit carries `auditClass: implementation`, `auditKind: tests`, `coverageRequirement: required`, and `parentUnitId` equal to its parent's `unitId` on every unit except the root, which omits it.

| Unit      | `unitId`                                               | Parent    | `subject`     | `priorContext.concernPartition` | `coverageStatus`                          | `skillName`, `skillOwningPluginName` of `expectedProducer`                                                                       |
| --------- | ------------------------------------------------------ | --------- | ------------- | ------------------------------- | ----------------------------------------- | -------------------------------------------------------------------------------------------------------------------------------- |
| Root      | `tests:root:<anchor>`                                  | —         | `<anchor>`    | `tests`                         | `audited`                                 | `audit-tests`, `spec-tree`                                                                                                       |
| Assertion | `tests:assertion-<NNN>:<spec-path>`                    | root      | `<spec-path>` | `assertion`                     | `audited`                                 | `audit-tests`, `spec-tree`                                                                                                       |
| Language  | `tests:assertion-<NNN>:<spec-path>:<lang>:<test-path>` | assertion | `<test-path>` | `language`                      | `audited`, `missing-skill`, `unsupported` | `audit-<lang>-tests`, `<lang>` when a validated result is consumed or the skill is missing; `audit-tests`, `spec-tree` otherwise |
| Retired   | `tests:retired:<path>`                                 | root      | `<path>`      | `retired`                       | `not-applicable`                          | `audit-<lang>-tests`, `<lang>` when a language result reported it; `audit-tests`, `spec-tree` otherwise                          |

`priorContext.changedFilePartition` is the unit's `subject`; a language unit adds `priorContext.languagePartition: <lang>`, and an `unsupported` unit uses `unknown`. The expected producer has `producerKind: skill`, the `runDriver`'s `agentName` and `agentOwningPluginName`, the skill named in the table, and `invocationRole: leaf-skill`. `recordedByRunDriver` carries the `runDriver` object unchanged. `producerProvenance` carries the request's `agentOwningPluginVersion`, the version of the plugin owning the unit's producer skill as `skillOwningPluginVersion`, and the exact `spx --version` output as `toolVersion`; a `missing-skill` unit omits it because no skill executed. That version is the `spec-tree` version from Step 1 for an `audit-tests` unit; for a language skill, Use skill `{lang}:{lang}-plugin` with the verb `version`, and a version that cannot be read is a `language-result-invalid` finding recorded with `audit-tests` as producer.

These objects are the sanctioned SPX audit payload schema for this auditor; use their fields exactly, never derive a replacement schema from command help, and never alter a refused payload by guesswork:

```json
{
  "unitId": "<unit-key>",
  "parentUnitId": "<parent-unit-key-for-a-non-root-unit-only>",
  "auditClass": "implementation",
  "auditKind": "tests",
  "subject": "<subject>",
  "coverageRequirement": "required",
  "coverageStatus": "<status>",
  "priorContext": {
    "changedFilePartition": "<subject>",
    "languagePartition": "<lang-for-a-language-unit-only>",
    "concernPartition": "<tests|assertion|language|retired>"
  },
  "expectedProducer": {
    "producerKind": "skill",
    "agentName": "<supplied-agent-name>",
    "agentOwningPluginName": "<supplied-agent-owning-plugin>",
    "skillName": "<producing-skill>",
    "skillOwningPluginName": "<producing-skill-plugin>",
    "invocationRole": "leaf-skill"
  },
  "recordedByRunDriver": "<the runDriver object, repeated exactly>",
  "producerProvenance": {
    "agentOwningPluginVersion": "<agent-owning-plugin-version>",
    "skillOwningPluginVersion": "<producing-skill-plugin-version>",
    "toolVersion": "<exact-spx-version>"
  }
}
```

A finding copies its unit's `expectedProducer` as `producerIdentity` and its unit's complete `producerProvenance`. `location` names the artifact path and line, or quotes the assertion; `message` names the assertion and the failed property; `evidence.observed` states what the artifact does, and `evidence.expected` states the required state and ends with `remediation: <target>`, the target drawn from `source-contract`, `harness`, `generator`, `fixture`, `eval-case`, `test-file`, `source-file`, `test-infrastructure`, `independent-oracle`, `skill-installation`, or `language-partition`. A native finding is `blocking`; its `rule` is one named in Steps 5 through 7. A composed finding keeps the language skill's rule, its mapped severity, its file and line as `location`, and its message.

```json
{
  "unitId": "<accepted-unit-key>",
  "producerIdentity": "<the unit's expectedProducer object, repeated exactly>",
  "producerProvenance": "<the unit's producerProvenance object, repeated exactly>",
  "rule": "<violated-rule-id>",
  "severity": "<blocking-or-debt>",
  "location": "<artifact-path-and-line-or-quoted-assertion>",
  "message": "<assertion and failed property>",
  "evidence": { "observed": "<observed-state>", "expected": "<required-state>; remediation: <target>" }
}
```

A scope unit's idempotency key is its `unitId`. A finding's key is `<unit-key>:finding-<three-digit-ordinal>-<rule>`, numbering the unit's findings from `001` in order of location, message, severity, observed evidence, and expected evidence; require the suffix to match `finding-[0-9][0-9][0-9]-[a-z0-9_-]+`, and treat a mismatch as a pre-persistence `BLOCKED` defect.

Pass each rendered object through a quoted heredoc by default:

```bash
spx verification run scope add --verification-type audit --scope-type '<file-or-changeset>' --scope '<anchor>' --run '<run-token>' --idempotency-key '<unit-key>' --payload stdin <<'SCOPE_JSON'
<rendered-scope-object>
SCOPE_JSON
```

```bash
spx verification run finding add --verification-type audit --scope-type '<file-or-changeset>' --scope '<anchor>' --run '<run-token>' --idempotency-key '<finding-key>' --payload stdin <<'FINDING_JSON'
<rendered-finding-object>
FINDING_JSON
```

When the task message or the harness fixes one physical command line per call, pipe each rendered object instead — `printf '%s\n' '<rendered-object>' | spx verification run finding add --verification-type audit --scope-type '<file-or-changeset>' --scope '<anchor>' --run '<run-token>' --idempotency-key '<finding-key>' --payload stdin`, and the same form for `scope add` and for the changeset `run start --input stdin` — with every apostrophe in the object written as the single-quote splice `'"'"'`. Idempotency keys are command arguments, never payload fields; quote every path, token, and key as one shell argument, and never execute spec or test text as shell syntax. Run every mutation serially, preserving each result before the next command.

</persistence_contract>

</audit_workflow>

<verdict_format>

**The verdict this skill returns.** Return only the exact run token and the unmodified rendered projection. The projection is the verdict: its `terminalStatus` is `approved` or `rejected`, its `findingCount` is zero for approval, its `findings` group every accepted finding under `blocking` and `debt`, its `auditScopeUnits` carry the root, assertion, language, and retired units, and its `events` carry every accepted finding payload and the terminal event. Both severities reject the run. Keep every SPX field unchanged, and add no `APPROVED` or `REJECTED` prose envelope.

A run that cannot complete — a request or prerequisite failure before the run starts, a refused SPX command or payload, or a changed subject — returns:

```text
BLOCKED
runToken: <exact-token-if-start-succeeded-or-not-started>
command: <exact-failed-command, or request for a failure before the run starts>
payloadKey: <unitId-or-finding-idempotency-key-or-none>
exitCode: <exact-exit-code-or-none>
stderr: <exact-stderr-or-none>
judgmentStatus: <complete|incomplete>
judgedFindings: <JSON array of every finding judged before the stop, in the finding-payload shape>
```

**The composed concern result.** Each `audit-<lang>-tests` skill returns one JSON object in this shape, which the language skills inherit; Step 7 validates it and records its findings. `overall` is `APPROVED` iff every present row is `PASS`. A row is `FAIL` iff it carries a `REJECT` finding; `WARNING` and `INFO` are non-blocking. Every finding carries all nine fields. `gate-2-architectural` is present only when the language judged architectural duplication; there is no `gate-0-deterministic` row.

```json
{
  "schema_version": 1,
  "skill": "audit-<lang>-tests",
  "target": "<spec-node-path>",
  "overall": "APPROVED | REJECTED",
  "rows": [
    {
      "name": "gate-1-assertion | gate-2-architectural",
      "status": "PASS | FAIL",
      "findings": [
        {
          "id": "f-001",
          "file": "<artifact-path>",
          "line": null,
          "assertion": "<full-assertion-text-or-stable-id | cross-assertion>",
          "property": "<testability | evidence-chain-completeness | declarations | predicate-ownership | source-ownership | oracle-independence | coupling | falsifiability | alignment | coverage | architectural-duplication | language-composition | unsupported-language>",
          "rule": "<rule-id>",
          "severity": "REJECT | WARNING | INFO",
          "message": "<one-line evidentiary gap, or extraction target for gate-2>",
          "remediation_target": "<source-contract | harness | generator | fixture | eval-case | test-file | source-file | test-infrastructure | independent-oracle | skill-installation | language-partition>"
        }
      ]
    }
  ],
  "metadata": { "evidence_chain": [], "coverage_traces": [] }
}
```

When every subject a language skill received is a retired path with no current `[test]` assertion and no current evidence-chain owner, it returns `{"status": "NOT_APPLICABLE", "subjects": [...], "explanation": "..."}` with no rows. A current broken `[test]` link stays applicable and is reported as missing evidence.

</verdict_format>

<failure_modes>

**Failure 1: Accepted a tautological test file**

Claude approved a test file that imported only vitest. It declared OKLCH color constants and verified they satisfied contrast thresholds — pure math with zero connection to any CSS file, theme, or component. Clean types and comprehensive scenarios distracted Claude from the imports.

How to avoid: Step 6 classifies imports before the other properties. Zero codebase imports is `no-coupling`.

**Failure 2: Accepted mocking as legitimate coupling**

Claude saw `import { database } from "../src/database"` and classified it as direct coupling. The next line was `vi.mock("../src/database")`, so the real module never ran.

How to avoid: After coupling, check for replacement doubles; an import plus a mock outside the seven Stage 5 cases is `severed-coupling`.

**Failure 3: Re-ran the project's coverage command inside the audit**

Claude ran the project's coverage command three times to measure a delta. Those runs added no audit evidence and repeated work the Author's agent session had already passed.

How to avoid: Trace coverage by reading and name the path from the code. The skill grants no command that runs project verification.

**Failure 4: Approved a prose-body substring test as direct coupling**

Claude rated coupling and falsifiability PASS on a test that read an authored skill body and asserted policy substrings, reasoning that the text was the thing under test. No code ran; only an edit to the prose could fail it.

How to avoid: Classify by whether the subject is executable behavior or authored text, however a harness mediates the read. A read of authored prose asserted for its content is `prose-coupling`.

**Failure 5: Accepted renamed test-local configuration**

Claude renamed a SCREAMING_CASE property-test run count to camelCase after a validator flagged it, then approved. The value was still runner configuration in the executed test file.

How to avoid: Classify ownership by what a binding chooses. Runner counts, seeds, setup choices, boundary bags, and expected outputs belong in harnesses, generators, source contracts, fixtures, or eval cases.

**Failure 6: Approved a thin test without auditing its harness**

Claude inspected a linked Python test, reviewed only three repeated `file.txt` values in its harness, and approved. The harness also declared SPX payload keys, command tokens, status values, and expected projection fields, none of which the audit classified.

How to avoid: Inventory and read the complete evidence chain before judging, and name the source of every protocol value.

**Failure 7: Used the defect location as the remediation owner**

Claude found copied protocol fields in a harness and named the harness as the remediation target because that file held the defect. Copied domain truth belongs to a source contract wherever the copy appears.

How to avoid: Locate the finding at the artifact holding the copy and name `source-contract` as its remediation target.

**Failure 8: Read an absent in-repository caller as proof of laundering**

Claude rejected a package's `__version__` as laundering because no module in the checkout consumed it. The packaging manifest declared it as published API, a surface the audit never opened.

How to avoid: Read the checkout's declared surfaces before reporting a symbol as laundered, and name the surfaces inspected.

**Failure 9: Rebased the audited branch while loading context**

A test-evidence audit loaded context through `/contextualize`, whose `/sync-base` rebased the branch and resolved two conflicts mid-audit, so a concurrent implementation audit found its sealed head superseded.

How to avoid: Load context read-only in Step 3 and invoke neither `/contextualize` nor `/sync-base`; the audited head stays the dispatched head.

</failure_modes>

<success_criteria>

The verdict is sound when:

- Every in-scope `[test]` assertion and every linked test's language concern carries a recorded unit, and every retired path carries a `not-applicable` unit, with no evidence partition left unjudged.
- Every assertion unit was recorded only after its evidence-chain inventory was complete, or carries the finding naming the unresolved artifact.
- Every protocol and domain value resolves to its production or platform owner; generated variable data to a generator, inert whole payloads to fixtures, setup policy to harnesses, and curated examples to eval cases.
- The sealed run's terminal status is `approved` only with no finding and every unit `audited` or `not-applicable`.
- Every finding is falsifiable: it names the assertion or artifact, the failed property, the evidence, and the remediation target.
- The same target, standards, committed subject, and run-driver identity yield the same units, finding keys, and terminal status.

</success_criteria>

The test-evidence package (JSON-encoded):

```json
{input_json}
```
