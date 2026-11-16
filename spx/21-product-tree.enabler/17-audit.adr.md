# Audit

CONSTRAINS implementation audit and the marketplace's other auditor agents
TO one product-tree `implementation-auditor` wrapper that runs the audit skills the artifact registry selects inside one isolated verifier context, and one artifact-type auditor for each other artifact type
SO THAT every changed path is either audited by the skill its registered artifact names or recorded as left to another auditor, in one sealed run

## Verification

### Audit: declaration form

- declaration-form: Declaration audits read each row's verification type from its group heading and its name from its leading slug, from the artifact itself, without requiring a caller identity or phase argument.
- row-checks: Declaration audits check every row for its applicable declaration-quality rules, check a row whose slug links its evidence also for evidence fit, and find a tag on a row a defect.
- approval-not-evidence: Approval of a row that links no evidence establishes neither evidence completeness, implementation correctness, nor Passing state.
- template-judged-structure: Section structure, atemporal voice, and group-heading validity for a decision record are judged by the artifact-type auditor reading the canonical decision template; the composed `audit-{lang}-architecture` skill carries only language-specific concerns.
- no-template-copy: No audit skill judges decision-record section structure, voice, or group-heading validity from a transcribed copy of the canonical template, because the copy drifts from and contradicts the template.

### Audit: auditor agents

- one-implementation-wrapper: The product-tree plugin ships one implementation-audit wrapper agent, `implementation-auditor`, and no other.
- artifact-type-auditors: Every auditor agent is generic and artifact-type-scoped, never language-scoped — the one product-tree-owned `implementation-auditor` composes the per-language implementation code, test, and architecture skills, and every other artifact type is covered by a single artifact-type auditor owned by the plugin that governs that artifact type; language audits ship as skills with no language-specific auditor agent.
- one-verifier-context: The `implementation-auditor` runs all implementation concern composition inside its one isolated verifier context because the main conversation agent launches only one subagent level.
- composing-auditors: `adr-auditor` composes the `audit-{lang}-architecture` skills and `test-evidence-auditor` composes the `audit-{lang}-test` skills for the language-specific concerns of the artifact each audits.
- no-language-auditor-agents: No language-specific auditor agent (`{lang}-architecture-auditor`, `{lang}-code-auditor`, `{lang}-test-auditor`) exists; language concerns reach an audit through skills composed inside the `implementation-auditor`.
- no-per-language-orchestrators: No plugin ships a per-language audit-orchestration agent such as `typescript-audit-orchestrator`; the implementation-auditor context serves every language by skill dispatch.
- language-audit-skills: Every marketplace plugin that ships an `author-{lang}-code` skill ships `audit-{lang}-code`, `audit-{lang}-test`, and `audit-{lang}-architecture` skills.
- skills-reach-policy: Audit wrapper agents reach audit policy and the audit verification run only by invoking audit skills; review agents reach review policy and the review journal only by invoking the `review-changes` skill.
- dispatch-wrapper-only: The main conversation reaches an implementation audit only by dispatching the `implementation-auditor` wrapper agent — the dispatched agent's isolated context produces the verdict, per `dispatch-to-separate-verifier` in [`spx/31-outcomeeng.enabler/31-verification.enabler/14-verification.pdr.md`](spx/31-outcomeeng.enabler/31-verification.enabler/14-verification.pdr.md).
- no-in-place-skill: The main conversation never invokes an implementation-audit skill in place to produce a verdict; an audit runs in the isolated wrapper-agent context.

### Audit: wrapper and orchestration content

- wrapper-no-language-tokens: The implementation-audit wrapper agent contains zero language-specific tokens beyond the dispatch template `audit-{lang}-{code|test|architecture}`.
- no-language-content: Implementation-audit orchestration and the audit wrapper agents carry no language-specific examples, file extensions, validation commands, test commands, or evidence patterns; that content belongs in the corresponding `audit-{lang}-{code|test|architecture}` skill.
- no-wrapper-pipelines: The wrapper agent prompts embed no deterministic shell pipelines (git diff, base-ref detection, scope partitioning); the implementation-audit orchestration skill prose owns these pipelines.
- no-agent-scripts-path: No agent prompt references `scripts/` by `${CLAUDE_PLUGIN_ROOT}`, `${CLAUDE_SKILL_DIR}`, or a hard-coded relative path, because neither variable is substituted in an agent prompt body.
- no-skill-self-description: No `audit-{lang}-{code|test|architecture}` skill carries a per-skill self-description block declaring file globs, configs, gate commands, or test commands; the dispatch contract is the skill name.
- no-plugin-root-helper: The consumer-side projection helper sits under the consuming skill, never at a plugin-root location.
- registry-not-copied: Neither the implementation audit's orchestration nor its wrapper agent carries its own copy of the artifact kind list; each reads the rendered registry.
- run-driver-identity: The `implementation-auditor` supplies its run-driver producer identity as explicit request data; `audit-implementation` accepts that identity generically and never names, detects, or otherwise depends on the agent, skill, or context that invokes it.

### Audit: orchestration behavior

- registry-selection: Orchestration dispatches the audit skills the scope resolver selected by matching each changed path, an advisory audit's live paths included, against the rendered artifact registry, most specific match within a kind and kinds in declaration order, and dispatches only the selected skills that follow the concern contract; it never selects from the installed inventory or invents an artifact for an unmatched path.
- scope-passed-unchanged: Implementation-audit orchestration passes the supplied scope unchanged to each selected skill that follows the concern contract, aggregates their projections, and records one audit verification run.
- missing-skill-unit: A registry-selected concern skill absent from the installed inventory is a required `missing-skill` unit naming that skill.
- no-deterministic-runs: Implementation-audit orchestration runs none of the project's validation or test commands, nor any other deterministic verification; it dispatches only the agentic concern audits, the main agent having passed deterministic verification on the changeset before dispatch and CI re-running validate and test over the CI scope, under `no-deterministic-in-agentic` in [`spx/31-outcomeeng.enabler/31-verification.enabler/14-verification.pdr.md`](spx/31-outcomeeng.enabler/31-verification.enabler/14-verification.pdr.md).
- shared-run-journal: Audit consumes the shared agentic-verification run journal and projection that [`spx/21-product-tree.enabler/16-verification.enabler/13-run-journal.adr.md`](spx/21-product-tree.enabler/16-verification.enabler/13-run-journal.adr.md) governs, and owns none of its storage, backend selection, event ordering, streaming, sealing, projection rendering, wrapper-agent shape, or changeset-scope derivation.
- eval-evidence-separate: Eval-evidence audits run in a separate artifact-type auditor, never as a fourth implementation-audit phase.

### Audit: run accounting

- inventory-equality: A sealed implementation-audit run's recorded path subjects equal the changed-path inventory its own start input carries, so a reader establishes the inspection's completeness from the run rather than from the run driver's account of it.
- coverage-gap-records: Orchestration records every resolved path no registered artifact matched, every matched path whose selected skill returned not applicable, and every path whose registered artifact's audit skill follows another contract, as an accounting record — an optional, skipped coverage-gap unit — that names the audit skill of a registered artifact which follows another contract.
- self-reconciliation: Implementation-audit reconciliation compares the run against the inventory its own start input sealed, and runs as a bundled command whose exit code carries the verdict.
- no-gap-partition: An accounting record for an unclaimed path carries no language partition, required coverage requirement, or final coverage status; it records that the path was considered and left to another auditor, never that it was audited.
