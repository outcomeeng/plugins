# Known issues — source and templating enabler

## FOLLOW-UP [evidence]: require_skill target-equivalence assertion is implicit

The compliance assertion says `{!% require_skill 'plugin:skill' %!}` expands to
identical coding-agent-neutral invocation text in both targets. Current tests
verify that the directive expands and that the rendered text names the required
skill, but they do not explicitly compare Claude-target and Codex-target output
bytes for the same source input.

The implementation guarantee is structural: `expand_require_skill` has no target
parameter, and target-specific path rewriting does not change the expansion
because the text contains no `${CLAUDE_SKILL_DIR}` token. Future evidence work in
this node should add a direct two-target comparison so the assertion remains
visible from the tests rather than only from source structure.

## FOLLOW-UP [coverage]: recursive include expansion and cycle detection are unspecified

`render_text` recursively expands directives found inside an included
fragment's body (`_render_directives` re-processes the inlined body) and raises
`CyclicIncludeError` when includes form a cycle; it also runs a Jinja pass when
the rendered output contains the variable delimiter `{{!`. None of these
behaviors is named by a spec assertion. The verbatim-inlining property
(`test_render_text.property.l1.py`) is deliberately scoped to directive-free,
variable-delimiter-free bodies precisely because render-level verbatim is
conditional on the absence of those tokens.

Required handling: add assertions (and `[test]` evidence) for recursive include
expansion, cycle detection (`CyclicIncludeError`), and the variable-delimiter
Jinja pass — each a behavior the build relies on but the spec does not yet
declare. Larger than a single property test; route through `/authoring` +
`/testing`.

Surfaced while reworking the verbatim-preservation evidence from named example
bodies into generated properties.
