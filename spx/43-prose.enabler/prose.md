# Prose

PROVIDES prose craft skills for writing and reviewing long-form text
SO THAT all skills and documentation across the marketplace
CAN maintain consistent, human-quality prose free of formulaic patterns

The prose plugin contains `/standardizing-prose` (reference, loaded by other skills), `/writing-prose` (always active when generating long-form text), and `/reviewing-prose` (on-demand review and editing).

## Assertions

### Compliance

- ALWAYS: invoke `/writing-prose` when generating articles, documentation, blog posts, specs, or any long-form text ([review])
- NEVER: write long-form text without the writing skill — unsupervised prose drifts toward formulaic patterns ([review])
