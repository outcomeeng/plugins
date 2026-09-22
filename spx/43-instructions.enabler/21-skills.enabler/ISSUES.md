# Issues: Skill Authoring

Actionable findings from the post-merge skill audit of PR 458 at
`f5aa313016964a10854117e026ec4c3529106490`.

## Split router authority by workflow needs

`src/plugins/instructions/skills/create-skill/SKILL.md:5` grants `Bash`, `Write`,
`WebFetch`, and `WebSearch` to every route. Read-only audit and pattern-explanation
routes inherit mutation and network capabilities they do not use.

Required handling: narrow the router's top-level `allowed-tools` surface or split
routes whose authority requirements differ. Preserve the tools required by creation
and improvement workflows without granting them to read-only routes.

Source: skill-auditor finding `f-003`, rule `overbroad_allowed_tools`, severity
`WARNING`.

## Reconcile the auditor Bash capability contract

`src/plugins/instructions/skills/create-skill/templates/auditor-skill.md:5` now uses
`allowed-tools: Read, Grep, Glob, {{! tool('use_skill') !}}`. The post-merge audit requires `Bash` for
auditor command-based verification, while an earlier audit rejected bare `Bash` as
overbroad. `/skill-standards`'s command-capability rules also require command-specific
`Bash(<command>:*)` grants. A generic auditor template cannot select those commands
without knowing the generated auditor's workflow.

Required handling: decide whether every auditor requires `Bash`, define how a generic
template expresses least-privilege command grants, and align `/skill-standards`,
`/audit-skill`, and the auditor template so the same surface cannot be rejected both
for granting and omitting bare `Bash`.

Source: skill-auditor finding `f-004`, rule `read_only_audit_capabilities`, severity
`REJECT`, reconciled with the earlier `overbroad_allowed_tools` rejection.

## Revalidate after exercise-driven edits

`src/plugins/instructions/skills/create-skill/workflows/create-new-skill.md:79`
allows the representative exercise to trigger iterative edits after deterministic
checks and the skill audit have already completed. The final bundle can therefore
differ from the bundle those gates evaluated.

Required handling: run the representative exercise before final validation, or loop
every exercise-driven edit back through deterministic checks and the complete-bundle
skill audit before publication.

Source: PR 458 review comment `3610850053`, classified as `DEBT` in the `evidence`
category after merge.

## `/audit-skill` declares no target argument and no no-target edge case

`src/plugins/instructions/skills/audit-subagent/SKILL.md` declares
`arguments: configured_agent_path` and stops with `REJECTED` naming the missing
argument when that path is empty. Its sibling
`src/plugins/instructions/skills/audit-skill/SKILL.md` declares no `arguments`,
no `argument-hint`, and no `$ARGUMENTS`, and carries no matching edge case for a
dispatch that names no target.

The asymmetry has two effects. A direct `/audit-skill` invocation resolves its
target from surrounding conversation rather than a declared contract, which
`/skill-standards` `<skill_organization>` requires to stay independently
invocable. And a malformed dispatch that supplies no path has no defined stop,
so the audit proceeds against whatever the context suggests.

Required handling: declare the argument surface `audit-skill` actually takes —
the changed skill-surface paths plus governing nodes and verification state —
and add the no-target edge case its sibling already states. `/skill-standards`
`references/command-capabilities.md` carries both candidate forms: `arguments`
with a YAML name list for stable tokens, whose worked example is
`audit-subagent`'s own `configured_agent_path`, and `$ARGUMENTS` for whole-string
capture where multi-word intent must survive. Either choice also owes the
`argument-hint` the reference requires of every skill that takes arguments.

Source: `instructions:skill-auditor` findings `f-007` and `f-010`, severity
`WARNING`, on the changeset merged as PR 488.

## The composing-skill assertion awaits verification selection

The assertion under `## Assertions` in `skills.md` that a composing skill names each
static dependency through the shared `require_skill` directive, states an argument- or
run-time-named dependency as the owned `Use skill` sentence, and declares skill-use
capability through the optional `tool('use_skill')` token is an authoring declaration
with no tag; every other assertion in the file carries `[audit]`. It is the fifth
declaration of the optional-capability class, beside the four
`spx/18-plugin-build.enabler/ISSUES.md` records under "Optional tool-capability
rendering has no deterministic evidence yet".

