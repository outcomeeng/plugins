# Issues

## SPX evidence graph integration

The test-evidence audit receives an explicit evidence package from its caller and follows direct imports from the linked tests into harnesses, generators, fixtures, discovery files, and production code. It does not discover or claim an authoritative repository-wide evidence graph.

Revisit when SPX exposes its product document through decision records, specs, tests, and code as a structured graph projection. At that point, make the SPX projection the audit's evidence inventory input and remove caller-owned path discovery that the projection supersedes.

Do not implement a competing repository graph or Markdown walker in this repository.
