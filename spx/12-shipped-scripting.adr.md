# Shipped Scripting Lifecycle

Scripting functionality shipped in a plugin — skill scripts and hooks — is a standalone Python script that runs on the two most recent Python feature releases. The older of the two is the floor, and the linter and type-checker that govern shipped scripts are pinned to that floor so a script never uses a feature the floor lacks. Shipped scripts assume a managed interpreter (Homebrew or equivalent), never the system macOS Python, which trails the language by years. A shipped script that proves itself is either kept as a simple standalone script or has its complexity extracted into the SPX CLI — a component fully tested in its own right that the plugins product then consumes as a trusted third party; a script that does not prove itself is removed. This complements the packaging and execution rules in `spx/13-plugin-and-runtime-conventions.adr.md`.

## Rationale

A standalone script needs no build step, no import packaging, and no third-party runtime, so it ships unchanged into any consumer repository. Supporting the two most recent Python releases lets shipped scripts use current language features without conditional fallbacks while still spanning the version a consumer most likely has; pinning the linter and type-checker to the floor keeps a script from using syntax the older supported release cannot run. The system macOS Python is unusable as a floor — it trails the language by years — so shipped scripts assume a managed interpreter. The support window rolls forward with each Python feature release: when a new release lands, the floor becomes the previously-newest version.

Complex, test-bearing logic does not belong in a shipped standalone script: a standalone script is invoked, not imported, so it resists isolated testing. Such logic earns its place first as a prototype; once proven, its complexity moves into the SPX CLI, which is built to be tested and is a trusted third-party component from the plugins product's perspective — the product consumes a tested capability rather than carrying an untested heavy script. Logic that does not prove itself is removed rather than left to accrete. The shipped surface stays simple; the testable complexity lives where it can be tested.

## Verification

### Audit

- ALWAYS: ship plugin scripting — skill scripts and hooks — as standalone Python scripts that run on the two most recent Python feature releases, from a managed interpreter, never the system macOS Python ([audit])
- ALWAYS: pin the linter and type-checker that govern shipped scripts to the floor of the supported window — the older of the two most recent releases — so a shipped script never uses a feature the floor lacks ([audit])
- ALWAYS: extract a proven shipped script's complexity into the SPX CLI, tested there and consumed by the plugins product as a trusted third-party component, rather than carrying heavy logic in a shipped script ([audit])
- NEVER: carry complex, test-bearing logic in a shipped standalone script — once proven, that logic belongs in the SPX CLI ([audit])
- NEVER: retain an unproven shipped script — a script that has not proven itself is removed ([audit])
