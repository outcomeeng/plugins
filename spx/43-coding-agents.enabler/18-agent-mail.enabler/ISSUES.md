# Issues: Agent Mail

## DEBT: the usage-contract reader discards the grammar two checks need

`outcomeeng_testing/harnesses/cli_usage.py` reads a captured usage text into a `UsageContract` but drops two things the capture declares. It skips the first token of the usage line, the program name, and it reduces each option's value placeholder to a boolean, so `<SENDER>`, `<TO>`, `<SUBJECT>`, and `<BODY>` in the captured `am mail send` usage are not retained.

**Impact**: the mapping test binds each option to its own value, but it derives the option each record field is expected under from `PUBLIC_AM_RECORD_OPTIONS`, the same map the adapter builds the argument vector from. A consistent swap of two same-arity entries in that map — `sender` onto `--to` and `recipient` onto `--from` — moves the produced and the expected binding together, so the option-to-value check passes. The capture holds the placeholder names that would falsify it.

**Not the program name**: the sibling gap is closed for this node. `store_program_names` in `outcomeeng_testing/harnesses/agent_mail.py` reads the first token of each captured usage line directly, and the compliance test checks the adapter's store constant against that set, so the constant is read against the store's own declaration.

**Settlement condition**: `usage_contract` retains the program name and each option's value placeholder, and the agent-mail mapping test reads the record-field correspondence from those placeholders rather than from the source map alone.

**Why separate**: `cli_usage.py` is shared test infrastructure. The herdr and Prowl environment nodes read the same contract shape, so widening it reaches their evidence too, and each owning node takes the change through its own test-evidence audit.

**Evidence**: `spec-tree:test-evidence-auditor` findings `f-001` and `f-002`, rule `oracle-independence`, on head `1d7a14a2998039feec89d7ff19de82baaa4a30a8`; `f-001` is closed by `store_program_names` and recorded here only as the reason the reader still owes the placeholder half.

## DEBT: skill tool grants embed the skill-directory token

`src/plugins/coding-agents/skills/operate-agent-mail/SKILL.md` line 6 declares its narrow grant as `Bash(python3 "${CLAUDE_SKILL_DIR}/scripts/agent_mail.py":*)`. `/skill-standards` documents that token for the skill body, where the loader substitutes it before the command runs, and states nothing about whether a frontmatter permission pattern is substituted the same way. If it is not, the grant never matches at call time and each invocation falls through to a per-call approval prompt rather than erroring — a grant that reads as containment while providing none.

**Extent**: the question is the agent harness's, not this node's. At head `d9fbbcda840677190c915cfa435feedca30654fa`, 17 of the 106 authored skills that declare `allowed-tools`, among the 113 under `src/plugins/*/skills/*/SKILL.md`, carry the token inside that declaration: `coding-agents` six, `spec-tree` ten, and `contribute` one. `spx/ISSUES.md` entry `A skill-directory token inside an allowed-tools pattern may never match` is the cross-surface record of that population and of the executed invocation that settles it.

**Impact**: unresolved, and the same for every grant in the population. A grant that silently does not match is indistinguishable from an environment that prompts for other reasons, so the cost is invisible until an invocation is observed.

**Settlement condition**: an executed invocation establishes whether the agent harness substitutes the skill-directory token in a frontmatter permission pattern, `/skill-standards` records that scope, and, where frontmatter is not substituted, every affected grant — this skill's among them — takes a form that matches.

**Why separate**: the answer belongs to the `instructions` plugin's standard and changes grants across three plugins at once. Diverging this one skill from its peers on an unsettled question makes the convention harder to fix, not easier.

**Evidence**: `instructions:skill-auditor` finding `f-008`, rule `tool_restriction_specificity`, on head `1d7a14a2998039feec89d7ff19de82baaa4a30a8`, and the same rule again at severity `warning` against line 6 of this surface; the population count from a frontmatter sweep of `src/plugins/*/skills/*/SKILL.md` at head `d9fbbcda840677190c915cfa435feedca30654fa`.

## DEBT: the test-evidence gate rejects this node until the detectors move

