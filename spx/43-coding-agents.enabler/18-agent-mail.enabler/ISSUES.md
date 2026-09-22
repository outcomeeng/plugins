# Issues: Agent Mail

## DEBT: captured oracle artifacts lack source provenance

The captured usage and public-response artifacts under `outcomeeng_testing/fixtures/agent_mail/` carry no tool name or source version. The adapter ADR declares `am` 0.3.24 for store grammar and responses, together with the pin-change and live-drift recapture conditions, while the fixture family has no artifact-owned representation of that pin yet.

**Impact**: a reader cannot determine from a captured artifact or its fixture family which source-tool release produced it, so stale-oracle detection depends on the ADR rather than inspectable fixture provenance. The ADR declaration leads the fixtures until the evidence layer catches up.

**Settlement condition**: a separate Change adds the exact tool and version provenance to every captured usage and response artifact, or adds a fixture-owned manifest that each artifact declares, then establishes the applicable deterministic test evidence and test-evidence audit on the committed subject.

**Evidence**: changes-review run `2026-09-19_05-37-13-476-8f079ea7b727` reported the full fixture class at head `5ad33be7f066e9eae2272e085a6e31ec85fede2d`.

## DEBT: the usage-contract reader discards the grammar two checks need

`outcomeeng_testing/harnesses/cli_usage.py` reads a captured usage text into a `UsageContract` but drops two things the capture declares. It skips the first token of the usage line, the program name, and it reduces each option's value placeholder to a boolean, so `<SENDER>`, `<TO>`, `<SUBJECT>`, and `<BODY>` are not retained.

**Impact**: the record-field-to-option correspondence is asserted with `PUBLIC_AM_RECORD_OPTIONS` on both the produced and the expected side, so a consistent swap of two same-arity entries in that map — `sender` onto `--to` and `recipient` onto `--from` — leaves every option still declared and still seen once, and the grammar check passes. The capture holds the placeholder names that would falsify it.

**Not the program name**: the sibling gap is closed for this node. `store_program_names` in `outcomeeng_testing/harnesses/agent_mail.py` reads the first token of each captured usage line directly, so the adapter's store constant is checked against the store's own declaration.

**Settlement condition**: `usage_contract` retains the program name and each option's value placeholder, and the agent-mail mapping test reads the record-field correspondence from those placeholders rather than from the source map alone.

**Why separate**: `cli_usage.py` is shared test infrastructure. The herdr and Prowl environment nodes read the same contract shape, so widening it reaches their evidence too, and each owning node takes the change through its own test-evidence audit.

**Evidence**: `spec-tree:test-evidence-auditor` findings `f-001` and `f-002`, rule `oracle-independence`, on head `1d7a14a2998039feec89d7ff19de82baaa4a30a8`; `f-001` is closed by `store_program_names` and recorded here only as the reason the reader still owes the placeholder half.

## DEBT: skill tool grants embed the skill-directory token

Every skill in this marketplace that grants a bundled script names it as `Bash(python3 "${CLAUDE_SKILL_DIR}/scripts/<name>.py":*)` — fifteen of fifteen that grant a script path. `/skill-standards` documents that token for the skill body, where the loader substitutes it before the command runs, and states nothing about whether a frontmatter permission pattern is substituted the same way. If it is not, every such grant fails to match at runtime and each invocation falls through to a per-call approval prompt rather than erroring.

**Impact**: unresolved, and the same for all fifteen skills. A grant that silently does not match is indistinguishable from an environment that prompts for other reasons, so the cost is invisible until someone measures it.

**Settlement condition**: the substitution scope for frontmatter permission patterns is established against the agent harness and recorded in `/skill-standards`; if frontmatter is not substituted, every affected grant moves to a form that matches, in one sweep.

**Why separate**: the question belongs to the `instructions` plugin's standard and its answer changes fifteen grants across six plugins at once. Diverging this one skill from its fourteen peers on an unsettled question would make the convention harder to fix, not easier.

**Evidence**: `instructions:skill-auditor` finding `f-008`, rule `tool_restriction_specificity`, on head `1d7a14a2998039feec89d7ff19de82baaa4a30a8`, with the fifteen-of-fifteen count from a sweep over `src/plugins/*/skills/*/SKILL.md`.

## DEBT: the test-evidence gate rejects this node until the detectors move

