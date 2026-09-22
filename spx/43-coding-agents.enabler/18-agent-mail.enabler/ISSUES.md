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