**Impact.** The declaration is approved for form only; no evidence result attaches to
it until a verification type is selected and tagged.

**Settlement condition.** Verification is selected for the assertion — `[audit]`
through the skill auditor's composed-dependency rule in `skill-standards`, or a
`[test]` link once the authored-source compliance evidence Change #85 lands reaches
skill bodies — and the tag is applied.

**Evidence.** CI changeset review on PR #584, head
`b0a6237f359687bd40a01755af6f4ff2d88387b2`, finding `DEBT [evidence]` at
`spx/43-instructions.enabler/21-skills.enabler/skills.md:15`, during Change #76.

## `skill-standards` names the eager-foundation exception by a section that does not hold it

`src/plugins/instructions/skills/skill-standards/SKILL.md:14` (`<success_criteria>`
(a)) points to "the eager-foundation exception in `<progressive_disclosure>`", and
`<progressive_disclosure>` at lines 320 and 346 says "unless the eager-foundation
exception below applies", while the exception lives in its own
`<eager_foundation_exception>` tag at line 301, which precedes
`<progressive_disclosure>`.

**Impact.** An author following the tag-by-name convention this skill prescribes
lands on a section that does not hold the rule.

**Settlement condition.** `<success_criteria>` names `<eager_foundation_exception>`
and both `<progressive_disclosure>` branches drop "below".