`spx/43-coding-agents.enabler/ISSUES.md` records that the raw-command and project-key detectors ship inside the adapters with no production consumer, and names one home for that detection outside them as its settlement condition. The consequence for this node's gate is stated here, because it recurs every round.

The compliance assertion `NEVER: another shipped coding-agents script constructs a raw mail command or derives the project key from Git state` links a test whose only reachable enforcement is `raw_mail_command_violations`, `git_project_key_violations`, and their pattern tables in the shipped adapter. No adapter execution path reaches them, so the evidence couples to a declaration only the tests read.

**Impact**: an isolated test-evidence audit of this node returns `REJECTED` on rule `source-ownership` for that assertion, on every subject, regardless of what else the node carries. Three runs have now done so — heads `d6d1b5458af190ac9d1f05775c869c08ab206c95`, `18903ace30be971b041eba9e74606e97bf0182ae`, and `fc7619c0cd4224bb6fd6e25f5f02f0509aff2ba3` — the first two as a finding among others, the third as the round's only rejection.

**Why it does not block a `spec`-malleable changeset**: Passing at this node's declared malleability is Validate, the reachability tests, and a result for every tagged assertion. Evidence that passes audit is the `implementation` requirement. A Change whose Frame names the test-evidence audit meets that obligation by running it and disposing every finding, and the remediation this finding names is chartered to a successor Change, not to the Change that runs the audit.

**Settlement condition**: the successor Change that relocates raw-command and project-key detection to one home outside the shipped adapters lands, this node's compliance test imports the detector from that home, and an isolated test-evidence audit of this node returns no `source-ownership` finding for this assertion. Until then the rejection is expected and is not evidence of a defect in the changeset under audit.

**Evidence**: `spec-tree:test-evidence-auditor` finding `f-001`, rule `source-ownership`, on head `fc7619c0cd4224bb6fd6e25f5f02f0509aff2ba3`, naming the relocation as its remediation target; the same rule on the two earlier heads above.

## Two verifier rules collide on naming the evidence location in a shipped skill

`instructions:skill-auditor` reads the `<testing>` section of `src/plugins/coding-agents/skills/operate-agent-mail/SKILL.md` as an abstract testing record and asks it to name a runnable target — this node's `tests/` directory, or the repository's declared node-test invocation — so a reader can re-establish the claim from the skill alone. `spec-tree:changes-reviewer` reads that same directory, named in that same sentence, as a portability defect: the skill ships verbatim to every consumer install, where no `spx/` tree exists, and every other shipped skill that spells an `spx/` node path uses the synthetic `spx/55-example.…` form.

Each rule is right about its own subject, and shipped content cannot satisfy both. The tests that cover the adapter live in this repository; a consumer install carries the skill without them, so any runnable target the skill names is unreachable wherever the skill actually runs. The portability constraint governs, because `CLAUDE.md` `## Plugin Portability Constraints` states that a consumer checkout contains no `spx/`: the coverage stays recorded as domains with no address, and the auditor's warning is dropped as unbacked for shipped skill content.

**Impact**: the warning recurs on every audit of a shipped skill whose `<testing>` section records coverage, costing a round each time to answer with the same reasoning. No edit satisfies both readings at once.

**Settlement condition**: the skill-authoring standard states how a shipped skill records its coverage when the evidence lives only in the producing repository — either that a domain list carrying no address satisfies the testing rule for shipped content, or that the address belongs in a form the build strips from the consumer render — and `instructions:audit-skill` applies that rule.

**Why separate**: the fix belongs to the `instructions` plugin's audit skill and its standards, which no agent-mail changeset touches.

**Evidence**: `instructions:skill-auditor` finding `f-006`, rule `abstract_testing_record`, against the skill surface committed at `b3b1b32a068e2e492567f2bb3e6f5ce148c6914d`; the `spec-tree:changes-reviewer` warning on `src/plugins/coding-agents/skills/operate-agent-mail/SKILL.md` line 107 that required removing the same address.

**Recurrence**: the same rule returned as `f-008` against the surface committed at `b6ce460eab6ac1401eecdf652b1b631e868d4144`, this time proposing a remedy that keeps the address out — record which input each domain was exercised with and which result it must return. That remedy does not collide with the portability constraint, so it is a live option for the settlement above rather than a second contradiction; the reviewer's own reading, that the domain bullets already satisfy the script-testing rule, is the competing one.

