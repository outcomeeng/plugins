---
id: 01a1ba06-0435-7640-8c29-b757cc30f2b5
malleability: spec
---

# Change Standards

PROVIDES the change-standards skill, which states the Change record that the Change skills share, and its form check, one standard-library script that judges a Change Draft against that record
SO THAT the Change skills that record, move, and audit a Change
CAN judge a record's form through one check before each publish

## Assertions

### Compliance: form check

- pdr-rules: ALWAYS: the form check fails a Draft for each breach of these rules of the Change record decision, and each finding names the slug of the rule it breaks: record-keys, record-body, statement-of-intent, subsection-headings, payloads, headers, diff-lines, body-lines-only, no-tag, plain-slug, table-case, front-matter-block, no-index, move-reads, one-payload, fence, no-mode, operation-kinds, spec-deletion, one-subsection-per-file, slug-rename, path-naming, infrastructure-line, replaced-assertion, infrastructure-form, infrastructure-exists, spec-node-none, none-leaf, size-limit, and one-home.
- judges-form: ALWAYS: the form check judges a key's presence, its value's type, and the values a row lists; a part's label, the order of the parts, and the word count; each heading's form; and each - line and context line against the Base, and each + line by its form; what a value or a + line states stays with the audit.
- check-request: ALWAYS: the form check reads one JSON request on stdin carrying the Draft's text or naming its path, the Product's checkout root, the operation, the record the Change Store holds or null, the record of each Change the Draft names as a blocker, and the Change Store's size limit, and writes one JSON result on stdout holding pass or fail and every finding with the slug of the rule it breaks, the subsection or line it names, and its detail; a request it cannot read yields invalid-request and no finding.
- check-import: ALWAYS: the form check's module exposes one check function that returns, for a request, the result the script writes for it, so a sibling Change skill's script reaches the check by a `__file__`-relative import.
- check-reads-only: NEVER: the form check writes a file or the Change Store; it reads the Draft and runs only reading git commands at the Base in the checkout root.

### Scenario: reachability

- reachability: Given a Draft that records a Leaf adding one new Node, a checkout root whose one commit holds the parent spec its heading names, and no stored record, when the check function and the script each judge it, then each returns pass under the request and result names the module exports ([test](tests/test_form_check.scenario.l1.py)).
- reachability-fail: Given the same Draft with one metadata key the record-keys rule does not name, when the check function and the script each judge it, then each returns fail with one finding naming record-keys ([test](tests/test_form_check.scenario.l1.py)).

### Audit: change-standards

- standards-record: The change-standards skill states the Change record, the Change Draft, and the form check's request and result as the Change record decision states them, and names no rule the decision does not state.
