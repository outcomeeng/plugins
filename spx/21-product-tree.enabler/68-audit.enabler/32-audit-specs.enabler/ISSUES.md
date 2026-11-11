# Issues: Audit Specs

## Three declared eval suites are unbuilt; their four scenarios carry interim `[audit]` tags

The `voice`, `tag-validity`, and `prose-coupling` suites were declared and never authored. Their four scenarios — temporal language → `temporal-voice`; bare, missing, or multiple tags → `invalid-tag`; a universal `[test]` claim tagged `scenario` → `evidence-type-mismatch`; a `[test]` tag on a prose-content claim → `prose-coupling` — carry `[audit]` as an explicit interim so no evidence link dangles. Their real verification type is evaluate: `/audit-specs` is an LLM-driven producer emitting a structured verdict a deterministic grader scores, which [`spx/15-spec-coverage.adr.md`](spx/15-spec-coverage.adr.md) routes to the eval lane. The interim tag was an operator decision (2026-09-07) taken with the pushback recorded that it weakens declared evidence to match implementation state.

**Resolution shape.** Either fold the four scenarios into the existing `evals/structure` suite as additional cases (one prompt, one history, one producer coupling; the suite may be renamed from `structure` to a name covering all four categories) and re-point the four links, or author the three suites as declared. Then run `just eval-node spx/21-product-tree.enabler/68-audit.enabler/32-audit-specs.enabler` at the default budget, commit the fresh `history.jsonl` rows, and restore `[eval](…)` tags. Do it after the verification-run migration (`outcomeeng/changes#327`) rewrites the producer's verdict contract, so run evidence is paid for once.

## The `structure` prompt re-materializes on every producer edit

`evals/structure/eval.toml` embeds `src/plugins/product-tree/skills/audit-specs/SKILL.md` verbatim through `prompt.template.md`, so every producer edit re-materializes `prompt.md` and leaves the committed `history.jsonl` rows scoring prompt content the suite no longer carries. Refresh run evidence in the same pass as the suite work above.

## Rename `/audit-specs` to `/audit-spec`

[`spx/14-skill-naming.pdr.md`](spx/14-skill-naming.pdr.md) names a workflow skill after the artifact one invocation judges. One `/audit-specs` invocation judges one spec node — the `spec-auditor` role task carries a single full node path — so the plural overstates the invocation's scope. The rename reaches further than the instructions-plugin renames that established the rule: the skill name is also this node's slug, directory, and spec filename, so it is `/refactor` work, and the producer is embedded verbatim in the `structure` prompt, so the rename re-materializes that prompt and invalidates its committed history rows. Do it in the same pass as the suite work above. Reconcile with the family-wide audit-skill concerns in `spx/21-product-tree.enabler/32-decisions.enabler/ISSUES.md`.

## The skill name is plural while one invocation judges one spec

[`spx/14-skill-naming.pdr.md`](spx/14-skill-naming.pdr.md) requires a workflow skill to name the artifact one
invocation judges, in the grammatical number that invocation handles. The skill's
own frontmatter judges "one enabler or outcome spec", its `argument-hint` is
`<node-spec-file-path>`, and its agent is `spec-auditor` — all singular. The skill
is named `audit-specs`.

File history shows the name reached its current form through the gerund-to-imperative
rename `auditing-specs` to `audit-specs`, which changed the verb form and carried the
plural across unexamined. No record decides the plural.

The sibling plurals are not the same case and stay as they are: `audit-tests` judges
a node's tests, several artifacts per invocation, and `audit-eval-evidence` takes a
mass noun.

**Why this is a separate larger concern.** The rename reaches seventeen source files
and is not a text sweep. It renames this product-tree node, which `/refactor` owns; it
moves the eval producer path this node's `evals/structure/eval.toml` and `prompt.md`
declare, requiring an eval re-run; it changes both generated root instruction blocks
through `just build-instructions`, whose pinned policy tuples assert literal substrings; it
changes both marketplace catalogs and the generated README catalog; it reaches
`src/plugins/instructions/skills/author-subagent/references/subagents.md`, which
carries its own plugin bump and `skill-auditor` gate; and it is a MINOR bump that
breaks `/audit-specs` invocation for every consumer.

