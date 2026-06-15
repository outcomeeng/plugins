# Issues: Python Standards

## 1. Python skills use deprecated gerund names

The Python plugin's skills — `architecting-python`, `coding-python`,
`testing-python`, `standardizing-python`, and the auditing skills — use gerund
names. `spx/local/skills.md` declares that new skills use imperative form and
the marketplace is in a transition period; the skill auditor flags the gerund
names as a transition follow-up, not an immediate must-fix.

Required handling: rename the Python skills to imperative form when the
marketplace executes the gerund-to-imperative transition. This is a
marketplace-wide breaking change — every `/skill` invocation path,
`require_skill` directive, agent `skills:` field, catalog entry, and
cross-reference moves together — so it is sequenced as its own coordinated change
across all plugins, never folded into a single plugin's content work.

The marketplace-wide transition — naming scheme, full skill inventory (the nine
Python skills among them), mechanical recipe, breaking-change handling, and
sequencing against the queued `you`-voice sweeps — is planned at
`spx/43-develop.enabler/21-skills.enabler/PLAN.md`. The Python rename is the
subset tabled there; execute it as part of that coordinated transition, not on
its own.

Surfaced by the skill auditor during the Python-standards content hardening.
