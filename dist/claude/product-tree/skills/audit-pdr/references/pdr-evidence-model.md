<overview>

Detailed boundary guidance for PDR content classification, property quality, and declaration form and tag validity. Read this before auditing any PDR.

The audit skill owns the complete five-property workflow, including atemporal voice and consistency. This reference defines the three properties whose classification boundaries require extended examples.

</overview>

<contents>

- `<content_classification>` — observable product behavior versus architecture, grounded in the product document's declared audience and interaction surfaces, with tooling-product examples
- `<property_quality>` — observable, falsifiable, stable behavior the CAN RELY ON line names
- `<tag_validity>` — declaration form, tag absence, slug uniqueness, and assertion-type fit

</contents>

<content_classification>

PDRs govern observable product behavior. Every statement must pass the user test: "Would the product document's declared audience observe or operate this?" The product document the audit loads names the audience and the interaction surfaces through which it operates the product; "observable" is judged against that declaration, never a fixed end-user-application assumption.

**Product behavior (belongs in PDR):**

- "Sessions expire after 1 hour of inactivity" — user observes expiry
- "Search results appear within 500ms" — user observes latency
- "The product supports 4 theme variants" — user selects themes
- "Uploaded files are limited to 10MB" — user hits the limit
- "Export produces valid CSV" — user opens the file

**Architecture (belongs in ADR):**

- "Sessions use JWT with 1-hour TTL" — user doesn't know about JWT
- "Search uses Elasticsearch" — user doesn't know the engine
- "Themes are implemented via CSS custom properties" — user doesn't see CSS
- "File validation uses multer middleware" — user doesn't see middleware
- "CSV generation uses fast-csv library" — user doesn't see the library

**Boundary cases:**

| Statement                                         | Verdict                                 | Reasoning                           |
| ------------------------------------------------- | --------------------------------------- | ----------------------------------- |
| "The API returns JSON responses"                  | PDR if user-facing API, ADR if internal | Depends on who the "user" is        |
| "Pages load in under 2 seconds"                   | PDR                                     | User observes load time             |
| "Response time is O(n log n)"                     | ADR                                     | User observes speed, not complexity |
| "The system handles 500 concurrent users"         | PDR                                     | User experiences the capacity       |
| "The database handles 500 concurrent connections" | ADR                                     | User doesn't see connections        |
| "Dark mode is the default theme"                  | PDR                                     | User sees the default               |
| "Dark mode uses L=0.03 OKLCH background"          | ADR                                     | User sees dark, not the color math  |

**Tooling and infrastructure products.** When the product document declares an audience that operates the product through a command-line, filesystem, version-control, or other infrastructure surface — engineers, agents, operators — the surface that audience runs and inspects is the product's observable behavior. Naming a command, a path, or a version-control concept is not by itself architecture; the audience operates exactly those things.

**Tooling product behavior (belongs in PDR):**

- "The tool recognizes two on-disk layouts: a single working tree and a worktree pool" — the audience inspects the layout on disk
- "Running the build command in a clean checkout produces a `dist/` directory" — the audience runs the command and sees the output
- "A shared state directory resolves to the same path from every worktree in a pool" — the audience relies on the resolved path
- "An unknown subcommand exits non-zero with a usage message" — the audience observes the exit code and message

**Tooling architecture (belongs in ADR), even though the product is tooling:**

- "The layout detector caches results in an in-memory map keyed by path" — the audience never sees the cache
- "The classifier reads metadata in a single pass and skips re-validating unchanged entries" — internal algorithm of the tool
- "State is persisted as newline-delimited JSON records" — a serialization schema the audience does not operate
- "The CLI is built on the Cobra command framework" — a library choice invisible to the audience

| Statement                                            | Verdict | Reasoning                                       |
| ---------------------------------------------------- | ------- | ----------------------------------------------- |
| "The repository uses a bare-repo worktree pool"      | PDR     | The audience inspects the layout on disk        |
| "Layout detection queries a version-control config"  | ADR     | The detection mechanism is internal to the tool |
| "A new worktree is created detached at the base tip" | PDR     | The audience observes the worktree state        |
| "Worktree records are held in a linked list"         | ADR     | The data structure is invisible to the audience |

