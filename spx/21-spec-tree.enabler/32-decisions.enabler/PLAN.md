# Plan: collapse to generic artifact-type auditors composing language skills

Branch `feat/adr-audit-verifier-composition`. Governing decisions: `spx/14-verification.pdr.md` (root principle) and `spx/21-spec-tree.enabler/17-auditing.adr.md` (auditing architecture).

## Design (decided)

The verification isolation separates the **author context** (the context that produced the work under audit) from the **verifier context** — not one verifier from another. A dispatched auditor runs in verifier context and MAY compose other verification skills; no author bias is reintroduced. Therefore:

- The marketplace ships **generic artifact-type auditor agents only**: `adr`, `pdr`, `code`, `test` (the `/audit` orchestrator family covers code). No language-specific auditor agent exists.
- Language-specific concerns are composed by the generic auditor **invoking the language audit SKILL** (`audit-{lang}`, `audit-{lang}-architecture`, `audit-{lang}-tests`) by language partition, as `17-auditing.adr` already does for `/audit`.
- Section/voice/tag authority for ADRs/PDRs lives once, read from the canonical template (`21-templates.enabler` already forbids copying template content into skills); the language architecture audit drops its duplicated structure/voice/tag checks and carries language-only concerns (DI, no-mocking, level accuracy).

## Staging (decided)

Two PRs, each internally coherent with no behavioral regression. The PR-1 description below matches what PR 1 actually ships — the composition *mechanism* is PR-2 work, not PR-1.

- **PR 1 (this branch `feat/adr-audit-verifier-composition`)** — the spec foundation (Phase A: `verification.pdr` author≠verifier principle reconciled with the merged verification-ownership contract, `17-auditing.adr` collapse architecture, `adr-auditing.md`, the three language specs) **plus one composition increment**: `audit-adr` reads the canonical ADR template for section structure and drops a structural finding that contradicts it. The composition *mechanism* (generic auditors invoking `audit-{lang}*` skills) is NOT in PR 1 — the `17-auditing.adr` composition assertions lead implementation and are satisfied in PR 2 (future product truth, tracked here). spec-tree bumped to 0.59.9.
- **PR 2** — the composition mechanism and the agent collapse together (indivisible; landing the agent removals alone would regress language-specific auditing):
  - Generic `audit-adr` / `audit-tests` / `audit` skills compose the matching `audit-{lang}*` skill by language partition; **add `Skill` to those skills' `allowed-tools` and to `adr-auditor` / `test-evidence-auditor` `tools`** (the allowlist update the spec's composition assertions require).
  - Simplify each `audit-{lang}-architecture` skill to language-only concerns (defer section structure, atemporal voice, and tag validity to the composing auditor), updating its dispatch-gate, process, and verdict schema together.
  - Remove the 10 redundant language auditor agents; render `spx-claude.md` to generic-only (template_version 0.19.0); salvage the `rust-unsafe-auditor` unsafe-checker methodology into `audit-rust`.
  - Complete the 16-verification conformance for the surviving generic auditors (`tools: Bash, Read, Skill`, `scripts/` arbiters, thread-store persistence, eval suites).

  PR-2 WIP is durably preserved as branch refs `wip/composition-partial` (partial audit-adr Step 5b + adr-auditor `Skill` tool + python-arch gate) and `wip/pr2-agent-removal-template` (the 10 agent removals + template render), with `.wip.patch` backstops in `/tmp/pr2-wip-backstop/`.

The committed spec foundation declares the PR-2 end state (no language auditor agents, composition active); that is future product truth leading implementation, with this PLAN recording the downstream PR-2 work.

## Sequence (audit gate after each spec/structural step)

