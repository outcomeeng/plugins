<test_double_taxonomy>

Read this catalog only when a Stage 5 exception case matches and the controlled implementation must be selected. Routine evidence design at Stages 1–4 uses the real dependency and never reaches this file.

| Type  | Purpose                           | Use for                                     |
| ----- | --------------------------------- | ------------------------------------------- |
| Stub  | Returns predetermined responses   | Failure simulation, safety, contract probes |
| Spy   | Records calls for verification    | Interaction protocols, observability        |
| Fake  | Simplified working implementation | Time control, combinatorial cost            |
| Dummy | Placeholder that is never called  | Satisfying type requirements                |

Framework mocks remain forbidden. Supply a recording collaborator or spy through dependency injection when call recording is required.

Each controlled implementation preserves the behavior boundary the assertion claims. A double that replaces the behavior under test, rather than the dependency that behavior crosses, fails the exception it was admitted under.

</test_double_taxonomy>
