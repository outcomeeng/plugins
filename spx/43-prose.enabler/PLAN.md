# Plan — prose surface

Fifteen skills become five, over three kinds instead of four.

## Starting point

`work/prose-kind-as-input` already carries the three-kind collapse: eleven commits replacing the `docs` and `internal-docs` skills with `author-document`, `audit-document`, and `document-standards`, making the kind an explicit router input, moving the ownership check ahead of kind resolution in both routers, and describing the three-kind taxonomy in the marketplace catalog. It stops at twelve skills.

Rebase it onto the default branch and extend it to five skills, `architect-prose`, and journal-backed audit delivery.

## Target surface

```text
architect-prose               produces the artifact's structure
author-prose                  produces its text
audit-prose                   audits the artifact

prose-architecture-standards  structural conventions
  references/copy.md  interface.md  documentation.md
prose-standards               anti-pattern catalog
  references/copy.md  interface.md  documentation.md
```

The three workflow skills mirror the language triple: a skill produces or audits an artifact, and `/apply` drives producer then auditor. Which artifact a skill produces is that skill's own decision, not a property of the pattern. Each skill pulls the standards it needs through `require_skill` at the top of its body, as `architect-python` pulls `python-standards` and `python-architecture-standards`.

## Kinds

Copy, interface, documentation. A kind varies on two axes, so it carries two reference files: its structure under `prose-architecture-standards`, its style overrides under `prose-standards`.

Documentation is one kind. Sentence mechanics and page architecture are two layers of every document, not two audiences — which is why the former `docs` and `internal-docs` layers partitioned by level rather than by reader.

## architect-prose

Writes a scaffold on first invocation. Against an existing artifact it takes the change prompt, owns that artifact's structure, and mutates it into a shape `author-prose` completes.

For prose the structure is not separable into its own document the way code architecture is, so the artifact `architect-prose` produces is the artifact itself.

### The seam

Architect moves, adds, removes, and renames sections. It leaves every moved section's bytes untouched and marks each section it moved. Author writes and re-fits, guided by those marks.

Architect never writes prose. Author never decides structure. A section moved into a new position rarely reads there — its opening refers to what used to precede it — and the mark is how that crosses the seam instead of being silently left or silently repaired.

Open: whether a mark is an in-artifact annotation or a return value, and what carries it in an artifact format with no comment syntax.

## Kind resolution

Resolved once, at whichever entry the caller invokes, and carried in the dispatch. An audit resolves the kind only when invoked with no declared kind.

## Audit delivery

`audit-prose` streams its run through `spx journal` using the projection in `/project-run-journal`, and returns the raw run token. `spx/15-audit-result-delivery.pdr.md` requires an audit to reveal scope progress and each finding as the run advances; a verdict emitted only at the end satisfies neither property.

`prose-auditor`'s final message becomes that token. The verdict assertion in `spx/43-prose.enabler/prose.md` names the journal projection rather than a terminal JSON object.

`audit-prose` records its own run rather than returning results to a run driver.

An `[eval]` assertion on this node waits for that run. A suite built against a prompt-imposed schema grades the prompt author rather than the skill, so eval evidence needs a verdict the skill itself emits; `ISSUES.md` carries the deferral until then.

## The node's own assertions

`prose.md` carries nine assertions in one `### Compliance` subsection, above the decomposition guidance, and this refactor rewrites most of them. `/decompose` runs before they are rewritten, not after.

## Descriptions

A description names the artifact and the domain, and carries one NEVER clause. `architect-python`'s is 96 characters: `ALWAYS invoke this skill when writing ADRs for Python. NEVER author a Python ADR without this skill.` Kind, artifact enumeration, and exclusion classes are resolved inside the skill, not in the field the runtime matches.

Open: the current surface states its exclusions in the description because the body runs after activation. Reconcile that against the length the model above sets.

## Removals

- The twelve per-kind skills: four `author-*`, four `audit-*`, four `*-standards`.
- The `internal-docs` kind.
- The term `durable text artifact`, wherever it appears.
- Provenance narration in shipped skills — a consumer agent reads no account of this repository's authoring decisions.
- `audit-prose`'s `<verdict_format>` block, its `overall`-from-finding-count rollup, and the `<prose_variant>` exemption in the auditor skeleton that existed to accommodate it.

## Out of scope

The `/apply` integration for this triple, and the equivalent for the instructions plugin.

Converting the other nineteen shipped audit skills that emit a terminal verdict against `spx/15-audit-result-delivery.pdr.md`. Only `audit-implementation` complies today; the gap is recorded at the node that owns each surface rather than carried here.

## Verification

`just build-skills` after every `src/` edit, then `just check`, `just check-skills`, `just docs-check`, `spx validation markdown`, and `spx spec status --format json`.

Gates over the exact committed head, in order: `spec-auditor` on each changed node, `skill-auditor` over the changed skill surface, `subagent-auditor` on `prose-auditor`, `changes-reviewer`. Then `just check-full` once against the converged head.