- [x] A1. Amend `spx/14-verification.pdr.md`: author≠verifier; verifier may compose (principle only — topology pushed to A2 per pdr-auditor). GATE: pdr-auditor APPROVED.
- [x] A2. Amend `spx/21-spec-tree.enabler/17-auditing.adr.md`: generic-only auditor agents, compose `audit-{lang}*` skills, template-authority. GATE: adr-auditor APPROVED.
- [x] A3. Amend `21-adr-auditing.enabler/adr-auditing.md`: audit-adr reads canonical template as sole structure authority + composes `audit-{lang}-architecture`. (pdr-auditing.md unchanged — PDRs are language-neutral.) Spec-lane validation green.
- [x] A4. Language specs (`spx/43-{python,typescript,rust}.enabler/*`): restated as composed-by-generic-auditor; no per-language auditor agent. Rust `unsafe`/FFI soundness folded into `audit-rust` (the `rust-unsafe-auditor` agent is removed in C; its unsafe-checker methodology moves into `audit-rust` as a reference/section). Spec-lane validation green.

Phase A committed as the spec layer (specs lead; agent removal + skill composition are downstream, tracked below).

- [ ] B1. Update shipped template `src/plugins/spec-tree/skills/understand/templates/spx-claude.md` Quick Reference tables: generic auditors only; bump template_version.
- [ ] B2. Reconcile the doc surfaces that still reference the language auditor agents the committed spec now forbids (each contradicts `17-auditing.adr` until PR 2 lands — spec leads, tracked here):
  - Re-render product `spx/CLAUDE.md` (spx guide) via `/update-spx`.
  - Hand-update the **root `AGENTS.md`** "When to Dispatch Agents vs Invoke Skills" dispatch table (the per-language `audit-{lang}*` → `{lang}-*-auditor` rows) — `/update-spx` does NOT touch the root `AGENTS.md`.
  - Regenerate the README plugin catalog (`just docs`) after the agents are removed.
  - Update `develop/skills/create-subagents/references/subagents.md` examples that use `typescript-code-auditor` (a removed agent) as a sample.
- [ ] C1. Remove language auditor agents: python/typescript/rust × {architecture,code,test} (+ resolve `rust-unsafe-auditor`). Salvage the `rust-unsafe-auditor` unsafe/FFI soundness methodology (rule IDs `ptr-*`, `ffi-*`, SAFETY-comment enforcement, UB categories — aliasing, lifetimes, validity invariants, panic safety) into `audit-rust`. The committed `spx/43-rust.enabler/rust.md` line-19 assertion is the present-tense contract this salvage implements; it is intentionally spec-leading (atemporal voice, no "will pass" hedge) and currently unmet until C1 lands.
- [~] C2. Generic audit skills compose `audit-{lang}*` by partition, AND add `Skill` to `audit-adr`/`audit-tests`/`audit` `allowed-tools` and to `adr-auditor`/`test-evidence-auditor` `tools` (composition is unexecutable without it). Partial: `audit-adr` already reads the canonical ADR template for section structure (shipped in PR 1, commit on this branch); the invoke-the-language-skill step + the tool-allowlist update remain for PR 2.
- [ ] C3. `audit-{lang}*` skills: drop "dispatch the {lang}-auditor agent" dispatch_gate prose; `audit-{lang}-architecture` drops duplicated structure/voice/tag checks (defer to the composing `adr-auditor`).
- [ ] C4. `architect-python` Phase 0: point at canonical template (understand skill), not `/author`.
- [ ] D. Fold in 16-verification conformance for surviving generic auditors: `tools: Bash, Read, Skill`, model field, `scripts/` arbiter, thread-store persistence, eval suites; build unbuilt `test_pdr_auditing` suites; update `spx/EXCLUDE`.
- [ ] E. `just build-skills`; marketplace catalogs; `just bump`; `develop:skill-auditor` on changed skills; `subagent-auditor` on changed agents; `just check`; `/merge`.

## Notes

- Removing shipped language auditor agents is a breaking change for consumers dispatching them by name — intended; the generic auditors + composed skills replace them.
- This folds the deferred "16-verification.enabler conformance for adr-auditor / pdr-auditor / test-evidence-auditor" item from `ISSUES.md` into the same change.
