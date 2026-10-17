# Go Skill Issues

## Standing skill-audit findings on text the skill rename leaves unchanged

Sealed `skill-auditor` runs over the renamed Go skills rejected each skill on text that the rename (Change 475) neither changes nor invalidates. Each finding below falls on a line outside `git diff -M -U0 origin/main HEAD -- src/plugins/go`, and each is recorded once with every run that raised it. Paths are the current skill directories; line numbers are current-head lines. Severity is the run's: `blocking` or `debt`.

### `audit-go-test`

- `composed_dependency_form` (blocking): `src/plugins/go/skills/audit-go-test/SKILL.md:35` invokes `/contextualize` through a bare slash mention where the four other dependencies use the `require_skill` directive. Run `2026-10-17_00-42-07-107-fe367b6df7dd`.
- `auditor_skeleton_violation` (debt): `src/plugins/go/skills/audit-go-test/SKILL.md:257-259` (between `</verdict_format>` and `<success_criteria>`) carries no `<failure_modes>` section; the auditor skeleton orders objective, constraints, audit_workflow, verdict_format, failure_modes, success_criteria. Run `2026-10-17_00-42-07-107-fe367b6df7dd`.

### `go-code-standards`

- `caller_coupling` (blocking): `src/plugins/go/skills/go-code-standards/SKILL.md:22` (`<repo_local_overlay>`) conditions the overlay check on "When another skill loads this reference", so the reference branches on its caller; `:18` (`<reference_note>`) states that "Composing Go skills load these standards explicitly". Runs `2026-10-17_00-48-04-175-ecbf379e2ad5` (`:22`) and `2026-10-17_00-42-15-862-2991c6b3de29` (`:18`, `:22`).

### `simplify-go-code`

- `composed_dependency_form` (blocking): `src/plugins/go/skills/simplify-go-code/SKILL.md:28`, `:29`, and `:30` invoke `/understand`, `/scope-changeset`, and `/contextualize` by bare slash mention instead of `Use skill` naming `spec-tree:understand`, `spec-tree:scope-changeset`, and `spec-tree:contextualize`. Run `2026-10-17_00-42-11-122-9ab2980f81ed`.

### `author-go-architecture`

- `composed_dependency_form` (blocking): `src/plugins/go/skills/author-go-architecture/SKILL.md:36` (`Invoke spec-tree:contextualize`), `:101` (`See /author`), and `:119` (`Read /go-test-standards`) name dependencies by mention or by an Invoke, Read, or See verb instead of `Use skill` naming the exact installed skill. Runs `2026-10-17_00-47-53-545-2931b54aa073` and `2026-10-17_00-42-31-429-f4cd90c6cd7f` (lines `:37`, `:101`, `:119`).
- `objective_criteria_duplication` (debt): `src/plugins/go/skills/author-go-architecture/SKILL.md:14` (`<objective>`) states that the ADR encodes testability as `## Verification` `### Audit` rules; `:206` restates it as a success criterion, and `:210` restates the ALWAYS/NEVER shape of the Verification rules. Runs `2026-10-17_00-47-53-545-2931b54aa073` (`:14`, `:206`) and `2026-10-17_00-42-31-429-f4cd90c6cd7f` (`:14`, `:206`, `:210`).
- `known_content` (debt): `src/plugins/go/skills/author-go-architecture/references/go-principles.md:21-27`, `:38-47`, `:58-68`, `:79-86`, `:97-105`, and `:125-128` teach general Go idioms through generic code samples (consumer-side interface, validating constructor, injected clock, sentinel errors with `Unwrap`, `errgroup` fan-out, `unsafe.String`). Run `2026-10-17_00-42-31-429-f4cd90c6cd7f`.
- `closing_tag_after_list` (debt): `src/plugins/go/skills/author-go-architecture/SKILL.md:206-207` (`</success_criteria>` follows the final list item `- [ ] Security boundaries identified` with no blank line). Run `2026-10-17_01-03-09-768-c5937928cdaa`, read at head `a7fa46e993cb5af6d2140a9a31fbf0f580f802fe`. Base-ref evidence: `git diff -M -U0 origin/main HEAD` against `architect-go/SKILL.md` changes only the success-criterion line `:199` of this region; lines `:206-207` are outside every hunk.
- `closing_tag_after_list` (debt): `src/plugins/go/skills/author-go-architecture/references/go-principles.md:115-116` (`</resource_lifecycle>`) and `:138-139` (`</module_selection>`) follow a list item with no blank line. Run `2026-10-17_01-03-09-768-c5937928cdaa`, read at head `a7fa46e993cb5af6d2140a9a31fbf0f580f802fe`. Base-ref evidence: `git diff -M -U0 origin/main HEAD` records the file as a pure rename of `architect-go/references/go-principles.md` (similarity 100%), so no line is changed.

### `author-go-code`

- `composed_dependency_form` (blocking): `src/plugins/go/skills/author-go-code/SKILL.md:102` (`invoke spec-tree:contextualize`) states the dependency as a bare invocation instead of `Use skill`. Runs `2026-10-17_00-47-57-213-5b46b6eddc88` and `2026-10-17_00-41-56-237-2b10d35afb55`.
- `skill_directory_token_explanation` (debt): `src/plugins/go/skills/author-go-code/SKILL.md:17-19` (`<bundled_files>`) explains where the skill-directory token resolves and adds search-avoidance guidance, which the skill-directory standard excludes. Run `2026-10-17_00-47-57-213-5b46b6eddc88`.
- `nested_reference` (debt): `src/plugins/go/skills/author-go-code/references/verification-checklist.md:58` routes a read to `${CLAUDE_SKILL_DIR}/references/test-patterns.md` `<anti_patterns>`. Runs `2026-10-17_00-47-57-213-5b46b6eddc88` and `2026-10-17_00-41-56-237-2b10d35afb55`.
- `bundled_file_reference` (blocking): `src/plugins/go/skills/author-go-code/workflows/implementation.md:4-6` and `src/plugins/go/skills/author-go-code/workflows/remediation.md:4-6` name `references/outcome-engineering-patterns.md`, `references/test-patterns.md`, and `references/verification-checklist.md` by bare relative path instead of `${CLAUDE_SKILL_DIR}/references/<file>.md`. Runs `2026-10-17_00-47-57-213-5b46b6eddc88` and `2026-10-17_00-41-56-237-2b10d35afb55`.

**Resolution shape**: state each composed dependency as ``Use skill `{plugin}:{skill}`.`` naming the exact installed skill; reach every bundled file through `${CLAUDE_SKILL_DIR}`; phrase `go-code-standards` without naming or conditioning on the skills that load it; drop general-knowledge samples; state each reference criterion in place instead of routing to a sibling reference; add the missing `<failure_modes>` section to `audit-go-test`.

**Revisit condition**: resolve each file when its skill next changes, since each fix needs a go version bump and its own `skill-auditor` gate.

**Evidence**: the sealed runs named per finding, under the audit run store of branch `work/change-475`. Findings on lines the rename changes are not standing and are not recorded: `author-go-architecture/SKILL.md` lines `:72`, `:117`, and `:120`, `author-go-code/SKILL.md` lines `:26`, `:48`, and `:88`, `go-code-standards/SKILL.md` lines `:26` and `:33`, and `go-test-standards/SKILL.md` lines `:6`, `:17`, and `:331`.
