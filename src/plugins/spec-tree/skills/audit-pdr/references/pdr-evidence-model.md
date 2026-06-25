<overview>

Detailed evidence model for PDR auditing. Read this before auditing any PDR.

Five properties define PDR evidence: content classification, property quality, tag validity, atemporal voice, consistency. This reference provides detailed definitions, boundary cases, and concrete examples for each.

</overview>

<contents>

- `<content_classification>` — observable product behavior versus architecture, grounded in the product document's declared audience and interaction surfaces, with tooling-product examples
- `<property_quality>` — observable, falsifiable, stable product properties
- `<tag_validity>` — per-rule verification tag and evidence-type fit

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

Product properties are guarantees users can rely on. They must be:

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

Verification rules are the enforceable part of a PDR, grouped under `## Verification` into `### Testing`, `### Eval`, and `### Audit` by verification type. Each rule carries a tag valid for its subsection, and a `### Testing` rule's evidence type fits the claim:

1. **Tag matching its subsection** — under `### Testing`, a `/test`-routed evidence type (`scenario`/`mapping`/`conformance`/`property`/`compliance`); under `### Eval`, `([eval])`; under `### Audit`, `([audit])`. A bare mechanism (`([review])`/`([test])`), a missing tag, more than one tag, or a tag that disagrees with its subsection is `invalid-tag`.
2. **Evidence-type fit** — a `### Testing` rule's evidence type fits the claim's quantifier per the `/test` router; a universal `ALWAYS`/`NEVER` claim tagged `scenario` is `evidence-type-mismatch`, since a single case cannot establish a universal.

A rule earns a sound tag only when it is verifiable (a test, eval, or audit skill can determine pass/fail) and specific (two independent reviewers would agree on the verdict); an unverifiable or vague rule cannot carry a meaningful evidence tag.

**Well-formed verification rules:**

```markdown
## Verification

### Testing

- ALWAYS: all text/background color pairs maintain ΔL ≥ 0.80 contrast in all themes ([property])
- ALWAYS: export files conform to RFC 4180 CSV format ([conformance])
- NEVER: expose internal database IDs in user-facing URLs ([property])
- NEVER: display raw error messages from backend services to users ([compliance])

### Audit

- ALWAYS: every theme variant is selectable from the settings surface ([audit])
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

- "Follow accessibility best practices" → "Meet WCAG 2.1 Level AA for all interactive components ([compliance])"
- "Be fast" → "API responses return within 200ms at p95 under normal load ([property])"

</tag_validity>
