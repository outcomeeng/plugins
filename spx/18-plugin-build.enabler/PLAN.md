# Plan

Concrete remaining steps for the 18-plugin-build subtree, in dependency
order. Remove steps as they complete.

## Context

The include-directive vertical slice (committed `5eb8c8c`) demonstrates the
canonical test pattern for this subtree: stage-isolated test files,
source-owned constants from `outcomeeng.scripts.build_plugins`, named
scenarios from `outcomeeng_testing.harnesses.scenarios`, optional
Hypothesis property tests where algebraic structure exists, IMPLEMENTED
flag skip-gate. Each subsequent slice repeats this pattern for one
directive family or behavioral concern.

`outcomeeng.scripts.build_plugins` is currently a typed stub with
`IMPLEMENTED: Final = False`. All test files skip cleanly until the
flag flips to True after the build is implemented.

## Step 1 — require_skill directive vertical slice

Smallest of the remaining slices in `21-source-and-templating.enabler`.
Closes assertion 5 ("`{!% require_skill 'plugin:skill' %!}` expands to
identical agent-runtime-neutral invocation text in both targets").

Files to add:

- `tests/test_expand_require_skill.scenario.l1.py` — expansion produces
  agent-neutral text containing the skill ref; identical bytes for
  Target.CLAUDE and Target.CODEX inputs (the "identical in both targets"
  half of the assertion the auditor flagged as unverified).
- `tests/test_render_text_with_require_skill.scenario.l1.py` (or extend
  existing `test_render_text.scenario.l1.py`) — end-to-end render of a
  template containing only a require_skill directive.

Spec update: link assertion 5 to the new test files.

## Step 2 — source-format scenarios

Closes assertions 1 and 2 in `21-source-and-templating.enabler` (src/
tree shape and shared content shape).

Approach: rather than asserting against the live repo `src/` (the false
coupling the auditor rejected), the tests build a malformed src/ tree
via SrcTreeBuilder and assert that `build()` raises `SourceFormatError`.
This tests the build's input validation contract against the spec's
shape rules.

File to add:

- `tests/test_source_format.scenario.l1.py` — happy path (well-shaped
  src/ tree builds without error) + fault scenarios (missing skill
  directory, fragment.md absent under a topic, non-canonical plugin
  subdir, etc.).

Spec update: link assertions 1 and 2 to the new test file. Optionally
revise the assertion text to describe the build's behavior (raises
SourceFormatError on malformed src/) rather than the static shape.

## Step 3 — Jinja2 environment configuration tests

Closes assertion 3 in `21-source-and-templating.enabler` (Jinja2
environment uses custom delimiters).

Files to add:

- `tests/test_jinja_environment.compliance.l1.py` (or fold into
  `test_parse_directives` since the parser is the visible contract) —
  asserts that `parse_directives` recognizes only the custom delimiters
  and that standard delimiters pass through verbatim. The latter is
  already covered by `test_parse_directives.scenario.l1.py`'s
  `TestIgnoresStandardJinjaSyntax`.

Decision: the existing `test_parse_directives.scenario.l1.py` may
already satisfy this assertion fully via its delimiter-passthrough
tests. If so, just update the spec link and add no new test file.

## Step 4 — 43-target-emission slices

Seven assertions across the per-target translation concern. Roll out the
slice pattern with stage tests for each operation:

- `tests/test_rewrite_paths_for_target.scenario.l1.py` — Target.CLAUDE
  preserves CLAUDE_SKILL_DIR_TOKEN; Target.CODEX rewrites it to a
  relative path.
- `tests/test_rewrite_paths_for_target.property.l1.py` — idempotence:
  applying the rewrite twice yields the same result as applying once.
- `tests/test_strip_frontmatter_fields.scenario.l1.py` — exercises ALL
  three fields in `CLAUDE_ONLY_FRONTMATTER_FIELDS` (closes the audit's
  coverage-gap finding that only one of three was verified).
