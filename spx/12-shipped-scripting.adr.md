# Shipped Scripting Lifecycle

Scripting functionality shipped in a plugin — skill scripts and hooks — is a standalone Python script that runs on the two most recent Python feature releases. The older of the two is the floor, and the linter and type-checker that govern shipped scripts are pinned to that floor so a script never uses a feature the floor lacks. Shipped scripts assume a managed interpreter (Homebrew or equivalent), never the system macOS Python, which trails the language by years. A generic shipped script beyond fifty lines carries debt: once it proves its value its logic moves into the runtime-neutral SPX CLI, and a script that never proves its value is removed rather than extracted. Runtime-specific adapter logic remains plugin-local only when moving it into SPX would couple SPX to one external runtime and the adapter is deterministic, bounded, standard-library-only, and independently tested. A value the spec tree declares and a source complies with is verified by audit, because every oracle for that agreement is a second declaration. This complements the packaging and execution rules in `spx/13-plugin-and-runtime-conventions.adr.md`.

## Rationale

A standalone script needs no build step, no import packaging, and no third-party runtime, so it ships unchanged into any consumer repository. Supporting the two most recent Python releases lets shipped scripts use current language features without conditional fallbacks while still spanning the version a consumer most likely has; pinning the linter and type-checker to the floor keeps a script from using syntax the older supported release cannot run. The system macOS Python is unusable as a floor — it trails the language by years — so shipped scripts assume a managed interpreter. The support window rolls forward with each Python feature release: when a new release lands, the floor becomes the previously-newest version.

Testability does not decide where shipped logic lives, because a standalone script is importable: loading it through its module path and driving it with injected collaborators exercises every branch in isolation. Size decides whether generic logic belongs in the plugin or SPX. Past fifty lines a generic script accumulates state, branching, and contracts that a consumer repository cannot version independently and cannot repair without a marketplace release, while the SPX CLI carries that weight where it is versioned, released, and tested in its own right. Runtime-specific integration instead stays beside the skill that owns that runtime boundary when extraction would compromise SPX neutrality. Extraction follows proof rather than preceding it: a script earns extraction by proving its value in use, and one that never proves it is deleted, since extracting unproven logic moves cost into the CLI without establishing that the capability is wanted.

A value the spec tree declares and a source complies with admits no test of their agreement. Any oracle for it is a third statement of the value — after the spec tree's declaration and the source's compliance — and the second of those three to declare rather than comply: read from the source under test it compares that source to itself and holds for whatever the source contains, and transcribed into a test or a harness it creates a declaration in an artifact with no authority to make one. Behavior that depends on such a value is tested by importing the value from its complying source and exercising what it changes; the agreement between the declaration and that source is audit evidence. A value with no behavior to exercise — a process exit code, a protocol token — therefore reaches only audit.

## Invariants

- A plugin-local runtime adapter performs a bounded operation and exits; it owns no daemon, background watcher, or open-ended polling loop.
- A runtime adapter reads only the external runtime's public interface and produces a versioned, machine-readable result.

## Verification

### Audit

- ALWAYS: ship plugin scripting — skill scripts and hooks — as standalone Python scripts that run on the two most recent Python feature releases, from a managed interpreter, never the system macOS Python ([audit])
- ALWAYS: pin the linter and type-checker that govern shipped scripts to the floor of the supported window — the older of the two most recent releases — so a shipped script never uses a feature the floor lacks ([audit])
- ALWAYS: extract a generic shipped script's logic into the SPX CLI once the script proves its value, tested there and consumed by the plugins product as a trusted third-party component, leaving the skill its instruction and no script ([audit])
- ALWAYS: runtime-specific adapter logic remains plugin-local only when moving it into SPX would violate runtime neutrality and the adapter is deterministic, bounded, standard-library-only, and independently tested ([audit])
- ALWAYS: shipped Python that invokes external tools accepts a dependency-injected runner implementing a Protocol at the orchestration boundary, while its default runner owns subprocess execution ([audit])
- ALWAYS: tests supply controlled runner implementations through explicit dependency injection only under `/test` Stage 5 exception 1 (failure simulation) or exception 2 (interaction protocols) for external-tool failure and interaction evidence ([audit])
- ALWAYS: a test that depends on a value the spec tree declares imports that value from the source complying with the declaration, and exercises the behavior the value governs ([audit])
- NEVER: a generic shipped script beyond fifty lines stands as settled — it is debt awaiting extraction once proven, or removal when it is not ([audit])
- NEVER: retain an unproven shipped script — a script that has not proven its value is removed rather than extracted ([audit])
- NEVER: framework mocks replace shipped-script behavior or its external-tool boundary ([audit])
- NEVER: a plugin-local runtime adapter installs dependencies, starts a background process, or implements an open-ended polling wait ([audit])
- NEVER: a test or test-infrastructure artifact restates a spec-declared value to verify that a source honors it — that agreement is audit evidence, because every oracle for it is a second declaration ([audit])
