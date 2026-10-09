# Issues: Subagent Authoring

Known defects in the subagent cluster. Coordination note; not spec truth.

## Auditor model policy does not account for the prose strong-model assignment

`src/plugins/prose/agents/prose-auditor.md` selects the central Strong profile.
The shared policy selects Standard by default and permits an explicitly governed
Strong selection; it supplies no role-specific justification. The prose node owns the
unresolved justification for that exception:
`spx/43-prose.enabler/ISSUES.md`, under "Strong model selection for prose auditing
has no recorded justification".

**Required handling.** During the model-selection rules' migration into
`/subagent-standards`, reconcile the general auditor rule with the prose node's
decision. Preserve Standard by default and explicitly governed Strong selection,
then align authoring guidance,
audit enforcement, and both agent-harness outputs. Do not infer a justified
exception from an existing generated model selection.

**Disposition and revisit condition.** Tracked at the operator's request. Resolve
alongside the prose node's model-tier decision and before treating the shared
auditor model policy as settled.

## The auditor skeleton's worked example states its categories in a second sentence

`src/plugins/instructions/skills/audit-subagent/SKILL.md` and
`src/plugins/instructions/skills/audit-skill/SKILL.md` each state their sealed-run
verdict and its finding shape in one sentence whose em-dash clause names them.
The ADR example in `/skill-standards` `references/auditor-skeleton.md` still names
its finding categories in a second sentence.

Successive `instructions:skill-auditor` runs read the earlier two-sentence
`audit-subagent` objective differently. One run
flagged the shortened objective and required the categories be named; a later run
accepted the categories and flagged the second sentence. The two governing
references model the shape differently. `/skill-standards`
`references/auditor-skeleton.md` requires `<objective>` to carry the finding
categories, and its worked example states them in a second sentence.
`/agent-prompt-standards` `<objective_shape>` holds an objective to one sentence,
reaching for a second only when the output has two distinct parts, and gives the
canonical auditor shape as a single sentence whose em-dash clause names the
categories. Naming categories is settled; whether they form a second part is not.

Required handling: decide once whether an auditor's finding-category clause is a
distinct output part or a subordinate clause, record it so `<objective_shape>`
and the skeleton's worked example stop modelling opposite shapes, and bring the
auditor objectives onto the chosen shape.

Source: `instructions:skill-auditor` finding `f-009`, severity `WARNING`, on the
changeset merged as PR 488, reconciled against an earlier run's opposing finding.

## The model-reproducibility rule belongs in `/subagent-standards`

`/subagent-standards` owns model selection, so the canonical rule belongs in it: a
subagent that produces a verification verdict never inherits its model from the invoking
context, because a verdict a later invocation cannot reproduce is not evidence. Its
`[test]` evidence follows the structural-constraint shape
`spx/15-validation.enabler/32-hook-safety.enabler` uses — a source-owned validator
exercised against violating cases, never a scan asserting this repository's own files
comply, which would be the second declaration [`spx/12-shipped-scripting.adr.md`](spx/12-shipped-scripting.adr.md) forbids.
`outcomeeng/distribution/profiles.py` owns complete native configurations for all
roles, with Standard as the default. `outcomeeng/distribution/agents.py` rejects
independent native fields, and the source guard checks authored assignments
throughout `src/`. The remaining work is to make `/subagent-standards` own this
authoring rule and obtain independent evidence and standards audits.

## The `invocation-scope` eval suite is unbuilt; its assertion carries an interim `[audit]` tag

The per-invocation-scope assertion — `/audit-subagent` judges exactly one configuration
per invocation — carries `[audit]` as an explicit interim so no evidence link dangles.
Its real verification type is evaluate: `/audit-subagent` is an LLM-driven producer
emitting a structured verdict whose `target` a grader scores, which
[`spx/15-spec-coverage.adr.md`](spx/15-spec-coverage.adr.md) sends to the eval lane. The interim tag was an operator
decision (2026-09-07). `spx/43-instructions.enabler/ISSUES.md` entry 4 records the
matching gap for `/audit-skill`; both auditors need the instructions plugin's first eval
suite. Author `evals/invocation-scope/` (producer
`src/plugins/instructions/skills/audit-subagent/SKILL.md`, `plugin_dir`
`dist/claude/instructions`, cases for one configuration versus several), regenerate the
eval CI triggers with `just build-eval-triggers`, run it at the default budget, and
restore the `[eval](evals/invocation-scope/eval.toml)` tag once it passes.

