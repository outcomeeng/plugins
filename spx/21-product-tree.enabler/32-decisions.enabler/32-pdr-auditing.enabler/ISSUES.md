# Issues

## The shipped PDR audit still produces the structured JSON verdict

The assertions state the sealed-run verdict model: the audit run's terminal status is `approved` or `rejected`, and the `pdr-auditor` wrapper relays the run token, the run file and the rendered projection. The shipped `src/plugins/product-tree/skills/audit-pdr/SKILL.md` and the `pdr-auditor` wrapper still emit the `<verdict_format>` JSON object with an `overall` field and no run token or run file, so the `[eval]` expectations and the `[audit]` run-recording assertion describe behavior the shipped producer does not yet have.

**Settlement condition.** outcomeeng/changes#513 rewrites the skill and wrapper onto one `spx verification run` over the PDR file scope and migrates the producer-coupled eval expectations, under an unchanged semantic verdict model.

**Evidence**: current-head CI review of pull request 671, which reads the skill and finds no run token or run file.

## The shipped PDR audit loads context through `/contextualize`

The compliance rule that loads the PDR's context read-only never invokes `/contextualize` or `/sync-base`. `src/plugins/product-tree/skills/audit-pdr/SKILL.md` Step 1 still reads "use skill `product-tree:contextualize` on the directory containing the PDR", and `/contextualize` runs `/sync-base`, which rebases the audited branch, so the skill contradicts the rule.

**Settlement condition.** The skill loads the PDR context through the read-only procedure the rule states, without `/contextualize` or `/sync-base`, matching the settlement of the entry in `spx/21-product-tree.enabler/18-context-loading.enabler/ISSUES.md`; outcomeeng/changes#513 carries the rewrite.

**Evidence**: current-head CI review of pull request 671, `src/plugins/product-tree/skills/audit-pdr/SKILL.md:51`. The same gap for the test-evidence audit is recorded in `spx/21-product-tree.enabler/68-audit.enabler/32-audit-tests.enabler/ISSUES.md`.
