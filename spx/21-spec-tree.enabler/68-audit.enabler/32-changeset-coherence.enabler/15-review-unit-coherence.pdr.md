# Review-Unit Coherence

A review unit is defined by semantic cohesion rather than a fixed size threshold. One review unit carries one independently understandable behavioral outcome, one coherent verification story, and one coherent rollback story; independently mergeable semantic clusters are separate review units, while deterministic generated fanout remains attached to its producer.

## Rationale

Semantic cohesion tracks reviewer context and independent mergeability more faithfully than raw line or file counts, while still allowing large mechanical transformations whose generated or repetitive breadth derives from one authored change.

## Product properties

1. A coherent review unit is independently understandable, verifiable, mergeable, and reversible without relying on an unrelated behavioral cluster.
2. A rejected aggregate receives a dependency-ordered sequence of review units that covers its authored artifacts and preserves required cross-unit dependencies.
3. Missing semantic or dependency evidence produces an unknown result that blocks publication until the evidence is resolved.

## Verification

### Eval

- ALWAYS: semantic cohesion, verification unity, rollback unity, and independent mergeability decide review-unit acceptance ([eval])
- ALWAYS: deterministic generated fanout is attributed to its producing authored artifact before review load is judged ([eval])
- NEVER: raw line count, file count, or an uncalibrated review-load score determines acceptance or rejection by itself ([eval])
- NEVER: a rejected or unknown coherence verdict authorizes publication ([eval])
