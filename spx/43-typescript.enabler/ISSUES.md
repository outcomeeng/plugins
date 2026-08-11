# TypeScript Skill Issues

## `architect-typescript` tells a Codex reader that Claude Code invoked it

`<accessing_typescript>`'s file-access section reads "When this skill is invoked, Claude Code provides the base directory in the loading message". The build substitutes `${CLAUDE_SKILL_DIR}` for `${SKILL_DIR}` when rendering the Codex tree but leaves the sentence, so `dist/codex/typescript/skills/architect-typescript/SKILL.md` ships a claim about the wrong runtime to a Codex-reading agent. The variable substitution is correct; only the prose is wrong.

**Resolution shape**: phrase it runtime-neutrally — "the skill loader provides the base directory" — and prefer that phrasing in the skill templates so a new skill does not reintroduce it.

**Revisit condition**: resolve when `architect-typescript` next changes, since the fix needs a typescript version bump and its own `skill-auditor` gate.

**Evidence**: raised by `instructions:skill-auditor` against `code-rust`, which named the cross-plugin spread. The two rust instances were corrected to the neutral phrasing in the changeset that found them.

## Legacy XML Structure Cleanup

Observed during the TypeScript test-data policy cleanup.

Several TypeScript `SKILL.md` files still mix XML sections with markdown headings inside the skill body. The skill authoring standard requires pure XML structure in `SKILL.md`, with markdown headings reserved for generated report templates or reference content where appropriate.

Known examples:

- `test-typescript/SKILL.md` uses markdown headings inside `<write_mode_workflow>`, `<literal_reuse_remediation>`, and `<fix_mode_workflow>`.
- `code-typescript/SKILL.md` uses markdown headings inside `<mandatory_code_patterns>` and discovery sections.
- `typescript-architecture-standards/SKILL.md` uses markdown headings inside architecture-standard sections.
- Some TypeScript reference files still use the older markdown-heading style. If the cleanup expands to references, make the format decision explicitly instead of migrating one file at a time by accident.

Revisit condition: run a focused TypeScript skill-structure cleanup after the test-data policy and level-document rename changes are reviewed.

## Methodology Restatement Inside TypeScript Standards Skills

The TypeScript standards skills (`typescript-standards`, `typescript-architecture-standards`, `typescript-test-standards`) currently restate Spec Tree fundamentals that belong to the methodology layer rather than to TypeScript:

- `typescript-architecture-standards/SKILL.md` includes `<adr_sections>` and `<atemporal_voice>` sections that duplicate `spx/21-spec-tree.enabler/spec-tree.md` and inline `/understand` `<atemporal_voice>`.
- `<anti_patterns>` in the same skill mixes methodology-level prohibitions (no Status field, no Testing Strategy section) with TypeScript-specific anti-patterns.

The TypeScript specs under `spx/43-typescript.enabler/25-typescript-standards.enabler/` cover only TypeScript-specific concerns. The skill content remains broader so that downstream agents can be evaluated for both Spec Tree adherence and TypeScript-plugin conformance.

Resolution path: factor the Spec Tree fundamentals into a marketplace-wide PDR (or extend an existing one) so the language-standards skills can reference it instead of restating it. Until then, evaluations of these skills must check both layers.

## `audit-typescript-code` Spot Defects — RESOLVED (PR2, branch `fix/typescript-skill-delegation-allowed-tools`)

Both defects fixed alongside the Skill-gap remediation:

- The dangling `${CLAUDE_SKILL_DIR}/rules/` fallback block (referencing `tsconfig.strict.json`, `eslint.config.js`, `semgrep_sec.yaml` — none of which ship in the typescript skill; it carries `references/` only) was removed. (Creating actual TypeScript reference configs for parity with `audit-python-code`/`audit-rust-code`, which ship a partial `rules/` dir, is a separate cross-language concern below.)
- The `quick_start` step-1 `/test` + `/test-typescript` invocations were rewritten to "Read" — matching the read-only `audit-python-code`/`audit-rust-code` siblings — so the step no longer delegates test execution from a read-only audit skill.

## Skill-delegation `Skill` allowed-tools gap — PR2 (CLOSED, branch `fix/typescript-skill-delegation-allowed-tools`)

**Shipped:** `Skill` appended to `allowed-tools` on all 6 delegating skills (`code-typescript`, `test-typescript`, `audit-typescript-architecture`, `audit-typescript-tests`, `architect-typescript`, `audit-typescript-code`); `audit-*` kept read-only (no `Write`/`Edit`). Entangled remediation: `architect-typescript` gained a TypeScript-accurate `<objective>` (no reviewer-gate claim — its Phase 4 is "Verify Consistency", not a reviewer dispatch); `audit-typescript-code` gained a dedicated `<repo_local_overlay>` tag, the `quick_start` Read-rewrite, and removal of the dangling `rules/` block. Two typescript-unique defects the `instructions:skill-auditor` gate surfaced were fixed as touched-file debt: `code-typescript` was missing the required `<objective>` tag (every sibling `code-python`/`code-rust` has it) and `audit-typescript-code`'s `<output_format>` carried a garbled duplicate sentence (the `audit-python-code` sibling has the clean form). Every changed `SKILL.md` was gated with `instructions:skill-auditor`.

