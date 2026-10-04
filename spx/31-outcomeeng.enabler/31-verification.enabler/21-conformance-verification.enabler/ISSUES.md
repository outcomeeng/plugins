# Issues: Conformance verification

Known defects, contradictions and gaps in this node. Coordination note; not spec truth.

## The conformance machinery exists only as declarations

The emitter reference implementation, the contract schema, the checker, the inference and the aggregation are built in the external component `spx/31-outcomeeng.enabler/31-verification.enabler/18-verification-component.adr.md` places outside this repository. The component's build plan owns the runner bake-off and the golden-trace corpus, one frozen trace per violation code, authored before the checker. The component repository's name and bootstrap await operator direction.

**Settlement condition.** The component repository exists, its first release carries the emitter, schema and checker, and this node's assertions comply with it.

## No shipped skill is instrumented for conformance checking

`spx/31-outcomeeng.enabler/31-verification.enabler/21-conformance-verification.enabler/15-skill-instrumentation.pdr.md` requires every contract-relevant state to be a script call. No shipped skill meets it, and the instrumentation policy has not reached the skill-authoring standards in the `instructions` plugin, so new skills are not designed with script-realized states.

**Settlement condition.** One shipped skill is restructured so every contract-relevant state is a script call, with stdout-cleanliness evidence, and the policy reaches the skill-authoring standards in a cross-plugin changeset.
