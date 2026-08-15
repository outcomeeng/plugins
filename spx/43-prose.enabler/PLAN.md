# Plan — prose surface

Fifteen skills become five, over three kinds instead of four.

## Starting point

`work/prose-kind-as-input` carries the three-kind collapse, rebased onto the default branch: the `docs` and `internal-docs` skills replaced with `author-document`, `audit-document`, and `document-standards`, the kind an explicit router input, the ownership check ahead of kind resolution in both routers, and the three-kind taxonomy described in the marketplace catalog. It stops at twelve skills.

Extend it to five skills, `architect-prose`, and journal-backed audit delivery.

## Target surface

```text
architect-prose               writes prose ADRs in the spec tree
author-prose                  writes the artifact's text
audit-prose                   audits the artifact

prose-architecture-standards  prose ADR conventions
  references/copy.md  interface.md  documentation.md
prose-standards               anti-pattern catalog
  references/copy.md  interface.md  documentation.md
```

The three workflow skills mirror the language triple: `architect-python` writes Python ADRs and `code-python` writes the code; `architect-prose` writes prose ADRs and `author-prose` writes the text. Each skill pulls the standards it needs through `require_skill` at the top of its body.

## Structure ownership (resolved)

`architect-prose` owns a prose ADR — driven by the governing spec node, located in the spec tree — and never writes the prose artifact. `author-prose` is the artifact's sole writer, complying with the governing ADR. Structural moves, including sequencing across sibling and descendant artifacts, are decision content, so nothing structural leaks into the artifact and no cross-skill mark exists. This supersedes the earlier seam in which architect mutated the artifact and marked moved sections; the open mark-carrier question is closed with it.

## Kinds

Copy, interface, documentation. A kind varies on two axes, so it carries two reference files: its structure under `prose-architecture-standards`, its style overrides under `prose-standards`.

Documentation is one kind. Sentence mechanics and page architecture are two layers of every document, not two audiences — which is why the former `docs` and `internal-docs` layers partitioned by level rather than by reader.

## Kind resolution

Resolved once, at whichever entry the caller invokes, and carried in the dispatch. A dispatched audit never resolves a kind: a dispatch with no kind or no target records a blocked run and judges no text.

## Audit delivery

`audit-prose` streams its run through `spx journal` using the projection in `/project-run-journal`, and returns the raw run token. `spx/15-audit-result-delivery.pdr.md` requires an audit to reveal scope progress and each finding as the run advances; a verdict emitted only at the end satisfies neither property.

`prose-auditor`'s final message becomes that token. The verdict assertion in `spx/43-prose.enabler/prose.md` names the journal projection rather than a terminal JSON object.

`audit-prose` records its own run rather than returning results to a run driver.

An `[eval]` assertion on this node waits for that run. A suite built against a prompt-imposed schema grades the prompt author rather than the skill, so eval evidence needs a verdict the skill itself emits; `ISSUES.md` carries the deferral until then.

## Descriptions (resolved)

`architect-prose` takes the python-minimal form (~100 characters): `ALWAYS invoke this skill when writing ADRs for prose. NEVER author a prose ADR without this skill.` `author-prose` and `audit-prose` take a compact directive around 200 characters: the trigger in user speech with a few concrete examples, and one terse NEVER naming the exclusion classes — chat responses, code comments, commit messages, agent-facing instructions. The enumeration bags in the current 477- and 514-character descriptions do not survive.

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