**Deferred — marketplace-wide / cross-language defect classes the skill-auditor gate also surfaced (parallel instances in already-shipped python/rust siblings; a typescript-only fix would diverge from untouched nodes per `spx/31-outcomeeng.enabler/31-verification.enabler/14-verification.pdr.md`'s defect-class-sweep rule, so each is its own cross-plugin pass):**

- **Verification-run payload portability** — `audit-typescript-code`/`audit-typescript-architecture` output contracts must stay aligned with the SPX verification-run payload boundary; present across audit skills marketplace-wide. Already tracked in `spx/43-instructions.enabler/ISSUES.md` §1.
- **`architect-*` / `code-*` product-path portability** — `spx/CLAUDE.md`, `spx/{NN}-{slug}.adr.md`, `spec-tree:contextualize` invocations, and `spx/`-rooted example paths in shipped skill bodies. `architect-python`/`architect-rust`/`code-*` carry identical references (`architect-rust` has the same `spec-tree:contextualize` calls); a cross-language portability pass, not this PR. **CLOSED — mis-framed:** the language plugins are scoped by their node specs to "projects using spec-tree," so the `spx/`-rooted references are correct and there is no standalone-consumer scenario to conditionalize. See `spx/43-instructions.enabler/ISSUES.md` §0.
- **Operational-effectiveness gaps** — `code-typescript`/`test-typescript` (and every `code-*`/`test-*` sibling, all `failure_modes=0`) lack a `<failure_modes>` section and carry qualitative, non-command-verifiable `<success_criteria>`; `test-typescript` flagged for procedural/operational imbalance. Marketplace-wide builder-skill operational pass.
- **`<quick_start>` on validator/audit skills** — carried by `audit-typescript-code` and its `audit-python-code`/`audit-rust-code` siblings; tracked in `spx/43-instructions.enabler/ISSUES.md` §1 as the family-wide `<quick_start>`-on-validator question.
- **Worth-improving WARNINGs** — reference files using markdown headings rather than pure XML; `<what_to_avoid>` vs canonical `<anti_patterns>` tag name; `<example_review>` vs `<reference_guides>` consolidation. Style-level, marketplace-wide.

The marketplace-wide `require_skill` → `Skill` sweep closed spec-tree/python/rust in PR #279; typescript
is held for its own PR because two of its skills also carry pre-existing skill-auditor REJECTs that must
be remediated in the same change (touched-file debt — once a SKILL.md is edited, its auditor must-fixes
are in scope). A skill whose body invokes another skill needs `Skill` in `allowed-tools`, or the
delegation requires per-call approval; the cross-plugin context and detection heuristic are in
`spx/43-instructions.enabler/ISSUES.md` §2.

**The 6 skills needing `Skill` appended to `allowed-tools`** (each carries `{!% require_skill … %!}`
and/or an `Invoke /<skill>` prerequisite):

- **Clean, frontmatter-only** (`audit-*` stay read-only — append `Skill`, never `Write`/`Edit`):
  `code-typescript`, `test-typescript`, `audit-typescript-architecture`, `audit-typescript-tests`.
- **`architect-typescript` — append `Skill` AND remediate its pre-existing REJECTs:**
  1. Product-path portability: the body cites `spx/CLAUDE.md` and `spx/{NN}-{slug}.adr.md` directly,
     which do not exist in a consumer that installs the typescript plugin without spec-tree. Reword to a
     conditional ("If this repository uses the spec-tree methodology, read its spec-tree root guide and
     the relevant ancestor ADRs/PDRs …"). NOTE `architect-python`/`architect-rust` carry the same
     `spx/CLAUDE.md` references but their PR #279 audits did not flag them — if the auditor flags those
     too, that is a separate cross-language portability pass, not this PR.
  2. Missing `<objective>` tag: `architect-python` and `architect-rust` have one; `architect-typescript`
     does not (skill-auditor REJECT). Add a TypeScript-accurate `<objective>` after the `require_skill`
     directive (no reviewer-gate claim unless the body actually dispatches one). An earlier session
     drafted this objective in a now-stale git stash — re-author from scratch.
- **`audit-typescript-code` — do NOT add `Skill` to enable its quick_start `/test` invocation; that
  invocation is the defect** (see the `audit-typescript-code` Spot Defects entry above). Fixes:
  1. Change quick_start step 1 "invoke `/test` … `/test-typescript`" to "Read `/test` … `/test-typescript`"
     to match the read-only sibling pattern — `audit-python-code`/`audit-rust-code` carry NO `Skill` and say "Read".
  2. Move the `spx/local/typescript.md` overlay check out of `<objective>` into a dedicated
     `<repo_local_overlay>` tag (siblings use that tag), removing the quick_start duplication.
  3. Fix the broken `${CLAUDE_SKILL_DIR}/rules/` reference (Spot Defects line 77) — the skill ships
     `references/` only.
  4. Verify whether `audit-typescript-code`'s body carries a `{!% require_skill … %!}` macro: if YES it needs
     `Skill` regardless (append it); if its only delegation was the quick_start `/test`, the Read-rewrite
     resolves it and NO `Skill` is added — matching audit-python-code/audit-rust-code.

**Procedure:** edit src → `just build-skills` → gate EVERY changed SKILL.md with `instructions:skill-auditor`
(CI/changes-reviewer do not load skill standards; only the auditor catches voice/structure/portability)
→ fix every must-fix on touched files → `just bump` (typescript patch) → `/merge`. Marketplace-wide
classes the auditor will also flag are tracked in `spx/43-instructions.enabler/ISSUES.md` §2
(the SPX verification-run payload vocabulary; `<quick_start>` on validators; reference
markdown-heading style — see also "Legacy XML Structure Cleanup" above).

Surfaced by PR #279 (the spec-tree/python/rust Skill-gap sweep).
