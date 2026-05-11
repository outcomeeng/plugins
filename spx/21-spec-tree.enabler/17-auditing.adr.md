# Auditing Architecture

## Purpose

This decision governs the architecture of audit orchestration in the marketplace — how the generic `/auditing` skill and `auditor` agent dispatch to language-specific audit skills, how language detection happens, where the supporting deterministic computations live, and which naming patterns are load-bearing across plugins.

## Context

**Business impact:** Audit orchestration runs the audit-skill family on TypeScript, Python, Rust, and any future language plugin. Without a uniform pattern, each language plugin grows its own orchestrator that drifts in protocol, embeds language-specific knowledge in the wrong place, and duplicates the determinism contract (frozen scope, scope hash, frozen concerns, frozen findings, re-run protocol). Audit verdicts become incomparable across languages; bug fixes in one orchestrator do not propagate to the others; and the cost of adding a new language scales linearly rather than as a no-op.

**Technical constraints:** The marketplace has a precedent for generic-to-language-specific dispatch: `spx/21-spec-tree.enabler/65-applying.enabler/` defines `/applying`, which detects language by project-file presence and dispatches to `coding-{lang}` and `testing-{lang}` via a hardcoded skill map. LLMs running an orchestrator skill cannot reliably execute deterministic shell computations in-process — sha256, git diff parsing, branch slug derivation, lock acquisition all need a Python helper module. Plugin consumers do not receive `outcomeeng/scripts/`; that path is repo-internal marketplace tooling. Plugins ship their Python helpers strictly co-located with the skill that consumes them — every existing Python file in `plugins/` lives under a specific skill's `scripts/` or `references/` directory (see `spx/13-plugin-and-runtime-conventions.adr.md`).

## Decision

The marketplace ships a single generic `/auditing` skill and a single `auditor` agent in the spec-tree plugin. Both dispatch to language-specific `auditing-{lang}*` skills via template substitution from the language detected in scope. Every language plugin MUST ship `auditing-{lang}`, `auditing-{lang}-tests`, and `auditing-{lang}-architecture`. The deterministic computations the orchestrator depends on — scope hashing, branch slug, base-ref detection, monotonic finding IDs, lock acquisition — live in a Python helper module co-located with the `/auditing` skill at `plugins/spec-tree/skills/auditing/scripts/audit_orchestrator.py`.

## Rationale

The factoring rule that the orchestrator never embeds language-specific knowledge follows directly from `/applying`'s working precedent. `/applying` detects language by project-file presence and dispatches to `{verb}-{lang}` skills; the generic skill itself contains zero language-specific tokens beyond the dispatch template. `/auditing` adopts the same model with one refinement appropriate to its scope: where `/applying` operates on a whole TDD flow rooted in a project, `/auditing` operates on a frozen file list (the audit scope), so language detection happens at scope-partition time rather than at project-detection time. The LLM running the orchestrator reads the file extensions in scope (`*.ts`, `*.tsx`, `*.py`, `*.rs`), partitions by language, and runs the orchestration loop once per partition. No detection helper or required argument is needed — file-extension recognition is trivial training-time knowledge for any LLM that can run the orchestrator at all.

The naming convention as a hard invariant follows from the dispatch model. Template substitution requires that `auditing-{lang}` resolve to a real skill; any missing skill in the trio halts the orchestrator mid-audit with an error the caller cannot work around. Validating the trio at marketplace-validation time rather than at first-audit time makes the failure mode loud and immediate.

The dispatch model uses hardcoded template substitution rather than a per-skill self-description block (YAML or otherwise) because the audit skills' content already IS the contract. The orchestrator does not need to query a skill for what file globs it cares about, what config files it reads, or what gate command it runs — the skill's own protocol handles those concerns when the orchestrator dispatches into it. The skill name resolves the dispatch on its own; a metadata layer adds an authoring surface every language audit skill must maintain in exchange for nothing the dispatch lacks.

The Python helper module's placement under the `/auditing` skill's `scripts/` directory follows the marketplace-wide co-location convention. Every existing Python file in `plugins/` lives under a specific skill: excalidraw's `references/render_excalidraw.py` (with its own `pyproject.toml`), creating-skills' `scripts/init_skill.py`, github-actions' `scripts/workflow_inspect.py`. None lives at plugin root. The `/auditing` skill is the helper module's exclusive consumer; co-location matches the consumer, mirrors precedent, and avoids inventing a new "shared infrastructure" plugin-root convention solely to host one module.

Naming the skill `/auditing` and the agent `auditor` parallels `/applying` and `applier`. The orchestration role is the skill's purpose, not its name — `applier` applies, `auditor` audits, both via dispatch. The bare `auditor` name coexists cleanly with the existing narrow `*-auditor` agents (`pdr-auditor`, `test-evidence-auditor`): the bare form is the broad multi-phase orchestrator; compound forms wrap specific narrow audit skills. This is the same disambiguation pattern the `auditing-*` skill family uses.

Alternatives considered:

