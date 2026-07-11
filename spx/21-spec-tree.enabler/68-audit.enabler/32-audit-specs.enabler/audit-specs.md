# Audit Specs

PROVIDES an audit methodology verifying a spec node declares a well-formed node whose assertions carry a valid verification-type tag that fits each claim — including that parseable runtime/configuration contracts may use deterministic evidence while semantic claims about authored prose or documentation content never carry `[test]`
SO THAT all spec-tree projects
CAN eliminate malformed node specs, preserve deterministic conformance for parseable contracts, and block prose-bound claims from masquerading as behavioral `[test]` evidence

## Node Spec Evidence Model

The audit answers one question: **does this spec node declare a well-formed node whose assertions carry a valid verification-type tag that fits each claim?**

Three properties checked in order:

1. **Section structure** — the node opens with its kind statement (an enabler's `PROVIDES … SO THAT … CAN …` or an outcome's `WE BELIEVE THAT … WILL … CONTRIBUTING TO …`) and carries an `## Assertions` section; assertion-type headings appear only where that type applies
2. **Atemporal voice** — the node states product truth, never history
3. **Per-assertion tag validity, evidence-type fit, and coupling fitness** — every assertion carries exactly one verification-type tag (`[test]`, `[eval]`, or `[audit]`; `[review]` is the compatibility form of `[audit]`); a `[test]` assertion's assertion type fits the claim's quantifier (a universal is never `scenario`); a claim about a parseable runtime or configuration contract may carry `[test]` when deterministic evidence checks structure such as field presence, schema conformance, registered command shape, generated output shape, or configured section names; and a claim whose subject is semantic authored prose or documentation content — text the product authors and maintains in a document, not executable or parseable structure — never carries `[test]`

## Per-assertion Tag Fitness Model

A `[test]` assertion's assertion type is chosen from the claim's shape via `/test` (see `spx/21-spec-tree.enabler/35-evidence.enabler/evidence.md`). The audit verifies the selection fits the claim and does not relitigate a choice the router leaves open between equally valid types. A missing tag, a bare mechanism tag, a tag that disagrees with its heading, more than one tag, or an assertion type the router would not produce for the claim is a finding.

The **prose-coupling** check is the verification-type analog: when a claim's subject is the semantic content of an authored prose or documentation artifact rather than executable behavior or parseable structure, behavioral evidence cannot verify it — evidence would read the authored text and assert on it, proving the prose was authored rather than that code behaves, whether the read is direct or laundered through test infrastructure. Such a claim's verification type is `[eval]` (a graded judgment over the producer's structured verdict) or `[audit]` (a semantic constraint), never `[test]`. A `[test]` tag on a prose-content claim is a finding; the remediation retags it `[eval]` or `[audit]`. A parseable runtime or configuration contract stays eligible for deterministic `[test]` evidence when the test checks the structural contract rather than prose meaning.

## Assertions

### Scenarios

- Given a spec node missing or malforming its kind statement, missing its `## Assertions` section, or carrying an assertion-type heading mismatched to its assertions, when audited by `/audit-specs`, then the overall verdict is FAIL with a structure finding (`missing-section`, `malformed-kind-statement`, or `heading-mismatch`) ([eval](evals/structure/eval.toml))
- Given a spec node with temporal language in any section, when audited by `/audit-specs`, then the overall verdict is FAIL with finding category "temporal-voice" ([eval](evals/voice/eval.toml))
- Given a spec node whose assertion carries a bare mechanism tag, no tag, or more than one tag, when audited by `/audit-specs`, then the overall verdict is FAIL with finding category "invalid-tag" ([eval](evals/tag-validity/eval.toml))
- Given a spec node whose `[test]` assertion tags a universal claim (ALWAYS/NEVER/"for all") as `scenario`, when audited by `/audit-specs`, then the overall verdict is FAIL with finding category "evidence-type-mismatch" ([eval](evals/tag-validity/eval.toml))
- Given a spec node whose `[test]` assertion makes a claim about the content of an authored prose or documentation artifact, when audited by `/audit-specs`, then the overall verdict is FAIL with finding category "prose-coupling" ([eval](evals/prose-coupling/eval.toml))
- Given a spec node with a well-formed kind statement, an `## Assertions` section, and assertion-type headings that match their assertions, when audited by `/audit-specs`, then the section-structure row is PASS ([eval](evals/structure/eval.toml))

### Compliance

- ALWAYS: check section structure, atemporal voice, and per-assertion tag fitness in that order ([review])
- ALWAYS: verify each `[test]` assertion's assertion type fits the claim's quantifier per the `/test` router — a universal is never `scenario` — without relitigating a choice the router leaves open ([review])
- ALWAYS: allow `[test]` on a claim about a parseable runtime or configuration contract when deterministic evidence checks structure such as field presence, schema conformance, registered command shape, generated output shape, or configured section names, and flag `[test]` on a claim whose subject is semantic authored prose or documentation content — the prose verification belongs in `[eval]` or `[audit]`, and the check holds whether the would-be evidence reads the authored artifact directly or through test infrastructure ([review])
- ALWAYS: `/audit-specs` is reached only by dispatching the `spec-auditor` agent; the main conversation does not invoke `/audit-specs` in place — the agent's isolated context produces the verdict, per `spx/31-outcomeeng.enabler/31-verification.enabler/14-verification.pdr.md` ([review])
- NEVER: classify a node's content as architecture-versus-product-behavior — that classification is the decision-record audits' concern, not the node audit's ([review])
