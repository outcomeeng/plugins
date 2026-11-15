---
id: 01a0ebba-5f63-709a-9097-ec003c9fd339
malleability: spec
---

# Instruction Block

PROVIDES deterministic generation and validation of a managed Product Tree instruction surface in a product's root agent-harness instruction files — `CLAUDE.md` for Claude Code and `AGENTS.md` for Codex — composed of a generated router block rendered from the harness templates committed under `dist/`, `shared` regions kept byte-identical across both files, and independent product content free to differ per file, scoped to the project's enabled languages and rendered per agent harness
SO THAT every agent working a product-tree project
CAN retain the Product Tree routing instructions and reach the product's own phase commands across compaction while preserving the product's other root instructions and keeping the two root files consistent

## Assertions

- token-file-mapping: ALWAYS: the instruction-block generator reads the agent tokens from the data file the build renders beside it and maps to a root instruction file only the tokens that have one: `claude` to `CLAUDE.md` and `codex` to `AGENTS.md`
- no-token-declaration: NEVER: the toolchain's instruction-block writer or a test of this node declares an agent token; each takes it from the module that owns it
- change-lifecycle-section: ALWAYS: both harness routers carry a Change Lifecycle section that routes a held Change whose work stops with continuation remaining to the release Transition of `manage-change`, a held Change that meets the close condition of its type to its applied Transition, and a held Change whose work ends before it produces its Output, or that a merge absorbs into another Change, to its abandoned Transition

### Test.Compliance: switch

- [switch-dispatch](tests/test_instruction_block_switch.compliance.l1.py): ALWAYS: when the environment variable `OUTCOMEENG_INSTRUCTION_BLOCKS` holds exactly `off`, the instruction-block command-line entry runs no generation and no drift check, names the variable on stderr, and exits 0; under every other value or none it runs the generator with its arguments and exits with the generator's code
- [switch-command-line](tests/test_instruction_block_switch.compliance.l2.py): ALWAYS: the module's command line, run with `OUTCOMEENG_INSTRUCTION_BLOCKS=off` in check mode and in write mode, leaves both root instruction files byte-identical, names the variable on stderr, and exits 0

### Test.Scenario: rendering

- [harness-render](tests/test_instruction_block.scenario.l1.py):
  - Given a template with language blocks and per-harness blocks
  - When the managed surface is generated for an enabled-language set
  - Then both `CLAUDE.md` and `AGENTS.md` are written, each with its router block first, preserving content outside every managed fence, and containing inside the router block exactly the enabled languages' blocks and only its own harness's blocks
- [shared-and-independent-kept](tests/test_instruction_block.scenario.l1.py):
  - Given a generation over a file with a `shared` region and independent product prose
  - When the managed surface is written
  - Then the router block is re-rendered from the template at the top, each `shared` region body is preserved, and independent content outside every fence is preserved verbatim
- [router-marker-shape](tests/test_instruction_block.scenario.l1.py):
  - Given the router block
  - When it is written
  - Then its opening marker is `<!-- PRODUCT-TREE v{template_version} langs:{enabled-languages} -->` carrying only the version and the recorded enabled-language list, its closing marker is `<!-- /PRODUCT-TREE -->`, and no template-source field is recorded
- [harness-outputs-differ-by-spans](tests/test_instruction_block.scenario.l1.py):
  - Given the `CLAUDE.md` and `AGENTS.md` outputs of one generation
  - When they are compared
  - Then they share every line except the per-harness spans the template marks and their own filename; the router content, shared regions, and out-of-fence content are otherwise identical
- [superset-template-update](tests/test_instruction_block.scenario.l1.py):
  - Given template version B whose section set is a strict superset of version A
  - When a version-A managed surface is updated from version B
  - Then both re-rendered router blocks contain the additional section, still carry the recorded enabled languages, and preserve every `shared` region body
- [template-path-validated](tests/test_instruction_block.scenario.l1.py):
  - Given a `--template` argument that is a symlink or does not resolve to an existing regular file
  - When the CLI runs
  - Then the path is validated and rejected before any read, so a faulty argument cannot escape into an unintended file
- [template-version-required](tests/test_instruction_block.scenario.l1.py):
  - Given a template whose frontmatter omits `template_version` while its body carries a router marker with a parseable version
  - When the CLI runs
  - Then it exits nonzero with `error: template has no template_version` before rendering or writing either root instruction file