Source: `instructions:skill-auditor` finding rule `stale_cross_reference`, severity
`WARNING`, on head `524b9c46c7960a106d84ef856b4020a0ce904b16` during Change #76;
[Change #92](https://github.com/outcomeeng/changes/issues/92) carries the
standards-skill pass that owns it.

## The Claude render of `skill-standards` sits 930 code points under the eager-payload ceiling

`dist/claude/instructions/skills/skill-standards/SKILL.md` measures 39070 code
points against the 40,000-code-point ceiling `skill-standards`
`<eager_foundation_exception>` declares for itself.

**Impact.** The next small edit to a Claude-only section tips the reference past
the ceiling and turns a routine change into a must-fix on this reference.

**Settlement condition.** Conditional detail leaves the eager body for its
reference — the `<context>` bash-block constraints at lines 274-280, already
carried by `references/command-capabilities.md` `<dynamic_context>`, are one
candidate — so a routine edit has room.

Source: `instructions:skill-auditor` finding rule `eager_payload_headroom`, severity
`WARNING`, on head `524b9c46c7960a106d84ef856b4020a0ce904b16` during Change #76;
[Change #92](https://github.com/outcomeeng/changes/issues/92) carries the
standards-skill pass that owns it.

## `script-standards.md` states the testing-record requirement with a weak modal

`src/plugins/instructions/skills/skill-standards/references/script-standards.md:32`,
inside `<script_testing_rule>`, reads "The skill's documentation should record what
was tested and with what inputs"; `/agent-prompt-standards` `<constraint_language>`
bars "should" from a rule block.

**Impact.** The testing-record requirement reads as optional beside the preceding
"must be tested" sentence.

**Settlement condition.** The sentence reads "records what was tested and with what
inputs".

Source: `instructions:skill-auditor` finding rule `weak_modal_in_rule`, severity
`WARNING`, on head `524b9c46c7960a106d84ef856b4020a0ce904b16` during Change #76;
[Change #92](https://github.com/outcomeeng/changes/issues/92) carries the
standards-skill pass that owns it.

## The skill auditor returns opposite verdicts on unchanged skill text

`instructions:skill-auditor` ran against `src/plugins/coding-agents/skills/orchestrate-officers/`
on two consecutive heads and reversed itself in both directions.

On head `08d4ef11a7085974f27e3cf58afe92942cde066c` it raised finding `f-007`, rule
`unverified_allow_list_match`, severity `WARNING`, against `SKILL.md` line 6: the `allowed-tools`
entry spells `${CLAUDE_SKILL_DIR}` inside a permission pattern, and whether that pattern matches
the command the loader issues is unestablished. On head
`387ba22d437193295ddd3287e449732ca52d7a96` it reported the same line as keep-these finding `f-003`,
rule `narrow_allowed_tools`, severity `INFO`, stating the grant satisfies `/skill-standards`
`references/command-capabilities.md` `<tool_restriction_security>`. The line is byte-identical
across the two heads: `git diff` between them over that file has no hunk before line 13, and
line 6 hashes to `67d58e26697f8a475031b50628f88ad7937c9c78f16c647d6dd000058971cbc4` at both.

The reversal runs the other way in the same pair. On the first head, keep-these finding `f-002`
praised the `<essential_principles>` result-acceptance contract for naming exact proof fields —
`response.result` against `response.output`, and the non-empty `projectKey`/`response`/`data` set —
as satisfying `/skill-standards` `<conciseness>` concrete-over-abstract, and stated that removing it
would leave every workflow's validation instruction pointing at nothing. On the second head,
finding `f-008`, rule `restated_dependency_contract`, severity `WARNING`, raised that restatement as
a defect and asked for its replacement by a citation to the owning capability skill. That passage is
not byte-identical between the heads: the second head rewrites the framing sentence to scope the
rule to a result reporting a store or environment command, and adds a paragraph carving out the
agent-mail project-key answer as the one result the rule does not govern. What does not change is
the restatement itself — every proof field `f-002` named survives verbatim, moving only from lines
43-47 to lines 39-44. `f-008` targets the presence of those fields, which is what `f-002` said the
skill would be worse without.

The auditor's own rule vocabulary is unbounded, which is what lets the two readings coexist. Its
`<verdict_format>` types the `rule` field as a free-form `<strength-name>` or `<issue-name>`
placeholder, and `src/plugins/instructions/skills/audit-skill/SKILL.md` fixes only
`configuration_issue`, `actor_or_activity_objective`, and `auditor_skeleton_violation`. None of
`unverified_allow_list_match`, `narrow_allowed_tools`, or `restated_dependency_contract` appears
anywhere under `src/plugins/` or `dist/`, so each run mints the slug it judges under and nothing
binds one run's classification of a line to the next run's.

**Impact.** `src/plugins/instructions/skills/audit-skill/SKILL.md` `<success_criteria>` states "The
same SKILL.md yields the same verdict"; these two runs falsify that criterion on its own subject.
Convergence requires a verdict to be a function of its subject. Where the same Verifier definition
returns opposite judgments on unchanged input, repair chases noise, and a changeset cannot converge,
because the next round raises what this one blessed and dropping a finding as unbacked is
indistinguishable from dropping a finding the next round will restore. It also makes the
finding-disposition rule in `spx/15-merging.pdr.md` undecidable for this auditor: a finding whose
severity is unstable across runs on unchanged text carries no `blocking`-versus-`debt` reading to
act on, and the repeated-class invalidation rule in the same decision reads a re-raised reversal as
a failed repair invariant when no repair was owed.

**Settlement condition.** Two runs of `instructions:skill-auditor` against one unchanged skill
surface return the same rule and severity for every line both judge. Reaching that needs the rule
vocabulary bounded — `/skill-standards` owning the enumerated rule slugs `/audit-skill` may emit,
which is what the node assertion requiring `/skill-standards` to own every rule `/audit-skill`
enforces already declares — so a line cannot be classified under a slug minted for one run.

**Related.** `spx/ISSUES.md` records three adjacent Verifier-judgment problems; this is the fourth
and the first where one auditor definition contradicts itself on unchanged input, rather than two
Verifiers disagreeing or one raising an unactionable finding. "Auditors read a conforming absent
`<failure_modes>` section as a gap" is the same auditor raising a finding no edit satisfies; this
entry is the stronger claim, because there the finding was at least stable across runs. "Two
verifier rules collide on pinning a spec-declared tuning value", and "Two verifier rules collide on
naming the evidence location in a shipped skill" in
`spx/43-coding-agents.enabler/18-agent-mail.enabler/ISSUES.md`, each record two different Verifiers
reading two decisions to opposite verdicts — resolvable by amending one decision, which a
self-contradiction is not. "A skill-directory token inside an `allowed-tools` pattern may never
match" in `spx/ISSUES.md` is opened by `f-007`, the first half of the reversal above; its settlement
condition rests on an executed invocation rather than an auditor verdict, and the `f-003` reversal
neither answers nor closes it.