- `tests/test_strip_frontmatter_fields.property.l1.py` — idempotence:
  double-strip is a no-op.
- `tests/test_emit_skill.scenario.l1.py` — emits skill outputs to both
  runtime trees with the right structure and content.
- `tests/test_runtime_outputs.compliance.l1.py` — high-level checks
  using DistTreeReader: no `!`cat injection in any output, no
  `${CLAUDE_SKILL_DIR}` in `dist/codex/` outputs.

## Step 5 — 65-build-orchestration recategorization

Per `ISSUES.md` item 2, the four assertions in build-orchestration.md
need splitting between `[review]` and `[test]` at l2.

Spec edits:

- Recipe existence, hook config existence, marketplace JSON path
  prefixes → `[review]` with a documented manual checklist.
- Behavioral assertions (just recipe actually invokes build; lefthook
  hook actually fails on dist drift; marketplace install resolves
  paths) → `[test]` at l2.

Files to add (l2 tests):

- `tests/test_just_build_skills.scenario.l2.py` — invokes
  `just build-skills` as a subprocess against a fixture src/, asserts
  exit code and that dist/ contents match expected.
- `tests/test_lefthook_drift.scenario.l2.py` — modifies src/ without
  rebuilding, attempts a commit, asserts the hook rejects.
- `tests/test_marketplace_install.scenario.l2.py` — dry-runs the
  marketplace install path resolution.

## Step 6 — parent enabler tests

Three assertions on the whole pipeline: traceability, determinism,
idempotence. Plus two new high-value tests the auditor recommended:

- `tests/test_plugin_build.compliance.l1.py` — every dist/ file traces
  to a src/ ancestor through the build.
- `tests/test_plugin_build.property.l1.py` — determinism and idempotence
  using Hypothesis-generated SrcTreeConfig values.
- `tests/test_plugin_build.headline.l1.py` — high-level invariant: no
  installable `standardizing-*` skills appear in either marketplace's
  published plugin set.
- `tests/test_marketplace_migration.scenario.l2.py` — runs the build
  on the actual repo's `plugins/` (after migration to `src/`) and
  verifies the resulting `dist/claude/` and `dist/codex/` contain the
  same installable skill set as the current `plugins/` minus the 12
  `standardizing-*` skills. This is the migration safety test.

## Step 7 — implement outcomeeng.scripts.build_plugins

Once all tests are scaffolded and skipping via the IMPLEMENTED flag,
flip to /python:coding-python and implement each stage until tests
pass:

1. parse_directives, format_directive (round-trip property locks the
   contract).
2. expand_include, expand_require_skill.
3. render_text (orchestrates parse + expand for each directive type).
4. rewrite_paths_for_target, strip_frontmatter_fields.
5. emit_skill.
6. build (orchestrates everything; validates src/ shape; raises
   SourceFormatError on invalid input).

When the full test suite passes, set IMPLEMENTED = True.

## Step 8 — source migration

Move `plugins/<plugin>/` content into `src/plugins/<plugin>/`. For each
of the 27 currently-`!cat`-using consumer files, replace the
`!`cat ${CLAUDE_SKILL_DIR}/...`` injection with the equivalent
`{!% include %!}` or `{!% require_skill %!}` directive. Extract the 12
`standardizing-*` skills' bodies into `src/_shared/<scope>/<topic>/`.

Run `just build-skills`. Verify `dist/claude/` and `dist/codex/` are
sane.

## Step 9 — marketplace JSON re-pointing

Update `.claude-plugin/marketplace.json` to use
`metadata.pluginRoot: "./dist/claude"`. Update each plugin entry in
`.agents/plugins/marketplace.json` to set `source.path` under
`./dist/codex/`. Verify install via `just push-marketplace` against a
clean Claude Code and Codex environment.

## Step 10 — full-tree audit

Run `/python:auditing-python` on the build module and
`/python:auditing-python-tests` on the test layer. Address findings.
Run `/spec-tree:aligning` on the subtree to verify all assertion
links resolve and the spec is internally consistent.
