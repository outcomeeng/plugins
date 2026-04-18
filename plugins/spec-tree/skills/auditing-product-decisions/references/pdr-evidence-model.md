<overview>

Detailed evidence model for PDR auditing. Read this before auditing any PDR.

Six properties define PDR evidence: content classification, invariant quality, compliance quality, atemporal voice, consistency, downstream flow. This reference provides detailed definitions, boundary cases, and concrete examples for each.

</overview>

<content_classification>

PDRs govern observable product behavior. Every statement must pass the user test: "Would a user care about this?"

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

**The escalation test:** When a statement is ambiguous, ask: "If this changed, would a user file a bug report or a feature request?" If yes → PDR. If only engineers would notice → ADR.

</content_classification>

<invariant_quality>

Product invariants are guarantees users can rely on. They must be:

1. **Observable** — a user can perceive whether the invariant holds
2. **Falsifiable** — you can describe a scenario where it's violated
3. **Stable** — the invariant holds across all contexts, not just happy paths

**Good invariants:**

| Invariant                                  | Observable                    | Falsifiable                         | Stable                 |
| ------------------------------------------ | ----------------------------- | ----------------------------------- | ---------------------- |
| "All pages load in under 2 seconds"        | User times page load          | Load a page, measure > 2s           | Applies to all pages   |
| "Theme selection persists across sessions" | User returns, sees same theme | Change theme, close browser, reopen | Applies always         |
| "Uploaded files never exceed stated limit" | User gets rejection           | Upload 11MB to 10MB limit           | Applies to all uploads |

**Bad invariants:**

| Invariant                         | Problem                                  |
| --------------------------------- | ---------------------------------------- |
| "Good user experience"            | Not falsifiable — what counts as "good"? |
| "Database connections are pooled" | Not user-observable                      |
| "Code follows best practices"     | Not falsifiable — whose practices?       |
| "The system is scalable"          | Not falsifiable without a threshold      |
| "Fast response times"             | Not falsifiable — how fast is "fast"?    |

**Fixing bad invariants:**

- "Good user experience" → "Core user flows complete in under 3 clicks"
- "The system is scalable" → "The system handles 500 concurrent users without degradation"
- "Fast response times" → "API responses return within 200ms at p95"

</invariant_quality>

<compliance_quality>

Compliance rules are the enforceable part of a PDR. Each MUST/NEVER rule needs:

1. **Verifiability** — can a reviewer, test, or lint rule determine pass/fail?
2. **Tagging** — `([review])` for human/agent review, `([test](...))` for automated verification (including tests that exercise a lint rule)
3. **Specificity** — two independent reviewers would agree on the verdict

**Good compliance rules:**

```markdown
### MUST

- All text/background color pairs maintain ΔL ≥ 0.80 contrast in all themes ([review])
- Export files conform to RFC 4180 CSV format ([test](tests/export.unit.test.ts))

### NEVER

- Expose internal database IDs in user-facing URLs ([test](tests/url-safety.unit.test.ts))
- Display raw error messages from backend services to users ([review])
```

**Bad compliance rules:**

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

- "Follow accessibility best practices" → "Meet WCAG 2.1 Level AA for all interactive components ([review])"
- "Be fast" → "API responses return within 200ms at p95 under normal load ([test](tests/performance.e2e.test.ts))"

</compliance_quality>

<downstream_flow>

The critical property. A compliance rule that no spec assertion references is an unenforced declaration.

**Verification procedure:**

1. List every MUST/NEVER rule in the PDR
2. Determine the governed subtree (all specs below the PDR's location in the tree)
3. For each rule, search the subtree for assertions that implement or reference it
4. Report flow status

**What counts as "referenced":**

- A spec assertion that directly tests the behavior the rule requires
- A spec assertion whose `[test]` link verifies the rule
- A `[review]` reference pointing back to the PDR

**What does NOT count:**

- A spec that mentions the same concept but doesn't assert it
- A test that happens to cover the behavior but isn't linked from an assertion
- Another PDR that restates the same rule (that's duplication, not enforcement)

**Example audit output:**

```text
PDR: 15-dark-first-design.adr.md (treating as PDR for product invariants)

Rule 1: "MUST: all text/background pairs maintain ΔL ≥ 0.80"
→ spx/.../21-token-contract.enabler assertions: foreground/background ΔL ≥ 0.80 ✓

Rule 2: "NEVER: use hardcoded hex/rgb values in component styles"
→ spx/.../: no assertion references this ✗
→ Finding: unenforced rule — declare an assertion or remove the rule

Rule 3: "MUST: default to dark theme when no preference detected"
→ spx/.../: no assertion references this ✗
→ Finding: unenforced rule
```

**Why this matters:**

Unenforced rules create false confidence. Stakeholders read the PDR and believe the product guarantees certain behaviors. But no spec declares it, no test verifies it, and no review checks it. The guarantee exists only on paper. This is the PDR equivalent of a tautological test — it looks like evidence but provides none.

</downstream_flow>