**Third recurrence**: the same collision returned as `f-007`, rule `script_testing_record_not_rerunnable`, against the surface committed at `8026287fa64ddc9c0f569849b2a2132f40422d89`, asking again for a test file, node test directory, or command beside the coverage claims. The verdict was `APPROVED` with the finding at `WARNING`, and it is dropped as unbacked under the portability constraint above. The rule reaches this surface under two spellings now — `abstract_testing_record` and `script_testing_record_not_rerunnable` — so the settlement states the rule for shipped content rather than for one finding identifier.

## A constraint's rationale rests on facts about sibling skills

The verbatim-identity constraint in `src/plugins/coding-agents/skills/operate-agent-mail/SKILL.md` justifies itself with "downstream skills index on the literal and the operator compares it against the store", so the reason a value must not be transformed is stated as a fact about the skills that consume this one. `/skill-standards` `<skill_organization>` requires the one-way dependency to hold in the other direction: a skill's own rules stand without knowledge of its consumers.

**Impact**: the rationale stops being true in a composition that has no such downstream reader, and a reader weighing whether the rule still applies has to reason about surrounding skills rather than about the output.

**Settlement condition**: the constraint states the property of the value itself — store identities are the store's own lookup keys, so any transformation makes the value address nothing — and the skill surface passes the typed skill auditor.

**Evidence**: `instructions:skill-auditor` finding `f-008`, rule `caller_independence`, against the surface committed at `dce2ced56b7bceefe265f668d0d458a9a0bbecc0`; the line predates this changeset, which reached the file for three unrelated findings.

## DEBT: the operation-surface shape for the project-key form is contested

`project-key` is invocable but takes no JSON request, so it is a CLI form rather than a member of the request-operation registry. Three independent readings of `src/plugins/coding-agents/skills/operate-agent-mail/SKILL.md` have pulled its presentation in opposite directions, and each was correct against the surface it read.

1. On head `18903ace30be971b041eba9e74606e97bf0182ae`, `instructions:skill-auditor` finding `f-011`, rule `operation_surface_omits_documented_operation`: the form appeared only under `<invocation_forms>`, so a caller consulting the operation table concluded the capability offered no such operation and would derive the key itself. It asked for a row.
2. On head `1d7a14a2998039feec89d7ff19de82baaa4a30a8`, with the row present, `instructions:skill-auditor` finding `f-007`, rule `surface_conflation`, and `spec-tree:changes-reviewer` run `2026-09-21_23-42-42-028-42e88f3fa3af` both found that a table introduced as the request operations, under workflow steps applying to every row, leads a caller to submit a `run` request the registry rejects as `operation-unavailable`. The row was removed and the framing narrowed to request operations.
3. On head `7150fdc3bf9a7068a3b16eec7c184e366bdada6a`, `instructions:skill-auditor` finding `f-008`, rule `operation_surface_completeness`: the one table claiming to be the operation surface enumerates four forms while a fifth equally invocable form is described only in following prose, so a reader forms a four-operation model the rejection at the workflow step then contradicts. It asked for a row or a companion table.

Readings 1 and 3 ask for visibility; reading 2 objects to placement among request operations. A companion table satisfies all three and is the shape the surface now carries.

**Impact**: none of the three findings is wrong, and the surface has changed three times. The cost is a repair round per reading, not a defect a consumer meets.

**Settlement condition**: a governing standard states how a skill's operation surface presents forms that share an invocation entry point but not a request shape — one table with a form column, two tables, or a table plus a named companion — so a later reading applies that rule instead of judging the shape afresh. Until then the companion table stands, and a fourth reading pulling on this line is reported against this entry rather than repaired again.

**Evidence**: the three findings above, with the heads each was produced on. The `instructions:skill-auditor` verdicts carry no run token; the reviewer reading carries the run token named in item 2.

**Fifth recurrence, fourth rule name.** The same collision reached a fifth run under a fourth identifier: `abstract_testing_record`, then `script_testing_record_not_rerunnable`, then `script_testing_record`, now `unlocated_testing_record` on head `83de2bf1fc526231a3ab797afa7a60b4316196cf`. The conflict is stable and its name is not, so the settlement must state the rule for shipped content rather than name a finding identifier — an entry keyed to any one of those four will be missed by the next run.

## The probe confirms three of the four variables the lookup removes

