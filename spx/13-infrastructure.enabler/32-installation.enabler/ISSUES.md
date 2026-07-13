# Installation issues

## Independent custom-agent provenance oracle

The checkout-local runtime evidence compares each installed custom-agent TOML
digest with the TOML rendered from the generated agent through
`convert_agents()` and `render_agent_toml()`. The test-evidence audit rejects
that oracle as insufficiently independent because `build_project_runtime()`
uses the same conversion path when installing agents.

Revisit when the expected agent identity can derive from a source-owned
generated-agent contract independently of the installation conversion path.
The evidence must still prove that every generated agent resolves from the
checkout-local runtime with content identity, not only name parity.
