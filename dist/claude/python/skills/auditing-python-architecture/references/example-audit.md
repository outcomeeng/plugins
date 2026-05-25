# Example Architecture Review

This is a complete example of a REJECTED review showing all concern types.

# ARCHITECTURE REVIEW

**Decision:** REJECTED

## Verdict

| # | Concern               | Status | Detail                                   |
| - | --------------------- | ------ | ---------------------------------------- |
| 1 | Section structure     | PASS   | Uses authoritative sections only         |
| 2 | Testability in Compl. | REJECT | Compliance has no DI/no-mocking rules    |
| 3 | Atemporal voice       | REJECT | Context narrates code state              |
| 4 | Mocking prohibition   | REJECT | "Mock at the PyTrakt API boundary"       |
| 5 | Level accuracy        | REJECT | `l2` assigned to SaaS service (Trakt.tv) |
| 6 | Anti-patterns         | PASS   | No phantom sections                      |
| 7 | Ancestor consistency  | PASS   | Consistent with product ADRs             |

---

## Violations

### `l2` Assigned to SaaS Service

**Where:** Compliance section, "`l2` for Trakt list operations"
**Concern:** Level accuracy
**Why this fails:** Trakt.tv is a SaaS service that cannot run locally. Per `/testing` Five Factors: SaaS services have no `l2` -- jump from `l1` to `l3`.

**Correct approach:**

```markdown
### MUST

- List operations accept a `TraktListProvider` Protocol parameter --
  enables `l1` testing with controlled implementation ([review])
- Real Trakt API testing uses test account at `l3` ([review])
```

---

### Mocking External Services

**Where:** Compliance section, "Mock at the PyTrakt API boundary"
**Concern:** Mocking prohibition
**Why this fails:** Violates the NO MOCKING cardinal rule. Use dependency injection with Protocol interfaces instead.

**Correct approach:**

```python
class TraktListProvider(Protocol):
    def __call__(self, list_name: str, username: str) -> Any | None: ...


# l1: Inject controlled implementation (Exception 1: Failure modes)
# l3: Use real PyTrakt
```

---

### Missing Testability in Compliance

**Where:** Compliance section
**Concern:** Testability in Compliance
**Why this fails:** The Compliance section has constraints for data validation but no MUST/NEVER rules for dependency injection or mocking prohibition. Without these, nothing prevents direct API calls or mocking in tests.

---

### Temporal Language in Context Section

**Where:** Context section, "The current PyTrakt wrapper in trakt_client.py uses direct API calls without dependency injection, making it impossible to test at `l1`."
**Concern:** Atemporal voice
**Why this fails:** Narrates code state -- becomes false the moment the file changes. The ADR states what the architecture IS, not what code currently exists.

**Correct approach:**

```markdown
**Technical constraints:** List operations depend on a SaaS API (Trakt.tv)
that cannot run locally. Dependency injection isolates business logic from
API transport.
```

---

## Required Changes

1. Remove all `l2` assignments for SaaS operations
2. Remove "Mock at boundary" language
3. Add DI Protocol definitions in Compliance per `/standardizing-python-architecture`
4. Document which exception case justifies any test doubles
5. Rewrite Context section in atemporal voice -- remove all references to current code state

---

## References

- /standardizing-python-architecture: `<adr_sections>` (authoritative sections)
- /standardizing-python-architecture: `<testability_in_compliance>` (MUST/NEVER pattern)
- /standardizing-python-architecture: `<atemporal_voice>` (temporal patterns)
- /standardizing-python-architecture: `<di_patterns>` (mocking prohibition)
- /testing: Stage 2 Factor 2 (SaaS services jump `l1` to `l3`)
- /testing: Cardinal Rule (no mocking)

---

Revise and resubmit.
