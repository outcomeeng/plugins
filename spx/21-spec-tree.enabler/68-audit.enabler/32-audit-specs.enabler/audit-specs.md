# Audit Specs

PROVIDES an audit methodology verifying a spec node declares a well-formed node whose assertions carry a valid verification-type tag that fits each claim — including that a claim about authored prose or documentation content never carries `[test]`
SO THAT all spec-tree projects
CAN eliminate malformed node specs and stop prose-bound claims from masquerading as behavioral `[test]` evidence before they accumulate

## Node Spec Evidence Model

The audit answers one question: **does this spec node declare a well-formed node whose assertions carry a valid verification-type tag that fits each claim?**

Three properties checked in order:

1. **Section structure** — the node opens with its kind statement (an enabler's `PROVIDES … SO THAT … CAN …` or an outcome's `WE BELIEVE THAT … WILL … CONTRIBUTING TO …`) and carries an `## Assertions` section; claim-shape headings group assertions by quantifier and form independently of each assertion's verification-type tag
2. **Atemporal voice** — the node states product truth, never history
3. **Per-assertion tag validity, evidence-type fit, and coupling fitness** — every assertion carries exactly one verification-type tag (`[test]`, `[eval]`, or `[audit]`); a `[test]` assertion's assertion type fits the claim's quantifier (a universal is never `scenario`); and a claim whose subject is authored prose or documentation content — text the product authors and maintains in a document, not executable behavior — never carries `[test]`

## Per-assertion Tag Fitness Model

A `[test]` assertion's assertion type is chosen from the claim's shape via `/test` (see `spx/21-spec-tree.enabler/35-evidence.enabler/evidence.md`). The audit verifies the selection fits the claim and does not relitigate a choice the router leaves open between equally valid types. The heading describes the claim's shape for every verification type: a universal audit-backed rule remains under `### Compliance` without acquiring the test-only compliance assertion type. A missing tag, a bare mechanism tag, more than one tag, a claim whose shape disagrees with its heading, or an assertion type the router would not produce for a `[test]` claim is a finding.

The **prose-coupling** check is the verification-type analog: when a claim's subject is the content of an authored prose or documentation artifact rather than executable behavior, behavioral evidence cannot verify it — evidence would read the authored text and assert on it, proving the prose was authored rather than that code behaves, whether the read is direct or laundered through test infrastructure. Such a claim's verification type is `[eval]` (a graded judgment over the producer's structured verdict) or `[audit]` (a semantic constraint), never `[test]`. A `[test]` tag on a prose-content claim is a finding; the remediation retags it `[eval]` or `[audit]`.

## Assertions

### Scenarios

- Given a spec node missing or malforming its kind statement, missing its `## Assertions` section, or carrying a claim-shape heading mismatched to its assertions, when audited by `/audit-specs`, then the verdict is REJECT with a structure finding (`missing-section`, `malformed-kind-statement`, or `heading-mismatch`) ([eval](evals/structure/eval.toml))
- Given a spec node with universal `[audit]` assertions under `### Compliance`, when audited by `/audit-specs`, then the verdict is APPROVED because the heading describes claim shape independently of verification type ([eval](evals/structure/eval.toml))
- Given a spec node that replaces the canonical claim-shape heading with a verification-type heading such as `### Audit`, when audited by `/audit-specs`, then the verdict is REJECT with finding category "heading-mismatch" ([eval](evals/structure/eval.toml))
- Given a spec node with temporal language in any section, when audited by `/audit-specs`, then the verdict is REJECT with finding category "temporal-voice" ([eval](evals/voice/eval.toml))
- Given a spec node whose assertion carries a bare mechanism tag, no tag, or more than one tag, when audited by `/audit-specs`, then the verdict is REJECT with finding category "invalid-tag" ([eval](evals/tag-validity/eval.toml))
- Given a spec node whose `[test]` assertion tags a universal claim (ALWAYS/NEVER/"for all") as `scenario`, when audited by `/audit-specs`, then the verdict is REJECT with finding category "evidence-type-mismatch" ([eval](evals/tag-validity/eval.toml))
- Given a spec node whose `[test]` assertion makes a claim about the content of an authored prose or documentation artifact, when audited by `/audit-specs`, then the verdict is REJECT with finding category "prose-coupling" ([eval](evals/prose-coupling/eval.toml))
- Given a spec node where structure, voice, and every assertion's tag fitness all hold, when audited by `/audit-specs`, then the verdict is APPROVED ([eval](evals/structure/eval.toml))

### Compliance

- ALWAYS: check section structure, atemporal voice, and per-assertion tag fitness in that order ([audit])
- ALWAYS: interpret assertion headings as claim-shape groupings independently of verification type, so universal `[audit]` rules remain under `### Compliance` without acquiring the test-only compliance assertion type ([audit])
- ALWAYS: verify each `[test]` assertion's assertion type fits the claim's quantifier per the `/test` router — a universal is never `scenario` — without relitigating a choice the router leaves open ([audit])
- ALWAYS: flag a `[test]` tag on a claim whose subject is authored prose or documentation content — the verification belongs in `[eval]` or `[audit]`, and the check holds whether the would-be evidence reads the authored artifact directly or through test infrastructure ([audit])
- ALWAYS: `/audit-specs` names no caller and stays invocable on its own; the author context produces a verdict by dispatching the audit to a separate verifier context rather than grading its own work in place, per `spx/31-outcomeeng.enabler/31-verification.enabler/14-verification.pdr.md` ([audit])
- NEVER: classify a node's content as architecture-versus-product-behavior — that classification is the decision-record audits' concern, not the node audit's ([audit])
