# Issues

## The shipped PDR audit still produces the structured JSON verdict

The assertions state the sealed-run verdict model: the audit run's terminal status is `approved` or `rejected`, and the `pdr-auditor` wrapper relays the run token, the run file and the rendered projection. The shipped `src/plugins/product-tree/skills/audit-pdr/SKILL.md` and the `pdr-auditor` wrapper still emit the `<verdict_format>` JSON object with an `overall` field and no run token or run file, so the `[eval]` expectations and the `[audit]` run-recording assertion describe behavior the shipped producer does not yet have.

**Settlement condition.** outcomeeng/changes#513 rewrites the skill and wrapper onto one `spx verification run` over the PDR file scope and migrates the producer-coupled eval expectations, under an unchanged semantic verdict model.

**Evidence**: current-head CI review of pull request 671, which reads the skill and finds no run token or run file.
