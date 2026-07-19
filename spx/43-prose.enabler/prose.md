# Prose

PROVIDES prose craft skills for writing and reviewing long-form text
SO THAT all skills and documentation across the marketplace
CAN maintain consistent, human-quality prose free of formulaic patterns

The prose plugin contains `/prose-standards` and `/internal-doc-standards` (references, loaded by other skills), `/write-prose` and `/write-internal-docs` (authoring), and `/audit-prose` and `/audit-internal-docs` (on-demand audit and editing). Prose written for strangers routes to the prose skills; workspace-native documents written for colleagues route to the internal-doc skills.

Artifact ownership decides that routing before audience does. A document a repository or domain workflow governs belongs to that workflow whatever its readership, so the internal-doc surface covers only documents no such workflow owns.

## Assertions

### Compliance

- ALWAYS: invoke `/write-prose` when generating long-form text for readers outside the team — articles, public documentation, blog posts, and customer-facing release or marketing copy ([audit])
- ALWAYS: route a document to the internal-doc skills only when no repository or domain workflow governs the artifact — artifact ownership outranks reader audience ([audit])
- NEVER: write long-form text without the writing skill its artifact routes to — unsupervised prose drifts toward formulaic patterns ([audit])
- NEVER: classify a repository-governed engineering artifact as an internal doc because colleagues read it or it lives in a workspace ([audit])
