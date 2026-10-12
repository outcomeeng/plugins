# Issues - Runtime Token Validation

Known follow-ups for runtime-token validation. Coordination note; not spec
truth.

## Compound target predicates are outside the canonical scanner form

Review run `2026-07-15_03-20-51-675-5765b9592066` found that the runtime-token
scanner recognizes the canonical `target == '<runtime>'` and
`elif target == '<runtime>'` forms emitted by the production formatter, while a
compound or reordered predicate falls back to flat scanning and can report a
runtime name inside an otherwise target-constrained branch.

The scanner contract currently covers the canonical formatter-owned form used
by authored plugin source and its generated evidence. Revisit when the authoring
surface permits compound or reordered target predicates: decide whether the
source contract remains canonical equality only or expands to a parsed predicate
model, then align `spx/15-validation.enabler/32-runtime-token.enabler/runtime-token.md`,
the formatter, scanner, generators, and violating-case evidence in one change.

## Bare-else target scoping lacks generated evidence

PR #432 current-head review comment
`https://github.com/outcomeeng/plugins/pull/432#issuecomment-4982176438`
confirmed that `outcomeeng_testing/generators/runtime_tokens.py` generates
single-branch, nested, and explicit target-branch cases without generating a
bare `{!% else %!}` branch. The missing case leaves the complement-target logic
in `outcomeeng/validation/runtime_tokens.py::_update_else_frame` without an
independent targeted oracle even though bare `if`/`else` conditionals are the
dominant authored-source form.

This is an evidence defect against the clean-conditional scenario in
`spx/15-validation.enabler/32-runtime-token.enabler/runtime-token.md`: the
whole-corpus zero-violation assertion cannot distinguish correct target
complement scoping from a scanner that silently permits the same corpus for the
wrong reason.

Required handling:

- Extend the source-owned runtime-token generator with matching and mismatching
  bare-`else` cases for every enforced runtime name.
- Assert that the `else` branch is scoped to the parent target set minus every
  target matched by preceding branches.
- Run the focused runtime-token tests and a test-evidence audit over the repaired
  generator chain before removing this issue.

## The node and its spec use the prohibited agent-concept term

[`spx/15-agent-terminology.pdr.md`](spx/15-agent-terminology.pdr.md) maps `runtime`, `per-runtime` and `runtime-specific` to `agent`, `per-agent` and `agent-specific` where the subject is a selectable coding agent. This node's spec says "per-runtime conditional" and "runtime-divergent name", which mean per-agent, and the node's name encodes the term. "Runtime" stays valid for execution-time behavior and for an execution environment such as Python.

**Settlement condition.** The node and its spec align to the decision's wording, as part of the tree-wide sweep `spx/18-plugin-build.enabler/ISSUES.md` records. The node name encodes the term, so the sweep includes a `/refactor` node rename.

## DEBT [evidence]: profile harness and compliance test hand-write build-token text (f-002, f-003)

A second `spec-tree:test-evidence-auditor` verdict on this node at head `7e15b3c437ca8326e0e63dbd0e54d45a62245ba6`, recorded after the first audit's debt entries, rejected existing text in the compliance test that drives the profile harness. The verdict carries no sealed run token. Every entry below that cites this audit shares that property.

- f-002 (REJECT, source-ownership): `spx/15-validation.enabler/32-runtime-token.enabler/tests/test_profile_configuration.compliance.l1.py:64` hand-writes the build token.
- f-003 (REJECT, test-owned data): the same test file, line 42, holds the expected violation lines (2, 5) as literals that mirror the harness file layout.

The defects share one class: the text spells out what the contracts owner defines, or restates the harness file layout, so a change to either leaves the evidence asserting the old spelling.

Resolution shape: build the f-002 token from the contracts owners; read the f-003 expected lines from the harness that writes the file.

Evidence that the text lies outside the change: `git diff -U0 origin/main...HEAD` (merge base `149a55f71befdf61e88be9bda2aae725db1f2381`) reports no hunk on lines 42 or 64 of the compliance test file.

