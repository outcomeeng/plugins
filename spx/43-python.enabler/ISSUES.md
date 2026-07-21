# Issues: Python Enabler

## 1. Python ships no per-language simplifier agent while Rust and TypeScript do

The `rust` and `typescript` plugins each ship a `-simplifier` agent (`rust-simplifier`, `typescript-simplifier`) that preloads its language `code`/`test` skills and simplifies recently modified code while preserving behavior and coverage. Each is declared in its node spec (`spx/43-rust.enabler/rust.md`, `spx/43-typescript.enabler/typescript.md`). The `python` plugin ships no agent at all, and `spx/43-python.enabler/python.md` declares none.

**Status against the standard.** `spx/21-spec-tree.enabler/17-audit.adr.md` governs only *auditor* agents — it mandates that no per-language auditor agent exist, and all three plugins comply (language audits ship as skills composed by the generic `implementation-auditor`). The simplifier is a different agent class, and no decision governs whether per-language simplifier agents should exist. So this is an unresolved cross-plugin inconsistency, not a contradiction of a loaded decision: Python authors get no simplifier entry point that their Rust and TypeScript counterparts get.

**Evidence.** Surfaced while auditing cross-language parity for the test-evidence-seam alignment. The Rust and TypeScript plugins carry `agents/{lang}-simplifier.md`; the Python plugin has no `agents/` directory. The `.claude-plugin/marketplace.json` descriptions reflect the same split (typescript and rust list a simplifier agent; python does not).

**Resolution shape.** Resolve with a governing decision on per-language simplifier agents before conforming the plugins, because the choice spans all three language plugins and TypeScript is owned by a separate worktree:

- add a `python-simplifier` agent mirroring `rust-simplifier`/`typescript-simplifier` and declare it in `python.md` (parity up), or
- retire `rust-simplifier` and `typescript-simplifier`, routing language simplification through the built-in `/simplify` plus each `code-{lang}` skill (parity down), coordinated across the rust, typescript, and python plugins.

Either direction wants an ADR blessing the standard before the agent set changes.
