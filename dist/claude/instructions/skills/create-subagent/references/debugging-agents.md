<inspect_the_observed_run>

1. Read the actual configuration and the native loader's diagnostic.
2. Compare the requested role with the configured dispatch name and installation record.
3. Inspect the invocation's supplied target and context-isolation setting.
4. Read available progress, tool observations, and the final response.
5. Identify whether the evidence supports a configuration, discovery, launch, execution,
   or result-contract failure.

Use observations already exposed by the native harness. A claim that the workflow is
unobservable cannot replace inspecting those observations.

</inspect_the_observed_run>

<diagnostic_record>

Retain the configured role, target, exact subject revision, complete native
configuration, call result, and final output. Include only task-relevant diagnostic
data; keep credentials and unrelated user content out of the record.

State what the evidence proves and which boundary remains unknown. For a stale
registry, distinguish the installed artifact from the definitions the session actually
loaded. For a malformed result, identify the missing or invalid contract field.

</diagnostic_record>

<correction>

Return the failing boundary and its supporting evidence to the invoking workflow.
That workflow owns corrections and any later verification of a changed subject.
Apply the one-call failure policy from `/subagent-standards` throughout diagnosis.

</correction>
