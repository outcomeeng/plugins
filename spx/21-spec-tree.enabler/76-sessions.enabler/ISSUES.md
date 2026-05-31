# ISSUES: sessions enabler

## 1. Multi-ID pickup spec assertion and test coverage

The spec asserts singular pickup behavior while the picking-up skill documents `spx session pickup [ids...]` (plural). Add a spec assertion for multi-ID pickup and a corresponding test (mirroring `test_release_multiple_ids_in_single_invocation`).

Surfaced by: spec-tree-review on PR #96 (FOLLOW-UP [consistency]).