Invalidation check. The cited text neither cites, restates, nor depends on anything this changeset changed. The changeset adds symbols to `outcomeeng/distribution/profiles.py` (model prices; no existing symbol changes) and adds one filter to `outcomeeng/validation/profile_configuration.py` (`_is_authored_binding`, which drops a match whose binding reads a value or is an interpolation placeholder). The cited text hand-writes token and directory spelling and literal expected lines. The inputs it drives are literal and template-token bindings, which `_is_authored_binding` accepts exactly as the guard did before, so the expected result is unchanged and the defect does not depend on the filter.

**Settlement condition.** The compliance test holds no hand-written delimiter or token and no literal expected line, and a focused run of the node's tests plus a test-evidence audit over the repaired chain pass.

## DEBT [evidence]: native-field mapping tests hand-pick their inputs (f-004, f-005)

The same second `spec-tree:test-evidence-auditor` verdict at head `7e15b3c437ca8326e0e63dbd0e54d45a62245ba6` rejected two existing assertions in `spx/15-validation.enabler/32-runtime-token.enabler/tests/test_profile_configuration.mapping.l1.py`. The verdict carries no sealed run token.

- f-004 (REJECT, test-owned data): line 22, `test_every_native_field_assignment_is_rejected`, hand-picks three assignment shapes and the payload inline.
- f-005 (REJECT, alignment): line 15 drives only `MODEL_IDENTIFIERS` members; no generated non-member identifier matching `MODEL_IDENTIFIER_PATTERN` is driven, so the assertion cannot show that a non-member identifier passes.

Resolution shape: drive f-004 from the source-owned generator that owns `AUTHORED_BINDINGS` and `SURROUNDING_CONTEXTS`, and drive f-005 from a generator that produces non-member identifiers matching `MODEL_IDENTIFIER_PATTERN`.

Evidence that the text lies outside the change: `git diff -U0 origin/main...HEAD` (merge base `149a55f71befdf61e88be9bda2aae725db1f2381`) reports no hunk on line 15 or line 22 of the cited file.

Invalidation check. The cited text neither cites, restates, nor depends on anything this changeset changed. The changeset adds symbols to `outcomeeng/distribution/profiles.py` (model prices; no existing symbol changes) and adds one filter to `outcomeeng/validation/profile_configuration.py` (`_is_authored_binding`, which drops a match whose binding reads a value or is an interpolation placeholder). The cited tests drive literal `"value"` bindings and owned model identifiers; the filter leaves both results unchanged, and no symbol the tests use was renamed or altered.

**Settlement condition.** Both assertions take their inputs from source-owned generators, and a focused run plus a test-evidence audit over the repaired chain pass.

## DEBT [evidence]: runtime-token harness oracle reuses production enumeration (f-006, f-007)

The same second `spec-tree:test-evidence-auditor` verdict at head `7e15b3c437ca8326e0e63dbd0e54d45a62245ba6` rejected existing text in `outcomeeng_testing/harnesses/runtime_tokens.py`. The verdict carries no sealed run token.

- f-006 (REJECT, oracle-independence): line 104, `ignored_files` is computed with production `is_ignored()` and then compared by membership in the same table, so a defect in production is shared by the code and its check.
- f-007 (REJECT, oracle-independence): line 91, `expected_files` repeats the algorithm of `runtime_token_files()`, and `enforced_roots` is the single root `src` instead of the three roots the assertion names.

Resolution shape: give f-006 an independent oracle that does not call `is_ignored()`, and give f-007 an independent enumeration over `src/plugins`, `src/_shared`, and `src/templates`.

Evidence that the text lies outside the change: `git diff -U0 origin/main...HEAD` (merge base `149a55f71befdf61e88be9bda2aae725db1f2381`) reports no hunk on line 91 or line 104 of the cited file.