`spx/43-coding-agents.enabler/ISSUES.md` records that the raw-command and project-key detectors ship inside the adapters with no production consumer, and names one home for that detection outside them as its settlement condition. `spx/43-coding-agents.enabler/18-agent-mail.enabler/21-agent-mail-adapter.adr.md` keeps the scanner beside the grammar it detects and leaves a home shared by the Prowl, herdr, and agent-mail adapters to a decision above any one adapter. The consequence for this node's gate is stated here, because it recurs on every test-evidence audit.

The compliance assertion `NEVER: another shipped coding-agents script constructs a raw mail command or derives the project key from Git state` links a test whose only reachable enforcement is `raw_mail_command_violations`, `git_project_key_violations`, and their pattern tables `RAW_MAIL_COMMAND_PATTERNS` and `GIT_PROJECT_KEY_PATTERNS` in `src/plugins/coding-agents/skills/operate-agent-mail/scripts/agent_mail.py`. The adapter's CLI dispatches only `run` and `project-key`, and neither reaches the scanners; the compliance test is their only caller, running them over the shipped coding-agents scripts and over argument-vector, shell-string, and Git-derivation violating fixtures. The evidence therefore couples to a declaration only the tests read.

**Impact**: an isolated test-evidence audit of this node returns `REJECTED` on rule `source-ownership` for that assertion, on every subject, regardless of what else the node carries. Three runs have returned it — heads `d6d1b5458af190ac9d1f05775c869c08ab206c95`, `18903ace30be971b041eba9e74606e97bf0182ae`, and `fc7619c0cd4224bb6fd6e25f5f02f0509aff2ba3` — the first two as a finding among others, the third as the round's only rejection.

**Why it does not block a `spec`-malleable changeset**: Passing at this node's declared malleability is Validate, the reachability tests, and a result for every tagged assertion. Evidence that passes audit is the `implementation` requirement. A Change whose Frame names the test-evidence audit meets that obligation by running it and disposing every finding, and the remediation this finding names belongs to a successor Change, not to the Change that runs the audit.

**Settlement condition**: raw-command and project-key detection has one home outside the shipped adapters, this node's compliance test imports the detector from that home, and an isolated test-evidence audit of this node returns no `source-ownership` finding for this assertion. Until then the rejection is expected and is not evidence of a defect in the changeset under audit.

**Evidence**: `spec-tree:test-evidence-auditor` finding `f-001`, rule `source-ownership`, on head `fc7619c0cd4224bb6fd6e25f5f02f0509aff2ba3`, naming the relocation as its remediation target; the same rule on the two earlier heads above.

## DEBT: the terminal-handback reduction and the request builder ship with no reachable form

`src/plugins/coding-agents/skills/operate-agent-mail/scripts/agent_mail.py` defines `terminal_handback` and `reduce_terminal` (lines 639–713), which build one terminal handback and reduce a repeat onto the terminal state for its coordination reference, and `operation_request` (line 1005), which builds a checked request from keyword arguments. The script's `main` dispatches the two `CliOperation` members only: `run` parses one versioned JSON request from stdin and hands it to `execute`, and `project-key` resolves the key. Neither form calls any of the three. `src/plugins/coding-agents/skills/operate-agent-mail/SKILL.md` documents only those two forms and forbids importing the script from another location (line 134). The callers of the three are this node's tests — `spx/43-coding-agents.enabler/18-agent-mail.enabler/tests/test_agent_mail.property.l1.py` alone for the reduction — and, for `operation_request`, `outcomeeng_testing/generators/agent_mail.py` and `outcomeeng_testing/harnesses/agent_mail.py`. `FieldDifference` (line 403), the record of one differing field that a conflicting-handback rejection carries, ships with the reduction and no further reach: `reduce_terminal` is its only constructor, so no documented form reaches it either.

The scanners at lines 1091–1104, `raw_mail_command_violations` and `git_project_key_violations`, are the same shape and are already recorded: `DEBT: the test-evidence gate rejects this node until the detectors move` above, and `Compliance scanners ship inside the environment adapters` in `spx/43-coding-agents.enabler/ISSUES.md`, whose settlement condition covers them. This entry records what those do not: a reduction and a request builder, neither a detector, shipped with no form that reaches them.

