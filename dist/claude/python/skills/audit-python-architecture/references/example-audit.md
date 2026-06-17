# Example Architecture Review

This is a complete example of a REJECTED review showing all concern types.

# ARCHITECTURE REVIEW

**Decision:** REJECTED

## Verdict

| # | Concern               | Status | Detail                                   |
| - | --------------------- | ------ | ---------------------------------------- |
| 1 | Section structure     | PASS   | Uses authoritative sections only         |
| 2 | Testability in Verif. | REJECT | Verification has no DI/no-mocking rules  |
| 3 | Atemporal voice       | REJECT | Decision statement narrates code state   |
| 4 | Mocking prohibition   | REJECT | "Mock at the PyTrakt API boundary"       |
| 5 | Level accuracy        | REJECT | `l2` assigned to SaaS service (Trakt.tv) |
| 6 | Anti-patterns         | PASS   | No phantom sections                      |
| 7 | Ancestor consistency  | PASS   | Consistent with product ADRs             |

---

## Violations

### `l2` Assigned to SaaS Service

**Where:** `## Verification`, "`l2` for Trakt list operations"
**Concern:** Level accuracy
**Why this fails:** Trakt.tv is a SaaS service that cannot run locally. Per `/test` Five Factors: SaaS services have no `l2` -- jump from `l1` to `l3`.

**Correct approach:**

```markdown
### Audit

- ALWAYS: list operations accept a `TraktListProvider` Protocol parameter --
  enables `l1` testing with controlled implementation ([audit])
- ALWAYS: real Trakt API testing uses a test account at `l3` ([audit])
```

---

### Mocking External Services

**Where:** `## Verification`, "Mock at the PyTrakt API boundary"
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

### Missing Testability in Verification

**Where:** `## Verification`
**Concern:** Testability in Verification
**Why this fails:** The `## Verification` rules cover data validation but include no ALWAYS/NEVER rules for dependency injection or mocking prohibition. Without these, nothing prevents direct API calls or mocking in tests.

---

### Temporal Language in the Decision Statement

**Where:** decision statement, "The current PyTrakt wrapper in trakt_client.py uses direct API calls without dependency injection, making it impossible to test at `l1`."
**Concern:** Atemporal voice
**Why this fails:** Narrates code state -- becomes false the moment the file changes. The ADR states what the architecture IS, not what code currently exists.

**Correct approach:**

```markdown
List operations use dependency injection to isolate business logic from the
SaaS API (Trakt.tv) transport, which cannot run locally.
```

---

## Required Changes

1. Remove all `l2` assignments for SaaS operations
2. Remove "Mock at boundary" language
3. Add DI Protocol definitions under `## Verification`'s `### Audit` per `/python-architecture-standards`
4. Document which exception case justifies any test doubles
5. Rewrite the decision statement in atemporal voice -- remove all references to current code state

---

## References

- /python-architecture-standards: `<adr_sections>` (authoritative sections)
- /python-architecture-standards: `<testability_in_verification>` (ALWAYS/NEVER pattern)
- /python-architecture-standards: `<atemporal_voice>` (temporal patterns)
- /python-architecture-standards: `<di_patterns>` (mocking prohibition)
- /test: Stage 2 Factor 2 (SaaS services jump `l1` to `l3`)
- /test: Cardinal Rule (no mocking)

---

Revise and resubmit.