`GIT_LOCATION_VARIABLES` in `src/plugins/coding-agents/skills/operate-agent-mail/scripts/agent_mail.py` removes four names. The mapping test's domain is the set Git's own behaviour confirms moves a lookup's answer off the invoking working directory, and on the pools that test builds Git confirms three of them: `GIT_DIR` and `GIT_COMMON_DIR` by answering with another repository, `GIT_CEILING_DIRECTORIES` by giving the answer it gives where no repository exists. `GIT_WORK_TREE` is removed and not confirmed.

`GIT_WORK_TREE` names a work tree rather than a repository, so it changes what `--git-common-dir` is asked about only alongside a variable the probe already confirms. The complete-set case covers it there; no individual falsification is claimed for it, which is the accurate reading rather than a gap in the probe.

**Impact**: the removal of that one name rests on the class the declaration states rather than on a case confirming it alone, so a regression that dropped it from the removal list would pass this node's tests. Removal costs nothing and stays, because the declaration is the class and the name belongs to it.

**Settlement condition**: `GIT_WORK_TREE` enters the confirmed domain from a shape where it alone moves the answer off the working directory, and the reason it otherwise stays out is stated where the domain is derived — or it is established as unfalsifiable by observation and the agreement between the declaration and the removal list is routed to audit under `spx/12-shipped-scripting.adr.md`.

**Evidence**: `spec-tree:changes-reviewer` warning on `spx/43-coding-agents.enabler/18-agent-mail.enabler/21-agent-mail-adapter.adr.md` line 28, which named `GIT_CEILING_DIRECTORIES` as a boundary member inside the stated domain; the ceiling member is closed by the repair that added it to the removal list and drew the test domain from Git, and this entry records what that repair left unreproduced. The same warning named `GIT_DISCOVERY_ACROSS_FILESYSTEM` as a second such member and it was added on that reading; restating the class by its claim removed it again, because a variable that only widens discovery toward the repository genuinely there cannot move the answer off the working directory, and stripping it would prevent a right answer rather than a wrong one.

## The removal set's composition is unprotected against re-addition

Re-adding `GIT_DISCOVERY_ACROSS_FILESYSTEM` to `GIT_LOCATION_VARIABLES` leaves every linked test passing. The only assertion constraining that set is a subset relation over the variables Git's own behaviour confirms redirect a lookup, which fails on under-removal and never on over-removal; the probe's candidate list holds only the names that can confirm on a single-filesystem pool; and every checkout shape the pool builds sits inside one temporary directory.

**The gap is structural, not an omission.** A variable that only widens discovery governs nothing where no boundary exists to cross, so no pool built on one filesystem can confirm or refute its exclusion however carefully the probe is written. Trying harder does not close this; a checkout shape spanning a real boundary does. A later reader who finds the removal set unprotected is looking at a property of the variable, not at a case someone forgot.

**Two claims ride on that one piece of evidence.** The composition of the set — which names are in it and which are not — is a declared value, and the agreement between the spec's enumeration and the module's list is what `spx/12-shipped-scripting.adr.md` routes to audit, because every oracle for it is a second declaration. The behavioural reason for the exclusion — that a variable which only widens the search cannot move the answer off the working directory — is a claim about Git, and it is load-bearing only where a mount boundary exists. The first is reachable without a boundary; the second is not.

**Impact**: a regression that re-adds the excluded name, or drops an included one, reaches no failing case in this node. The adapter would then strip a variable whose removal prevents a right answer rather than a wrong one, which is the availability regression the exclusion exists to avoid.

**Settlement condition**: the pool gains a checkout shape whose repository lies across a filesystem boundary the harness can create without privilege and portably in CI, a case confirms that a widening variable is load-bearing for resolution there, and stripping it fails that case — or the composition agreement is established as audit evidence under `spx/12-shipped-scripting.adr.md` and the behavioural claim keeps this record until a boundary shape exists.

**Evidence**: `spec-tree:implementation-auditor` run `2026-09-22_05-11-14-334-52e8071117c7` on head `86340fec128ed2d277b96f6ece6c759c1347face`, rule `carried-through-variable-unfalsifiable`, severity `blocking`. Earlier runs raised the same shape as `debt` against the wider removal set; the severity moved when the exclusion became a declared decision rather than an unconfirmed member.

## Whether the config-selection variables belong in the removal set is unestablished

