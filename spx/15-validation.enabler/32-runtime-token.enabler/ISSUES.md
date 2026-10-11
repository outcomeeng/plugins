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

## DEBT [evidence]: existing harness and test hand-write build-token text (f-002, f-003)

A `spec-tree:test-evidence-auditor` verdict on this node at head `dd0d8cd6678c7619f1474d35f12e81f0df52e3c2` rejected two pieces of existing text with the same defect. The verdict carries no sealed run token. Every entry below that cites this audit shares that property.

- f-002: `outcomeeng_testing/harnesses/profile_validation.py:27` hand-writes build token delimiters and directory names in the harness.
- f-003: `spx/15-validation.enabler/32-runtime-token.enabler/tests/test_profile_configuration.compliance.l1.py:64` holds an existing hand-written token.

Both defects are the same class: the text spells out what the contracts owner and the shared path owner define, so a change to either owner leaves the evidence asserting the old spelling.

Resolution shape: build the delimiters from the contracts-owned delimiters, build the token with `format_runtime_token`, and build the directory names from the shared path owner.

Evidence that the text lies outside the change: `git diff -U0 origin/main...HEAD` (merge base `149a55f71befdf61e88be9bda2aae725db1f2381`) reports no hunk on `outcomeeng_testing/harnesses/profile_validation.py`, and none on line 64 of the compliance test file.

**Settlement condition.** Neither cited location holds a hand-written delimiter, directory name, or token, and a focused run of the node's tests plus a test-evidence audit over the repaired chain pass.

## DEBT [evidence]: native-field mapping tests hand-pick their inputs (f-004, f-005)

The same `spec-tree:test-evidence-auditor` verdict at head `dd0d8cd6678c7619f1474d35f12e81f0df52e3c2` rejected two existing assertions in `spx/15-validation.enabler/32-runtime-token.enabler/tests/test_profile_configuration.mapping.l1.py`. The verdict carries no sealed run token.

- f-004: line 22, `test_every_native_field_assignment_is_rejected`, hand-picks the assignment shapes it drives.
- f-005: line 15, the existing assertion on identifiers absent from the profiles, is never driven past the profile members, so it cannot show that a non-member identifier passes.

Resolution shape: drive f-004 from a generator that owns the shapes, and drive f-005 from a generator that produces non-member identifiers.

Evidence that the text lies outside the change: `git diff -U0 origin/main...HEAD` (merge base `149a55f71befdf61e88be9bda2aae725db1f2381`) reports no hunk on line 15 or line 22 of the cited file.

**Settlement condition.** Both assertions take their inputs from source-owned generators, and a focused run plus a test-evidence audit over the repaired chain pass.

## DEBT [evidence]: runtime-token compliance test reuses production enumeration and magic line numbers (f-006, f-007)

The same `spec-tree:test-evidence-auditor` verdict at head `dd0d8cd6678c7619f1474d35f12e81f0df52e3c2` rejected existing text in `spx/15-validation.enabler/32-runtime-token.enabler/tests/test_runtime_token.compliance.l1.py`. The verdict carries no sealed run token.

- f-006 (REJECT): line 34, the oracle reuses the production enumeration, so a defect in the enumeration is shared by the code and its check.
- f-007 (WARNING): line 42 holds magic line numbers.

Resolution shape: give f-006 an independent oracle that does not import the production enumeration, and derive the f-007 line numbers from the generated source.

Evidence that the text lies outside the change: `git diff -U0 origin/main...HEAD` (merge base `149a55f71befdf61e88be9bda2aae725db1f2381`) reports no hunk on this file, so lines 34 and 42 are unchanged.

**Settlement condition.** The oracle shares no enumeration with production, no literal line number remains, and a focused run plus a test-evidence audit over the repaired chain pass.