The reduction is not test-only in the way the scanners are, because the declarations assign it to this adapter. The property assertion in `spx/43-coding-agents.enabler/18-agent-mail.enabler/agent-mail.md` maps every terminal handback to exactly one terminal result carrying the complete initiating coordination reference; `spx/43-coding-agents.enabler/18-agent-mail.enabler/21-agent-mail-adapter.adr.md` states that the adapter exposes typed importable operations and rejects a conflicting handback; and the skill's `<testing>` section (line 165) lists that reduction among its coverage domains. The decision's importable operations and the skill's import prohibition therefore describe two different shipped surfaces, and the only surface that reaches the declared reduction is the one the skill forbids.

**Impact**: a consumer install carries a reduction no documented form performs. A workflow that receives two terminal handbacks for one reference either reduces them itself or does not reduce them, although the skill's testing record presents the reduction as covered behavior of the capability. The property evidence exercises the function directly, so its passing result establishes the reduction's behavior and nothing about a surface a consumer can invoke. Shipping only what `run` and `project-key` reach, and keeping the reduction with the product's tests, would remove behavior the spec and the adapter decision assign to this adapter, so that remediation contradicts those declarations while they stand.

**Settlement condition**: the adapter decision and the skill describe one shipped surface, and every definition the script ships is reached by a form that surface documents. The reduction is either reachable through a documented form or no longer assigned to this adapter by the spec and the decision. `operation_request` either has a production caller or is not shipped. The skill's `<testing>` section claims coverage only for behavior a documented form reaches.

**Related**: the Prowl adapter shows the reduction half of the same shape. Its `terminal_handback` is reached through a CLI form and its `operation_request` sits on its execution path, while its `reduce_terminal` (`src/plugins/coding-agents/skills/operate-prowl/scripts/prowl_environment.py` line 1506) has no caller outside `spx/43-coding-agents.enabler/18-prowl-environment.enabler/tests/`.

**Evidence**: `instructions:skill-auditor` finding `f-010`, severity `WARNING`, rule `shipped_script_unreachable_surface`, at `scripts/agent_mail.py:627` on the `src/plugins/coding-agents/skills/operate-agent-mail/` surface at head `a4fbdf287527ba6af2d3cd570e32021de1619daa`, overall verdict `APPROVED`. The finding names shipping only the surface the `run` and `project-key` forms reach as its remediation. A `git grep` for the five names across `src/`, `spx/`, and `outcomeeng_testing/` at that head finds no caller of the agent-mail definitions outside the tests and test infrastructure listed above.

## Two verifier rules collide on naming the evidence location in a shipped skill

`instructions:skill-auditor` reads the `<testing>` section of `src/plugins/coding-agents/skills/operate-agent-mail/SKILL.md` as a testing record that must name a runnable or locatable target, so a reader can re-establish each coverage claim from the skill alone. `CLAUDE.md` reads shipped skill content the other way: `## Two audiences, two design surfaces` requires authored skill content to render into portable plugin output that never names a product-internal node path, and `## Plugin Portability Constraints` states that a consumer checkout contains no `spx/`. `spec-tree:changes-reviewer` applied that reading to an earlier form of the same section and required its node address removed.

The deterministic gate decides the path half of that question. The `reference-portability` step, governed by `spx/15-validation.enabler/32-reference-portability.enabler`, rejects in every file under `src/plugins/` a node or decision path carrying a numeric index (`spx/` followed by digits and a hyphen) and any path under the `outcomeeng/plugins` or `outcomeeng/spx` slug, which includes a full URL into the repository such as `https://github.com/outcomeeng/plugins/tree/main/spx/…`. It admits the bare slug and the bare repository URL `https://github.com/outcomeeng/plugins`, which every plugin manifest carries as its `repository` field. An address that locates the node by a path inside the producing repository therefore fails the gate in every spelling.

The section at `SKILL.md` lines 146–180 takes the auditor's side in the one form the gate admits. Line 148 names the producing repository by its bare URL and the node by the `id` its spec front matter carries, `01a0b229-e718-7996-988b-d465e39f898d`, which the foundation makes unique across the tree and stable under re-indexing and re-placement. It states that the paths below are relative to that node's directory, and that a consumer install carries the skill without the evidence. The coverage domains follow, grouped under the node's three pytest files and its probe protocol. No other shipped skill under `src/plugins/` names the producing repository or a node in its `<testing>` section: the `coding-agents` siblings record coverage with no address, as `orchestrate-officers` does in `references/ledger-script-coverage.md`, which places its suite "beside the spec node governing this skill" in "the source repository". The gate rules only on path shape. Neither verifier's standard says whether a repository URL plus a node identity satisfies the portability constraint's intent, which is that shipped content names nothing product-internal.