Invalidation check. The cited text neither cites, restates, nor depends on anything this changeset changed. The changeset adds symbols to `outcomeeng/distribution/profiles.py` (model prices; no existing symbol changes) and adds one filter to `outcomeeng/validation/profile_configuration.py` (`_is_authored_binding`, which drops a match whose binding reads a value or is an interpolation placeholder). The harness drives the runtime-token scanner and its ignore list; the changeset changes neither.

**Settlement condition.** The ignored-file oracle shares no predicate with production, the expected files come from an independent enumeration over the three named roots, and a focused run plus a test-evidence audit over the repaired chain pass.

## DEBT [consistency]: a read-expression prefix exempts a binding that also carries a literal

Local review run `2026-10-11_07-00-03-767-748ffd1ab022` at head `f40dc3cb3fe9b9eb646da1160692d1a6b3abe86e` reported, at `outcomeeng/validation/profile_configuration.py` (`_is_authored_binding`), that the guard decides the read-expression branch with a prefix match. A binding that begins with a call, a subscript, or an attribute access is therefore no assignment even when the rest of the binding carries an authored literal, as in `effort = settings.get("effort") or "high"` and `effort: lookup(key) if flag else "high"`. The interpolation-placeholder branch decides by the whole binding, so the two branches differ.

**Impact**: a native model or reasoning field bound to a read expression joined with a literal fallback passes the guard although the binding carries an authored value.

**Why it is a separate larger concern**: anchoring the read-expression decision to the whole binding needs a rule for where an expression ends: a boolean or conditional operator, an arithmetic operator, a closing delimiter of the surrounding code, or a trailing comment. Neither [`spx/15-validation.enabler/32-runtime-token.enabler/runtime-token.md`](spx/15-validation.enabler/32-runtime-token.enabler/runtime-token.md) nor [`spx/18-plugin-build.enabler/15-build-architecture.adr.md`](spx/18-plugin-build.enabler/15-build-architecture.adr.md) states that rule. The guard decides by the syntactic form of the binding alone and parses no expressions, so stating the rule is a ruling on the guard's grammar and not a pattern edit.

**Settlement condition.** The spec and the decision state where a read expression ends, the guard decides the read-expression branch by that rule, and the generator and the mapping and compliance tests drive a read expression joined with a literal fallback; a focused run of the node's tests passes.

## DEBT [consistency]: the interpolation placeholder forms have no owner but the guard's pattern

Local review run `2026-10-11_07-31-47-634-135100d3b226` at head `c75b66dd5d909083270ba559d80f748086122382` reported, at `outcomeeng/validation/profile_configuration.py` (`_INTERPOLATION_PLACEHOLDER`), that [`spx/15-validation.enabler/32-runtime-token.enabler/runtime-token.md`](spx/15-validation.enabler/32-runtime-token.enabler/runtime-token.md) and [`spx/18-plugin-build.enabler/15-build-architecture.adr.md`](spx/18-plugin-build.enabler/15-build-architecture.adr.md) state that a field bound to an interpolation placeholder is no assignment without saying which forms are placeholders. The pattern fixes an undeclared set: brace fields over a narrow character class, the percent conversions `s`, `d`, `r`, and `f`, and `$name` and `${name}`. Placeholders of the same families fall outside it and count as authored: `{name:>8}`, `%5s`, `%x`, `%i`, and `%(name)5d`.

**Impact**: a native model or reasoning field bound to a placeholder of a family the pattern omits is reported as an authored assignment, and the generator `PLACEHOLDER_BINDINGS` drives only the forms the pattern already accepts, so no test exposes the gap.

**Why it is a separate larger concern**: which placeholder forms exist is a ruling for the spec and the decision, as the expression-end rule above is. The guard recognizes the forms the spec and the decision name, and neither names a set. Widening the pattern without that ruling would move the set from one undeclared extent to another.

**Settlement condition.** The spec and the decision list the placeholder forms the guard recognizes, the guard matches that list, and the generator drives every listed form and the boundary forms named above; a focused run of the node's tests passes.
