<dependency_design>

Read the governing skill's explicit launch instructions. Classify calls by their
dependency on artifacts, then express that dependency in the skill's workflow.

| Shape        | Use                                                                     |
| ------------ | ----------------------------------------------------------------------- |
| Sequential   | A later task requires an artifact produced by an earlier task           |
| Independent  | Several explicitly requested tasks read independent committed subjects  |
| Verification | A completed authoring subject is judged in an isolated verifier session |

The native tool schema and root guide own invocation mechanics. This reference
supplies no additional launch trigger or tool-call schema.

</dependency_design>

<sequence>

1. Establish the exact committed subject each invocation reads.
2. Dispatch the configured role with the skill's target.
3. Collect the native result and preserve its identity.
4. Validate the declared result contract before using the artifact in a dependent step.
5. Follow the owning skill's failure or finding-repair workflow.

</sequence>

<independent_calls>

Use independent calls only when the active skill explicitly requests them and their
subjects can be read without depending on unfinished authoring work. Keep each result
associated with its exact role and target. Changes to a subject reopen the evidence
whose verdict depended on that version.

</independent_calls>

<profile_selection>

Read each role's central profile selection from its configuration and governing
requirement. Coordination, verification, and implementation are responsibilities;
none automatically selects Strong or Fast.

</profile_selection>
