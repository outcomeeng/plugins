---
name: "{{domain}}-standards"
user-invocable: false
description: >-
  {{Domain}} standards enforced across {{scope}}. Loaded by other skills, not invoked directly.
allowed-tools: Read
---

<objective>
The {{domain}} standards {{scope}}.
</objective>

<reference_note>

This is a declarative reference skill: it standardizes {{domain}} and carries no standalone procedure.

</reference_note>

<standards>

- {{Standard 1 with its observable boundary.}}
- {{Standard 2 with its observable boundary.}}

</standards>

<success_criteria>

- Each rule has one canonical statement here, with an observable boundary.
- The description remains passive, the skill remains non-user-invocable, and the tool surface remains read-only.

</success_criteria>
