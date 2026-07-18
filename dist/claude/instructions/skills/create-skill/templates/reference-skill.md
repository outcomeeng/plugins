---
name: "{{domain}}-standards"
user-invocable: false
description: >-
  {{Domain}} standards enforced across {{scope}}. Loaded by other skills, not invoked directly.
allowed-tools: Read
---

<objective>
The {{domain}} standards that {{consuming skills}} apply across {{scope}}.
</objective>

<reference_note>

This is a declarative reference skill loaded by composing workflows. It is not a standalone procedure.

</reference_note>

<standards>

- {{Standard 1 with its observable boundary.}}
- {{Standard 2 with its observable boundary.}}

</standards>

<success_criteria>

- Every consuming skill loads this reference before applying its rules.
- Each rule has one canonical statement here and is absent from creator and auditor workflow references.
- The description remains passive, the skill remains non-user-invocable, and the tool surface remains read-only.

</success_criteria>
