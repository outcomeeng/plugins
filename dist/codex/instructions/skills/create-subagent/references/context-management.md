<target_discovery>

1. Start from the supplied path or scope and the configured instructions.
2. Load the invoked skill's required context using its existing workflow.
3. Read durable decisions and specs independently before examining their evidence and implementation.
4. Track which artifacts and exact revisions support each finding.
5. Use focused retrieval for further questions the target exposes.

The calling prompt contains only the target. Apply the verifier isolation boundary
from `/subagent-standards`; the authoring conversation supplies no evidence packet.

</target_discovery>

<long_work>

Use the owning skill's context and continuation mechanism when a task exceeds one
context window. Preserve source paths and exact evidence identities so the next
context can reload the subject. Distinguish observations made by the verifier from
requirements declared by the product.

After compaction, re-establish the foundation and target context required by the active
workflow. A summary identifies where to resume; it cannot replace required source reads.

</long_work>

<cache_and_memory>

Keep stable role instructions in the configured definition and task-dependent evidence
in the target-discovery workflow. Use native caching or memory only where the role's
actual work justifies it and the current harness exposes that capability.

Inspect what a resumed invocation receives before treating it as independent
verification. An inherited authoring transcript remains authoring context even when
stored in a summary, memory file, or another session.

</cache_and_memory>
