# Issues

## DEBT [criterion]: the hosted-runner rule names no criterion for when a skill presents the hosted form

Defect class: `criterion`.

Finding: the first audit rule under `### Audit` in `spx/15-agent-tools.pdr.md` requires command forms for "hosted programmatic runners such as GitHub Actions when relevant". The qualifier "when relevant" states no criterion, while product property 1 scopes tool guidance to hosted programmatic runners without it.

Evidence: `spec-tree:pdr-auditor` on `spx/15-agent-tools.pdr.md` at head `dd1e5e3f5c124f29669422e6f0632120d2d8e9fd` returned finding rule `invalid-tag`, severity `WARNING`, against `Verification > Audit` rule 1 (the first audit rule). The Change that added the page-bound rule to the same file leaves the qualifier unchanged, because the qualifier belongs to older decision text and the criterion is a product judgment.

Impact: two Auditors can reach opposite verdicts on whether a skill that instructs a `gh` or `spx` call must present the hosted-runner form.

Revisit and settlement condition: the rule states the criterion under which a skill presents the hosted-runner form, or drops the qualifier to match product property 1; one `spec-tree:pdr-auditor` run over `spx/15-agent-tools.pdr.md` then raises no `invalid-tag` finding against it.
