<four_part_progression>

| Phase                   | Evidence                                | Confidence gain  |
| ----------------------- | --------------------------------------- | ---------------- |
| 1. Typical cases        | Happy paths and common scenarios        | Baseline         |
| 2. Edge and boundary    | Limits, special values, and error cases | Robustness       |
| 3. Systematic coverage  | Loops, states, and combinations         | Completeness     |
| 4. Property-based tests | Invariants across generated inputs      | Deep correctness |

Small pure functions often need phases 1 and 2. Complex algorithms often need all four. Glue code often needs phase 1 plus the correct outer-level evidence. Treat property-based tests as mandatory candidates for parsers, serializers, mathematical transformations, seed-driven generators, normalization rules, and algorithms with difficult edge cases.

</four_part_progression>
