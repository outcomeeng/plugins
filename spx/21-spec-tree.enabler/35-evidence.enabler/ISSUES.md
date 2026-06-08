# Issues: Evidence Enabler

## Evidence vocabulary has drifted across the spec-tree skills

The spec-tree skills name the same evidence concepts inconsistently. Scanning
`src/plugins/spec-tree/skills/` for the phrase `evidence <word>` surfaces ten
distinct noun phrases — `evidence harness`, `evidence lane`, `evidence lanes`,
`evidence matrix`, `evidence mechanism`, `evidence model`, `evidence strategy`,
`evidence tag`, `evidence type`, `evidence types` — several of which name the
same thing.

```bash
rg 'evidence \w+' src/plugins/spec-tree/skills/ \
  | sd '.*(evidence \w+).*' '$1' | sort -u
```

The drift collapses onto two concepts that must each carry exactly one name:

- **The three `[test]` / `[eval]` / `[audit]` tags an assertion carries.** Named
  "evidence lane" in `understanding/references/verification-kinds.md`
  (`<evidence_lanes>`), "evidence mechanism" once in
  `understanding/references/assertion-types.md` (`<evidence_mechanisms>` prose),
  and "Lane" in that file's table column. `verification-kinds.md` is the
  authority for the lane↔type mapping and uses "evidence lane" throughout;
  standardize on **evidence lane** and retire "evidence mechanism".
- **The five structured types** (scenario, mapping, conformance, property,
  compliance). Named "structured types" and "assertion type" in
  `assertion-types.md`, and "evidence type" in this enabler's `evidence.md` and
  in the decision-record templates. This name is genuinely unsettled and must be
  decided: `evidence.md` says "evidence type", the reference says "structured
  types" / "assertion type". "Evidence type" collides confusingly with "evidence
  lane" (both lead with *evidence* but denote different axes); weigh adopting
  **assertion type** for disambiguation against the cost of re-terming the
  existing `evidence.md` assertions. Settle it, then conform every occurrence.

Reconcile the remaining phrases — `evidence matrix`, `evidence model`,
`evidence strategy`, `evidence harness`, `evidence tag` — against the chosen
vocabulary: each either resolves to lane/type or names a distinct artifact that
should be defined once and used consistently.

The verification-TYPE vocabulary (the five activities: validation, testing,
reviewing, auditing, evaluating) is governed by the sibling
`spx/21-spec-tree.enabler/16-verification.enabler/` and
`understanding/references/verification-kinds.md`; coordinate the term "evidence
lane ← backed by a verification type" across both nodes.

Resolution: settle the canonical terms (define them once — here in `evidence.md`
and/or in `verification-kinds.md`), then conform every skill, reference, and
template under `src/plugins/spec-tree/skills/`. Edit the source and re-render
`dist/`.

## Evidence-type selection guidance lives outside `/testing`, contradicting this enabler's assertions

`evidence.md` already declares the correct truth:

- `/testing` is the single authority that selects an assertion's evidence type
  from the shape of the claim it proves.
- The type is never inferred from the section a rule appears in — a MUST/NEVER
  rule under a `## Compliance` heading does not imply `compliance` evidence.

Downstream skills contradict both, leaving selection guidance scattered outside
`/testing`:

- `authoring/SKILL.md` Step 5 ("Match assertion type to test strategy:
  Scenario → example-based, Property → property-based, …") and the Step 6
  checklist ("Assertion types match test strategy") direct the author to select
  the type inline.
- The decision-record templates
  `understanding/templates/decisions/decision-name.pdr.md` and
  `decision-name.adr.md` enumerate the five types under `### Testing` and put a
  `([{evidence type}])` placeholder on every rule, pulling type selection into
  decision authoring — a phase that is both language-agnostic and upstream of any
  implementing test.
- `understanding/references/assertion-types.md` carries the entire selection
  procedure (`<choosing_type>`, `<choosing_mechanism>`) in the foundation every
  skill loads, read as a self-serve license.

The contradiction is internal to `authoring`: it both routes the decision
("routed through `/testing`" in the templates; "the evidence type `/testing`
routes" in Failure 7) and licenses self-service (Step 5, checklist). The
self-serve path is the one followed in practice — a PDR-drafting pass tagged a
`### Testing` rule `[compliance]` from its ALWAYS/NEVER phrasing, exactly the
inference `evidence.md` forbids, instead of routing to `/testing`.

Resolution:

1. Remove all evidence-type selection from every skill except `/testing`. Strip
   `<choosing_type>` and `<choosing_mechanism>` from `assertion-types.md`,
   leaving a pointer to `/testing`. Delete `authoring/SKILL.md` Step 5's
   type-matching line and the Step 6 checklist line. Remove the five-type
   enumeration and the `([{evidence type}])` placeholder from both decision
   templates.
2. A decision-record `## Verification` rule carries only its evidence lane
   (`[test]` / `[eval]` / `[audit]`), fixed by the subsection it sits under —
   never a five-type tag. The implementing spec's `[test]`, authored via
   `/testing` + `/testing-{language}`, binds the type and the language-specific
   filename.
3. Name `/testing-{language}` alongside `/testing` wherever the routing is
   stated. Today only `/testing` is named, yet the language-specific binding of
   the type and the test filename is a spec-authoring concern owned by
   `/testing-{language}`, never a decision-record one.

Affected source under `src/plugins/spec-tree/`:
`skills/understanding/references/assertion-types.md`,
`skills/understanding/templates/decisions/decision-name.pdr.md`,
`skills/understanding/templates/decisions/decision-name.adr.md`,
`skills/authoring/SKILL.md`. Confirm `skills/testing/` is the sole remaining home
of the selection procedure after the move, and re-render `dist/` from source.

Surfaced while drafting a worktree-management PDR in the `spx` product: a
`### Testing` rule was mis-tagged `[compliance]` by its ALWAYS/NEVER phrasing,
and the root cause traced to evidence-type selection guidance living outside
`/testing`, in violation of this enabler's own assertions.
