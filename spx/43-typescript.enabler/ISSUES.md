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

**Deferred — marketplace-wide / cross-language defect classes the skill-auditor gate also surfaced (parallel instances in already-shipped python/rust siblings; a typescript-only fix would diverge from untouched nodes per [`spx/31-outcomeeng.enabler/31-verification.enabler/14-verification.pdr.md`](spx/31-outcomeeng.enabler/31-verification.enabler/14-verification.pdr.md)'s defect-class-sweep rule, so each is its own cross-plugin pass):**

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

## Standing skill-audit findings on text the skill rename leaves unchanged

Sealed `skill-auditor` runs over the renamed TypeScript skills rejected each skill on text that the rename (Change 475) neither changes nor invalidates. Each finding below falls on a line outside `git diff -M -U0 origin/main HEAD -- src/plugins/typescript`, and each is recorded once with every run that raised it. Paths are the current skill directories; line numbers are current-head lines, with the run's own line given where it differs. Severity is the run's: `blocking` or `debt`.

### `audit-typescript-test`

- `composed_dependency_form` (blocking): `src/plugins/typescript/skills/audit-typescript-test/SKILL.md:38` names `spec-tree:contextualize` as a bare `/contextualize` mention where the four sibling dependencies use the `require_skill` directive. Run `2026-10-17_00-18-56-089-e4c24f23711f`.

### `typescript-code-standards`

- `caller_coupling` (blocking): `src/plugins/typescript/skills/typescript-code-standards/SKILL.md:18` states what composing skills do with the reference; `:24` requires "another skill" that loads it to check the overlay; `:319` points to `/audit-typescript-code` for false-positive handling. The reference names and constrains its callers. Run `2026-10-17_00-18-43-807-d218f6f62d75`.
- `composed_dependency_form` (blocking): `src/plugins/typescript/skills/typescript-code-standards/SKILL.md:20` and `:164` depend on `typescript:typescript-test-standards` through a bare `/typescript-test-standards` mention instead of the `Use skill` instruction. Run `2026-10-17_00-18-43-807-d218f6f62d75`.

### `simplify-typescript-code`

- `composed_dependency_form` (blocking): `src/plugins/typescript/skills/simplify-typescript-code/SKILL.md:28`, `:29`, and `:30` invoke `/understand`, `/scope-changeset`, and `/contextualize` by bare slash mention instead of `Use skill` naming `spec-tree:understand`, `spec-tree:scope-changeset`, and `spec-tree:contextualize`. Runs `2026-10-17_00-18-30-775-9d847172c16c` and `2026-10-17_00-24-59-217-b362af15ecb2`.

### `author-typescript-test`

- `duplicated_standards` (debt): `src/plugins/typescript/skills/author-typescript-test/SKILL.md:123-188` (`<literal_reuse_remediation>`) and `:99-101` (Mandatory elements) restate the test-data ownership rules (laundering, shared constant bags, source-owned import versus generator versus inert fixture, valid hardcoded strings) that `src/plugins/typescript/skills/typescript-test-standards/SKILL.md` owns. Run `2026-10-17_00-25-24-767-0aca198a14a6`.

### `author-typescript-architecture`

- `composed_dependency_form` (blocking): `src/plugins/typescript/skills/author-typescript-architecture/SKILL.md:31` (`Invoke spec-tree:contextualize`), `:94` (`See /author`), `:110` (`Read /typescript-architecture-standards`), `:111` (`Invoke /typescript-test-standards`), and `:116` (`Read /author`) name dependencies by mention or by an Invoke, Read, or See verb instead of `Use skill` naming the exact installed skill. Runs `2026-10-17_00-18-28-990-c444ecfdb216` (lines `:30`, `:96`, `:112`, `:113`, `:118`) and `2026-10-17_00-25-21-844-c2bd3f860213`.
- `objective_criteria_duplication` (debt): `src/plugins/typescript/skills/author-typescript-architecture/SKILL.md:12` (`<objective>`) and `:198` (`<success_criteria>`): the first success criterion restates the objective. Run `2026-10-17_00-18-28-990-c444ecfdb216`.
- `artifact_language_order` (debt): `src/plugins/typescript/skills/author-typescript-architecture/SKILL.md:5` (frontmatter description, located by the run at line 4): "NEVER author a TypeScript ADR without this skill" names the language before the artifact. Run `2026-10-17_00-18-28-990-c444ecfdb216`.
- `duplicated_standards` (debt): `src/plugins/typescript/skills/author-typescript-architecture/SKILL.md:18` and `:140-145` (Phase 3) restate the ADR template sections and Verification structure that the authoritative template and `typescript-architecture-standards` own. Run `2026-10-17_00-18-28-990-c444ecfdb216`.
- `removable_sentence` (debt): `src/plugins/typescript/skills/author-typescript-architecture/SKILL.md:22` repeats the objective and the out-of-scope item at `:157`; `:110` re-reads `typescript-architecture-standards`, which the `require_skill` directive at `:9` already loads. Run `2026-10-17_00-18-28-990-c444ecfdb216`.
- `reference_toc_missing` (debt): `src/plugins/typescript/skills/author-typescript-architecture/references/typescript-principles.md:1` is a 144-line reference without a table of contents. Runs `2026-10-17_00-18-28-990-c444ecfdb216` and `2026-10-17_00-25-21-844-c2bd3f860213`.
- `known_content` (debt): `src/plugins/typescript/skills/author-typescript-architecture/references/typescript-principles.md:5-9`, `:11-27`, `:31-34`, `:60-71`, `:104-107`, `:122-127`, and `:129-144` teach general TypeScript and clean-architecture practice (strict mode, `unknown` over `any`, `Readonly`/`Pick`/`Omit`, single responsibility, interface versus type, typed error classes, `execa` array arguments). Runs `2026-10-17_00-18-28-990-c444ecfdb216` (all ranges) and `2026-10-17_00-25-21-844-c2bd3f860213` (`:5-9`, `:31-34`, `:104-107`, `:124-127`).

### `author-typescript-code`

- `composed_dependency_form` (blocking): `src/plugins/typescript/skills/author-typescript-code/SKILL.md:221` (`Use /typescript-test-standards`), `:250` (`Invoke spec-tree:contextualize`), `:261` (`Invoke /contextualize`), and `:283` (`through /verify`); `src/plugins/typescript/skills/author-typescript-code/workflows/implementation.md:22` and `:23` (`invoke /verify`, `/test`, `/typescript-test-standards`); `src/plugins/typescript/skills/author-typescript-code/workflows/remediation.md:34` (`return to /verify`). Each names a dependency by mention or verb instead of `Use skill` naming the exact installed skill. Runs `2026-10-17_00-18-28-505-35c266f7d0f4` (`SKILL.md:250`, `:261`, `:283`; `implementation.md:22`; `remediation.md:34`) and `2026-10-17_00-24-57-654-48f38e0bff56` (`SKILL.md:221`, `:250`, `:261`; `implementation.md:22`, `:23`; `remediation.md:34`).
- `motivational_prose` (debt): `src/plugins/typescript/skills/author-typescript-code/SKILL.md:289` ("Humility: ... Write code that will survive adversarial review") and `:41` ("These patterns are enforced by the reviewer. Violations will be REJECTED.") urge care instead of stating a constraint. Runs `2026-10-17_00-18-28-505-35c266f7d0f4` (`:289`) and `2026-10-17_00-24-57-654-48f38e0bff56` (`:41`, `:289`).
- `known_content` (debt): `src/plugins/typescript/skills/author-typescript-code/SKILL.md:165-182` (Discovery Anti-Patterns) and `:320-339` (Never Ignore Type Errors, Never Hardcode Secrets); `src/plugins/typescript/skills/author-typescript-code/workflows/implementation.md:73-160`; `src/plugins/typescript/skills/author-typescript-code/workflows/remediation.md:38-73` teach general TypeScript and security practice. Runs `2026-10-17_00-18-28-505-35c266f7d0f4` (`SKILL.md:167-182`, `:320-339`; `implementation.md:73-160`; `remediation.md:40-63`) and `2026-10-17_00-24-57-654-48f38e0bff56`.
- `duplicated_standards` (debt): `src/plugins/typescript/skills/author-typescript-code/SKILL.md:43-60`, `:320-327`, and `:341-377` restate the magic-literal, `@ts-ignore`, and deep-relative-import rules that `typescript-code-standards` owns. Run `2026-10-17_00-24-57-654-48f38e0bff56`.
- `reference_toc_missing` (debt): `src/plugins/typescript/skills/author-typescript-code/references/outcome-engineering-patterns.md:1` (138 lines) and `src/plugins/typescript/skills/author-typescript-code/references/vocabulary-registry-pattern.md:1` (116 lines) open without a table of contents. Runs `2026-10-17_00-18-28-505-35c266f7d0f4` and `2026-10-17_00-24-57-654-48f38e0bff56`.

**Resolution shape**: state each composed dependency as ``Use skill `{plugin}:{skill}`.`` naming the exact installed skill; point to the owning standards skill instead of restating its rules; drop general-knowledge examples and motivational sentences; open each reference over 100 lines with a table of contents; phrase `typescript-code-standards` without naming or constraining the skills that load it.

**Revisit condition**: resolve each file when its skill next changes, since each fix needs a typescript version bump and its own `skill-auditor` gate.

**Evidence**: the sealed runs named per finding, under the audit run store of branch `work/change-475`. Findings on lines the rename changes (`audit-typescript-test/SKILL.md:25`, `author-typescript-architecture/SKILL.md` evidence-routing lines, `author-typescript-code/SKILL.md:219`, `author-typescript-code/workflows/implementation.md:5`, `author-typescript-code/workflows/remediation.md:6`, `simplify-typescript-code/SKILL.md:34`) are not standing and are not recorded.

## `typescript-test-standards` does not cite the test-verification spec or the test-infrastructure PDR

`src/plugins/typescript/skills/typescript-test-standards/SKILL.md` does not cite `spx/31-outcomeeng.enabler/31-verification.enabler/31-test-verification.enabler/test-verification.md` or [`spx/31-outcomeeng.enabler/31-verification.enabler/31-test-verification.enabler/15-test-infrastructure.pdr.md`](spx/31-outcomeeng.enabler/31-verification.enabler/31-test-verification.enabler/15-test-infrastructure.pdr.md) by path. The assertion at ordinal 3 of `spx/43-typescript.enabler/typescript.md` declares that the plugin's test standards cite both for the language-neutral seam rules, with the `25-typescript-standards.enabler` subtree declaring only the TypeScript delta. Rule `test-standards-citation-absent`, filed as debt.

**Revisit condition**: resolve when `typescript-test-standards` next changes, since the citation needs a typescript version bump and its own `skill-auditor` gate.

**Evidence**: run `2026-10-17_00-18-22-492-992f79d495fc` (assertion audit of `spx/43-typescript.enabler/typescript.md`, ordinal 3).
