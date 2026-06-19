# Plan: collapse to generic artifact-type auditors composing language skills

Branch `feat/adr-audit-verifier-composition`. Governing decisions: `spx/14-verification.pdr.md` (root principle) and `spx/21-spec-tree.enabler/17-auditing.adr.md` (auditing architecture).

## Design (decided)

The verification isolation separates the **author context** (the context that produced the work under audit) from the **verifier context** — not one verifier from another. A dispatched auditor runs in verifier context and MAY compose other verification skills; no author bias is reintroduced. Therefore:

- The marketplace ships **generic artifact-type auditor agents only**: `adr`, `pdr`, `code`, `test` (the `/audit` orchestrator family covers code). No language-specific auditor agent exists.
- Language-specific concerns are composed by the generic auditor **invoking the language audit SKILL** (`audit-{lang}`, `audit-{lang}-architecture`, `audit-{lang}-tests`) by language partition, as `17-auditing.adr` already does for `/audit`.
- Section/voice/tag authority for ADRs/PDRs lives once, read from the canonical template (`21-templates.enabler` already forbids copying template content into skills); the language architecture audit drops its duplicated structure/voice/tag checks and carries language-only concerns (DI, no-mocking, level accuracy).

## Sequence (audit gate after each spec/structural step)

- [x] A1. Amend `spx/14-verification.pdr.md`: author≠verifier; verifier may compose (principle only — topology pushed to A2 per pdr-auditor). GATE: pdr-auditor APPROVED.
- [x] A2. Amend `spx/21-spec-tree.enabler/17-auditing.adr.md`: generic-only auditor agents, compose `audit-{lang}*` skills, template-authority. GATE: adr-auditor APPROVED.
- [x] A3. Amend `21-adr-auditing.enabler/adr-auditing.md`: audit-adr reads canonical template as sole structure authority + composes `audit-{lang}-architecture`. (pdr-auditing.md unchanged — PDRs are language-neutral.) Spec-lane validation green.
- [x] A4. Language specs (`spx/43-{python,typescript,rust}.enabler/*`): restated as composed-by-generic-auditor; no per-language auditor agent. Rust `unsafe`/FFI soundness folded into `audit-rust` (the `rust-unsafe-auditor` agent is removed in C; its unsafe-checker methodology moves into `audit-rust` as a reference/section). Spec-lane validation green.

Phase A committed as the spec layer (specs lead; agent removal + skill composition are downstream, tracked below).

- [ ] B1. Update shipped template `src/plugins/spec-tree/skills/understand/templates/spx-claude.md` Quick Reference tables: generic auditors only; bump template_version.
- [ ] B2. Re-render product `spx/CLAUDE.md`/`AGENTS.md` via `/update-spx`.
- [ ] C1. Remove language auditor agents: python/typescript/rust × {architecture,code,test} (+ resolve `rust-unsafe-auditor`).
- [ ] C2. Generic audit skills (`audit-adr`, `audit-tests`, `/audit` orchestrator) compose `audit-{lang}*` by partition.
- [ ] C3. `audit-{lang}*` skills: drop "dispatch the {lang}-auditor agent" dispatch_gate prose; `audit-{lang}-architecture` drops duplicated structure/voice/tag checks.
- [ ] C4. `architect-python` Phase 0: point at canonical template (understand skill), not `/author`.
- [ ] D. Fold in 16-verification conformance for surviving generic auditors: `tools: Bash, Read, Skill`, model field, `scripts/` arbiter, thread-store persistence, eval suites; build unbuilt `test_pdr_auditing` suites; update `spx/EXCLUDE`.
- [ ] E. `just build-skills`; marketplace catalogs; `just bump`; `develop:skill-auditor` on changed skills; `subagent-auditor` on changed agents; `just check`; `/merge`.

## Notes

- Removing shipped language auditor agents is a breaking change for consumers dispatching them by name — intended; the generic auditors + composed skills replace them.
- This folds the deferred "16-verification.enabler conformance for adr-auditor / pdr-auditor / test-evidence-auditor" item from `ISSUES.md` into the same change.