- [unparseable-version-stale](tests/test_instruction_block.scenario.l1.py):
  - Given a router block whose `template_version` is not parseable as dotted integers
  - When staleness is checked
  - Then it is treated as stale rather than raising, so a re-render normalizes it to the installed version
- [symlinked-claude-copied](tests/test_instruction_block.scenario.l1.py):
  - Given root `CLAUDE.md` is a symlink to `AGENTS.md`
  - When the managed surface is updated
  - Then `CLAUDE.md` becomes a regular file copy and both root instruction files preserve the shared root body outside their harness-specific router blocks
- [markerless-surface-replaced](tests/test_instruction_block.scenario.l1.py):
  - Given a root instruction file contains a markerless full-file Product Tree instruction surface
  - When the managed surface is updated
  - Then the generated full-file body is replaced rather than preserved ahead of the router block

### Test.Scenario: delegation

- [delegation-candidate-kept](tests/test_instruction_block.scenario.l1.py):
  - Given one root instruction file whose body names the other root instruction file within the absolute stub bound
  - When the managed surface is updated with no operator answer
  - Then that body survives intact, the file is reported as a delegation candidate, and the surface reports `stale` until the answer arrives
- [answer-adopts-side](tests/test_instruction_block.scenario.l1.py):
  - Given a reported delegation candidate and an operator answer naming the side both files take
  - When the managed surface is updated with that answer
  - Then both files carry the named body wrapped as one `shared` region under each harness's router, so neither file retains the pointer and the two files are identical outside their router blocks
- [mutual-pointers-kept](tests/test_instruction_block.scenario.l1.py):
  - Given both root instruction files name each other within the absolute stub bound
  - When the managed surface is updated
  - Then both are reported as delegation candidates and each file keeps its own body under its router block, because no answer names a side and neither carries content the other could take
- [pointer-side-refused](tests/test_instruction_block.scenario.l1.py):
  - Given an operator answer naming a side whose own body points at the other root instruction file
  - When the managed surface is updated with that answer
  - Then the update is refused and both root files stand unchanged, because adopting that side installs a body sending the reader to a file carrying the same pointer
- [content-body-refused](tests/test_instruction_block.scenario.l1.py):
  - Given an operator answer whose adoption would replace a body carrying content of its own rather than a pointer
  - When the managed surface is updated with that answer
  - Then the update is refused and both root files stand unchanged, because adoption replaces a whole body and no report offered that body up
- [closed-bootstrap-refused](tests/test_instruction_block.scenario.l1.py):
  - Given an operator answer arriving once the bootstrap pass has closed, a root instruction file already carrying a `shared` region or a malformed shared fence
  - When the managed surface is updated with that answer
  - Then the update is refused rather than written, so no run reports success for an answer nothing applied
- [answer-needs-write](tests/test_instruction_block.scenario.l1.py):
  - Given an operator answer supplied without the write that applies it
  - When the CLI runs
  - Then it exits nonzero naming the required write and both root files stand unchanged, so the answer is never discarded behind a clean render

### Test.Scenario: superseded markers and inline quotes

- [alternate-markers-replaced](tests/test_instruction_block.scenario.l1.py):
  - Given a root instruction file carries a managed block delimited by the alternate `BEGIN MANAGED SPEC TREE INSTRUCTIONS` / `END MANAGED SPEC TREE INSTRUCTIONS` markers and their metadata comment lines
  - When staleness is checked
  - Then it reports `stale`
  - And when the managed surface is updated, the alternate-marker block is replaced in place with the compressed `PRODUCT-TREE` router marker rather than duplicated
- [spec-tree-router-replaced](tests/test_instruction_block.scenario.l1.py):
  - Given a root instruction file carries a router block under the superseded `<!-- SPEC-TREE v{template_version} langs:{enabled-languages} -->` / `<!-- /SPEC-TREE -->` markers
  - When staleness is checked
  - Then it reports `stale`
  - And when the managed surface is updated, that block is replaced in place with the `PRODUCT-TREE` router marker rather than duplicated and the product prose after it is preserved
- [spec-tree-shared-rewritten](tests/test_instruction_block.scenario.l1.py):
  - Given a root instruction file carries a `shared` region fenced with the superseded `SPEC-TREE:shared` namespace
  - When staleness is checked
  - Then it reports `stale`
  - And when the managed surface is updated, each such fence standing alone on its line is rewritten to `PRODUCT-TREE:shared` with the region body preserved, so the region keeps reconciling across both root files