## The governing-context rule speaks spec-tree vocabulary the instructions plugin does not define

**Evidence:** `instructions:skill-auditor` finding `f-008` (WARNING) on
`src/plugins/instructions/skills/subagent-standards/SKILL.md` at head
`195826dfdd0480c08f9cfacf48a20999317fea6e`: the rule that resolves a definition's
governing context — the owning node as the node whose linked test or audit assertion
names the definition, and a declaration as an assertion in that node's spec or a decision
on the path from the root that reaches it by index — uses vocabulary the `instructions`
plugin neither defines nor loads.

**Impact:** a repository that installs `instructions` without a spec tree resolves no
governing context, so `/audit-subagent` reports every inheriting definition as declaring
nothing. That is the standard's stated result for an undeclared boundary, so the verdict is
not spurious, but the rule names no methodology and states no non-applicability.

**Settlement condition:** the standard names the methodology its resolution rule assumes,
or states how a definition with no governing spec tree is judged, and one typed skill audit
approves the wording. Deferred as a product-design question outside the changeset that
amended the rule: the Change that amended it settled where a declaration lives, not how a
tree-less consumer reads the rule.

## The marketplace's own definitions carry no inheritance declaration

**Evidence:** `spec-tree:changes-reviewer` finding `F-001` (debt, consistency) in review
run `2026-09-21_15-38-19-791-ab0ae6d854aa`, subject
`src/plugins/instructions/agents/subagent-auditor.md`. The Claude rendering of
`subagent-auditor` carries `tools` and no `permissionMode`, the shape that inherits the
invoking session's execution policy, and no assertion under `spx/` names
`subagent-auditor`, `skill-auditor`, or any `src/plugins/spec-tree/agents/*.md` wrapper —
the verification node names those wrappers only by directory — so no owning node resolves
for them and none declares their inheritance.

**Independence:** the gap predates the strengthened admission rule and is not caused by it.
Those definitions have always inherited the session's execution policy and their owning
nodes have never named them; the rule made an existing silence legible rather than
creating it. Closing it means adding an assertion, with linked evidence, to the owning node
of every shipped definition across the instructions and spec-tree trees — a changeset whose
coherence is those trees' specs, not this standard.

**Settlement condition:** a Change adds, for each inheriting definition, the owning node's
assertion that names it and declares its execution-policy inheritance with linked evidence,
and this node's spec records that the declarations exist. Scheduled as
<https://github.com/outcomeeng/changes/issues/128>.

## The two instructions auditors carry no retained release-acceptance evidence

**Evidence:** `instructions:subagent-auditor` finding `f-002`, severity `REJECT`, on
`src/plugins/instructions/agents/skill-auditor.md` and on
`src/plugins/instructions/agents/subagent-auditor.md` at head
`add3e3e862f7512a55e8b9655d07f78412abe87c`: [`spx/15-subagent-execution.pdr.md`](spx/15-subagent-execution.pdr.md) declares per-harness, per-profile release
acceptance — native loading and one minimal isolated execution for every profile — and the
tree retains no acceptance artifact for the Claude or the Codex Standard row either
definition selects, and no exact-definition minimal isolated invocation of either. The
same runs raised `f-001`, the undeclared execution-policy inheritance the entry above
records for every marketplace definition.

**Impact:** nothing in the tree shows either emitted definition loading natively and
returning its run token and projection; the Codex Standard configuration of both has no
execution evidence.

**Settlement condition:** the release retains passing Standard-profile acceptance rows for
both harnesses at a location the auditor reads, or an exact-definition minimal isolated
invocation of each definition, and one `subagent-auditor` run on each definition raises no
`f-002` class finding.

## The instructions auditors' descriptions read as launch triggers

**Evidence:** `instructions:subagent-auditor` warning `f-003` (rule
`description-invites-inferred-launch`) on `src/plugins/instructions/agents/skill-auditor.md`
lines 3-5 at head `8e631614b562ec5edf05c0e4c80a38625ada90d7`: the description is directive task-pattern wording ("ALWAYS invoke
when auditing, reviewing, or evaluating SKILL.md files ..."), while `/subagent-standards`
`<invocation>` bars turning a description or task pattern into a launch request.
`src/plugins/instructions/agents/subagent-auditor.md` carries the same form.

**Impact:** the wording invites a launch on user phrasing rather than on an active skill's
explicit instruction.

**Settlement condition:** both descriptions state the role and the calling-skill condition
in passive form, and one `subagent-auditor` run on each raises no such finding.