**Impact**: each rule is right about its own subject, and a shipped surface satisfies one at a time. The address-free form draws the auditor's finding on every audit. A path-qualified address fails the deterministic gate before any verifier reads it. The identity-qualified form passes the gate but still names a product-internal identifier, which a review applying the portability intent can reject. The marketplace carries both forms of the testing record for shipped adapters, so neither reading can be answered by pointing at a convention.

**Settlement condition**: the skill-authoring standard states how a shipped skill records coverage whose evidence lives only in the producing repository — a domain list carrying no address, the producing repository's URL with a node identity that is not a path, or an address in a form the build strips from the consumer render — `instructions:audit-skill` applies that rule, and the portability constraint and the `reference-portability` step admit the same form.

**Why separate**: the rule belongs to the `instructions` plugin's standards and to the product's portability constraint, neither of which an agent-mail changeset owns.

**Evidence**: against the address-free section, `instructions:skill-auditor` raised the rule under six identifiers across seven audits — `abstract_testing_record` (`f-006`, surface committed at `b3b1b32a068e2e492567f2bb3e6f5ce148c6914d`), again as `f-008` on `b6ce460eab6ac1401eecdf652b1b631e868d4144` proposing a record of each domain's input and expected result, `script_testing_record_not_rerunnable` (`f-007`, `8026287fa64ddc9c0f569849b2a2132f40422d89`), `script_testing_record`, `unlocated_testing_record` (`83de2bf1fc526231a3ab797afa7a60b4316196cf`), `script_testing_record_incomplete`, and `script_testing_rule`, the last on a head whose `<testing>` section was unchanged since the recurrence before it, so the finding follows the surface rather than an edit to it. Against the addressed section, the `spec-tree:changes-reviewer` warning on `SKILL.md` line 107 required removing the node address. Against the path-qualified form on head `6b7fb0a08c8add29460cba11b46aea5998921440`, `just check` failed at its `reference-portability` step with exactly one violation, whose step log reads:

```text
/Users/shz/Code/outcomeeng/plugins/worktrees/change-132/src/plugins/coding-agents/skills/operate-agent-mail/SKILL.md:148: non-portable reference 'spx/43-coding-agents.enabler/18-agent-mail.enabler/' does not resolve in a consumer checkout
```

The step's pattern and its accepted forms are in `outcomeeng/validation/reference_portability.py`, and its compliance assertions are in `spx/15-validation.enabler/32-reference-portability.enabler/reference-portability.md`.

## DEBT: the operation-surface shape for the project-key form is contested

`project-key` is invocable but takes no JSON request, so it is a CLI form rather than a member of the request-operation registry. `src/plugins/coding-agents/skills/operate-agent-mail/SKILL.md` presents the five request operations — `register`, `send`, `list`, `read`, and `acknowledge` — in one table at lines 17–25 and the `project-key` form in a companion table at lines 27–31, whose lead sentence states that a `run` request naming it is rejected as `operation-unavailable`. Three independent readings of the surface pulled that presentation in opposite directions, and each was correct against the surface it read.

1. On head `18903ace30be971b041eba9e74606e97bf0182ae`, `instructions:skill-auditor` finding `f-011`, rule `operation_surface_omits_documented_operation`: the form appeared only under `<invocation_forms>`, so a caller consulting the operation table concluded the capability offered no such operation and would derive the key itself. It asked for a row.
2. On head `1d7a14a2998039feec89d7ff19de82baaa4a30a8`, with the row present, `instructions:skill-auditor` finding `f-007`, rule `surface_conflation`, and `spec-tree:changes-reviewer` run `2026-09-21_23-42-42-028-42e88f3fa3af` both found that a table introduced as the request operations, under workflow steps applying to every row, leads a caller to submit a `run` request the registry rejects as `operation-unavailable`. It asked for the row's removal and a framing narrowed to request operations.
3. On head `7150fdc3bf9a7068a3b16eec7c184e366bdada6a`, `instructions:skill-auditor` finding `f-008`, rule `operation_surface_completeness`: the one table claiming to be the operation surface enumerated its request operations while a further, equally invocable form was described only in following prose, so a reader formed a model the rejection at the workflow step then contradicted. It asked for a row or a companion table.

