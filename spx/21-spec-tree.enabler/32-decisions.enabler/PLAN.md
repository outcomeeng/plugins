# Plan (detailed): decision-record mode-floor, audit-adr node, audit-pdr rename, naming overlay

Exact execution spec. Tier 1 (`21-templates`, `35-evidence`) is landed on `work/evidence-mode-implementation`. The child plan `spx/21-spec-tree.enabler/32-decisions.enabler/32-pdr-auditing.enabler/PLAN.md` carries the PDR-audit-node specifics. Both decision audits run through the per-rule mode tag from `spx/21-spec-tree.enabler/21-templates.enabler` and the `/testing` authority from `spx/21-spec-tree.enabler/35-evidence.enabler`.

## Settled design (from operator at pickup)

- Per-rule tag is a MODE (one of `scenario`/`mapping`/`conformance`/`property`/`compliance`), never a mechanism. `[eval]` is a downstream mechanism, never a per-rule mode tag.
- KISS-additive: `audit-adr` and `audit-pdr` are standalone skills, NOT folded into the `/auditing` language orchestrator. Language ADR concerns (DI/no-mocking testability, level accuracy) stay in `auditing-{lang}-architecture`.
- Imperative names (`audit-adr`, `audit-pdr`), no command shims, authorized via the repo-local overlay only. The shipped `develop` plugin stays gerund-preferred for consumers.
- New `adr-auditing` node placed at index **21** under `32-decisions.enabler` (ADR-before-PDR convention; lower than `32-pdr-auditing`).

## ⚠️ Scope decision required before executing parts D–F

The high-level plan said both skills "conform to `spx/21-spec-tree.enabler/16-verification.enabler`." The **current** `auditing-product-decisions` skill + `pdr-auditor` agent do NOT conform:

- `pdr-auditor.md` has `tools: Read, Glob, Grep`, no `model: sonnet`, `skills: [spec-tree:auditing-product-decisions]`. `16-verification.enabler` requires `model: sonnet`, `tools: Bash, Read, Skill`.
- No `scripts/` CLI arbiter module (verification policy must live in a `scripts/` Python module the wrapper agent invokes).
- No thread-store persistence (verification skills persist machine-readable result + markdown surface through `21-thread-store.enabler`).
- The skill emits a JSON verdict in prose but does not route through a `scripts/` validator.

Full `16-verification.enabler` conformance for BOTH audit skills (arbiter module + agent reshape + thread-store) is a **large** effort, comparable to building a verification skill from scratch (cf. the `reviewing-changes` instance under `32-evidence.enabler`/`68-reviewing.enabler`). Two options:

- **Option SCOPE-MIN (recommended):** Land the per-rule-mode feature now — naming overlay, `decisions.md` assertion, `adr-auditing` node + spec, `audit-adr` skill, `audit-pdr` rename, mode-floor assertions, reference updates — at the **current** skill/agent shape (the existing `pdr-auditor` agent pattern: `tools: Read, Glob, Grep`, JSON verdict in prose). Record the `16-verification.enabler` conformance (arbiter + agent reshape + thread-store) as a separate follow-up node/ISSUES entry, because it is an architecture-alignment concern independent of the evidence-mode feature and applies equally to every existing audit skill.
- **Option SCOPE-FULL:** Build the `scripts/` arbiter, reshape both agents to `model: sonnet` + `Bash, Read, Skill`, and wire thread-store as part of this PR. Multiplies the PR size and couples an architecture migration to a methodology feature.

Parts D–F below are written for **SCOPE-MIN**. If SCOPE-FULL is chosen, add an `audit_decision_record.py` arbiter design and agent reshape before executing.

## A. Naming overlay — `spx/local/standardizing-skills.md` (NEW, prerequisite)

Must land before any audit-skill create/rename so `/auditing-skills` does not flag the imperative names. Exact content:

