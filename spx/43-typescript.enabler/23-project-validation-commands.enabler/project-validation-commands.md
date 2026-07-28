# Product Validation Commands

PROVIDES repository-canonical validation command selection for TypeScript workflows
SO THAT TypeScript testing, coding, remediation, and audit skills
CAN run the checks that product maintainers intend instead of bypassing wrappers with generic tool invocations

## Assertions

### Compliance

- ALWAYS: TypeScript skills resolve validation commands from repository documentation, package scripts, Makefiles, Justfiles, or local agent instructions before naming a raw tool command — product wrappers encode local configuration, exclusions, and quality gates ([audit])
- ALWAYS: verification guidance distinguishes type checking, linting, test execution, and full product validation by the product command that owns each check — users see the command surface their repository supports ([audit])
- ALWAYS: raw commands such as `tsc`, `eslint`, or `vitest` are fallback examples only when a repository has no validation wrapper — direct tools do not supersede product policy ([audit])
- NEVER: declare a bare TypeScript compiler invocation as the universal type-check command — product-specific wrappers can supply paths, scopes, exclusions, runtime setup, and subprocess safety behavior ([audit])
- NEVER: treat a focused command as the full quality gate when repository documentation defines a broader validation pipeline — partial checks do not prove readiness ([audit])