Readings 1 and 3 ask for visibility; reading 2 objects to placement among request operations. The companion table satisfies all three.

**Impact**: none of the three findings is wrong, and each cost a repair round. No rule fixes the shape, so every reading judges it afresh and can pull it again; the cost is verification rounds, not a defect a consumer meets.

**Settlement condition**: a governing standard states how a skill's operation surface presents forms that share an invocation entry point but not a request shape — one table with a form column, two tables, or a table plus a named companion — so a later reading applies that rule instead of judging the shape afresh.

**Evidence**: the three findings above, with the heads each was produced on. The `instructions:skill-auditor` verdicts carry no run token; the reviewer reading carries the run token named in item 2.

## Git confirms three of the four variables the lookup removes

`GIT_LOCATION_VARIABLES` in `src/plugins/coding-agents/skills/operate-agent-mail/scripts/agent_mail.py` removes four names. The mapping test's domain is the set Git's own behaviour confirms moves a lookup's answer off the invoking working directory, and on the pools that test builds, `git_location_variables` in `outcomeeng_testing/harnesses/agent_mail.py` confirms three of them: `GIT_DIR` and `GIT_COMMON_DIR` by answering with another repository, `GIT_CEILING_DIRECTORIES` by giving the answer Git gives where no repository exists. `GIT_WORK_TREE` is removed and not confirmed.

`GIT_WORK_TREE` names a work tree rather than a repository, so it changes what `--git-common-dir` is asked about only alongside a variable Git already confirms. The complete-set case covers it there; no individual falsification is claimed for it, which is the accurate reading rather than a gap in the confirmation.

**Impact**: the removal of that one name rests on the class the declaration states rather than on a case confirming it alone, so a regression that dropped it from the removal list would pass this node's tests. Removal costs nothing and stays, because the declaration is the class and the name belongs to it.

**Settlement condition**: `GIT_WORK_TREE` enters the confirmed domain from a shape where it alone moves the answer off the working directory, and the reason it otherwise stays out is stated where the domain is derived — or it is established as unfalsifiable by observation and the agreement between the declaration and the removal list is routed to audit under `spx/12-shipped-scripting.adr.md`.

**Evidence**: `spec-tree:changes-reviewer` warning on `spx/43-coding-agents.enabler/18-agent-mail.enabler/21-agent-mail-adapter.adr.md` line 28, which named `GIT_CEILING_DIRECTORIES` as a boundary member inside the stated domain; the ceiling member is closed by the repair that added it to the removal list and drew the test domain from Git, and this entry records what that repair left unreproduced. The same warning named `GIT_DISCOVERY_ACROSS_FILESYSTEM` as a second such member and it was added on that reading; restating the class by its claim removed it again, because a variable that only widens discovery toward the repository genuinely there cannot move the answer off the working directory, and stripping it would prevent a right answer rather than a wrong one.

## The removal set's composition is unprotected against re-addition

Re-adding `GIT_DISCOVERY_ACROSS_FILESYSTEM` to `GIT_LOCATION_VARIABLES` leaves every linked test passing. The only assertion constraining that set is a subset relation over the variables Git's own behaviour confirms redirect a lookup, which fails on under-removal and never on over-removal; the candidate list of `git_location_variables` — Git's own `rev-parse --local-env-vars` report widened by `GIT_CEILING_DIRECTORIES` — holds only names that can confirm on a single-filesystem pool; and every checkout shape the pool builds sits inside one temporary directory.

**The gap is structural, not an omission.** A variable that only widens discovery governs nothing where no boundary exists to cross, so no pool built on one filesystem can confirm or refute its exclusion however the confirmation is written. A checkout shape spanning a real boundary closes it; more careful confirmation on one filesystem does not. A reader who finds the removal set unprotected is looking at a property of the variable, not at a case someone forgot.

**Two claims ride on that one piece of evidence.** The composition of the set — which names are in it and which are not — is a declared value, and the agreement between the spec's enumeration and the module's list is what `spx/12-shipped-scripting.adr.md` routes to audit, because every oracle for it is a second declaration. The behavioural reason for the exclusion — that a variable which only widens the search cannot move the answer off the working directory — is a claim about Git, and it is load-bearing only where a mount boundary exists. The first is reachable without a boundary; the second is not.

