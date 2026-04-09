# Context Loading

WE BELIEVE THAT loading complete spec-tree context deterministically before any implementation work
WILL eliminate implementations that miss requirements or violate architectural decisions
CONTRIBUTING TO reduced rework and higher first-pass implementation quality

## Assertions

### Scenarios

- Given a target node with a complete ancestor chain, when context is loaded, then all ancestor specs, lower-index sibling specs, and ADRs/PDRs are read ([test](tests/test_context_loading.unit.py))
- Given a target node with a missing ancestor spec, when context is loaded, then the skill aborts with the missing file path and remediation guidance ([test](tests/test_context_loading.unit.py))
- Given an empty tree with only a product spec, when context is loaded for authoring, then an empty manifest with `bootstrap=true` is returned ([test](tests/test_context_loading.unit.py))
- Given a target node at index 43 with siblings at indices 15, 21, and 65, when context is loaded, then siblings at 15 and 21 are read and sibling at 65 is not ([test](tests/test_context_loading.unit.py))

### Properties

- Context loading is deterministic: the same tree structure and target always produces the same context manifest ([test](tests/test_context_loading.unit.py))

### Compliance

- ALWAYS: read every ADR/PDR returned by globs — do not filter by title relevance ([review])
- NEVER: proceed with partial context — abort if any required document is missing ([review])
