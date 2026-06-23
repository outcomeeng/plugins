<overview>

Verification is the set of activities that establish a Spec Tree node's standing. There are five named types, each with a fixed verdict mode, classified by purpose. Anything outside this set is not verification.

</overview>

<axes>

Two orthogonal axes describe every verification activity.

**Verdict mode** — how a result is produced:

- **deterministic** — a command scores against fixed expectations and returns pass or fail; no model judges the verdict.
- **agentic** — Claude executes a skill and judges the subject. This spans a wide range of judgment: from mechanical (a checklist yielding a binary verdict) to open-ended (principal-level assessment with no fixed answer).

**Purpose** — what the verdict establishes:

- **conformance** to global standards (the Spec Tree methodology, language skills, validation-tool config), or
- **correctness** of the spec→execution chain (decisions→spec→tests→implementation hang together).

The axes are independent: one operation can serve both purposes, pointed at different standards.

</axes>

<types>

**Conformance — against global standards**

- **audit** (agentic) — spec, tests, and implementation against the Spec Tree methodology, and against the language skills.
- **validate** (deterministic) — spec format, and per-language tests and implementation, against tool config.

**Correctness — of the spec→execution chain**

- **audit** (agentic, mechanical) — a checklist skill yielding a binary verdict: the three verification-type tags (`[test]`, `[eval]`, `[audit]`) match the spec.
- **review** (agentic, open-ended) — principal-level judgment: consistency across spec, tests, and implementation, plus the quality, architecture, and design judgment that no checklist captures.
- **evaluate** (deterministic) — Claude runs a case set; its JSON outputs are scored against spec-derived expectations, with a pass threshold. Subjects include skills, agents, and classifiers.
- **test** (deterministic) — execution of `[test]` assertions.

The entries above are applications of the five types — audit recurs because it serves both purposes.

</types>

<assertion_tags>

Three of the five types back the tag an assertion can carry: `[test]` by test, `[eval]` by evaluate, `[audit]` by audit. Validate and review are gates that back no tag. Audit and review are both agentic but sit at opposite ends of judgment depth — audit is a binary checklist, review is irreducible principal-level assessment.

The assertion tag `[review]` is the legacy spelling of the `[audit]` tag and resolves to it during migration; it does not denote the `review` type. The collision is between a tag and a type — `[review]`-the-tag marks the audit verification type, `review`-the-type is the open-ended gate that backs no tag.

</assertion_tags>

<compliance>

- ALWAYS: an activity declares its type and purpose.
- NEVER: a type's verdict mode differs from the one its definition binds — the binding is fixed, not chosen per run.
- NEVER: a model judges the verdict of a deterministic type — it may run inside the process, but the verdict is the deterministic score.
- NEVER: the type set or the two verdict modes are extended — a new type amends this reference and its grounding decision.

</compliance>
