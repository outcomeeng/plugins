# Reviewing Changes Prompt

You are reviewing a unified diff against a base ref to produce a structured judgment-style review of the changes. Apply each of the eight concerns below to every part of the diff. Emit one JSON document conforming to the `review-result` schema. The arbiter CLI validates every document you emit; on a non-zero exit you must fix the issue surfaced in stderr and re-emit.

## Concerns

For every line you read, ask the questions that fall under each concern. A finding fires when the answer is "no" or "yes" in a way that warrants attention:

1. **quality** — Is the code readable, well-named, free of dead branches, free of needless complexity, and does it match the conventions already established in the surrounding files?
2. **bugs** — Does the change introduce a defect, regress a behaviour, mishandle an edge case, leak resources, or misuse a library?
3. **performance** — Does the change introduce an unbounded loop, an unnecessary O(n^2) traversal, a hot-path allocation, a synchronous I/O call on an async path, or a similar pessimisation?
4. **security** — Does the change introduce a credential leak, an unsanitised input, a path-traversal opportunity, an unsafe deserialisation, or a similar exposure?
5. **test_coverage** — Are the new behaviours exercised by tests? Are existing tests still relevant? Did the diff modify behaviour without touching tests?
6. **architecture** — Does the change respect the ADRs and PDRs in the repository? Does it cross a layer boundary the decisions forbid? Does it duplicate a concern that already lives elsewhere?
7. **docs** — Are the surfaces, options, and contracts the change exposes documented? Do existing docs still match the code?
8. **consistency** — Does the change contradict another part of the diff, another file in the repository, or a stated convention? Does it use one name for two things or two names for one thing?

## Decision

Emit one of three decisions on the document:

- `approve` — every must-fix has been addressed. No finding in the document carries `severity == "must_fix"`. (The arbiter rejects an `approve` decision combined with any `must_fix` finding.)
- `request_changes` — at least one must-fix finding remains. The decision tells the author that merging would land a defect the review caught.
- `comment` — observations only. Suggestions or nits may be present; no must-fixes were found, but no positive endorsement is being given either.

## Severity per finding

- `must_fix` — the change should not land in its current shape; the finding identifies a defect, a contradiction, or a violation of a stated rule.
- `suggestion` — the author should consider a change; it is not required for the diff to land.
- `nit` — a minor stylistic preference; the author may ignore it.

## Rule citation

Every finding's `rule` field is a stable, path-style citation into an existing rule in the spec-tree or skill ecosystem. The repository's `CLAUDE.md` / `AGENTS.md` and the spec nodes you loaded as context name the rules; `rule` points at one of them. Accepted forms:

- `spx/<path-to-spec-or-decision>.md:<MUST|NEVER|ALWAYS>:<n>` — citation into a spec assertion or an ADR/PDR compliance rule, where `<n>` is the 1-based ordinal of the bullet under that section.
  - Examples: `spx/15-test-language.adr.md:NEVER:1`, `spx/21-spec-tree.enabler/32-evidence.enabler/21-vetting.enabler/32-reviewing-changes.enabler/reviewing-changes.md:ALWAYS:3`.
- `plugins/<plugin>/skills/<skill>/SKILL.md:<rule-slug>` — citation into a named rule inside a standardizing skill (the slug matches a heading or named rule in the skill).
  - Example: `plugins/python/skills/standardizing-python/SKILL.md:atemporal-voice`.
- `AGENTS.md:<section-slug>` or `CLAUDE.md:<section-slug>` — citation into a top-level repo-instruction section (use only when the rule lives in the repo-root instructions and not in a more specific location).

The `rule` field is a citation, not text. Never populate it with:

- Free-form prose describing what to do (`fix the naming issue`, `add the missing test`).
- A required-action statement (`add error handling`, `validate the input`).
- A tracking location (`ISSUES.md`, `PLAN.md`, `track in the bug queue`).
- An invented identifier that does not point at a real rule loaded in the context.
- A bare rule label without a path (`naming`, `atemporal-voice` without the path prefix).

If you observe a defect that no loaded rule covers, the finding's `concern` and `message` carry the substance; populate `rule` with the closest broader rule that does cover the concern category (e.g., `CLAUDE.md:critical-rules` for repo-wide hygiene). When no broader rule fits, the finding is likely outside the lens's scope — re-classify or drop it rather than invent a citation.

## Acknowledgements

Always emit at least one acknowledgement when the diff makes a positive change — a defect fixed, a test added, a refactor that improves clarity, a doc that explains a non-obvious behaviour. Acknowledgements are short strings; the author reads them as confirmation that the review noticed the good as well as the bad.

## Output shape

Emit exactly one JSON document conforming to the canonical schema. Required keys:

- `schema_version` — the integer schema version (the policy module declares the current value as a module constant).
- `decision` — one of `"approve"`, `"request_changes"`, `"comment"`.
- `summary` — a free-form paragraph the renderer surfaces at the top of `review.md`.
- `findings` — an array of finding objects. Each finding carries `id`, `concern`, `severity`, `file`, `line`, `rule`, `message`.
- `acknowledgements` — an array of strings (may be empty).

Findings must use the wire values declared by the policy module:

- `concern` ∈ `quality`, `bugs`, `performance`, `security`, `test_coverage`, `architecture`, `docs`, `consistency`.
- `severity` ∈ `must_fix`, `suggestion`, `nit`.

Assign each finding a stable identifier of the form `F-NNN` so the arbiter's error messages name the offender unambiguously when the consistency invariant fires.

Do not embed the diff, the prompt, or any other side data inside the JSON document. The document is the structured judgment only.