`GIT_LOCATION_VARIABLES` holds four names, and `repository_lookup_environment` carries every other `GIT_` variable through, the config-selection variables among them: `GIT_CONFIG_GLOBAL`, `GIT_CONFIG_SYSTEM`, `GIT_CONFIG_NOSYSTEM`, and the `GIT_CONFIG_COUNT`/`GIT_CONFIG_KEY_n` pairs. The class the decision states is an effect — a variable that can make Git answer the location question from something other than the invoking working directory — so a variable reaches it by any mechanism, not only by naming a repository or bounding discovery.

**The reasoning that would admit them.** A caller carrying one of these replaces the configuration Git reads, so a `safe.directory` entry that a differently-owned repository depends on is no longer visible. The lookup would then refuse in a working directory whose repository resolves without that variable — the same observable effect that admits `GIT_CEILING_DIRECTORIES`, reached a different way.

**Why they are not in the set.** The reasoning rests on a precondition no case in this node establishes: a repository owned by a different user than the one running the lookup. Nothing in the changeset or the pool demonstrates it, and admitting a name on reasoning alone is exactly how the widening variable entered the set and had to be removed again. The set stays at four until a case shows the effect.

**Settlement condition**: the harness can build a repository whose ownership differs from the invoking user and whose resolution depends on a `safe.directory` entry, a case confirms that a config-selection variable makes the lookup refuse where it otherwise resolves, and the name enters the set from that case — or the precondition is established as unreachable in this product's test environment and the exclusion is recorded as resting on that.

**Evidence**: `spec-tree:changes-reviewer` warning on `spx/43-coding-agents.enabler/18-agent-mail.enabler/21-agent-mail-adapter.adr.md` line 7, which read the decision's two-mechanism wording as an exhaustive partition and named these variables as a constructed member outside it. The partition wording is repaired by stating the class by its effect; this entry records the classification question that wording concealed.

## Restating the record mapping in the skill body keeps dropping conditions

`src/plugins/coding-agents/skills/operate-agent-mail/SKILL.md` describes how a read-back record's kind is decided, a predicate `_split_kind` and `record_from_inbox_item` own in the adapter. Three successive rewrites each lost a different condition of it: a paragraph split separated the threadless case from the prefix case so the first read as a complete rule; the consolidated single sentence dropped the empty-remainder conjunct while its lead qualifier still covered it; the enumeration that replaced the sentence dropped the space in `KIND_PREFIX_CLOSE`, so a subject like `[fact]hello` satisfied none of its listed clauses while the adapter still reports `unclassified`.

**Impact**: each form was more careful than the one before and each was wrong in a new place, so a consumer reading the shipped body could predict a kind the adapter does not report. The loss is invisible on inspection and appears only when a worked example is run against the predicate.

**Settlement condition**: the shipped body states the outcome a caller must handle rather than the predicate the adapter owns, or any enumeration it carries is checked against worked examples covering each condition, and a rule governs which of the two a shipped skill uses when a decision already owns the predicate.

**Evidence**: `instructions:skill-auditor` `f-010` on head `1d7a14a2998039feec89d7ff19de82baaa4a30a8` (the split), `f-008` on `be342cd8a9ce62bd3dc8508492928190f7d96cbe` (the sentence), and `spec-tree:changes-reviewer` run `2026-09-22_08-47-52-583-e8b09f841f52` on `83de2bf1fc526231a3ab797afa7a60b4316196cf` (the enumeration, with the `[fact]hello` example).

## Two skill-surface presentation warnings left unrepaired

Both are valid and bounded, and both are recorded rather than repaired because every recent presentation rewrite of this surface introduced a correctness defect, so another one trades demonstrated risk for no correctness gain.

The workflow's first step admits two input forms — one request operation with its arguments, or a complete JSON request — while every worked example shows only the JSON form, so the operation-plus-arguments form has no shown mapping onto the argument names. The project-key paragraph carries four separable rules in one block: the key is the common Git directory, the pool-wide equivalence that follows, the variable-dropping policy with its non-exhaustive qualifier, and the `repository-unresolved` outcome.

**Settlement condition**: both are taken with the settlement above, so the surface is revised once under whatever rule governs restating an adapter-owned predicate, rather than in separate passes that each risk a new dropped condition.

**Evidence**: `instructions:skill-auditor` findings `f-008` (`argument_form_unexemplified`) and `f-010` (`dense_single_paragraph`) on head `83de2bf1fc526231a3ab797afa7a60b4316196cf`.