**Resolution shape**: one changeset routing the node move through `/refactor`,
propagating the skill rename across both plugins, regenerating the
instruction blocks and README catalog, re-running this node's eval against the moved
producer path, and taking the MINOR bump with a `Breaking` changelog entry naming the
retired invocation.

**Evidence.** Surfaced by the plugin-wide skill-name review that `spx/local/skills.md`
requires of any material skill change, run during the `audit-implementation`
completion-contract repair.

## Eval run history is stale for the structure suite

The newest passing row for `evals/structure` (6/6, git SHA
`90bdeb9925e4a395269c6f3c7722f1fab0e86322`, 2026-07-13) predates nine commits to
the producer `src/plugins/product-tree/skills/audit-specs/SKILL.md` (new
`missing-assertions`, `missing-frontmatter`, and `unfalsifiable-assertion` rules;
a rewritten Step 3), a changed `prompt.template.md`, and the rematerialized
`prompt.md`, so no committed run proves the current producer, prompt, and case set.

**Settlement condition**: one passing run of
`just eval spx/21-product-tree.enabler/68-audit.enabler/32-audit-specs.enabler/evals/structure/eval.toml`
on a head that carries the current producer, with its row committed to
`history.jsonl`.

**Evidence**: `product-tree:eval-evidence-auditor` finding `f-005` on
head `a65659114b99767b90b4d920550fff5dc0824794` during Change #76, whose prototype boundary runs no eval.

## The shipped spec audit still produces the structured JSON verdict

The assertions state the sealed-run verdict model: the audit run's terminal status is `approved` or `rejected`, and the `spec-auditor` wrapper relays the run token, the run file and the rendered projection. `src/plugins/product-tree/skills/audit-specs/SKILL.md` and the wrapper still emit a plain verdict object with no run token or run file, so the `[eval]` expectations describe behavior the shipped producer does not yet have.

**Settlement condition.** outcomeeng/changes#513 rewrites the skill and wrapper onto one `spx verification run` over the spec file scope and migrates the producer-coupled eval expectations, under an unchanged semantic verdict model.

**Evidence**: current-head CI review of pull request 671.

## The spec audit judges the previous spec template form `src/plugins/product-tree/skills/audit-specs/SKILL.md` `group headings and tag routing` `consistency`

`src/plugins/product-tree/skills/audit-specs/SKILL.md` names the plural group headings `### Scenarios`, `### Mappings`, `### Conformance`, `### Properties`, and `### Compliance`, reports a verification-type heading such as `### Test`, `### Eval`, or `### Audit` as `heading-mismatch`, and treats a routed assertion as one that carries its tag. The spec templates write `### Mapping: <slug>`, `### <assertion type>: <subject>`, `### Eval: <slug>`, `### Probe`, and `### Audit`, and a spec rule carries no tag until its evidence exists. A spec written from the templates therefore draws `heading-mismatch` for its `### Eval:` and `### Audit` subsections.

The same previous form stands in the `align`, `audit-assertions`, `verify`, and `author` skills of the product-tree plugin.

**Why this is a separate larger concern.** The fix edits five skill surfaces. Each takes the `skill-auditor` gate and a plugin bump. The `audit-specs` producer is embedded verbatim in this node's `evals/structure` prompt, so an edit re-materializes the prompt and invalidates the committed run history, and the group-heading and tag side of `/verify` and the foundation grammar belongs to the Change that carries the grammar, outcomeeng/changes#904.

**Settlement condition.** The five skills describe the template form and the rule-tag rule, `/audit-specs` reports no `heading-mismatch` for a spec written from the shipped templates, and this node's `evals/structure` suite passes on a head that carries the amended producer.

**Evidence**: current-head CI review of pull request 734, head `2bdb0e1b90542c7434ccee972dedde2135bc4302`.