```markdown
# Marketplace Skill Authoring Overrides

Loaded by `/standardizing-skills` `<repo_local_overlay>` when authoring or auditing skills in this repository. These specialize the base skill-authoring standards for the Outcome Engineering marketplace.

## Imperative names for standalone decision-record audit skills

The base standard prefers gerund skill names. In this marketplace the standalone decision-record audit skills use imperative `audit-{artifact}` names:

- `audit-adr`
- `audit-pdr`

Each is invoked as a direct command (`/audit-adr <path>`, `/audit-pdr <path>`) and ships no gerund command shim. `/auditing-skills` does not flag `audit-adr` or `audit-pdr` against the gerund preference.

The gerund preference still governs every other skill in the marketplace — the language audit skills (`auditing-python`, `auditing-typescript`, and their `-tests` / `-architecture` variants) and the generic `/auditing` orchestrator. This override is scoped to the two standalone decision-record audit skills only.
```

Validation: `spx/local/` is product-instruction surface; no plugin bump. `just check-skills` reads overlays via the skill chain at audit time.

## B. `decisions.md` — lifecycle assertion (spec)

Add as a third Compliance assertion, after the existing `ALWAYS: ... flow into spec assertions`:

```markdown
- ALWAYS: every decision-record compliance rule declares a single evidence mode — one of scenario, mapping, conformance, property, compliance — chosen via /testing from the rule's claim shape ([review])
```

`[review]`: a lifecycle/design rule about decision-record authoring, consistent with the node's existing `[review]` Compliance assertions. The structural per-record enforcement is the `audit-adr`/`audit-pdr` job (parts D / child plan).

## C. New node `21-adr-auditing.enabler` (spec) + EXCLUDE