- [inline-router-marker-kept](tests/test_instruction_block.scenario.l1.py):
  - Given product prose that quotes the literal router marker as an inline example before the managed block
  - When the managed surface is updated
  - Then only the marker on its own fence line opens the block, so the inline example prose is preserved rather than replaced through the real closing fence
- [inline-closing-marker-kept](tests/test_instruction_block.scenario.l1.py):
  - Given a router block whose body or following independent content quotes the literal `<!-- /PRODUCT-TREE -->` closing marker inline
  - When the managed surface is updated
  - Then only the standalone-line closing fence bounds the router block, so the inline-quoted marker and the content around it are preserved rather than swallowed at the quote
- [inline-shared-fence-kept](tests/test_instruction_block.scenario.l1.py):
  - Given product prose that quotes a literal `shared`-region fence as an inline example
  - When the managed surface is read or written
  - Then only a fence on its own line delimits a `shared` region, so the quoted example is not mistaken for a region opener and the prose is preserved
- [blank-runs-kept](tests/test_instruction_block.scenario.l1.py):
  - Given a root instruction file whose independent product content carries a run of blank lines
  - When the managed surface is written
  - Then the blank-line run is preserved verbatim rather than collapsed

### Test.Scenario: shared regions

- [newer-region-wins](tests/test_instruction_block.scenario.l1.py):
  - Given two root files whose same-named `shared` region diverges and whose region-touching commits carry different dates
  - When the shared regions are reconciled
  - Then the side whose region was committed more recently is written whole into the other file, decided by that region's own line-range history rather than the whole file's last commit
- [losing-region-replaced-whole](tests/test_instruction_block.scenario.l1.py):
  - Given two root files whose same-named `shared` region diverges
  - When the shared regions are reconciled
  - Then the losing file's region body is replaced in full by the winning side and no line of the two bodies is blended
- [same-date-tie-reported](tests/test_instruction_block.scenario.l1.py):
  - Given two root files whose same-named `shared` region diverges but whose region-touching commits carry the same date
  - When reconciliation runs
  - Then the tie is reported as an ambiguous case for `/update-instruction-block` reconciliation rather than resolved by guess
- [one-sided-region-reported](tests/test_instruction_block.scenario.l1.py):
  - Given a `shared`-region fence present in one root file with no same-named region in the other
  - When the managed surface is checked
  - Then the mismatch is reported as an ambiguous case for skill reconciliation rather than auto-resolved
- [malformed-fence-reported](tests/test_instruction_block.scenario.l1.py):
  - Given a root instruction file carries a malformed `shared` fence, an open marker with no matching closing fence or a name opened more than once
  - When the managed surface is checked
  - Then the malformed region is reported as stale drift for skill reconciliation rather than silently skipped or collapsed
- [malformed-fence-not-wrapped](tests/test_instruction_block.scenario.l1.py):
  - Given two root files carry a malformed `shared` fence and no valid shared region
  - When the managed surface is written
  - Then the bootstrap does not wrap the malformed fence into a new region; it inserts only the router and leaves the fence as independent content the drift gate reports as stale
- [dirty-file-untouched](tests/test_instruction_block.scenario.l1.py):
  - Given a root instruction file with uncommitted working-tree changes
  - When shared-region reconciliation runs
  - Then it makes no change and reports the dirty file, operating only on committed state
- [router-first-checked](tests/test_instruction_block.scenario.l1.py):
  - Given a root instruction file whose router block is preceded by product content
  - When staleness is checked
  - Then it reports `stale`, so a re-render moves the router back to the first content of the file
- [shared-region-line-snapped](tests/test_instruction_block.scenario.l1.py):
  - Given two root files whose biggest identical span begins at a line boundary in one file but mid-line in the other
  - When the bootstrap wraps a `shared` region
  - Then the region is snapped to whole lines in both files, so a harness-specific prefix on the shared line is never split

### Test.Scenario: agent-token input

- [token-file-failure](tests/test_agent_tokens_load.scenario.l1.py):
  - Given the agent-tokens data file beside the generator is absent, unreadable, malformed JSON, a JSON value that is not an object, or missing the `CLAUDE` or `CODEX` key
  - When the generator runs
  - Then it prints one `error:` line on stderr naming the file, what is wrong, and the fix, exits 2, and raises no traceback, in the form of its other input failures

