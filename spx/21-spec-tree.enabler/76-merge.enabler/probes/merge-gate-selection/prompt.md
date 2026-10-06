The current directory holds three files: `merge-SKILL.md`, the `/merge` skill; `merge-policy.md`, the merge-lifecycle reference that skill directs Claude to read; and `fixtures.md`, three fixture changesets. Read all three files completely. Use no other source.

For each fixture, state which Verifier agent sessions the `/merge` lifecycle dispatches before `VERIFICATION_READINESS` holds — evidence Auditors (`test-evidence-auditor`, `eval-evidence-auditor`) and the local review (`changes-reviewer`) — and the deterministic commands it runs. Base every answer on the text of the two skill files, and quote the sentence or table row that decides it.

End with one JSON object on its own line, of this shape:

{"fixture1": {"dispatched": ["..."], "deterministic": ["..."]}, "fixture2": {"dispatched": ["..."], "deterministic": ["..."]}, "fixture3": {"dispatched": ["..."], "deterministic": ["..."]}}
