# PLAN — migrate 21-backend-abstraction.adr.md to the lean decision template

Coordination note for a dedicated, human-reviewed migration. Verify every claim here against the current tree before acting — it is a stale-prone input, not authority.

## Goal

Migrate `spx/21-spec-tree.enabler/16-verification.enabler/21-thread-store.enabler/21-backend-abstraction.adr.md` from the legacy seven-section layout (`## Purpose` / `## Context` / `## Decision` / `## Rationale` / `## Trade-offs accepted` / `## Compliance` with `### Recognized by` / `### MUST` / `### NEVER`) to the canonical decision-first template, matching the TS/Python/Rust architecture-skill exemplars and the `15-audit-verdict-format.pdr.md` migration #117 produced.

Target structure (from `src/plugins/spec-tree/skills/understanding/templates/decisions/decision-name.adr.md`):

- `# Backend Abstraction` then the decision stated directly in the opening (no `## Purpose`, no `## Context`).
- `## Rationale` — fold the Context business-impact/technical-constraints and the Trade-offs reasoning into dense prose; name a rejected alternative only when it sharpens the decision.
- `## Invariants` (optional) — only if an algebraic property holds for all governed code.
- `## Verification` with `### Testing` / `### Eval` / `### Audit` subsections; include only those that apply.

## Key simplification — the implementing spec already carries the test coverage

`21-backend-abstraction.adr.md`'s `## Compliance` has 13 rules, 12 tagged `([test](tests/…))` path links plus one `([review])`. Decision records carry **pathless** evidence-type tags (the path lives on the implementing spec). The implementing spec `thread-store.md` **already** carries `[test](tests/…)` assertions for every test file the ADR references:

- `tests/test_backend_protocol.compliance.l1.py` — `thread-store.md` Compliance (Backend protocol conformance)
- `tests/test_thread_store.compliance.l1.py` — `thread-store.md` Compliance (atomicity, slug re-export, root confinement, harness shape)
- `tests/test_cli.compliance.l1.py` — `thread-store.md` Compliance (CLI routes through facade; optional `--slug`)
- `tests/test_slug.property.l1.py` — `thread-store.md` Properties (idempotent, injective, path-safe, bounded)
- `tests/test_plugin_portability.compliance.l1.py` — `thread-store.md` Compliance (stdlib-only; no direct backend import)

So the migration needs **no new tests and no path-moving** — the deterministic coverage stays on `thread-store.md`. The ADR's rules become pathless evidence-type tags; the paths are dropped.

## Per-rule routing (route each through `/testing` by claim shape — do not hand-pick)

The 13 ADR rules are architecture guarantees about the persistence design. Classify each:

- Rules whose claim is a deterministic property/contract already proven on `thread-store.md` (protocol conformance, slug contract, atomic write, root confinement, stdlib-only) → `### Testing` with the matching evidence type (`compliance`, `property`, `scenario`) — pathless.
- Rules that are pure architecture judgment with no deterministic oracle (DI-not-mocking as the intended strategy; env-var selection keeps skills backend-unaware; one-way dependency direction) → `### Audit` with `([audit])`.
- The single `([review])` rule (backend selection via `SPX_VERIFY_BACKEND`) → it is deterministically tested by `thread-store.md` scenarios, so route to `### Testing ([scenario])`, or `### Audit ([audit])` if framed as an architecture guarantee — `/testing` decides by claim shape.

Do not relitigate a choice `/testing` leaves open between equally-valid types.

## Steps

1. `/understanding` (load), then `/contextualizing spx/21-spec-tree.enabler/16-verification.enabler/21-thread-store.enabler`.
2. Read `21-backend-abstraction.adr.md` and `thread-store.md` together; for each of the 13 ADR rules, confirm the matching coverage on `thread-store.md` and route the rule through `/testing` for its evidence type.
3. Rewrite to the lean template: decision in the opening; Context + Trade-offs folded into `## Rationale`; rich Decision-body detail (the slug-grammar contract, the `BRANCH_SLUG_MAX_LENGTH = 64` rule) kept in the opening/Rationale; `## Verification` with the routed `### Testing`/`### Audit` rules, all tags pathless.
4. Atemporal voice throughout (no "we discovered", no current-code narration).
5. Gates: `/audit-adr` clean; `just check` green; local `changes-reviewer` at parity converged. Spec-only change → no plugin version bump.
6. On completion, mark this record done in the `spx/ISSUES.md` "Migrate the remaining decision records" entry and delete this PLAN.md.