### Test.Mapping: [budget-report](tests/test_budget_measurement.mapping.l1.py)

Generation and the `--check` verb measure each rendered root instruction file's byte size against the 32768-byte combined Codex project-doc ceiling declared in [`spx/21-product-tree.enabler/43-instruction-block.enabler/21-render-model.adr.md`](spx/21-product-tree.enabler/43-instruction-block.enabler/21-render-model.adr.md), and map it to a per-file report carrying the exact size and breach state.

| Case   | Rendered size                        | Report                                    |
| ------ | ------------------------------------ | ----------------------------------------- |
| within | at most the ceiling                  | the exact size and no breach              |
| breach | above the ceiling                    | the exact size and a breach               |
| utf-8  | a file holding multi-byte UTF-8 text | the size counted in bytes, not characters |

### Test.Mapping: [router-spacing](tests/test_router_spacing.mapping.l1.py)

For every agent harness and enabled-language subset, rendering the canonical instruction-block template maps to a router block with exactly one blank line between its opening marker and first body content.

| Case        | Render                                        | Router block                            |
| ----------- | --------------------------------------------- | --------------------------------------- |
| any-harness | any agent harness and enabled-language subset | one blank line after the opening marker |

### Test.Mapping: [duplicate-flag](tests/test_instruction_block.mapping.l1.py)

Each supported CLI flag maps to a duplicate-flag rejection when it appears more than once in raw arguments, before argument parsing reads a template or repository path.

| Case          | Raw arguments                  | Outcome                                   |
| ------------- | ------------------------------ | ----------------------------------------- |
| repeated-flag | any supported flag given twice | exit 2 with the rejection naming the flag |

### Test.Mapping: [language-block](tests/test_instruction_block.mapping.l1.py)

Over the languages the template defines blocks for, a language's block appears in a rendered router block when the language is in the detected enabled set and is omitted otherwise.

| Case     | Language                         | Router block               |
| -------- | -------------------------------- | -------------------------- |
| enabled  | in the detected enabled set      | holds the language's block |
| disabled | outside the detected enabled set | omits the language's block |

### Test.Mapping: [extension-language](tests/test_instruction_block.mapping.l1.py)

A test-file extension present under `spx/**/tests/` maps to the language it denotes, and the detected enabled-language set is the set of those mappings.

| Case         | Input                                       | Result                                 |
| ------------ | ------------------------------------------- | -------------------------------------- |
| extension    | one test-file extension the generator knows | the language that extension denotes    |
| detected-set | the test files under `spx/**/tests/`        | the set of their extensions' languages |

### Test.Mapping: [router-check-state](tests/test_instruction_block.mapping.l1.py)

The `--check` verb maps a router-block state to its report.

| Case                 | Router block                                    | Report    |
| -------------------- | ----------------------------------------------- | --------- |
| current              | version-current with the detected languages     | `current` |
| absent               | missing                                         | `absent`  |
| version-behind       | below the installed template version            | `stale`   |
| language-set-differs | detected languages differ from the recorded set | `stale`   |

### Test.Mapping: [shared-check-state](tests/test_instruction_block.mapping.l1.py)

The `--check` verb maps a `shared`-region state to its report.

| Case           | Same-named regions                     | Report    |
| -------------- | -------------------------------------- | --------- |
| byte-identical | two regions with byte-identical bodies | `current` |
| diverged       | two regions with diverged bodies       | `stale`   |
| one-sided      | a region present in only one file      | `stale`   |

### Test.Mapping: [bootstrap-topology](tests/test_instruction_block.mapping.l1.py)

An initial root-instruction-file topology maps to its bootstrap outcome.

| Case                  | Initial topology                                                                     | Outcome                                                                                             |
| --------------------- | ------------------------------------------------------------------------------------ | --------------------------------------------------------------------------------------------------- |
| one-file              | only one file present                                                                | the other created identical, with one `shared` region under the router                              |
| symlinked             | a symlinked file                                                                     | both regular files, with one `shared` region under the router                                       |
| stub-pointer          | one file whose body names the other within the absolute stub bound                   | both bodies preserved under their routers, no `shared` region, adoption awaiting an operator answer |
| identical             | both identical with no managed block                                                 | one `shared` region under an inserted router                                                        |
| identical-alternate   | both identical carrying an alternate managed block                                   | the router replacing that block, with the remainder wrapped `shared`                                |
| over-threshold        | both differing, with a biggest contiguous identical span over 80% of the larger file | the router plus that one `shared` region and an independent remainder                               |
| at-or-below-threshold | both differing, at or below that threshold                                           | the router only                                                                                     |

