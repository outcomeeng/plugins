<overview>

Pre-submission verification checks for TypeScript implementation work.

</overview>

<required_checks>

- [ ] The resolved product type-check command passes
- [ ] The resolved product lint/format check command passes after the canonical auto-fix command runs when available
- [ ] The resolved product test command passes for the governed node or changeset
- [ ] Any coverage, documentation, TODO, logging, or security threshold enforced by the resolved commands or loaded standards passes through those commands
- [ ] Manual review confirms the implementation follows `/typescript-standards` and any loaded `spx/local/typescript.md` overlay

</required_checks>

<tool_commands>

Resolve placeholders from the repository's docs, package scripts, Makefile, Justfile, or local agent instructions. Raw `tsc`, `eslint`, or `vitest` commands are fallback commands only when the repository has no validation wrapper.
When sources conflict, resolve in this priority: local agent instructions, repository docs, Justfile, Makefile, package scripts, raw tool fallback.

```bash
# TypeScript validation through the repository's canonical command
<product-typecheck-command>

# Auto-fix style issues through the repository's canonical command, when available
<product-lint-fix-command>

# Lint validation through the repository's canonical command
<product-lint-command>

# Run tests through the repository's canonical command
<product-test-command>

# Bare-repo fallback examples only when no repository wrapper exists:
# npx tsc --noEmit
# npx eslint src/ test/ --fix
# npx eslint src/ test/
# npx vitest run
```

</tool_commands>

<completion_criteria>

| Criterion                           | Status                |
| ----------------------------------- | --------------------- |
| Product type-check command passes   | Required              |
| Product lint/format command passes  | Required              |
| Product test command passes         | Required              |
| Loaded standards are followed       | Required              |
| Repo-local overlay is followed      | Required when present |
| Supplied reviewer findings resolved | Required in FIX mode  |

</completion_criteria>

<review_focus>

<type_safety>

- Follow the type-safety rules in `/typescript-standards`
- Treat `any`, suppression comments, and missing annotations according to the loaded standards and resolved type-check command

</type_safety>

<code_quality>

- Follow the code-quality, dependency-injection, source-owned-value, import, and hygiene rules in `/typescript-standards`
- Apply documentation, TODO, logging, and security requirements only when they are declared by the loaded standards, repo-local overlay, or resolved product commands

</code_quality>

<testing>

- Tests required by the governing spec assertions exist and pass through the resolved product test command
- Test shape and mocking rules come from `/typescript-test-standards` and any loaded `spx/local/typescript-tests.md` overlay

</testing>

</review_focus>
