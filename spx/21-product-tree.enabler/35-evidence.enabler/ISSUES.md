# Issues: Evidence Enabler

## Verification/assertion-type vocabulary: remaining conformance

The canonical names are settled in `evidence.md`:

- **verdict mode** — deterministic / agentic.
- **verification type** — test / evaluate / audit, named by the `[test]` / `[eval]` / `[audit]` tag an assertion carries; selected from the real subject's verdict.
- **assertion type** — under the testing verification type only, one of scenario, mapping, conformance, property, compliance, read from the assertion's quantifier.

`/verify` is the authority that selects the verification type. After it selects test, `/test` selects the test assertion type from the assertion's quantifier, never from a section heading, and `/test-{language}` supplies only language-specific expression. The retired names — "evidence lane", "evidence mechanism", "evidence type", "evidence mode" — and "claim" as a structural term remain excluded from these surfaces.

One piece of conformance is deferred:

1. **Filename segment `<evidence>`.** The canonical model `<subject>.<evidence>.<level>[.<runner>]` ([`spx/31-outcomeeng.enabler/31-verification.enabler/31-test-verification.enabler/15-test-infrastructure.pdr.md`](spx/31-outcomeeng.enabler/31-verification.enabler/31-test-verification.enabler/15-test-infrastructure.pdr.md)) keeps `<evidence>` as the segment that holds the assertion type. Renaming it to `<assertion-type>` touches that PDR, every `spx/**/tests/` filename, and the filename validators — a separate focused PR (operator-decided).

## The routed probe case has no committed eval run

**Evidence:** `/verify` routes an assertion whose claim only an executed observation settles to `/probe` when the runtime skill catalog carries it, and the product-tree plugin ships `/probe`. The routing eval of `69-verify-skill.enabler` has no committed passing run against the shipped specialist: the newest row of its `history.jsonl` predates the `/probe` skill. `69-verify-skill.enabler/ISSUES.md` records the same unrun suite.

**Impact:** The routed probe case rests on authored cases and no committed run of the routing eval against `/probe` as an installed specialist.

**Settlement condition:** One passing run of the routing eval at a head that carries the shipped `/probe`, with its row committed to `history.jsonl`.

## Consumers of the shared test-evidence standard hand-copy its category list

`src/plugins/product-tree/skills/test/SKILL.md` `<shared_standards>` and `src/plugins/product-tree/skills/audit-tests/SKILL.md` Step 0 each carry the same verbatim enumeration of the categories `/test-evidence-standards` owns — predicate-seam, semantic-binding, case-provenance, oracle-independence, assertion-type-litmus, assertion-design-record, and mutation litmus. The `<predicate_and_oracle_litmus>` intro in each of `go-test-standards`, `python-test-standards`, `rust-test-standards`, and `typescript-test-standards` carries the same shape for its own subset. Every new section in the shared standard therefore requires an edit in every consumer, and a consumer that misses one drifts silently.

**Status against the standard.** The enabler's second assertion requires authoring and auditing to consume one independently loadable standard; both consumers do, so the evidence they judge from is the same. The duplication is in the descriptive sentence naming what that standard owns.

**Why it is large.** The fix is one shape for the whole consumer family — `/test`, `/audit-tests`, and the four language test-standards (`go-test-standards`, `python-test-standards`, `rust-test-standards`, `typescript-test-standards`) — either an enumeration-free reference to every section the standard declares or a build-injected list the standard owns, so the consumers stop restating it. A string-equality test over the two sentences is the prose-grep evidence that [Change #354](https://github.com/outcomeeng/changes/issues/354) rejects through a validation gate, and one consumer citing the other's sentence makes two consumers depend on each other instead of on the standard.

**Resolution shape.** Choose the enumeration-free reference or the build-injected list, apply it across the six consumers in one changeset, and gate each plugin with `instructions:skill-auditor`.

**Evidence.** Surfaced by `instructions:skill-auditor` on `src/plugins/product-tree/skills/test/SKILL.md` (finding f-004, rule `duplicated_enumeration_maintenance_risk`) on the verification-readiness safeguards changeset, which added `assertion-design-record` to both consumer sentences in one commit.
