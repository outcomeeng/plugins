# Issues: Decisions Enabler

## 16-verification.enabler conformance for audit-adr / audit-pdr (deferred)

`audit-adr` and `audit-pdr` (skills + agents) landed at SCOPE-MIN per `spx/21-spec-tree.enabler/32-decisions.enabler/PLAN.md` — the established read-only verdict-producer shape shared by the other spec-tree audit agents. They do NOT yet conform to `spx/21-spec-tree.enabler/16-verification.enabler`:

- The wrapper agents use `tools: Read, Glob, Grep` and no `model:` field; `16-verification.enabler` requires `model: sonnet` and `tools: Bash, Read, Skill`.
- No `scripts/` CLI arbiter module encodes the verification policy (schema conformance) for the wrapper agent to invoke; the verdict schema is described in skill prose.
- No thread-store persistence of the machine-readable result + markdown surface.
- The audit skills' LLM-judgment assertions carry forward-referenced `[eval]` (the new mode-floor scenarios) alongside pre-existing `[test]` scenarios in `pdr-auditing.md`; the full re-tag to `[eval]` and the eval suites themselves are unbuilt (both `21-adr-auditing.enabler` and `32-pdr-auditing.enabler` are in `spx/EXCLUDE`).

This conformance is an architecture migration that applies to the whole audit-skill family, not just these two, and is independent of the per-rule-evidence-mode feature. Address it as its own change: build the `scripts/` arbiter, reshape the audit agents to `model: sonnet` + `Bash, Read, Skill`, wire thread-store persistence, and build the eval suites. Until then, audit-adr/audit-pdr run as read-only verdict producers in the established pre-conformance pattern.
