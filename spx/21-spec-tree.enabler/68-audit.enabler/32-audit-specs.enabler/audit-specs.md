# Audit Specs Delivery

PROVIDES the Spec Tree plugin's `audit-specs` skill and `spec-auditor` wrapper implementing the portable node-spec audit methodology
SO THAT the main conversation
CAN dispatch isolated, structured verdicts over spec nodes

## Assertions

### Scenarios

- Given a spec node missing or malforming its kind statement, missing its `## Assertions` section, or carrying a claim-shape heading mismatched to its assertions, when audited by `audit-specs`, then the verdict is REJECT with a structure finding (`missing-section`, `malformed-kind-statement`, or `heading-mismatch`) ([eval](evals/structure/eval.toml))
- Given a spec node with universal `[audit]` assertions under `### Compliance`, when audited by `audit-specs`, then the verdict is APPROVED because the heading describes claim shape independently of verification type ([eval](evals/structure/eval.toml))
- Given a spec node that replaces the canonical claim-shape heading with a verification-type heading such as `### Audit`, when audited by `audit-specs`, then the verdict is REJECT with finding category `heading-mismatch` ([eval](evals/structure/eval.toml))
- Given a spec node with temporal language in any section, when audited by `audit-specs`, then the verdict is REJECT with finding category `temporal-voice` ([eval](evals/voice/eval.toml))
- Given a spec node whose assertion carries a bare mechanism tag, no tag, or more than one tag, when audited by `audit-specs`, then the verdict is REJECT with finding category `invalid-tag` ([eval](evals/tag-validity/eval.toml))
- Given a spec node whose `[test]` assertion tags a universal claim as `scenario`, when audited by `audit-specs`, then the verdict is REJECT with finding category `evidence-type-mismatch` ([eval](evals/tag-validity/eval.toml))
- Given a spec node whose `[test]` assertion makes a claim about authored prose or documentation content, when audited by `audit-specs`, then the verdict is REJECT with finding category `prose-coupling` ([eval](evals/prose-coupling/eval.toml))
- Given a spec node where structure, voice, and every assertion's tag fitness hold, when audited by `audit-specs`, then the verdict is APPROVED ([eval](evals/structure/eval.toml))

### Compliance

- ALWAYS: `audit-specs` implements `spx/31-outcomeeng.enabler/31-verification.enabler/31-audit-verification.enabler/54-audit-specs.enabler/audit-specs.md` without redefining its structure, voice, or tag-fitness rules ([audit])
- ALWAYS: `audit-specs` is reached only by dispatching the `spec-auditor` agent; the main conversation does not invoke the audit skill in place ([audit])
