# Issues: Audit Specs

Coordination note; not spec truth.

## Three declared eval suites are unbuilt; their four scenarios carry interim `[audit]` tags

The `voice`, `tag-validity`, and `prose-coupling` suites were declared and never authored. Their four scenarios — temporal language → `temporal-voice`; bare, missing, or multiple tags → `invalid-tag`; a universal `[test]` claim tagged `scenario` → `evidence-type-mismatch`; a `[test]` tag on a prose-content claim → `prose-coupling` — carry `[audit]` as an explicit interim so no evidence link dangles. Their real verification type is evaluate: `/audit-specs` is an LLM-driven producer emitting a structured verdict a deterministic grader scores, which `spx/15-spec-coverage.adr.md` routes to the eval lane. The interim tag was an operator decision (2026-09-07) taken with the pushback recorded that it weakens declared evidence to match implementation state.

**Resolution shape.** Either fold the four scenarios into the existing `evals/structure` suite as additional cases (one prompt, one history, one producer coupling; the suite may be renamed from `structure` to a name covering all four categories) and re-point the four links, or author the three suites as declared. Then run `just eval-node spx/21-spec-tree.enabler/68-audit.enabler/32-audit-specs.enabler` at the default budget, commit the fresh `history.jsonl` rows, and restore `[eval](…)` tags. Do it after the verification-run migration in `spx/21-spec-tree.enabler/68-audit.enabler/PLAN.md` rewrites the producer's verdict contract, so run evidence is paid for once.

## The `structure` prompt re-materializes on every producer edit

`evals/structure/eval.toml` embeds `src/plugins/spec-tree/skills/audit-specs/SKILL.md` verbatim through `prompt.template.md`, so every producer edit re-materializes `prompt.md` and leaves the committed `history.jsonl` rows scoring prompt content the suite no longer carries. Refresh run evidence in the same pass as the suite work above.

## Rename `/audit-specs` to `/audit-spec`

`spx/14-skill-naming.pdr.md` names a workflow skill after the artifact one invocation judges. One `/audit-specs` invocation judges one spec node — the `spec-auditor` role task carries a single full node path — so the plural overstates the invocation's scope. The rename reaches further than the instructions-plugin renames that established the rule: the skill name is also this node's slug, directory, and spec filename, so it is `/refactor` work, and the producer is embedded verbatim in the `structure` prompt, so the rename re-materializes that prompt and invalidates its committed history rows. Do it in the same pass as the suite work above. Reconcile with the family-wide audit-skill concerns in `spx/21-spec-tree.enabler/32-decisions.enabler/ISSUES.md`.
