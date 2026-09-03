# Plan: Audit Tests

## Derive the language partition from installed language plugins

Governing declaration: the `### Compliance` assertion in `spx/21-spec-tree.enabler/68-audit.enabler/32-audit-tests.enabler/audit-tests.md` that `/audit-tests` derives a language partition for every test-file extension an installed language plugin's test standards declare, and rejects with `unsupported-language` only an extension no installed plugin claims.

The shipped skill `src/plugins/spec-tree/skills/audit-tests/SKILL.md` still derives the partition from a closed mapping — `.py` to Python, `.ts` or `.tsx` to TypeScript, `.rs` to Rust — and rejects every other extension, so a Go product's `_test.go` evidence is rejected as `unsupported-language` even once a Go plugin is installed.

The assertion leads the skill. Its fix is a plugin distribution-surface change — a spec-tree version bump, regenerated `dist/`, and the `skill-auditor` gate — and it maps `.go` to an `audit-go-tests` skill that exists only once the go plugin ships, so it is carried by the plugin lane of `https://github.com/outcomeeng/changes/issues/10` alongside the go plugin skills:

1. Replace the closed mapping with derivation from the installed `audit-<lang>-tests` skills: for each, the extension its language's `<lang>-test-standards` skill declares in its filename instantiation of `<subject>.<evidence>.<level>[.<runner>]`, per `spx/31-outcomeeng.enabler/31-verification.enabler/31-test-verification.enabler/21-evidence-types.pdr.md`.
2. Keep the `unsupported-language` rejection with remediation target `language-partition` for an extension no installed plugin claims.
3. Bump the spec-tree plugin with `just bump`, then regenerate `dist/` with `just build-skills`, and gate the surface with the configured `skill-auditor`.
