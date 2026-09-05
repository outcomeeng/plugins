You are the main authoring conversation of a coding agent working in a repository governed by the Spec Tree methodology. The repository's root instruction file carries no subagent dispatch mechanics and no role-task contracts: that guidance loads with the dispatching skill, as the verifier-dispatch reference reproduced below, one copy per agent harness.

Answer the case's question about dispatching the named configured verifier or reviewer role, using only the reference copy for the harness the case names. Name every role and tool exactly as that harness's reference copy spells it.

Case {case_id}:

{input_json}

Respond with only a JSON object of this shape, with no prose and no code fence. Use null for a field the case's harness or question leaves inapplicable:

{
"harness": "<claude or codex>",
"role": "<the exact agent-type string the reference uses for the role on that harness>",
"dispatch_mechanism": "<the exact tool the reference names for launching the role on that harness>",
"message_content": "<raw-scope-token or explicit-role-task-prompt>",
"success_output": "<sealed-review-journal-token, run-token-and-projection, or structured-json-verdict>",
"gate_on_missing_or_malformed_output": "<blocked or passed>",
"collection_tool": "<the exact tool the reference names for collecting the result on that harness, or null>",
"timeout_ms": "<the wait timeout in milliseconds the reference assigns for the role, as a number, or null>"
}

The verifier-dispatch reference for each harness follows, path-labeled.

{producer_files}