**The escalation test:** When a statement is ambiguous, ask: "If this changed, would the declared audience file a bug report or a feature request?" If yes → PDR. If only an implementer of the tool — never the audience — would notice → ADR.

</content_classification>

<property_quality>

The behavior the CAN RELY ON line names is a guarantee users can rely on. It must be:

1. **Observable** — a user can perceive whether the property holds
2. **Falsifiable** — a scenario exists where it's violated
3. **Stable** — the property holds across all contexts, not just happy paths

**Good properties:**

| Property                                   | Observable                    | Falsifiable                         | Stable                 |
| ------------------------------------------ | ----------------------------- | ----------------------------------- | ---------------------- |
| "All pages load in under 2 seconds"        | User times page load          | Load a page, measure > 2s           | Applies to all pages   |
| "Theme selection persists across sessions" | User returns, sees same theme | Change theme, close browser, reopen | Applies always         |
| "Uploaded files never exceed stated limit" | User gets rejection           | Upload 11MB to 10MB limit           | Applies to all uploads |

**Bad properties:**

| Property                          | Problem                                  |
| --------------------------------- | ---------------------------------------- |
| "Good user experience"            | Not falsifiable — what counts as "good"? |
| "Database connections are pooled" | Not user-observable                      |
| "Code follows best practices"     | Not falsifiable — whose practices?       |
| "The system is scalable"          | Not falsifiable without a threshold      |
| "Fast response times"             | Not falsifiable — how fast is "fast"?    |

**Fixing bad properties:**

- "Good user experience" → "Core user flows complete in under 3 clicks"
- "The system is scalable" → "The system handles 500 concurrent users without degradation"
- "Fast response times" → "API responses return within 200ms at p95"

</property_quality>

<tag_validity>

Derive the form from the canonical PDR template. A rule directly under `## Verification`, outside any group, awaits selection and receives the same clarity and falsifiability checks. The checks below apply to the declaration; authoring approval supplies no evidence result:

1. **Declaration form** — the PDR opens with a GOVERNS paragraph, writes each mapping rule as its own `### Mapping: <slug>` subsection holding one sentence and a table, keeps each group to at most seven rules, and holds no text outside its opening, a rule, or a table. A violation is `declaration-form`.
2. **No tag, one slug** — a rule carries no tag, because its group heading names its verification type, and its leading slug is its one name and repeats nowhere in the PDR. A tag on a rule, or a repeated slug, is `invalid-tag`.
3. **Assertion-type fit** — a rule's assertion type, named by its group heading, fits the claim's quantifier per the `/test` router; a universal `ALWAYS`/`NEVER` claim in a `### Scenario` group is `assertion-type-mismatch`, since a single case cannot establish a universal.

A rule is sound only when it is verifiable (a test, eval, or audit skill can determine pass/fail) and specific (two independent reviewers would agree on the verdict); an unverifiable or vague rule cannot sit in any group.

**Well-formed verification rules:**

```markdown
## Verification

### Property: contrast

- contrast-floor: ALWAYS: all text/background color pairs maintain ΔL ≥ 0.80 contrast in all themes.
- no-internal-ids: NEVER: expose internal database IDs in user-facing URLs.

### Conformance: export

- csv-format: ALWAYS: export files conform to RFC 4180 CSV format.

### Audit

- theme-variants-selectable: ALWAYS: every theme variant is selectable from the settings surface.
```

**Ill-formed verification rules:**

```markdown
### MUST

- Provide an intuitive interface ← unverifiable
- Follow accessibility best practices ← vague (which practices? what level?)
- Be fast ← no threshold

### NEVER

- Have bugs ← not actionable
- Break ← not specific
```

**Fixing bad rules:**

- "Follow accessibility best practices" → "wcag-aa: ALWAYS: all interactive components meet WCAG 2.1 Level AA", in a `### Compliance` group
- "Be fast" → "response-latency: ALWAYS: API responses return within 200ms at p95 under normal load", in a `### Property` group

</tag_validity>