**Impact**: a regression that re-adds the excluded name, or drops an included one, reaches no failing case in this node. The adapter would then strip a variable whose removal prevents a right answer rather than a wrong one, which is the availability regression the exclusion exists to avoid.

**Settlement condition**: the pool gains a checkout shape whose repository lies across a filesystem boundary the harness can create without privilege and portably in CI, a case confirms that a widening variable is load-bearing for resolution there, and stripping it fails that case — or the composition agreement is established as audit evidence under `spx/12-shipped-scripting.adr.md` and the behavioural claim keeps this record until a boundary shape exists.

**Evidence**: `spec-tree:implementation-auditor` run `2026-09-22_05-11-14-334-52e8071117c7` on head `86340fec128ed2d277b96f6ece6c759c1347face`, rule `carried-through-variable-unfalsifiable`, severity `blocking`. Earlier runs raised the same shape as `debt` against the wider removal set; the severity moved when the exclusion became a declared decision rather than an unconfirmed member.

## Whether the config-selection variables belong in the removal set is unestablished

`GIT_LOCATION_VARIABLES` holds four names, and `repository_lookup_environment` carries every other `GIT_` variable through, the config-selection variables among them: `GIT_CONFIG_GLOBAL`, `GIT_CONFIG_SYSTEM`, `GIT_CONFIG_NOSYSTEM`, and the `GIT_CONFIG_COUNT`/`GIT_CONFIG_KEY_n` pairs. The class the decision states is an effect — a variable that can make Git answer the location question from something other than the invoking working directory — so a variable reaches it by any mechanism, not only by naming a repository or bounding discovery.

**The reasoning that would admit them.** A caller carrying one of these replaces the configuration Git reads, so a `safe.directory` entry that a differently-owned repository depends on is no longer visible. The lookup would then refuse in a working directory whose repository resolves without that variable — the same observable effect that admits `GIT_CEILING_DIRECTORIES`, reached a different way.

**Why they are not in the set.** The reasoning rests on a precondition no case in this node establishes: a repository owned by a different user than the one running the lookup. Nothing in the node's evidence or the pool demonstrates it, and admitting a name on reasoning alone is exactly how the widening variable entered the set and had to be removed again. The set stays at four until a case shows the effect.

**Settlement condition**: the harness can build a repository whose ownership differs from the invoking user and whose resolution depends on a `safe.directory` entry, a case confirms that a config-selection variable makes the lookup refuse where it otherwise resolves, and the name enters the set from that case — or the precondition is established as unreachable in this product's test environment and the exclusion is recorded as resting on that.

**Evidence**: `spec-tree:changes-reviewer` warning on `spx/43-coding-agents.enabler/18-agent-mail.enabler/21-agent-mail-adapter.adr.md` line 7, which read the decision's two-mechanism wording as an exhaustive partition and named these variables as a constructed member outside it. The partition wording is repaired by stating the class by its effect; this entry records the classification question that wording concealed.

## Restating the record mapping in the skill body keeps dropping conditions

`_split_kind` and `record_from_inbox_item` in `src/plugins/coding-agents/skills/operate-agent-mail/scripts/agent_mail.py` own the predicate that decides a read-back record's kind. Three successive restatements of that predicate in the skill body each lost a different condition of it: a paragraph split separated the threadless case from the prefix case so the first read as a complete rule; the consolidated single sentence dropped the empty-remainder conjunct while its lead qualifier still covered it; the enumeration that replaced the sentence dropped the space in `KIND_PREFIX_CLOSE`, so a subject like `[fact]hello` satisfied none of its listed clauses while the adapter reports `unclassified`.

`src/plugins/coding-agents/skills/operate-agent-mail/SKILL.md` line 48 states the outcome a caller handles instead of the predicate: the kind read back is one a sender writes or `unclassified`, `subject` carries the text to use either way, and a row missing any condition the adapter owns reads as `unclassified` with its subject verbatim. That form carries no condition to drop, but no rule selects it over an enumeration.

**Impact**: each enumeration was more careful than the one before and each was wrong in a new place, so a consumer reading the shipped body could predict a kind the adapter does not report. The loss is invisible on inspection and appears only when a worked example is run against the predicate. Without a rule, a later rewrite of the surface can reintroduce an enumeration and the defect class with it.

