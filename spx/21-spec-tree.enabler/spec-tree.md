# Spec Tree

PROVIDES the Spec Tree methodology — context loading, spec authoring, testing, implementation, and commit workflows
SO THAT all language-specific and craft plugins
CAN operate within a structured, spec-first framework with deterministic context

## Assertions

### Scenarios

- Given a spec-tree enabler directory, when its contents are listed, then a spec file named `{slug}.md` exists ([test](tests/test_spec_tree.scenario.l1.py))
- Given a node directory with a numeric prefix, when validated, then the prefix is an integer between 10 and 99 ([test](tests/test_spec_tree.scenario.l1.py))
- Given a test file nested under a consumer `pyproject.toml`, when the marketplace root is detected, then the detector returns the root that also contains the marketplace plugin marker ([test](tests/test_spec_tree.scenario.l1.py))
- Given a test file outside the marketplace tree, when marketplace root detection exhausts the path, then the detector reports a configuration error ([test](tests/test_spec_tree.scenario.l1.py))

### Mappings

- A node directory name matching `{index}-{slug}.{kind}` maps to parsed index, slug, and kind fields ([test](tests/test_spec_tree.mapping.l1.py))
- A node directory name outside the node grammar maps to an absent parse result ([test](tests/test_spec_tree.mapping.l1.py))
- A node index maps to valid when it is between 10 and 99 and invalid otherwise ([test](tests/test_spec_tree.mapping.l1.py))
- Formatting a node directory name maps invalid indexes to a rejected operation ([test](tests/test_spec_tree.mapping.l1.py))
- A node directory maps to its `{slug}.md` spec file path ([test](tests/test_spec_tree.mapping.l1.py))
- Prepared tree directory traversal maps symlinked duplicate node paths to a single yielded node directory ([test](tests/test_spec_tree.mapping.l1.py))

### Conformance

- Every node directory in the tree contains exactly one spec file matching `{slug}.md` — no orphan directories exist ([test](tests/test_spec_tree.conformance.l1.py))

### Compliance

- ALWAYS: load complete spec-tree context before any implementation work ([audit])
- ALWAYS: use atemporal voice in all specs — specs are permanent truth ([audit])
- ALWAYS: the `/understand` skill's references declare that test harnesses, generators, and inert fixtures are governed by naturally placed spec nodes rather than by a mandatory top-level category subtree, per `spx/31-outcomeeng.enabler/31-verification.enabler/31-test-verification.enabler/15-test-infrastructure.pdr.md` ([audit])
- ALWAYS: the `/understand` skill's references declare that a higher-level declaration — product spec, PDR, ADR, or ancestor spec — may lead implementation, and that a change to a higher-level declaration aligns the first affected lower specs in the same change, recording any remaining downstream work in the first affected node's `PLAN.md` ([audit])
- ALWAYS: the `/understand` skill's artifact-placement foundation declares the artifact taxonomy closed — `spx/` admits no artifact outside the placement table (whose rows include the root product spec), the canonical node shape, and the optional knowledge root a node or the product root carries; operational files (`spx/local/` overlays, the exclusion mechanism) are configuration; coordination notes raise no placement question; placement decides only between the governing layer (ADR or PDR) and the declaring layer (spec); and verification and implementation artifacts are never placed by classification because assertion tags derive evidence locations and node ownership with the language's declared infrastructure home derives implementation locations ([audit])
- ALWAYS: the `/understand` skill's canonical node shape declares the eval lane's file set as following `eval.toml` — the co-located `evals/{rule-slug}/` directory holds `eval.toml` plus the case, prompt, and template artifacts it declares by eval-relative path, canonically `cases.jsonl`, `prompt.md`, and `prompt.template.md`; a declared case or prompt path may reach a sibling eval's shared artifact while a declared template stays inside the eval directory; a declared producer source is a repository path outside the eval directory, never a co-located artifact; and the harness-generated `history.jsonl` and ignored `runs/` transcripts are never declared ([audit])
- ALWAYS: the `/understand` skill declares the truth hierarchy as PDR/ADR → Spec → Verification → Code, with verification evidence derived from specs and code complying with verification evidence ([audit])
- ALWAYS: the `/understand` skill defines product content as every product artifact a spec node governs or must govern — source, tests, evals, generated output, specs, decisions, coordination notes, and spec-declared configuration, implementation being its code layer — with governance derived from node placement or the test-link chain as a search under the live foundation marker, an ungoverned artifact recorded as a coverage gap and left unread and unmodified, operational configuration under `spx/local/` and the exclusion mechanism read by its declaring skill under the live foundation marker with no node to contextualize, and the agent harness's own instruction and settings files, tool output, session store, and scratch space excluded ([audit])
- ALWAYS: the `/understand` skill declares that no product content is read or modified before its governing spec node has been contextualized in the conversation since the last compaction, that `/contextualize` on a node precedes any discussion of that node, that a compaction empties the set of contextualized nodes, and that an operational continuation — PR inspection, check wait, merge, deploy, release, `spx session` operations, occupancy proof — touches no product content and triggers neither `/understand` nor `/contextualize` ([audit])
- ALWAYS: for default-branch work, the `/understand` skill declares delivered value as value merged to the default branch on origin through `/merge`; passing deterministic verification and any required local review or audit gates are progress, a committed branch ahead of its resolved base remains unfinished even with a clean working tree, and the agent continues through `/merge` until the change reaches the default branch on origin or no independent local action remains without operator input or an external-state change ([eval](76-merge.enabler/evals/local-completion-boundary/eval.toml))
- ALWAYS: the `/understand` skill's imperfection protocol declares that command defaults are authority for cost-bearing and quota-bearing runs, and that raising an explicit or implicit spend, quota, token, worker, retry, timeout, hosted-runner, or paid-provider ceiling requires operator approval in the same turn ([audit])
- ALWAYS: the methodology — skill prose, references, templates, audit findings, examples — uses "infrastructure" as the category term for test harnesses, generators, and inert fixtures, per `spx/31-outcomeeng.enabler/31-verification.enabler/31-test-verification.enabler/15-test-infrastructure.pdr.md` ([audit])
- ALWAYS: methodology skills that instruct Claude to call `spx`, `gh`, or another CLI present payload command forms by supported harness environment, per `spx/15-agent-tools.pdr.md` ([audit])
- NEVER: proceed with partial context — abort if any required document is missing ([audit])
- NEVER: the methodology uses "support", "helpers", "utilities", or "tools" as a governing category in the testing context — these are anti-terms per `spx/31-outcomeeng.enabler/31-verification.enabler/31-test-verification.enabler/15-test-infrastructure.pdr.md` ([audit])
