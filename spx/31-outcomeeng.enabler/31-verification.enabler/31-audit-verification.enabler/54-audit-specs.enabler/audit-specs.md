# Audit Specs

PROVIDES an audit methodology for deciding whether a spec node is structurally valid, atemporal, and tagged with evidence that fits each claim
SO THAT artifact-type spec auditors across delivery plugins
CAN reject malformed declarations and prose-coupled test claims consistently

## Node Spec Evidence Model

The audit checks three properties in order:

1. **Section structure** — the node opens with its kind statement and carries an `## Assertions` section whose headings describe claim shape independently of verification type.
2. **Atemporal voice** — the node states product truth rather than history.
3. **Per-assertion tag fitness** — every assertion carries exactly one reachable verification-type tag, and a `[test]` assertion type fits the claim's quantifier.

A claim whose subject is authored prose or documentation content cannot carry `[test]`: reading authored text proves that text exists rather than that executable behavior fulfills the claim. Such a claim uses `[eval]` when a structured producer verdict can be scored and `[audit]` otherwise.

## Assertions

### Compliance

- ALWAYS: check section structure, atemporal voice, and per-assertion tag fitness in that order ([audit])
- ALWAYS: interpret assertion headings as claim-shape groupings independently of verification type, so universal `[audit]` rules remain under `### Compliance` without acquiring the test-only compliance assertion type ([audit])
- ALWAYS: verify each `[test]` assertion's assertion type fits the claim's quantifier per the test router — a universal is never `scenario` — without relitigating a choice the router leaves open ([audit])
- ALWAYS: flag a `[test]` tag on a claim whose subject is authored prose or documentation content, whether the evidence reads that content directly or through test infrastructure ([audit])
- NEVER: classify a node's content as architecture-versus-product behavior — that classification belongs to decision-record auditing ([audit])
- NEVER: inspect linked test quality inside the node-spec audit — test evidence has its own artifact-type audit ([audit])