**Settlement condition**: a rule in the skill-authoring standard governs whether a shipped skill states the outcome a caller handles or enumerates a predicate a decision already owns, and, where it admits an enumeration, requires worked examples covering each condition; `instructions:audit-skill` applies that rule.

**Evidence**: `instructions:skill-auditor` `f-010` on head `1d7a14a2998039feec89d7ff19de82baaa4a30a8` (the split), `f-008` on `be342cd8a9ce62bd3dc8508492928190f7d96cbe` (the sentence), and `spec-tree:changes-reviewer` run `2026-09-22_08-47-52-583-e8b09f841f52` on `83de2bf1fc526231a3ab797afa7a60b4316196cf` (the enumeration, with the `[fact]hello` example).

## The installed markdown validator rejects a dangling `[probe]` link the foundation admits

The Spec Tree foundation, in the `spec-tree:understand` skill's `<verification_types>`, states that a dangling `[test]`, `[eval]`, or `[probe]` link derives Declared without a structural defect. The markdown validator of the installed `@outcomeeng/spx` 0.7.2 reads the same link as an invalid relative link and fails Validate on it. The defect lies in the SPX CLI's validator, not in this node: line 40 of `agent-mail.md` carries the `[probe](probes/installed-store/probe.md)` assertion in the form the foundation admits.

**Impact**: a spec assertion's `[probe]` link cannot stand in a head ahead of its probe protocol without failing Validate. For this node, a head that carries the link without `probes/installed-store/probe.md` fails the deterministic floor, so the probe protocol lands in the same head as the link, or in an earlier one, before any verification dispatch that requires passing deterministic verification.

**Settlement condition**: an `@outcomeeng/spx` release whose markdown validator admits a dangling path-bearing evidence link as the foundation describes is adopted at this repository's declared spx version floor.

**Evidence**: on committed head `dc9db09166ebc0658f577d7297f3d3ca389ff98e`, where `agent-mail.md` carries the `[probe](probes/installed-store/probe.md)` assertion and the probe file does not exist, `spx validation markdown`, run at the repository root with the installed `@outcomeeng/spx` 0.7.2, exits 1 with one error:

```text
agent-mail.md:39 error relative-links Relative links should be valid ["probes/installed-store/probe.md" should exist in the file system]
```

On the same head, `just eval-links` and `spx spec status --format json` each exit 0, and spec status reports this node's state as `specified`.

## No Verifier can produce the evidence form the Change requires for this node's `[audit]` assertions

The Frame of Change [outcomeeng/changes#132](https://github.com/outcomeeng/changes/issues/132) requires this node to be Passing at merge. For each `[audit]` assertion, it names the evidence form as "an Agentic verdict recorded against that assertion's rule slug in the node's status claim". `agent-mail.md` carries three such assertions, at lines 37, 38, and 39. Each carries the pathless `[audit]` tag with no rule slug, which the Spec Tree foundation retains for a toolchain without slug support. The node carries no `spx.status.json`, and the repository tracks none anywhere in the tree. A verdict needs both a rule slug to key it and a status claim to hold it, and neither exists here.

**Impact**: no Verifier can produce a result in the required form, however its audit concludes. A current isolated verdict on each of the three assertions can exist only in another form, such as a sealed run or a recorded verdict outside the node. Such a verdict does not meet the evidence form the Frame names. The node's Passing requirement for its `[audit]` tags therefore cannot be met as written, and a merge that claims it rests on a form the Frame did not name.

**Settlement condition**: the Operator amends the Frame's evidence form for this node's `[audit]` assertions to one this toolchain can hold, or the toolchain adopts status claims and rule slugs, so that each assertion carries `[audit:{rule-slug}]` and the node's `spx.status.json` records a verdict keyed by that slug.

**Evidence**: the Frame's `Nodes` entry for `spx/43-coding-agents.enabler/18-agent-mail.enabler` in the Change record, read on 2026-09-28; lines 37–39 of `agent-mail.md`, each ending `([audit])`; `git ls-files` on head `6b7fb0a08c8add29460cba11b46aea5998921440`, which lists no `spx.status.json`, with the installed `@outcomeeng/spx` at 0.7.2.
