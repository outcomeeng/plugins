# Plan: collapse to generic artifact-type auditors composing language skills

PR-1 branch `feat/adr-audit-verifier-composition` (merged as #272). PR-2 branch `feat/auditor-collapse` (redo from this PLAN; the `wip/composition-partial` and `wip/pr2-agent-removal-template` refs were confirmed stale — they branch before #272/#273 and reusing them reverts the SessionStart-hook work and newer `14-verification.pdr` content; only their three small skill/agent edits were used as reference). Governing decisions: `spx/14-verification.pdr.md` (root principle) and `spx/21-spec-tree.enabler/17-auditing.adr.md` (auditing architecture).

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

- [x] B1. Updated shipped template `src/plugins/spec-tree/skills/understand/templates/spx-claude.md`: per-language audit tables now show the composing generic auditor (no per-language agent); `rust-unsafe-auditor` row dropped; `template_version` bumped 0.18.16 → 0.19.0.
- [x] B2. Reconciled the doc surfaces that referenced the removed language auditor agents:
  - [x] Root `AGENTS.md` "When to Dispatch Agents vs Invoke Skills" dispatch table — per-language rows replaced with the composed-by-generic-auditor note.
  - [x] README plugin catalog regenerated (`just docs`); rust plugin description in `.claude-plugin/marketplace.json` de-referenced `rust-unsafe-auditor`.
  - [x] `develop/skills/create-subagents/references/subagents.md` example switched from `typescript-code-auditor` to the surviving `adr-auditor`.
  - [x] `architect-python` Phase 5 reviewer reference re-pointed from `python-architecture-auditor` to the generic `adr-auditor`.
  - [x] Re-rendered product `spx/CLAUDE.md` (→ `spx/AGENTS.md`) via `/update-spx` to `template_version 0.19.0`, integrating the merged `audit-specs`/`spec-auditor` row.
  - Sweep confirms NO removed-agent reference remains anywhere in `src/`, `AGENTS.md`, `README.md`, or the marketplace catalogs.
- [x] C1. Removed language auditor agents: python/typescript/rust × {architecture,code,test} + `rust-unsafe-auditor` (10 total; `*-simplifier` agents kept). Salvaged the `rust-unsafe-auditor` unsafe/FFI soundness methodology into `audit-rust` as `references/unsafe-soundness.md` + a process subsection 3.4 + an `unsafe-soundness` verdict row (the `unsafe-checker` skill the agent referenced never existed; the baseline lives in `rust-standards`, the audit *workflow* is what was salvaged). Satisfies the `spx/43-rust.enabler/rust.md` line-19 contract.
- [x] C2. Generic audit skills compose `audit-{lang}*` by partition + `Skill` added to `audit-adr`/`audit-tests`/`audit` `allowed-tools` and to `adr-auditor`/`test-evidence-auditor` `tools` (the `/audit`-family agents already carried `Skill`). `audit-adr` gained a compose Step 5b; `audit-tests` gained a compose Step 3e; the generic `audit` skill already dispatched by partition. The PR-1 "template-missing → UNKNOWN" handling in `audit-adr` Step 3 was preserved (the WIP had dropped it).
- [x] C3. All 9 `audit-{lang}*` dispatch_gates + descriptions reconciled to the composed-by-generic-auditor model (no dangling `{lang}-*-auditor` agent references). The 3 `audit-{lang}-architecture` skills simplified to language-only concerns (DI, no-mocking, level accuracy, anti-patterns, ancestor-consistency); section-structure / atemporal-voice / tag-validity rows, steps, principles, failure-modes, and success-criteria removed (deferred to the composing `adr-auditor`).
- [x] C4. `architect-python` Phase 0 now sources ADR section structure from `/python-architecture-standards` (`<adr_sections>`) and the `adr-auditor` (Phase 5), not `/author` and not a non-portable cross-plugin template path.
- [→] D. **Split out and REFRAMED.** The original "16-verification conformance" framing (`scripts/` arbiter, thread-store persistence) is superseded by the run-journal architecture (`spx/21-spec-tree.enabler/16-verification.enabler/13-run-journal.adr.md`), whose `spx audit` channel is now published (`spx 0.5.6`). The real migration — re-scope the verdict-toolchain to a projection, decide thread-store's fate, rework `17-auditing.adr` onto the journal, give the wrapper agents `tools: Bash, Read, Skill`, re-home the verdict vocabulary — is a sequenced multi-node effort tracked in `spx/21-spec-tree.enabler/16-verification.enabler/PLAN.md` and handed off for a fresh session. The one independent slice (PDR-auditing `[eval]` suites + `[test]→[eval]` retag + EXCLUDE removal) ships separately on branch `feat/verification-conformance`. The conformance gap exists on `main` today and is unchanged by the collapse, so the split introduced no regression.
- [~] E (this PR). `just build-skills` ✓; marketplace catalogs ✓; `just bump` ✓ (spec-tree 0.60.1, python 0.20.0, rust 0.4.0, typescript 0.21.0, develop 0.10.3); `develop:skill-auditor` on the changed skills ✓ (representatives of every distinct edit shape; valid findings fixed, family-wide pre-existing patterns tracked in `ISSUES.md`); `subagent-auditor` on `adr-auditor`/`test-evidence-auditor` ✓; rebased onto `origin/main` (#274 audit-specs integrated) ✓; `just check` ✓ + local `changes-reviewer` converged ✓; `/merge` remaining.

## Notes

- Removing shipped language auditor agents is a breaking change for consumers dispatching them by name — intended; the generic auditors + composed skills replace them.
- PR 2 (`feat/auditor-collapse`) ships the composition mechanism + agent collapse + doc reconciliation (C1–C4, B1, B2): a regression-free unit that satisfies `17-auditing.adr`'s spec-leading composition assertions. The 16-verification conformance (step D) is split out as its own change per the decisions `ISSUES.md` entry, which already scopes it as independent of the per-rule-evidence-type feature.