- **Per-language orchestration skills and agents** (`typescript-audit-orchestrator`, `python-audit-orchestrator`, `rust-audit-orchestrator`). Rejected: the protocol is identical across languages; per-language wrappers duplicate it and drift. Language-specific content accumulates in the wrapper instead of in the corresponding `auditing-{lang}*` skill, and bug fixes to the protocol must be ported across every wrapper rather than landing once.
- **Audit-skill self-description block** declaring file globs, configs, gate command, test command. Rejected: `/applying` works without one. The dispatch contract is the skill name, not the skill's metadata. Adding a descriptor pattern would create a new authoring obligation for every language audit skill that solves a problem the dispatch does not have.
- **Plugin-root Python scripts** (`plugins/spec-tree/scripts/audit_orchestrator.py`). Rejected: contradicts every existing precedent in the marketplace. Would require establishing "shared infrastructure scripts at plugin root" as a new convention solely to host one helper module.
- **Project-file detection like `/applying`** (`tsconfig.json` → TypeScript) instead of scope-extension partitioning. Rejected for `/auditing`'s use case: an audit may be invoked on a strict subset of a multi-language repo; project-file detection at the repo level reports the wrong language for partial audits. Scope-extension partitioning correctly identifies the language under audit and naturally handles mixed scopes by running the audit once per language partition.

## Trade-offs accepted

| Trade-off                                                                                                | Mitigation / reasoning                                                                                                                                                  |
| -------------------------------------------------------------------------------------------------------- | ----------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| Language plugins MUST ship the auditing-{lang}* trio or the orchestrator halts mid-audit                 | Marketplace validation pipeline enforces the trio at install/check time; failure is loud and pre-runtime rather than mid-audit                                          |
| LLM extension partitioning relies on the orchestrator's LLM correctly recognizing file extensions        | File extensions are unambiguous training-time knowledge; the orchestrator already reads the scope in Phase 0 to compute the scope hash, so partitioning adds no new I/O |
| Helper module is co-located with the consumer skill rather than reusable across other spec-tree concerns | The `/auditing` skill is its sole consumer today; if a second consumer appears, the module migrates to a shared location at that time rather than speculatively         |
| State files per language under `.spx/audits/<lang>/<branch-slug>.md` produce one file per language       | Per-language scopes produce per-language state naturally; aggregation across languages is the orchestrator's responsibility, not the filesystem's                       |
| Mixed-language scopes produce multiple verdicts in a single orchestrator invocation                      | The orchestrator emits one verdict per language partition; the caller composes them; matches how the LLM running the orchestrator already reasons about mixed scopes    |

## Compliance

### Recognized by

The spec-tree plugin ships exactly one orchestration skill (`/auditing`) and one orchestration agent (`auditor`), neither of which embeds language-specific tokens beyond the dispatch template `auditing-{lang}*` and the language path-segment placeholder `<lang>`. Each language plugin ships exactly the trio `auditing-{lang}`, `auditing-{lang}-tests`, `auditing-{lang}-architecture`. The `/auditing` skill's `scripts/audit_orchestrator.py` Python module owns every deterministic computation invoked during an audit run. Audit state files use the path `.spx/audits/<lang>/<branch-slug>.md` with `<lang>` as a literal path segment.

### MUST

- The `/auditing` skill and the `auditor` agent contain zero language-specific tokens beyond the dispatch template `auditing-{lang}*` and the language path-segment placeholder `<lang>` — prevents the language-leakage failure mode where per-language wrappers absorb content that belongs in the corresponding `auditing-{lang}*` skill; the orchestrator is dispatch, not domain knowledge ([review])
- Every marketplace plugin that defines a programming language ships `auditing-{lang}`, `auditing-{lang}-tests`, and `auditing-{lang}-architecture` — the orchestrator's dispatch is template substitution; the trio's existence is the contract that makes dispatch resolvable ([review])
- Deterministic computations invoked by the `/auditing` skill or the `auditor` agent live in `plugins/spec-tree/skills/auditing/scripts/audit_orchestrator.py` — LLMs cannot reliably hash, derive branch slugs, run git plumbing, or acquire locks in-process; the helper module is the boundary that makes these computations testable ([review])
- The `/auditing` skill partitions multi-language scopes by file extension and runs the orchestration protocol once per language partition — handles mixed-language repos without requiring callers to filter the scope and without halting on plurality ([review])
- The `auditor` agent's state file lives at `.spx/audits/<lang>/<branch-slug>.md` — per-language scopes produce per-language state files; finding identity stays unambiguous across languages on the same branch ([review])

### NEVER

- Introduce language-specific examples, file extensions, validation commands, test commands, failure-mode prose, or evidence patterns into the `/auditing` skill or the `auditor` agent — that content belongs in the corresponding `auditing-{lang}*` skill; cross-cutting placement is the failure mode this ADR exists to prevent ([review])
- Ship per-language audit-orchestration skills or agents such as `typescript-audit-orchestrator` or `python-audit-orchestrator` — the generic skill and agent serve every language by dispatch; per-language wrappers reintroduce the duplication and drift this decision rejects ([review])
- Embed deterministic shell pipelines (`sha256sum`, `git diff`, branch detection, slug computation) directly in the `/auditing` skill prose or the `auditor` agent prompt — inline shell relies on Bash invocation discipline that LLMs cannot guarantee; the helper module exists to make these computations correct and testable ([review])
- Add a per-skill self-description block (YAML, XML, or otherwise) to `auditing-{lang}*` skills declaring file globs, configuration files, gate commands, or test commands — the `/auditing` skill's dispatch contract is the skill name; metadata blocks add an authoring surface that solves no dispatch problem ([review])
- Place the audit-orchestrator Python helper module at `plugins/spec-tree/scripts/` or any other plugin-root location — the marketplace co-locates Python under the consuming skill (see `spx/13-plugin-and-runtime-conventions.adr.md`); plugin-root scripts are not an established convention ([review])
