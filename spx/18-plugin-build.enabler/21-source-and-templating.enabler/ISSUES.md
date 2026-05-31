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
