---
id: 01a1b994-fafd-75d1-877d-589e0c968a9d
malleability: verification
---

# Audit change

PROVIDES the audit-change skill and the change-auditor agent, which audit a Sliced Leaf's record before its holder advances it to Applicable and, at close, the default branch against a Leaf's record
SO THAT the holder of a Leaf and the Operator
CAN advance a Leaf to Applicable and close it Applied only on a clean audit

## Assertions

### Audit: record content

- audit-before-applicable: ALWAYS: an Auditor audits a Sliced Leaf before its holder advances it to Applicable, each Declarations line against every Decision Record that governs its Node at the Base, read as the Declarations change it, and every finding blocks ([audit])
- audit-at-close: ALWAYS: before a Leaf closes Applied, an Auditor audits the default branch against its record: each Assertion and decision stands as its line states, and the verification the Statement of Intent names finds what it states ([audit])
- facts-checked: ALWAYS: the audit checks each fact the record cites against the checkout at the Base ([audit])
- sets-apart: ALWAYS: the audit finds that each part of the body holds only what sets this Change apart ([audit])
- no-person: NEVER: the audit finds in the record an accountable person or conversation text ([audit])

### Audit: audit-change

- audit-verdict: audit-change audits one Leaf's record, a Sliced Leaf's before its advance to Applicable or the default branch against it at close, and emits an Agentic verdict under [`spx/31-outcomeeng.enabler/31-verification.enabler/14-verification.pdr.md`](spx/31-outcomeeng.enabler/31-verification.enabler/14-verification.pdr.md) whose every finding blocks ([audit])
- change-auditor: ALWAYS: audit-change reaches the record, the repository, and the SPX store only through its bundled runner; the change-auditor loads audit-change and product-tree-plugin, takes a task message of the record's Change reference and the checkout root, and for the audit at close also the merge commit of the Changeset, and returns a blocked result for any other task message ([audit])

### Test.Mapping: audit-change runner

- read-relations-parent: `read-relations` maps a `Parent` number field value, integer or float, to the issue number it names and an absent value to `null` ([test](tests/test_audit_change_relations_parent.mapping.l1.py))

### Test.Compliance: audit-change runner

- audit-binding: ALWAYS: the runner binds each run to the SHA-256 of the record body and to the Base it read, names both in its finish result, and blocks a run whose body or Base differs at finish from the pair it read at start, so the advance to Applicable records the body and the Base the audit judged ([test](tests/test_audit_change_binding.compliance.l1.py))
- format-at-close: ALWAYS: at close the runner makes three comparisons and reports each one that fails as its own finding, and the Change stays open while any fails: the Base formatter leaves each declared replacement unchanged, the merge-commit formatter leaves the approved result unchanged, and the file on the default branch equals the approved result, the approved replacement with its plain slugs linked; the runner runs the formatter in its form that reads the text on stdin and writes the formatted text on stdout, so it writes no file ([test](tests/test_audit_change_format.compliance.l1.py))
- runner-reads: ALWAYS: the runner reads the issue's body and fields from the Change Store by the record's reference, assembles from the stored record a Change Draft, its metadata except the holder and then its body, and reads every Node and Decision Record the record names at the Base, under the checkout root the request names ([test](tests/test_audit_change_run.compliance.l1.py))
- runner-no-file: NEVER: the bundled runner of `audit-change` writes a file; each invocation reads one JSON request on stdin and writes one JSON result on stdout, and the SPX run journal is the only state that persists between requests ([test](tests/test_audit_change_run.compliance.l1.py))
- runner-checkout-root: ALWAYS: the `audit-change` request names the Product's checkout root, which its caller resolves from the coordination overlay, and the runner reads the candidate and every path a record names, the Decision Records and Nodes its Declarations name, under that root, runs its git and spx commands with that root as the working directory, returns a blocked result naming the root when the request carries none or the root is no repository checkout, and keeps its containment check against that root, so a change audit whose candidate and record paths lie in another worktree than the session's seals its run ([test](tests/test_audit_change_run.compliance.l1.py))
- read-authority: ALWAYS: the runner's `read-authority` operation reads a Change's field-change events at 100 per page and at most 10 pages, reads no comment, and returns a blocked result naming the bound when the read fills it ([test](tests/test_audit_change_authority.compliance.l1.py))
- read-relations-pages: ALWAYS: `read-relations` reads the store's issue pages in order until the store reports no further page, and returns a blocked result naming `100 issues per page, 10 pages` when the tenth page still reports a further page ([test](tests/test_audit_change_relations.compliance.l1.py))
- read-relations-fields: ALWAYS: `read-relations` returns a blocked result naming `50 issue field values per issue` when an issue's field-value connection reports a further page, and returns no Product or Parent read from that partial connection ([test](tests/test_audit_change_relations.compliance.l1.py))

### Test.Compliance: form check call

- form-check-request: ALWAYS: the runner passes the form check one request carrying the Change Draft it assembled as the subject, the Product's checkout root, the operation `audit`, the stored record, holder included, as the record the Change Store holds, the record of each Change the record names as a blocker, which runner-reads reads from the Change Store, and the Change Store's size limit, and records each finding of its result as a blocking finding naming the slug of the rule it breaks ([test](tests/test_audit_change_form_check.compliance.l1.py))
- form-check-held-leaf: ALWAYS: the form check passes the Change Draft the runner assembles from a valid held Leaf, which omits the holder the stored record carries ([test](tests/test_audit_change_form_check.compliance.l1.py))
- form-check-draft-holder: NEVER: the form check passes a Change Draft that carries a holder ([test](tests/test_audit_change_form_check.compliance.l1.py))
- form-check-import: ALWAYS: the runner reaches the form check through a `__file__`-relative import of the one check function of the change-standards skill, and carries no copy of its rules ([test](tests/test_audit_change_form_check.compliance.l1.py))
- form-check-reads-only: NEVER: the runner's call of the form check writes a file or the Change Store; the check reads the request's record text and runs only reading git commands at the Base in the checkout root ([test](tests/test_audit_change_form_check.compliance.l1.py))