### Test.Mapping: [language-gated-section](tests/test_instruction_block.mapping.l1.py)

The enabled-language set maps a section that introduces per-language content but carries no per-language block of its own to its presence in the rendered router.

| Case      | Enabled-language set | Section                                                                                          |
| --------- | -------------------- | ------------------------------------------------------------------------------------------------ |
| non-empty | non-empty            | rendered                                                                                         |
| empty     | empty                | omitted whole, rather than its heading and preamble standing above the tables the render dropped |

### Test.Mapping: [delegation-candidacy](tests/test_instruction_block.mapping.l1.py)

A root-instruction-file body maps to a delegation candidacy from two facts about the file and no reading of its prose: whether it names the other root instruction file, and its length against the absolute stub bound.

| Case          | Body                                                                         | Candidacy    |
| ------------- | ---------------------------------------------------------------------------- | ------------ |
| within-bound  | names the other root instruction file, its text within the bound             | candidate    |
| at-bound      | names the other root instruction file, its text exactly the bound            | candidate    |
| past-bound    | names the other root instruction file, its text one character past the bound | no candidate |
| no-other-file | names no other root instruction file                                         | no candidate |

### Test.Property: rendering and reconciliation

- [plugin-list-complete](tests/test_plugin_authorization.property.l1.py): The generated root guide contains the complete authorized plugin list derived from the owning catalog; adding a role within an authorized plugin leaves the guide unchanged, while adding an authorized plugin updates the list
- [language-override-rejected](tests/test_language_override.property.l1.py): For every explicit language token outside the language set declared by the canonical instruction-block template, the CLI rejects the `--languages` override and names every allowed language
- [router-version-installed](tests/test_instruction_block.property.l1.py): Every generated router block's `template_version` equals the installed template version
- [one-trailing-newline](tests/test_instruction_block.property.l1.py): Every rendered managed surface ends with exactly one trailing newline
- [staleness-order](tests/test_instruction_block.property.l1.py): Staleness ordering matches dotted-numeric version order: a product version is stale exactly when it is numerically below the installed template version
- [shared-bodies-identical](tests/test_instruction_block.property.l1.py): Every reconciled `shared` region body is byte-identical in `CLAUDE.md` and `AGENTS.md`
- [one-shared-region](tests/test_instruction_block.property.l1.py): The bootstrap pass wraps at most one `shared` region for any pair of root-file contents
- [span-threshold](tests/test_instruction_block.property.l1.py): For every pair of root-file contents, the biggest contiguous identical whole-line span determines the wrap decision from its length over the larger file: one `shared` region above the threshold and no region at or below it
- [reconcile-idempotent](tests/test_instruction_block.property.l1.py): Reconciling an already-byte-identical `shared` region is idempotent; the two files are unchanged

### Test.Compliance: budget and agent registry

- [budget-breach-report](tests/test_budget_measurement.compliance.l1.py): ALWAYS: a rendered root instruction file exceeding the ceiling is reported as a breach carrying the exact byte counts — file size, ceiling, and overage
- [budget-gate-regression](tests/test_budget_gate.compliance.l1.py): ALWAYS: the drift gate reports a breach the checked change did not introduce and fails a regression above the ceiling by a surface that previously fit
- [registry-names](tests/test_agent_registry.compliance.l1.py): ALWAYS: the Codex router states that the selected agent home contains one current canonical subagent definition per authored marketplace agent, with each name formed as `<plugin>_<unchanged-authored-role>`; a repeated word across those two components is valid
- [registry-repair](tests/test_agent_registry.compliance.l1.py): ALWAYS: the Codex router directs a missing-definition repair to refresh the owning plugin's definitions in the selected `CODEX_HOME/agents/` directory and then reload the harness plugin index or start a new session; it never directs the reader to create or commit checkout agent definitions
- [registry-scope-split](tests/test_agent_registry.compliance.l1.py): ALWAYS: the Codex router identifies plugin-owned checkout agent definitions whose invoked skills live in the selected agent home as a scope split, directs removal only for byte-identical plugin copies, and directs inspection of changed or unrecognized copies as shadowing collisions

### Test.Compliance: router authority