Create `spx/21-spec-tree.enabler/32-decisions.enabler/21-adr-auditing.enabler/adr-auditing.md`, `tests/` dir, and add `21-spec-tree.enabler/32-decisions.enabler/21-adr-auditing.enabler` to `spx/EXCLUDE`. Author via `/authoring`. Mirrors `pdr-auditing.md` but ADR-focused: NO product-vs-architecture content classification (an ADR's content IS architecture); checks structure, atemporal voice, per-rule mode validity, and downstream sufficiency. Exact spec body:

```markdown
# ADR Auditing

PROVIDES an audit methodology verifying ADRs declare well-formed architecture decisions whose compliance rules carry valid per-rule evidence modes and flow into spec assertions with sufficient evidence
SO THAT all spec-tree projects
CAN eliminate malformed or unenforced architecture decisions before they accumulate

## ADR Evidence Model

The audit answers one question: **does this ADR declare an enforceable architecture decision whose rules are both routed to a valid evidence mode and enforced downstream at or above that mode?**

Evidence requires four properties checked in order:

1. **Section structure** — the ADR carries the required sections (Purpose, Context, Decision, Rationale, Trade-offs, Compliance); Invariants only when algebraic properties hold
2. **Atemporal voice** — the ADR states architecture truth, never history
3. **Per-rule mode validity** — every Compliance MUST/NEVER rule carries exactly one evidence-mode tag naming one of the five claim shapes (scenario, mapping, conformance, property, compliance)
4. **Downstream sufficiency** — every Compliance rule resolves to a spec assertion in the governed subtree whose evidence meets or exceeds the rule's declared mode

Language-specific ADR concerns — testability-in-Compliance (dependency injection, no-mocking), execution-level accuracy — are out of scope here and stay in `auditing-{lang}-architecture`.

## Per-rule Mode Validity Model

Each Compliance rule names the minimum evidence mode its downstream enforcement must carry, chosen from the rule's claim shape via `/testing` (see `spx/21-spec-tree.enabler/35-evidence.enabler/evidence.md`). The audit checks the tag is present and names one of the five modes; it does not re-derive the mode (mode selection is `/testing`'s authority). A missing tag, a tag naming a non-mode (e.g. a bare mechanism `[review]`/`[test]`/`[eval]`), or more than one tag is a finding.

## Downstream Sufficiency Model

For each Compliance rule the auditor finds the spec assertion(s) enforcing it in the governed subtree and compares the assertion's evidence against the rule's declared mode. Presence alone is insufficient: a `property`-floor rule enforced only by a `scenario` assertion is a finding (`insufficient-evidence-mode`), not a judgment call. A rule with no downstream assertion is `unenforced-rule`.

## Assertions

### Scenarios

- Given an ADR missing a required section, when audited by `/audit-adr`, then the verdict is REJECT with finding category "missing-section" ([eval](evals/structure/eval.toml))
- Given an ADR with temporal language in any section, when audited by `/audit-adr`, then the verdict is REJECT with finding category "temporal-voice" ([eval](evals/voice/eval.toml))
- Given an ADR whose Compliance rule carries a bare mechanism tag instead of a mode tag, when audited by `/audit-adr`, then the verdict is REJECT with finding category "invalid-mode-tag" ([eval](evals/mode-validity/eval.toml))
- Given an ADR whose `property`-floor Compliance rule resolves only to a `scenario` spec assertion, when audited by `/audit-adr`, then the verdict is REJECT with finding category "insufficient-evidence-mode" ([eval](evals/mode-floor/eval.toml))
- Given an ADR whose Compliance rule has no downstream spec assertion, when audited by `/audit-adr`, then the verdict is REJECT with finding category "unenforced-rule" ([eval](evals/mode-floor/eval.toml))
- Given an ADR where all four properties hold, when audited by `/audit-adr`, then the verdict is APPROVED ([eval](evals/structure/eval.toml))

### Compliance

- ALWAYS: check the four properties in order — structure, voice, mode validity, downstream sufficiency — and stop at the first failure ([review])
- ALWAYS: validate each Compliance rule's mode tag against the five modes without re-deriving the mode — mode selection is `/testing`'s authority ([review])
- NEVER: approve an ADR whose Compliance rule resolves to a downstream assertion below the rule's declared mode — sufficiency, not mere presence, is the bar ([review])
- NEVER: classify ADR content as product-behavior-vs-architecture — an ADR's content is architecture by definition; that classification is the PDR audit's concern ([review])
```

Evidence mechanism rationale (per `spx/15-spec-coverage.adr.md`): the four behavior Scenarios about the audit's judgment carry `[eval]` (the skill emits a structured verdict; evals replay curated cases). The Compliance design rules carry `[review]`. Node is EXCLUDEd, so the `[eval]`/eval.toml targets are forward references — evals are built when the node leaves EXCLUDE. Confirm during `/authoring` that EXCLUDE silences the forward-referenced `[eval]` link-integrity check (it silences forward `[test]` links; verify the same for `[eval]`, else fall the four scenarios back to `[review]` for this pass and note the eval as follow-up).

## D. `audit-adr` skill (NEW) — `src/plugins/spec-tree/skills/audit-adr/`

Author via `develop:creating-skills` AFTER the naming overlay (A) lands. Mirror the shape of `audit-pdr` (the renamed `auditing-product-decisions`) at SCOPE-MIN. Frontmatter:

```yaml
---
name: audit-adr
description: Use when asked by the user to invoke the ADR audit skill
---
```

Body (pure XML): `<objective>` (the four-property model), `<quick_start>` (contextualize → read ADR → 4 properties in order → first failure REJECT), `<essential_principles>` (architecture-by-definition so no product classification; mode validity is presence-not-rederivation; downstream sufficiency not presence; atemporal voice), `<audit_workflow>` (load_context via `/contextualizing` on the ADR's dir → read_adr → audit_structure → audit_voice → audit_mode_validity → audit_downstream_sufficiency → verdict), `<verdict_format>` (JSON conforming to `verdict.py`, rows = structure/voice/mode-validity/downstream-sufficiency), `<failure_modes>`, `<success_criteria>`. No `references/` needed at SCOPE-MIN unless the model grows past 500 lines; if so add `references/adr-evidence-model.md`.

## E. `audit-adr` agent (NEW) — `src/plugins/spec-tree/agents/audit-adr.md`

SCOPE-MIN mirrors `pdr-auditor.md`:

```yaml
---
name: audit-adr
description: >-
  Audit ADR evidence quality. Use after writing an ADR or before
  implementing from it.
tools: Read, Glob, Grep
skills:
  - spec-tree:audit-adr
---
```

Body: `<role>` (adversarial ADR auditor, four properties in order), `<constraints>` (read-only, first-failure REJECT, never suggest rewrites), `<output_format>` (structured verdict mirroring pdr-auditor). (SCOPE-FULL would set `tools: Bash, Read, Skill` + `model: sonnet` and route through a `scripts/` arbiter.)

## F. Cross-references + catalog

- `spx/21-spec-tree.enabler/32-decisions.enabler/32-pdr-auditing.enabler/PLAN.md` covers the `auditing-product-decisions` → `audit-pdr` skill+agent rename and the `pdr-auditing.md` edits.
- Update `AGENTS.md`/`CLAUDE.md` agent tables: `pdr-auditor` → `audit-pdr`; add `audit-adr`. The "When to Dispatch Agents" + `spx/CLAUDE.md` Quick Reference tables map `/auditing-product-decisions` → `/audit-pdr` and add `/audit-adr`.
- `README.md` plugin catalog: regenerate via `just docs` (auto-sourced from frontmatter).
- Grep the repo for `auditing-product-decisions` and `pdr-auditor` and update every authored reference (skills, agents, AGENTS.md, spx specs/tests).
- Regenerate `dist/claude` + `dist/codex` via `just build-skills`.

## G. Commit + bump strategy (whole evidence-mode PR)

Per-plugin bump is once-per-branch and all-or-nothing (`outcomeeng/distribution/bump.py` refuses if any changed plugin is already bumped). The branch touches `spec-tree` (gains `audit-adr` skill+agent → `minor`) and, in tier 3, `python` (SKILL edit → `patch`). So: make ALL plugin edits across tiers, commit per concern WITHOUT bumping, then at the very end run `just bump` once (auto-detects `spec-tree` minor + `python` patch), `just build-skills`, `just check`, and a final `build(plugins):` bump commit. The pre-commit hook enforces `git diff --exit-code dist` but NOT bump-check, so unbumped per-tier commits are valid; CI `just bump-check` validates the final state.

Commit order within a concern: implementation+dist first (hook needs dist clean), then the spec/spx file.

## Implementation skills (in order)

1. `spec-tree:understanding` (done) → `spec-tree:contextualizing` on `spx/21-spec-tree.enabler/32-decisions.enabler` (done)
2. Write `spx/local/standardizing-skills.md` (part A) — prerequisite for the renames/creates
3. `spec-tree:authoring` for: `decisions.md` assertion (B), the `21-adr-auditing.enabler` node + `adr-auditing.md` (C), and (child plan) the `pdr-auditing.md` mode-floor assertion + ref updates
4. `develop:creating-skills` for `audit-adr` (D); `develop:standardizing-skills` for the `audit-pdr` rename (child plan) — both after A lands
5. `develop:creating-subagents` for the `audit-adr` agent (E) and the renamed `audit-pdr` agent (child plan)
6. `audit-pdr` (renamed) self-audit on `decisions.md` + `pdr-auditing.md`; `audit-adr` self-audit on `adr-auditing.md`
7. Cross-references + `just docs` (F); `spec-tree:committing-changes`

## Audit gates

- `audit-adr`/`audit-pdr` on the amended decision specs.
- `develop:auditing-skills` on `audit-adr` and the renamed `audit-pdr` — confirm the naming overlay clears the imperative-name finding.
- `develop:auditing-subagents` on the two agents.
- `just check` (plugin source + catalog + dist) — once, after the single bump.

## Related plans

- `spx/21-spec-tree.enabler/32-decisions.enabler/32-pdr-auditing.enabler/PLAN.md` — the `audit-pdr` rename + `pdr-auditing.md` edits
- `spx/21-spec-tree.enabler/21-templates.enabler/PLAN.md` — the per-rule mode tag these audits read (landed)
- `spx/21-spec-tree.enabler/35-evidence.enabler/PLAN.md` — the `/testing` router that picks the mode (landed)