- [authority-hierarchy](tests/test_instruction_block.compliance.l1.py): ALWAYS: generation emits and validates a strongly warned authority hierarchy of operator → active skills → repository decisions and specs → verification evidence → code, states that centrally managed skills outrank stale repository content, and requires a lower layer to be fixed rather than weakening a higher layer
- [overlay-below-skill](tests/test_instruction_block.compliance.l1.py): ALWAYS: generation emits and validates that an active skill loads a matching `spx/local/*.md` overlay only when the skill declares one, and that the overlay supplies repository-specific values and commands below the skill without replacing, weakening, or contradicting it
- [no-spec-citations-in-code](tests/test_instruction_block.compliance.l1.py): NEVER: generation permits code comments or docstrings to reference Product Tree specs or decisions through `spx/...` paths, ADR/PDR identifiers, or decision-file references
- [harness-guide-first](tests/test_instruction_block.compliance.l1.py): ALWAYS: generation emits and validates that the active harness guide in every directory is read before work in that directory when the guide exists — `CLAUDE.md` for Claude Code and `AGENTS.md` for Codex
- [foundation-marker-gate](tests/test_instruction_block.compliance.l1.py): ALWAYS: generation emits and validates a managed router that requires a live `PRODUCT_TREE_FOUNDATION` marker before direct filesystem access under `spx/` or access to source and test content, while exempting `spx session` operations — including inspection, archive, and release — `spx worktree status`, `spx diagnose`, and no-patch Git status, history, and topology until their output is followed into product content
- [operator-question](tests/test_instruction_block.compliance.l1.py): ALWAYS: when the operator asks a question, both harness routers revoke mutation privileges, stop destructive or state-changing non-verification processes, preserve running verification unless the operator explicitly instructs that process to stop, and require an immediate answer
- [codex-verifier-spawning](tests/test_instruction_block.compliance.l1.py): ALWAYS: the Codex router applies Verifier spawning only to the Author's main conversation; an already-dispatched Verifier executes its configured methodology directly and never searches for or launches another Verifier through typed-agent discovery or an external agent CLI
- [wait-for-load-pinned](tests/test_instruction_block.compliance.l1.py): NEVER: generation writes a router whose `/wait-for-load` section lacks a pinned requirement, carries one outside that section, omits a Codex-only requirement from the Codex router, names a host-load waiter or a lock switch, or carries a directive that uses host load to reduce verification; the render fails naming the missing or contradicted requirement
- [methodology-declaration](tests/test_methodology_declaration.compliance.l1.py): ALWAYS: generation emits, in the `/understand` section, the instruction to read the methodology source and version the repository follows from `spx.config.yaml` at the repository root, to read it again whenever `/understand` runs, and to treat an absent file, a missing `methodology` block, or a `methodology.version` of the sentinel `installed` as no declared methodology version, never inferring one from a plugin's distribution version, a changelog, or prose; the instruction reads the same declaration the SPX CLI resolves, as the reader's stand-in for the methodology declaration context loading delivers per `spx/21-product-tree.enabler/18-context-loading.enabler/context-loading.md`
- [branch-deletion-guard](tests/test_dangerous_branch_deletion.compliance.l1.py): ALWAYS: generation emits and validates a dangerous-command guard under which a block on a command holding one operation with every string written literally terminates that command family, a block on a command holding a process substitution, a pipe between two operations, a background `&`, a subshell, or a list that mixes `&&` and `||` — a composition the parts cannot carry — terminates its command family too, even when it also holds a join or an expansion, and a block on a compound command — two or more operations separated by `;` or a newline or joined by `&&` alone or by `||` alone, or one operation whose words the shell expands (a variable, a command substitution, a glob, or a tilde, brace or arithmetic expansion), or a heredoc with an unquoted delimiter whose body expands — runs its parts again one at a time with every string written literally, in their original order, `;` and a newline separating lists that each run regardless of the one before, and within a list the parts joined by `&&` alone running while the part before them succeeded and the parts joined by `||` alone running until one succeeds, each value resolved first (a command substitution's inner command run on its own, a variable's assigned literal or `printenv` output, a glob's matching entries from a listing of its literal directory, or from the file-search tool on the full pattern when a directory component has a wildcard, a tilde, brace or arithmetic expansion written out as its words) and the operation then run once with literal arguments, a secret value — a token, key or credential — never printed or written into a command and its resolution ending the command family instead; a heredoc that feeds one command holds one operation unless its delimiter is unquoted and its body expands, and an input redirect from a payload scratch file holds one operation, so neither counts as a join or separator; a part the guard blocks on its own terminates that part's family, and no blocked command is reformulated, stripped of its flagged clause, or replaced by an equivalent command; the guard routes through active skills and repository-declared sanctioned operations, otherwise reports the redacted command, purpose, and guard reason before stopping for operator direction, forbids dynamic branch names in `git branch -d` and `git branch -D` — variables, command substitutions, arrays, and globs even when quoted or placed after `--` — requires every branch name to be literal, and permits several literal names in one invocation

### Test.Compliance: router placement

- [both-root-files](tests/test_instruction_block.compliance.l1.py): ALWAYS: generation writes the managed surface in both root `CLAUDE.md` and root `AGENTS.md`, never one without the other — each agent reading the same repository gets its own harness router block in the root instruction file it retains across compaction
- [router-first](tests/test_instruction_block.compliance.l1.py): ALWAYS: generation places the router block first in each root file
- [read-whole-file](tests/test_instruction_block.compliance.l1.py): ALWAYS: generation emits a concrete instruction directing the reader to read the entire root instruction file
- [no-session-result-token](tests/test_instruction_block.compliance.l1.py): NEVER: generation emits a router block containing the session-result archive instruction token or the `result` session frontmatter field token
- [no-unresolved-delimiters](tests/test_instruction_block.compliance.l1.py): NEVER: instruction-block generation writes output from a harness template that still contains unresolved build-template delimiters such as `{{! ... !}}`
- [no-spx-guides](tests/test_instruction_block.compliance.l1.py): NEVER: `spx/CLAUDE.md` or `spx/AGENTS.md` remain after generation — the root managed surface is the canonical instruction surface
- [brace-tokens-kept](tests/test_instruction_block.compliance.l1.py): ALWAYS: rendering preserves brace-delimited template tokens byte-for-byte

### Test.Compliance: writer and workflows

- [dist-templates](tests/test_instruction_block.compliance.l1.py): ALWAYS: instruction-block generation reads the harness-specific templates from `dist/claude/` and `dist/codex/`, so the update surface consumes the same rendered output this product ships as installed plugin trees
- [just-recipes](tests/test_instruction_block.compliance.l1.py): ALWAYS: instruction-block writing is exposed to agents through the repository Justfile recipe `just build-instructions`; `just instructions-check` is the drift gate over the same writer
- [pre-commit-writer](tests/test_instruction_block.compliance.l1.py): ALWAYS: the pre-commit hook regenerates the root managed surface through `just build-instructions` — the rendered-`dist/` template writer — never by invoking the generator directly against the authored `src/` template
- [drift-intent-to-add](tests/test_instruction_block.compliance.l1.py): ALWAYS: the drift gate reports missing root instruction-file paths as drift and marks only existing generated instruction-file paths with `--intent-to-add`, so deleted `spx/CLAUDE.md` and `spx/AGENTS.md` instruction files are reported by `git diff` without causing a missing-path failure
- [regenerate-overwrites](tests/test_instruction_block.compliance.l1.py): ALWAYS: regenerating a drifted router block overwrites the drift — a re-render restores the template's content over any hand-edit, the basis of the regenerate-and-diff gate that keeps both files current without an agent invocation
- [refresh-opens-pr](tests/test_instruction_block.compliance.l1.py): ALWAYS: the refresh workflow regenerates skill output and the root managed surface, then opens or updates a pull request only when git drift exists
- [refresh-on-main](tests/test_instruction_block.compliance.l1.py): ALWAYS: the refresh workflow checks out the default branch `main`, so its regeneration and drift comparison run against the published tree
- [just-checksum](tests/test_instruction_block.compliance.l1.py): ALWAYS: the refresh workflow verifies the pinned `just` download against its recorded SHA-256 checksum before installing it, so a tampered or moved release fails the run rather than executing
- [dprint-provisioned](tests/test_instruction_block.compliance.l1.py): ALWAYS: the refresh workflow provisions `dprint` before regenerating skill output, because `just build-skills` formats generated `dist/` output with `dprint` and fails without it

### Test.Compliance: preservation

- [no-slot-fence](tests/test_instruction_block.compliance.l1.py): NEVER: the generator recognizes a `PRODUCT-TREE:{name}` slot fence as a managed command slot — the fence is ordinary independent content, never a slot the router resolves by name
- [no-blending](tests/test_instruction_block.compliance.l1.py): NEVER: a `shared`-region reconciliation blends the two bodies — the losing file's region is replaced whole by the winning side
- [no-hand-prose-kept](tests/test_instruction_block.compliance.l1.py): NEVER: an update keeps an unmodeled hand-prose edit inside the router block — a re-render reflects only the template, the recorded enabled languages, and the harness, while `shared` regions and independent content are preserved

### Audit: router content

- standing-request: ALWAYS: both generated root guides preserve the standing-request sentence in [`spx/15-subagent-execution.pdr.md`](spx/15-subagent-execution.pdr.md) verbatim within explicit authorization for every subagent supplied by their listed plugins; an active skill must explicitly instruct each launch, and availability, task wording, and role-description matching supply no launch instruction
- no-role-inventory: NEVER: a root guide contains a role inventory, per-role invocation table, task prompt, or per-role result-contract copy
- role-delegation: ALWAYS: root guides delegate role selection and target-only prompts to the calling skills while permitting minimal agent-specific mechanical guidance, including a call example for a demonstrated invocation problem; each generated guide addresses only its own agent; both guides require every audit and review to start without authoring history or author-written context packets and to discover evidence independently from the target and configured instructions, accepted requirements are persisted in decisions and specs before verification, and the native invocation guidance explicitly disables history inheritance when the tool otherwise enables it by default
- payload-rule: ALWAYS: generation emits and validates, in both generated root guides, the payload rule of [`spx/15-agent-tools.pdr.md`](spx/15-agent-tools.pdr.md): a payload reaches a command through a file the agent writes in the scratch directory its harness names for the session, under a file name unique to that agent, through the tool's own file argument or an input redirect from that file, and never through a heredoc, a pipe, or an inline form; a payload is any multi-line text or any text carrying a code span, a quote, a shell metacharacter, or JSON, while a path, a branch name, or an identifier is a command argument; the agent never removes its payload files
- guard-obeyed: ALWAYS: agents obey an emitted dangerous-command guard: a block on a command holding one operation with every string written literally ends that command family, a block on a command whose composition the parts cannot carry ends it too, a block on a compound command runs its parts again one at a time with every string written literally, in their original order, and a part the guard blocks on its own ends that part's family; no blocked command is reformulated, stripped of its flagged clause, or replaced by an equivalent command, and agents use only sanctioned alternatives or report the redacted command, purpose, and guard reason before stopping for operator direction
- wait-for-load-trigger: ALWAYS: generation emits a stop trigger that invokes `/wait-for-load` before every resource-intensive command — a test suite, an eval, a full gate, a compiling build, an install verification — and runs that command on one shell line as the argument vector of `spx orchestration lock --run-id <id> -- <command>`, so the command starts only when the host-wide slot admits it; lets a lightweight command — formatting, a single-file lint, a markdown or link validation, an instruction-block render, a status read — run without the guard; after a lock record lost from view recovers the existing invocation and its matching terminal record, starts no new invocation while that invocation's state is unresolved, and reports the outcome unknown when its terminal exit is known but the record is gone; and never uses host load to reduce scope, workers, limits, deadlines, or verification; both harness routers state the same line form, and the Codex router additionally keeps the line in one `functions.exec` call and reconciles every owned process handle to terminal exit or explicit interruption before another process sequence, operator question, merge or publication, or turn end rather than leaving a background terminal dangling
- codex-override-first: ALWAYS: the Codex router block begins with the operator-override rule as its first rendered body content, before the `Product Tree Instructions` heading, while the Claude router block omits that Codex-only rule
- no-file-removal: NEVER: either harness router permits an agent to run `rm`, `rm -f`, `rmdir`, `unlink`, or any other command that deletes a file, including a scratch file, a file under `$TMPDIR`, and the session scratchpad; each command is written without a cleanup step, while Git cleanup that a governing skill flow runs, a tracked file that a governing skill flow removes through Git, a file removal that a skill's bundled script performs, and a removal that a command the repository's own instructions declare performs stay outside the rule; a file a task needs gone, outside those removals, is moved to the user's trash through the trash command the host supplies, and where the host supplies none the session leaves the file in place and reports it to the operator, an instruction from the operator or the repository to keep a file or to report it without removing it takes precedence over the trash, and scratch files stay in place
- no-product-prose: NEVER: the router block carries product-specific prose — per-product commands live only as content the read-the-whole-file instruction reaches
