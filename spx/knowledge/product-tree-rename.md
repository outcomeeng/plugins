---
okf_version: "0.1"
---

# Product Tree rename tracker

The execution tracker of Change [outcomeeng/changes#767](https://github.com/outcomeeng/changes/issues/767): every edit the rename makes, as the tree stands at the base commit, so the Change record names the nodes and the mapping and this file carries the detail. Tick an item when the changeset carries it. This file declares no product, architecture, or methodology truth.

Base commit: `708f150169f21a58087e73e0f61382ea0b7e7dba`

## Spelling mapping

| Old         | New            | Where                                                                                              |
| ----------- | -------------- | -------------------------------------------------------------------------------------------------- |
| `Spec Tree` | `Product Tree` | prose, as a proper noun                                                                            |
| `spec tree` | `product tree` | prose, as a common noun                                                                            |
| `spec-tree` | `product-tree` | paths, identifiers, the plugin id, skill namespaces                                                |
| `SPEC_TREE` | `PRODUCT_TREE` | constants, markers                                                                                 |
| `SPEC-TREE` | `PRODUCT-TREE` | the instruction-block markers                                                                      |
| `SPECTREE`  | `PRODUCT_TREE` | the hook kill switch `SPECTREE_SESSION_HOOK_DISABLED` becomes `PRODUCT_TREE_SESSION_HOOK_DISABLED` |
| `spec_tree` | `product_tree` | Python modules and identifiers                                                                     |
| `SpecTree`  | `ProductTree`  | Python classes                                                                                     |

The literal `BEGIN MANAGED SPEC TREE INSTRUCTIONS` / `END MANAGED SPEC TREE INSTRUCTIONS` is the alternate marker pair the instruction-block updater recognizes in a consumer's older root file; it stays. Changelog history stays as written. The `@spec-tree` trigger phrase, the `SPEC_TREE_REVIEW_*` repository variables, and the caller workflows `.github/workflows/spec-tree.yml` and `.github/workflows/spec-tree-review.yml` belong to [outcomeeng/changes#770](https://github.com/outcomeeng/changes/issues/770).

## Directories and files renamed

- [x] `spx/21-spec-tree.enabler/` -> `spx/21-product-tree.enabler/` with `git mv`; the spec `spec-tree.md` -> `product-tree.md`; every descendant moves with it
- [x] `src/plugins/spec-tree/` -> `src/plugins/product-tree/`; `dist/claude/spec-tree/` and `dist/codex/spec-tree/` regenerate as `product-tree/` through `just build-skills`
- [x] `.github/workflows/spec-tree-evals.yml` -> `.github/workflows/product-tree-evals.yml`; `EVAL_TRIGGER_WORKFLOW` in `outcomeeng/validation/_steps.py` follows; `just build-eval-triggers` regenerates the trigger paths
- [x] `outcomeeng/spec_tree_structure.py` -> `outcomeeng/product_tree_structure.py`
- [x] `outcomeeng_testing/harnesses/spec_tree.py` -> `outcomeeng_testing/harnesses/product_tree.py`
- [x] `src/plugins/spec-tree/.claude-plugin/plugin.json` and `.codex-plugin/plugin.json`: `name` becomes `product-tree`; the version advances one MINOR through `just bump` at merge time, never by hand
- [x] `.claude-plugin/marketplace.json`, `.agents/plugins/marketplace.json`: the plugin entry, its source path, and its description
- [x] `.claude/settings.json`, `.codex/config.toml`, `.pi/claude-plugins.json`: `spec-tree@outcomeeng` -> `product-tree@outcomeeng`
- [x] `spx/local/generated-sources.toml`: the marker strings and the `dist/*/spec-tree` relation paths
- [x] `justfile`, `renovate.json`, `.sonarcloud.properties`: the eval workflow path and plugin paths
- [x] `src/plugins/spec-tree/CHANGELOG.md` (moved) and `MARKETPLACE-CHANGELOG.md`: a Breaking entry naming the plugin id, the skill namespace, the markers, and the kill switch, with the old name mapped to the new one
- [x] `README.md` plugin catalog: `just docs` regenerates it
- [x] `CLAUDE.md` and `AGENTS.md` managed blocks: `just build-instructions` regenerates them after the template changes; `outcomeeng/distribution/instruction_block.py` pinned tuples follow the template wording in the same change

## Markers, hook, and consumer-facing tokens

- [x] `<SPEC_TREE_FOUNDATION>` -> `<PRODUCT_TREE_FOUNDATION>` and `<SPEC_TREE_CONTEXT target=...>` -> `<PRODUCT_TREE_CONTEXT target=...>`: emitted by `understand` and `contextualize`; read by every skill that requires them, including `audit-go-test`, `audit-python-test`, `audit-rust-test`, `audit-typescript-test`, `author-typescript-test`
- [x] `<!-- SPEC-TREE v... langs:... -->`, `<!-- /SPEC-TREE -->`, `<!-- SPEC-TREE:shared ... -->` -> `PRODUCT-TREE`; the updater in `src/plugins/spec-tree/skills/update-instruction-block/scripts/instruction_block.py` reads the old marker as stale and replaces it in place once
- [x] `SPECTREE_SESSION_HOOK_DISABLED` -> `PRODUCT_TREE_SESSION_HOOK_DISABLED` in `hooks/hooks.json`, the hook script, the hook-safety tests and fixtures
- [x] skill references `spec-tree:<skill>` -> `product-tree:<skill>` in every plugin's skills and agents, and in `spx/local/*.md`

## Python identifiers

| Identifier                                                                                     | Occurrences | Becomes                                                                                           |
| ---------------------------------------------------------------------------------------------- | ----------- | ------------------------------------------------------------------------------------------------- |
| `SPEC_TREE_PLUGIN`                                                                             | 106         | `PRODUCT_TREE_PLUGIN`                                                                             |
| `SPEC_TREE_PLUGIN_NAME`                                                                        | 31          | `PRODUCT_TREE_PLUGIN_NAME`                                                                        |
| `SPEC_TREE_ROOT_DIRECTORY`                                                                     | 17          | `PRODUCT_TREE_ROOT_DIRECTORY`                                                                     |
| `SPEC_TREE_DIRECTORY`                                                                          | 15          | `PRODUCT_TREE_DIRECTORY`                                                                          |
| `spec_tree`                                                                                    | 13          | `product_tree`                                                                                    |
| `marketplace_root_for_spec_tree_root_test`                                                     | 11          | `marketplace_root_for_product_tree_root_test`                                                     |
| `SPEC_TREE_ROOT`                                                                               | 10          | `PRODUCT_TREE_ROOT`                                                                               |
| `include_spec_tree`                                                                            | 10          | `include_product_tree`                                                                            |
| `OUTSIDE_SPEC_TREE_FIXTURE`                                                                    | 5           | `OUTSIDE_PRODUCT_TREE_FIXTURE`                                                                    |
| `spec_tree_wrapper_agents`                                                                     | 5           | `product_tree_wrapper_agents`                                                                     |
| `SPEC_TREE_DIR`                                                                                | 4           | `PRODUCT_TREE_DIR`                                                                                |
| `SPEC_TREE_ROOT_GLOB`                                                                          | 4           | `PRODUCT_TREE_ROOT_GLOB`                                                                          |
| `spec_tree_structure`                                                                          | 4           | `product_tree_structure`                                                                          |
| `audit_contract_rejects_language_wrapper_under_spec_tree`                                      | 3           | `audit_contract_rejects_language_wrapper_under_product_tree`                                      |
| `is_in_spec_tree`                                                                              | 3           | `is_in_product_tree`                                                                              |
| `SPEC_TREE_AGENT_SOURCE_DIR`                                                                   | 2           | `PRODUCT_TREE_AGENT_SOURCE_DIR`                                                                   |
| `SPEC_TREE_MANIFEST`                                                                           | 2           | `PRODUCT_TREE_MANIFEST`                                                                           |
| `spec_tree_plugin_version`                                                                     | 2           | `product_tree_plugin_version`                                                                     |
| `SPECTREE_SESSION_HOOK_DISABLED`                                                               | 1           | `PRODUCT_TREE_SESSION_HOOK_DISABLED`                                                              |
| `SPEC_TREE_FOUNDATION`                                                                         | 1           | `PRODUCT_TREE_FOUNDATION`                                                                         |
| `test_a_root_without_a_spec_tree_exits_with_the_error_status`                                  | 1           | `test_a_root_without_a_product_tree_exits_with_the_error_status`                                  |
| `test_an_empty_selection_supplies_only_spec_tree_with_a_warning_and_disabled_codex_activation` | 1           | `test_an_empty_selection_supplies_only_product_tree_with_a_warning_and_disabled_codex_activation` |
| `test_conversion_changes_only_markdown_files_beneath_the_spec_tree`                            | 1           | `test_conversion_changes_only_markdown_files_beneath_the_product_tree`                            |
| `test_conversion_refuses_an_explicit_path_outside_the_spec_tree`                               | 1           | `test_conversion_refuses_an_explicit_path_outside_the_product_tree`                               |
| `test_every_spec_tree_node_directory_has_its_slug_spec_file`                                   | 1           | `test_every_product_tree_node_directory_has_its_slug_spec_file`                                   |
| `test_first_persistent_run_installs_only_spec_tree_and_warns`                                  | 1           | `test_first_persistent_run_installs_only_product_tree_and_warns`                                  |
| `test_language_wrapper_under_spec_tree_is_rejected`                                            | 1           | `test_language_wrapper_under_product_tree_is_rejected`                                            |
| `test_spec_tree_enabler_directories_have_slug_spec_files`                                      | 1           | `test_product_tree_enabler_directories_have_slug_spec_files`                                      |
| `test_spec_tree_node_prefixes_are_valid_indices`                                               | 1           | `test_product_tree_node_prefixes_are_valid_indices`                                               |
| `test_spec_tree_wrapper_agents_use_explicit_models`                                            | 1           | `test_product_tree_wrapper_agents_use_explicit_models`                                            |

## Phrasing to review

Outcome Engineering is not spec-driven; the spec files are spec files, and that is the extent of the term. Each site below is read and rewritten where it claims otherwise.

- [x] `methodology/skills/skill-structure.md` line 192: #### 10. Implement work items using spec-driven verification
- [x] `spx/21-spec-tree.enabler/spec-tree.md` line 10: CAN operate within a structured, spec-first framework with deterministic context
- [x] `src/plugins/go/skills/author-go-code/SKILL.md` line 14: Go implementation code with spec-driven behavior, explicit seams, and full validation passing.
- [x] `src/plugins/rust/skills/author-rust-code/SKILL.md` line 14: Rust implementation code with spec-driven behavior, explicit seams, and full validation passing.
- [x] `src/plugins/spec-tree/.claude-plugin/plugin.json` line 19: "spec-as-source"
- [x] `src/plugins/spec-tree/.codex-plugin/plugin.json` line 21: "spec-as-source"

## Decision records amended

Each line below is a line of the record that carries the term, as old -> new. The Change's Governance mutations state the resulting decisions by slug.

### [`spx/12-marketplace-state.adr.md`](spx/12-marketplace-state.adr.md)

- [x] line 5

  ```text
  old: Persistent selection is bounded and ordered by each agent's committed marketplace catalog, and the marketplace's name is the one those catalogs declare. Claude Code supplies its installed inventory for that marketplace at project or local scope in the invocation checkout for bootstrap, and every project- or local-scope install record it reports on the machine for a cataloged plugin for refresh. The invocation checkout's own records move through the native plugin update. Every other project- or local-scope record of a cataloged plugin is brought to the target by rewriting its entry in the agent's install-record file to the target install path, version, and commit, so every Claude Code session on the machine starts and reloads at the head of the registered source's default branch. A record whose plugin the catalog does not carry, or whose scope is neither project nor local, is left unchanged and reported. No agent command runs with any checkout other than the invocation checkout as its working directory; the one exception is the uncached-target fetch, whose working directory is a project the run creates for that fetch, which is no checkout. Codex selection comes from the plugin keys declared in the selected home's configuration, including disabled entries and entries whose caches are absent; merged product overrides and cache presence do not choose that home-wide set. Every nonempty selection contains `spec-tree`. An empty selection supplies only `spec-tree` and a warning to choose additional plugins; an empty Codex home receives it disabled. Claude Code bootstrap preserves any declared project activation and defaults an undeclared bootstrap plugin to disabled. The supply and its warning are one act: an empty inventory proposes the bootstrap, and the plan the run carries decides it, so an agent whose bootstrap a later condition withholds installs nothing, warns of no first install, and is reported as installing nothing.
  new: Persistent selection is bounded and ordered by each agent's committed marketplace catalog, and the marketplace's name is the one those catalogs declare. Claude Code supplies its installed inventory for that marketplace at project or local scope in the invocation checkout for bootstrap, and every project- or local-scope install record it reports on the machine for a cataloged plugin for refresh. The invocation checkout's own records move through the native plugin update. Every other project- or local-scope record of a cataloged plugin is brought to the target by rewriting its entry in the agent's install-record file to the target install path, version, and commit, so every Claude Code session on the machine starts and reloads at the head of the registered source's default branch. A record whose plugin the catalog does not carry, or whose scope is neither project nor local, is left unchanged and reported. No agent command runs with any checkout other than the invocation checkout as its working directory; the one exception is the uncached-target fetch, whose working directory is a project the run creates for that fetch, which is no checkout. Codex selection comes from the plugin keys declared in the selected home's configuration, including disabled entries and entries whose caches are absent; merged product overrides and cache presence do not choose that home-wide set. Every nonempty selection contains `product-tree`. An empty selection supplies only `product-tree` and a warning to choose additional plugins; an empty Codex home receives it disabled. Claude Code bootstrap preserves any declared project activation and defaults an undeclared bootstrap plugin to disabled. The supply and its warning are one act: an empty inventory proposes the bootstrap, and the plan the run carries decides it, so an agent whose bootstrap a later condition withholds installs nothing, warns of no first install, and is reported as installing nothing.
  ```

- [x] line 15

  ```text
  old: Plugin availability lets several products share one installed cache while choosing their own skill context. Disabled home defaults make product activation explicit; preserving an existing enabled home entry respects the operator's choice. `spec-tree` is the minimum coherent selection because it supplies the marketplace's governing methodology. Selection declarations survive an interrupted installation or a missing cache, so Codex refresh reads them independently of installed-file discovery. Native update operations preserve activation without a compensating write that could erase failure evidence.
  new: Plugin availability lets several products share one installed cache while choosing their own skill context. Disabled home defaults make product activation explicit; preserving an existing enabled home entry respects the operator's choice. `product-tree` is the minimum coherent selection because it supplies the marketplace's governing methodology. Selection declarations survive an interrupted installation or a missing cache, so Codex refresh reads them independently of installed-file discovery. Native update operations preserve activation without a compensating write that could erase failure evidence.
  ```

- [x] line 30

  ```text
  old: - A persistent plan refreshes only the agent's pre-run selected catalog plugins, except that empty state selects only `spec-tree` and carries a warning.
  new: - A persistent plan refreshes only the agent's pre-run selected catalog plugins, except that empty state selects only `product-tree` and carries a warning.
  ```

- [x] line 31

  ```text
  old: - A nonempty persistent selection contains `spec-tree` or the run stops before its first state-changing command.
  new: - A nonempty persistent selection contains `product-tree` or the run stops before its first state-changing command.
  ```

- [x] line 54

  ```text
  old: - ALWAYS: empty persistent selection supplies only `spec-tree` with a warning, disabled where no activation is declared; an empty Codex home declares `spec-tree` disabled. An agent whose bootstrap the run withholds supplies nothing, raises no first-install warning, and is reported as installing nothing.
  new: - ALWAYS: empty persistent selection supplies only `product-tree` with a warning, disabled where no activation is declared; an empty Codex home declares `product-tree` disabled. An agent whose bootstrap the run withholds supplies nothing, raises no first-install warning, and is reported as installing nothing.
  ```

- [x] line 71

  ```text
  old: - NEVER: a nonempty persistent agent selection omitting `spec-tree` reaches a state-changing command ([compliance])
  new: - NEVER: a nonempty persistent agent selection omitting `product-tree` reaches a state-changing command ([compliance])
  ```

- [x] line 79

  ```text
  old: - ALWAYS: isolated installation verifies every catalog plugin, a generated valid subset containing `spec-tree`, and a generated invalid subset omitting `spec-tree` in disposable homes without mutating persistent state ([compliance])
  new: - ALWAYS: isolated installation verifies every catalog plugin, a generated valid subset containing `product-tree`, and a generated invalid subset omitting `product-tree` in disposable homes without mutating persistent state ([compliance])
  ```

### [`spx/12-shipped-scripting.adr.md`](spx/12-shipped-scripting.adr.md)

- [x] line 3

  ```text
  old: Scripting functionality shipped in a plugin — skill scripts and hooks — is a standalone Python script that runs on the two most recent Python feature releases. The older of the two is the floor, and the linter and type-checker that govern shipped scripts are pinned to that floor so a script never uses a feature the floor lacks. Shipped scripts assume a managed interpreter (Homebrew or equivalent), never the system macOS Python, which trails the language by years. A generic shipped script beyond fifty lines carries debt: once it proves its value its logic moves into the agent-neutral SPX CLI, and a script that never proves its value is removed rather than extracted. Agent-specific adapter logic remains plugin-local only when moving it into SPX would couple SPX to one coding agent and the adapter is deterministic, bounded, standard-library-only, and independently tested. A value the spec tree declares and a source complies with is verified by audit, because every oracle for that agreement is a second declaration. This complements the packaging and execution rules in [`spx/13-plugin-and-runtime-conventions.adr.md`](spx/13-plugin-and-runtime-conventions.adr.md).
  new: Scripting functionality shipped in a plugin — skill scripts and hooks — is a standalone Python script that runs on the two most recent Python feature releases. The older of the two is the floor, and the linter and type-checker that govern shipped scripts are pinned to that floor so a script never uses a feature the floor lacks. Shipped scripts assume a managed interpreter (Homebrew or equivalent), never the system macOS Python, which trails the language by years. A generic shipped script beyond fifty lines carries debt: once it proves its value its logic moves into the agent-neutral SPX CLI, and a script that never proves its value is removed rather than extracted. Agent-specific adapter logic remains plugin-local only when moving it into SPX would couple SPX to one coding agent and the adapter is deterministic, bounded, standard-library-only, and independently tested. A value the product tree declares and a source complies with is verified by audit, because every oracle for that agreement is a second declaration. This complements the packaging and execution rules in [`spx/13-plugin-and-runtime-conventions.adr.md`](spx/13-plugin-and-runtime-conventions.adr.md).
  ```

- [x] line 11

  ```text
  old: A value the spec tree declares and a source complies with admits no test of their agreement. Any oracle for it is a third statement of the value — after the spec tree's declaration and the source's compliance — and the second of those three to declare rather than comply: read from the source under test it compares that source to itself and holds for whatever the source contains, and transcribed into a test or a harness it creates a declaration in an artifact with no authority to make one. Behavior that depends on such a value is tested by importing the value from its complying source and exercising what it changes; the agreement between the declaration and that source is audit evidence. A value with no behavior to exercise — a process exit code, a protocol token — therefore reaches only audit.
  new: A value the product tree declares and a source complies with admits no test of their agreement. Any oracle for it is a third statement of the value — after the product tree's declaration and the source's compliance — and the second of those three to declare rather than comply: read from the source under test it compares that source to itself and holds for whatever the source contains, and transcribed into a test or a harness it creates a declaration in an artifact with no authority to make one. Behavior that depends on such a value is tested by importing the value from its complying source and exercising what it changes; the agreement between the declaration and that source is audit evidence. A value with no behavior to exercise — a process exit code, a protocol token — therefore reaches only audit.
  ```

- [x] line 28

  ```text
  old: - ALWAYS: a test that depends on a value the spec tree declares imports that value from the source complying with the declaration, and exercises the behavior the value governs ([audit])
  new: - ALWAYS: a test that depends on a value the product tree declares imports that value from the source complying with the declaration, and exercises the behavior the value governs ([audit])
  ```

### [`spx/14-skill-naming.pdr.md`](spx/14-skill-naming.pdr.md)

- [x] line 27

  ```text
  old: - ALWAYS: a skill that acts on a changeset or across the spec tree, such as `commit-changes`, `review-changes`, `audit-tests`, `audit-specs`, or `test`, and a standards skill that governs a class of artifacts, such as `agent-prompt-standards`, take their names under the rules for a workflow skill outside the `{role}-{type}` form and for a reference skill outside the `{type}-standards` form ([audit])
  new: - ALWAYS: a skill that acts on a changeset or across the product tree, such as `commit-changes`, `review-changes`, `audit-tests`, `audit-specs`, or `test`, and a standards skill that governs a class of artifacts, such as `agent-prompt-standards`, take their names under the rules for a workflow skill outside the `{role}-{type}` form and for a reference skill outside the `{type}-standards` form ([audit])
  ```

### [`spx/15-spec-coverage.adr.md`](spx/15-spec-coverage.adr.md)

- [x] line 3

  ```text
  old: Every checked-in marketplace plugin has at least one enabler node in the spec tree. Plugins with implementation code carry `[test]` evidence on assertions about executable behavior. Plugins whose deliverable is LLM-driven behavior — audit skills, classifiers, content producers — carry `[eval]` evidence scored against curated cases through the eval harness governed by `spx/13-infrastructure.enabler/25-eval-harness.enabler/eval-harness.md`. Assertions whose subject is the design or intent of a skill rather than its runtime behavior carry `[audit]` evidence.
  new: Every checked-in marketplace plugin has at least one enabler node in the product tree. Plugins with implementation code carry `[test]` evidence on assertions about executable behavior. Plugins whose deliverable is LLM-driven behavior — audit skills, classifiers, content producers — carry `[eval]` evidence scored against curated cases through the eval harness governed by `spx/13-infrastructure.enabler/25-eval-harness.enabler/eval-harness.md`. Assertions whose subject is the design or intent of a skill rather than its runtime behavior carry `[audit]` evidence.
  ```

- [x] line 7

  ```text
  old: The spec tree's value derives from the truth hierarchy — specs declare, evidence verifies, code complies — and three evidence mechanisms cover the three subject categories: `[test]` for deterministic code paths verified by a test runner; `[eval]` for LLM-driven behavior that emits a structurally validatable verdict, where the per-eval verdict schema makes the grader deterministic and the case set bounds the claim; `[audit]` for semantic constraints about design or intent that no structural grader can falsify. Tautological tests over markdown structure prove formatting, not behavior, so they are excluded — eval evidence avoids that failure mode because the case set drives the skill end-to-end and the grader inspects the verdict the skill produces. Excluding LLM-driven plugins from `[test]`-class evidence entirely would conflate two failure modes — prose-interpreting tests, which are genuinely brittle, and structural-verdict evals over curated cases, which are deterministic at the grader and bounded at the runner.
  new: The product tree's value derives from the truth hierarchy — specs declare, evidence verifies, code complies — and three evidence mechanisms cover the three subject categories: `[test]` for deterministic code paths verified by a test runner; `[eval]` for LLM-driven behavior that emits a structurally validatable verdict, where the per-eval verdict schema makes the grader deterministic and the case set bounds the claim; `[audit]` for semantic constraints about design or intent that no structural grader can falsify. Tautological tests over markdown structure prove formatting, not behavior, so they are excluded — eval evidence avoids that failure mode because the case set drives the skill end-to-end and the grader inspects the verdict the skill produces. Excluding LLM-driven plugins from `[test]`-class evidence entirely would conflate two failure modes — prose-interpreting tests, which are genuinely brittle, and structural-verdict evals over curated cases, which are deterministic at the grader and bounded at the runner.
  ```

### [`spx/15-test-language.adr.md`](spx/15-test-language.adr.md)

- [x] line 3

  ```text
  old: Python (pytest) is the language and runner for all `[test]` evidence in the spec tree. Test files follow `test_{subject}.{evidence}.{level}[.{runner}].py` and live under each node's `tests/` directory. The `[test]` lane is one of the evidence-execution lanes declared in [`spx/31-outcomeeng.enabler/31-verification.enabler/14-verification.pdr.md`](spx/31-outcomeeng.enabler/31-verification.enabler/14-verification.pdr.md); this decision selects its language and runner. `[eval]` evidence lives in a separate lane this decision does not govern.
  new: Python (pytest) is the language and runner for all `[test]` evidence in the product tree. Test files follow `test_{subject}.{evidence}.{level}[.{runner}].py` and live under each node's `tests/` directory. The `[test]` lane is one of the evidence-execution lanes declared in [`spx/31-outcomeeng.enabler/31-verification.enabler/14-verification.pdr.md`](spx/31-outcomeeng.enabler/31-verification.enabler/14-verification.pdr.md); this decision selects its language and runner. `[eval]` evidence lives in a separate lane this decision does not govern.
  ```

- [x] line 7

  ```text
  old: Two categories of artifact produce `[test]` evidence: infrastructure scripts (validation, distribution, xml-spacing, eval-harness internals), which are Python tested with pytest; and skill behavior verified through observable side effects — file outputs, structured verdicts, link-integrity checks — where pytest verifies the harness contract and the lane stays deterministic because the grader is code, not an LLM. LLM-driven skill behavior, where the assertion is about what the model concludes rather than what observable artifact it produces, belongs in the `[eval]` lane. Implementation code in the marketplace is Python, the marketplace ships a single quality gate, and orphaned test files that no runner collects create phantom evidence — a single language and runner makes collection deterministic. Spec-tree node directories are kebab-case while Python modules require snake_case imports, so one file-naming rule reconciles both. A single runner spanning all evidence mechanisms collapses cost profiles into one gate; shell runners lose import-mode discovery and parametrization; per-node runner configuration drifts when a node moves.
  new: Two categories of artifact produce `[test]` evidence: infrastructure scripts (validation, distribution, xml-spacing, eval-harness internals), which are Python tested with pytest; and skill behavior verified through observable side effects — file outputs, structured verdicts, link-integrity checks — where pytest verifies the harness contract and the lane stays deterministic because the grader is code, not an LLM. LLM-driven skill behavior, where the assertion is about what the model concludes rather than what observable artifact it produces, belongs in the `[eval]` lane. Implementation code in the marketplace is Python, the marketplace ships a single quality gate, and orphaned test files that no runner collects create phantom evidence — a single language and runner makes collection deterministic. Product tree node directories are kebab-case while Python modules require snake_case imports, so one file-naming rule reconciles both. A single runner spanning all evidence mechanisms collapses cost profiles into one gate; shell runners lose import-mode discovery and parametrization; per-node runner configuration drifts when a node moves.
  ```

- [x] line 13

  ```text
  old: - ALWAYS: use Python (pytest) for all `[test]` evidence in the spec tree — the quality gate runs a single runner for this lane ([audit])
  new: - ALWAYS: use Python (pytest) for all `[test]` evidence in the product tree — the quality gate runs a single runner for this lane ([audit])
  ```

- [x] line 16

  ```text
  old: - NEVER: use a non-pytest runner for `[test]` evidence in the spec tree — the lane is single-runner by decision ([audit])
  new: - NEVER: use a non-pytest runner for `[test]` evidence in the product tree — the lane is single-runner by decision ([audit])
  ```

### [`spx/16-interfaces.enabler/21-browser.enabler/13-rendering.adr.md`](spx/16-interfaces.enabler/21-browser.enabler/13-rendering.adr.md)

- [x] line 3

  ```text
  old: The browser interface renders from the SPX CLI's JSON projection of the spec tree, applies the product's own vendored design system, and produces interactive HTML — drag-drop restructuring, inline commenting, expand/collapse — rather than static read-only output.
  new: The browser interface renders from the SPX CLI's JSON projection of the product tree, applies the product's own vendored design system, and produces interactive HTML — drag-drop restructuring, inline commenting, expand/collapse — rather than static read-only output.
  ```

- [x] line 7

  ```text
  old: The spec-tree projection — structure, derived state, and the node and decision categories — is available from the SPX CLI as JSON, so the interface reads it rather than re-deriving it. Re-parsing directory suffixes or deriving state in the interface would duplicate the methodology's own engine and drift from it.
  new: The product-tree projection — structure, derived state, and the node and decision categories — is available from the SPX CLI as JSON, so the interface reads it rather than re-deriving it. Re-parsing directory suffixes or deriving state in the interface would duplicate the methodology's own engine and drift from it.
  ```

### [`spx/16-interfaces.enabler/21-browser.enabler/15-transport.adr.md`](spx/16-interfaces.enabler/21-browser.enabler/15-transport.adr.md)

- [x] line 9

  ```text
  old: The decision binds the launch layer only. The transport-free state core — the monotonic revision counter, the append-only journal, the interaction lifecycle, and spec-tree integrity — and the browser shell are transport-agnostic, so the same core serves any launch model. Isolating transport in a replaceable launch layer is what lets the core be proven independently of the launch model.
  new: The decision binds the launch layer only. The transport-free state core — the monotonic revision counter, the append-only journal, the interaction lifecycle, and product-tree integrity — and the browser shell are transport-agnostic, so the same core serves any launch model. Isolating transport in a replaceable launch layer is what lets the core be proven independently of the launch model.
  ```

### [`spx/18-plugin-build.enabler/15-build-architecture.adr.md`](spx/18-plugin-build.enabler/15-build-architecture.adr.md)

- [x] line 30

  ```text
  old: owner's agent tokens into a data file beside each spec-tree script that reads
  new: owner's agent tokens into a data file beside each product-tree script that reads
  ```

- [x] line 31

  ```text
  old: them, because a shipped spec-tree script imports nothing from another plugin's
  new: them, because a shipped product-tree script imports nothing from another plugin's
  ```

- [x] line 57

  ```text
  old: not already have. A spec-tree script cannot import that module, because a
  new: not already have. A product-tree script cannot import that module, because a
  ```

- [x] line 74

  ```text
  old: - ALWAYS: the build derives its targets from the coding-agents agent-token module and renders its tokens beside each spec-tree script that reads them; no toolchain module and no authored spec-tree script declares an agent token ([audit])
  new: - ALWAYS: the build derives its targets from the coding-agents agent-token module and renders its tokens beside each product-tree script that reads them; no toolchain module and no authored product-tree script declares an agent token ([audit])
  ```

### [`spx/21-spec-tree.enabler/11-repository-layout.pdr.md`](spx/21-product-tree.enabler/11-repository-layout.pdr.md), moving with its node under `spx/21-product-tree.enabler/`

- [x] line 3

  ```text
  old: A product checkout governed by the Spec Tree methodology conforms to one of two git layouts: a single working tree, or a bare-repository worktree pool. The pool is a bare `{repo}.git` repository whose git-common-dir has, as siblings, a **main checkout** and the shared `.spx/` operational directory. Provisioning places the pool under one repository-name container directory, so a product's bare repo, main checkout, and `.spx/` nest as `<repo>/<repo>.git`, `<repo>/<repo>`, and `<repo>/.spx` — the container provisioning targets is the repository-name directory, never the multi-repository workspace that holds it. This is a provisioning invariant, enforced when the pool is built; classification reads the common dir's bareness, the repository-name sibling main checkout, and the `.spx/` placement, not the container directory's own name. The main checkout is the working tree whose directory basename equals the `origin` remote's repository name (`<pool>/<repo-name>`, e.g. `spx/spx`), placed beside the git-common-dir, with `git config --get core.bare` on the common dir selecting the pool layout — the main checkout is designated by the repository name and its sibling placement, independent of the checked-out or default branch. Provisioning sets the main checkout to track the git-resolved default branch `origin/<default>`, never a literal `origin/main`; classifying an existing pool reads the repository name, sibling placement, and bareness only, and does not re-verify the tracking ref. Additional pool worktrees are created detached at the `origin/<default>` tip and default to siblings of the git-common-dir, though their location is otherwise free. A pool whose git-common-dir has no sibling worktree named for the repository has no main checkout — the expected path stays derivable from the repository name for diagnostics and never falls back to a branch-named directory. A checkout that attaches linked worktrees to a non-bare repository, or a pool that lacks the bare root, the repository-name main checkout sibling, or `.spx/` beside the git-common-dir, is non-compliant.
  new: A product checkout governed by the Product Tree methodology conforms to one of two git layouts: a single working tree, or a bare-repository worktree pool. The pool is a bare `{repo}.git` repository whose git-common-dir has, as siblings, a **main checkout** and the shared `.spx/` operational directory. Provisioning places the pool under one repository-name container directory, so a product's bare repo, main checkout, and `.spx/` nest as `<repo>/<repo>.git`, `<repo>/<repo>`, and `<repo>/.spx` — the container provisioning targets is the repository-name directory, never the multi-repository workspace that holds it. This is a provisioning invariant, enforced when the pool is built; classification reads the common dir's bareness, the repository-name sibling main checkout, and the `.spx/` placement, not the container directory's own name. The main checkout is the working tree whose directory basename equals the `origin` remote's repository name (`<pool>/<repo-name>`, e.g. `spx/spx`), placed beside the git-common-dir, with `git config --get core.bare` on the common dir selecting the pool layout — the main checkout is designated by the repository name and its sibling placement, independent of the checked-out or default branch. Provisioning sets the main checkout to track the git-resolved default branch `origin/<default>`, never a literal `origin/main`; classifying an existing pool reads the repository name, sibling placement, and bareness only, and does not re-verify the tracking ref. Additional pool worktrees are created detached at the `origin/<default>` tip and default to siblings of the git-common-dir, though their location is otherwise free. A pool whose git-common-dir has no sibling worktree named for the repository has no main checkout — the expected path stays derivable from the repository name for diagnostics and never falls back to a branch-named directory. A checkout that attaches linked worktrees to a non-bare repository, or a pool that lacks the bare root, the repository-name main checkout sibling, or `.spx/` beside the git-common-dir, is non-compliant.
  ```

### [`spx/21-spec-tree.enabler/14-version-control.enabler/15-changeset-scope.enabler/13-changeset-derivation.adr.md`](spx/21-product-tree.enabler/14-version-control.enabler/15-changeset-scope.enabler/13-changeset-derivation.adr.md), moving with its node under `spx/21-product-tree.enabler/`

- [x] line 3

  ```text
  old: The git-derived changeset primitives — `branch_slug`, `detect_current_branch`, `detect_base_ref`, `commit_oid`, `branch_scope`, `expand_diff_range`, `remote_tracking_ref` — are defined once in `plugins/spec-tree/skills/scope-changeset/scripts/changeset_scope.py` and reached by implementation-audit orchestration, review-changes, and sync-base through import, never re-definition. Every changeset diff range over a git-derived base is composed against the remote-tracking ref `origin/<base>` (three-dot, merge-base) through the single `remote_tracking_ref` helper, never a bare local branch ref — `branch_scope` composes it for the audit surface and `compute_diff` for the review surface. Journal run-state identity uses `commit_oid` to stamp concrete head/base commit IDs rather than symbolic refs — the base identity is the fetched `origin/<base>` tip, never the merge-base commit. A committed selector whose base is git-derived or a remote-tracking ref resolves only against that fetched tip: the resolver fetches the base's remote-tracking ref and refuses a head whose merge base with the tip is not the tip itself, reporting the tip, the merge base, and the base commits the head lacks through a dedicated exit code and a diagnostic in place of a scope. An explicit range whose base names a local ref or a commit is the caller's exact endpoint pair and is compared as given, with no fetch and no refusal. That refusal is every verifier's first step for a git-derived or remote-tracking base: a verification skill that resolves a committed scope returns it as a `stale-base` block before it opens a run or reads a subject. Base synchronization is the remedy and resolves through the primitives without the refusal; the merge transport's classification partitions paths rather than verifying them and resolves the same way.
  new: The git-derived changeset primitives — `branch_slug`, `detect_current_branch`, `detect_base_ref`, `commit_oid`, `branch_scope`, `expand_diff_range`, `remote_tracking_ref` — are defined once in `plugins/product-tree/skills/scope-changeset/scripts/changeset_scope.py` and reached by implementation-audit orchestration, review-changes, and sync-base through import, never re-definition. Every changeset diff range over a git-derived base is composed against the remote-tracking ref `origin/<base>` (three-dot, merge-base) through the single `remote_tracking_ref` helper, never a bare local branch ref — `branch_scope` composes it for the audit surface and `compute_diff` for the review surface. Journal run-state identity uses `commit_oid` to stamp concrete head/base commit IDs rather than symbolic refs — the base identity is the fetched `origin/<base>` tip, never the merge-base commit. A committed selector whose base is git-derived or a remote-tracking ref resolves only against that fetched tip: the resolver fetches the base's remote-tracking ref and refuses a head whose merge base with the tip is not the tip itself, reporting the tip, the merge base, and the base commits the head lacks through a dedicated exit code and a diagnostic in place of a scope. An explicit range whose base names a local ref or a commit is the caller's exact endpoint pair and is compared as given, with no fetch and no refusal. That refusal is every verifier's first step for a git-derived or remote-tracking base: a verification skill that resolves a committed scope returns it as a `stale-base` block before it opens a run or reads a subject. Base synchronization is the remedy and resolves through the primitives without the refusal; the merge transport's classification partitions paths rather than verifying them and resolves the same way.
  ```

### [`spx/21-spec-tree.enabler/14-version-control.enabler/32-sync-base.enabler/13-base-sync-mechanism.adr.md`](spx/21-product-tree.enabler/14-version-control.enabler/32-sync-base.enabler/13-base-sync-mechanism.adr.md), moving with its node under `spx/21-product-tree.enabler/`

- [x] line 21

  ```text
  old: `git reset` moves the branch pointer without replaying its own commits. `--hard` also replaces the index and tracked working tree, discarding pending tracked work; `--soft` preserves the old index and working tree against the new HEAD, allowing a later commit to reverse changes from the advanced base. Rebase replays the branch's own commits onto the advanced base, preserving the branch's work while absorbing the base's movement. Composing the rebase target against the fetched `origin/<base>` through the shared `remote_tracking_ref` primitive fixes the target independent of a stale local ref, per [`spx/21-spec-tree.enabler/14-version-control.enabler/15-changeset-scope.enabler/13-changeset-derivation.adr.md`](spx/21-spec-tree.enabler/14-version-control.enabler/15-changeset-scope.enabler/13-changeset-derivation.adr.md).
  new: `git reset` moves the branch pointer without replaying its own commits. `--hard` also replaces the index and tracked working tree, discarding pending tracked work; `--soft` preserves the old index and working tree against the new HEAD, allowing a later commit to reverse changes from the advanced base. Rebase replays the branch's own commits onto the advanced base, preserving the branch's work while absorbing the base's movement. Composing the rebase target against the fetched `origin/<base>` through the shared `remote_tracking_ref` primitive fixes the target independent of a stale local ref, per [`spx/21-product-tree.enabler/14-version-control.enabler/15-changeset-scope.enabler/13-changeset-derivation.adr.md`](spx/21-product-tree.enabler/14-version-control.enabler/15-changeset-scope.enabler/13-changeset-derivation.adr.md).
  ```

- [x] line 42

  ```text
  old: - ALWAYS: base synchronization derives the base ref and its remote-tracking form through the shared changeset-scope primitives, never re-deriving them, per [`spx/21-spec-tree.enabler/14-version-control.enabler/15-changeset-scope.enabler/13-changeset-derivation.adr.md`](spx/21-spec-tree.enabler/14-version-control.enabler/15-changeset-scope.enabler/13-changeset-derivation.adr.md) ([compliance])
  new: - ALWAYS: base synchronization derives the base ref and its remote-tracking form through the shared changeset-scope primitives, never re-deriving them, per [`spx/21-product-tree.enabler/14-version-control.enabler/15-changeset-scope.enabler/13-changeset-derivation.adr.md`](spx/21-product-tree.enabler/14-version-control.enabler/15-changeset-scope.enabler/13-changeset-derivation.adr.md) ([compliance])
  ```

### [`spx/21-spec-tree.enabler/15-hook-state-delegation.adr.md`](spx/21-product-tree.enabler/15-hook-state-delegation.adr.md), moving with its node under `spx/21-product-tree.enabler/`

- [x] line 3

  ```text
  old: The spec-tree plugin ships exactly one runtime hook: a `SessionStart` hook that delegates to the `spx` CLI hook runner — `spx hook run <hook-name-kebab-case>`, here `spx hook run session-start` — through a hook-safety-compliant inline guard. The `spx` CLI, not a plugin-shipped script, performs the hook's effects: it writes the agent session identity and project directories into the harness-provided `$CLAUDE_ENV_FILE` and records the worktree-occupancy claim under the project's `.spx/`. The hook command embeds no `.spx/`, git, transcript, or session logic of its own; on the disabled-or-absent path the inline guard exits with a valid empty result and writes nothing — the Hook Safety Contract's degrade-to-no-op path. The hook exists because `SessionStart` is the only lifecycle point at which the harness supplies `$CLAUDE_ENV_FILE` and sources it into every later Bash tool call of the session; the `spx` CLI cannot reach that lifecycle on its own. Delegation hands the lifecycle to `spx hook run session-start`, so the CLI that owns the `.spx/` model performs the session-environment work rather than a plugin script reimplementing it.
  new: The product-tree plugin ships exactly one runtime hook: a `SessionStart` hook that delegates to the `spx` CLI hook runner — `spx hook run <hook-name-kebab-case>`, here `spx hook run session-start` — through a hook-safety-compliant inline guard. The `spx` CLI, not a plugin-shipped script, performs the hook's effects: it writes the agent session identity and project directories into the harness-provided `$CLAUDE_ENV_FILE` and records the worktree-occupancy claim under the project's `.spx/`. The hook command embeds no `.spx/`, git, transcript, or session logic of its own; on the disabled-or-absent path the inline guard exits with a valid empty result and writes nothing — the Hook Safety Contract's degrade-to-no-op path. The hook exists because `SessionStart` is the only lifecycle point at which the harness supplies `$CLAUDE_ENV_FILE` and sources it into every later Bash tool call of the session; the `spx` CLI cannot reach that lifecycle on its own. Delegation hands the lifecycle to `spx hook run session-start`, so the CLI that owns the `.spx/` model performs the session-environment work rather than a plugin script reimplementing it.
  ```

- [x] line 7

  ```text
  old: A plugin-shipped hook script is the wrong place to reimplement `.spx/` state, git inspection, or session and worktree logic. It would run stdlib-only and portable, duplicating the multi-worktree `.spx/` model the `spx` CLI owns and tests against a harness the script cannot reach, and drifting from that model over time. Concentrating every `.spx/` operation in one owner — the `spx` CLI — keeps a single implementation of the on-disk model whether a skill invokes it or the `SessionStart` hook does. `spx` resolves on `PATH` and spec-tree is non-functional without it, so delegating to it from the hook introduces no failure mode the methodology does not already carry; the hook-safety inline guard degrades to a no-op when `spx` is absent, so a missing CLI never traps the session.
  new: A plugin-shipped hook script is the wrong place to reimplement `.spx/` state, git inspection, or session and worktree logic. It would run stdlib-only and portable, duplicating the multi-worktree `.spx/` model the `spx` CLI owns and tests against a harness the script cannot reach, and drifting from that model over time. Concentrating every `.spx/` operation in one owner — the `spx` CLI — keeps a single implementation of the on-disk model whether a skill invokes it or the `SessionStart` hook does. `spx` resolves on `PATH` and product-tree is non-functional without it, so delegating to it from the hook introduces no failure mode the methodology does not already carry; the hook-safety inline guard degrades to a no-op when `spx` is absent, so a missing CLI never traps the session.
  ```

- [x] line 11

  ```text
  old: - The spec-tree plugin ships exactly one runtime hook, on `SessionStart`.
  new: - The product-tree plugin ships exactly one runtime hook, on `SessionStart`.
  ```

- [x] line 20

  ```text
  old: - ALWAYS: the spec-tree plugin ships exactly one runtime hook — a `SessionStart` hook that delegates to `spx hook run session-start`, and which on the disabled-or-absent path exits with a valid empty result and writes nothing ([audit])
  new: - ALWAYS: the product-tree plugin ships exactly one runtime hook — a `SessionStart` hook that delegates to `spx hook run session-start`, and which on the disabled-or-absent path exits with a valid empty result and writes nothing ([audit])
  ```

### [`spx/21-spec-tree.enabler/16-compact-continuity.pdr.md`](spx/21-product-tree.enabler/16-compact-continuity.pdr.md), moving with its node under `spx/21-product-tree.enabler/`

- [x] line 13

  ```text
  old: 3. The `SessionStart` hook is limited to session-environment and worktree-occupancy behavior and carries no compact-summary or methodology-reload behavior; its delegation mechanism is governed by [`spx/21-spec-tree.enabler/15-hook-state-delegation.adr.md`](spx/21-spec-tree.enabler/15-hook-state-delegation.adr.md).
  new: 3. The `SessionStart` hook is limited to session-environment and worktree-occupancy behavior and carries no compact-summary or methodology-reload behavior; its delegation mechanism is governed by [`spx/21-product-tree.enabler/15-hook-state-delegation.adr.md`](spx/21-product-tree.enabler/15-hook-state-delegation.adr.md).
  ```

- [x] line 19

  ```text
  old: - ALWAYS: the managed root instruction block requires a live `<SPEC_TREE_FOUNDATION>` marker before anything under `spx/` or any other product content — source or test files, generated output, evals, spec-declared configuration — is read, searched, listed, or changed; states that a marker present only in a compaction summary, Handoff, or prior-run statement is not live; and names `spx session`, `spx worktree status`, `spx diagnose`, no-patch Git status, history, and topology, and a skill's read of the `spx/local/` overlay or exclusion mechanism it declares as exempt, while task reconstruction remains with the resuming agent and Claude Code's standard summary ([audit])
  new: - ALWAYS: the managed root instruction block requires a live `<PRODUCT_TREE_FOUNDATION>` marker before anything under `spx/` or any other product content — source or test files, generated output, evals, spec-declared configuration — is read, searched, listed, or changed; states that a marker present only in a compaction summary, Handoff, or prior-run statement is not live; and names `spx session`, `spx worktree status`, `spx diagnose`, no-patch Git status, history, and topology, and a skill's read of the `spx/local/` overlay or exclusion mechanism it declares as exempt, while task reconstruction remains with the resuming agent and Claude Code's standard summary ([audit])
  ```

- [x] line 23

  ```text
  old: - NEVER: the `SessionStart` hook carries compact-summary or methodology-reload behavior — it remains the delegated session-environment and worktree-occupancy hook defined by [`spx/21-spec-tree.enabler/15-hook-state-delegation.adr.md`](spx/21-spec-tree.enabler/15-hook-state-delegation.adr.md) ([audit])
  new: - NEVER: the `SessionStart` hook carries compact-summary or methodology-reload behavior — it remains the delegated session-environment and worktree-occupancy hook defined by [`spx/21-product-tree.enabler/15-hook-state-delegation.adr.md`](spx/21-product-tree.enabler/15-hook-state-delegation.adr.md) ([audit])
  ```

- [x] line 25

  ```text
  old: - NEVER: spec-tree replaces or augments Claude Code's compact-summary prompt through project configuration ([audit])
  new: - NEVER: product-tree replaces or augments Claude Code's compact-summary prompt through project configuration ([audit])
  ```

### [`spx/21-spec-tree.enabler/16-verification.enabler/13-run-journal.adr.md`](spx/21-product-tree.enabler/16-verification.enabler/13-run-journal.adr.md), moving with its node under `spx/21-product-tree.enabler/`

- [x] line 3

  ```text
  old: Every agentic verification run — review or audit per `src/plugins/spec-tree/skills/understand/SKILL.md` `<types>` — is one append-only event journal, and that journal is the run's sole source of truth. The run streams: it opens the journal at the start, then appends each domain event at the moment the run reaches it — a scope-entered event when the run begins, a scope-advanced event as each unit of its scope is examined (a changed file for review, a partition for audit), a finding-reported event the instant a finding is raised, and a run-completed event at the end — and seals. A reader resuming from a cursor — on a developer machine or a hosted pull request — watches the run advance in flight and reads each finding as it is raised, never an opaque wait for one result at the end, per [`spx/15-audit-result-delivery.pdr.md`](spx/15-audit-result-delivery.pdr.md). The run never computes a finished result and appends its events as a single batch at completion; it appends them live, as the work happens. It resumes reads from a cursor and never reads authoritative run state from a rendered surface. Every output surface — the markdown report, the pull-request comment, the findings JSON, the check summary — is a projection rendered from the journal's event history, never authoritative state. The skill addresses the journal through one backend-neutral channel and hard-codes no storage path, backend, or surface; the channel binds the backend at the edge — a local run-journal file on a developer machine, a hosted pull-request comment under CI — and is swappable without changing the skill. The contract is invariant across backends: appended events carry strictly increasing, contiguous sequence numbers; a correction is a later event referencing the original, never a mutation of a persisted event; a read resumes from any cursor; a terminal seal makes the sequence final, after which no append succeeds; and a projection is a pure function of an event prefix, identical on every backend. A scope-advanced event records that the run read its unit, so a run advances a unit only after reading it, and a run that leaves any unit of its scope unread seals `failed` and never `approved`; the terminal event names each unread unit. A run journal's branch identity names a branch and never a commit, so a run finds its journal by branch scope. The run is driven by a thin wrapper agent under `src/plugins/spec-tree/agents/` that holds no verification or I/O policy, declares an explicit non-inherited verification model and required skill set, and converts into each runtime's native model, sandbox, tool, and skill-enablement configuration.
  new: Every agentic verification run — review or audit per `src/plugins/product-tree/skills/understand/SKILL.md` `<types>` — is one append-only event journal, and that journal is the run's sole source of truth. The run streams: it opens the journal at the start, then appends each domain event at the moment the run reaches it — a scope-entered event when the run begins, a scope-advanced event as each unit of its scope is examined (a changed file for review, a partition for audit), a finding-reported event the instant a finding is raised, and a run-completed event at the end — and seals. A reader resuming from a cursor — on a developer machine or a hosted pull request — watches the run advance in flight and reads each finding as it is raised, never an opaque wait for one result at the end, per [`spx/15-audit-result-delivery.pdr.md`](spx/15-audit-result-delivery.pdr.md). The run never computes a finished result and appends its events as a single batch at completion; it appends them live, as the work happens. It resumes reads from a cursor and never reads authoritative run state from a rendered surface. Every output surface — the markdown report, the pull-request comment, the findings JSON, the check summary — is a projection rendered from the journal's event history, never authoritative state. The skill addresses the journal through one backend-neutral channel and hard-codes no storage path, backend, or surface; the channel binds the backend at the edge — a local run-journal file on a developer machine, a hosted pull-request comment under CI — and is swappable without changing the skill. The contract is invariant across backends: appended events carry strictly increasing, contiguous sequence numbers; a correction is a later event referencing the original, never a mutation of a persisted event; a read resumes from any cursor; a terminal seal makes the sequence final, after which no append succeeds; and a projection is a pure function of an event prefix, identical on every backend. A scope-advanced event records that the run read its unit, so a run advances a unit only after reading it, and a run that leaves any unit of its scope unread seals `failed` and never `approved`; the terminal event names each unread unit. A run journal's branch identity names a branch and never a commit, so a run finds its journal by branch scope. The run is driven by a thin wrapper agent under `src/plugins/product-tree/agents/` that holds no verification or I/O policy, declares an explicit non-inherited verification model and required skill set, and converts into each runtime's native model, sandbox, tool, and skill-enablement configuration.
  ```

- [x] line 17

  ```text
  old: - ALWAYS: a thin wrapper agent under `src/plugins/spec-tree/agents/` drives each agentic verification skill, holds no verification or I/O policy, and declares an explicit non-inherited verification model plus its required skill set; target conversion emits an explicit native model and enables every required skill in source order ([mapping])
  new: - ALWAYS: a thin wrapper agent under `src/plugins/product-tree/agents/` drives each agentic verification skill, holds no verification or I/O policy, and declares an explicit non-inherited verification model plus its required skill set; target conversion emits an explicit native model and enables every required skill in source order ([mapping])
  ```

- [x] line 29

  ```text
  old: - ALWAYS: an agentic verification run derives its changeset scope — branch, slug, base ref, changed-file set — through the shared changeset-scope primitives (`spx/21-spec-tree.enabler/14-version-control.enabler/15-changeset-scope.enabler/changeset-scope.md`) ([audit])
  new: - ALWAYS: an agentic verification run derives its changeset scope — branch, slug, base ref, changed-file set — through the shared changeset-scope primitives (`spx/21-product-tree.enabler/14-version-control.enabler/15-changeset-scope.enabler/changeset-scope.md`) ([audit])
  ```

### [`spx/21-spec-tree.enabler/17-audit.adr.md`](spx/21-product-tree.enabler/17-audit.adr.md), moving with its node under `spx/21-product-tree.enabler/`

- [x] line 3

  ```text
  old: The marketplace ships one implementation-audit wrapper surface in the spec-tree plugin: an `implementation-auditor` agent invoking skill-owned orchestration that resolves, for each changed path, the registered artifacts whose detection matches it and the audit skills they name, from the artifact registry the build renders beside its provider skill's reader, which the scope resolver imports; validates that each selected skill is installed; passes the supplied scope unchanged to each selected skill that follows the concern contract; aggregates their projections; and records one audit verification run. Each concern skill owns language-specific applicability and claims the subject paths it audits or returns not applicable; a resolved path no registered artifact matches, a matched path whose selected skill returns not applicable, and a path whose registered artifact's audit skill follows another contract remain outside implementation-audit coverage and stay with their artifact-type auditor and the whole-changeset review, while the run records each as an accounting record — an optional, skipped coverage-gap unit carrying no language partition and, for a path whose registered artifact's audit skill follows another contract, naming that skill — so a sealed run's recorded path subjects equal the changed-path inventory its own start input carries, while a missing selected skill is recorded as a required unit naming that skill rather than a path. Audit consumes the shared agentic-verification run journal and projection governed by [`spx/21-spec-tree.enabler/16-verification.enabler/13-run-journal.adr.md`](spx/21-spec-tree.enabler/16-verification.enabler/13-run-journal.adr.md) and `spx/21-spec-tree.enabler/16-verification.enabler/18-journal-projection.enabler`; those shared layers own storage, backend selection, event ordering, streaming, sealing, projection rendering, wrapper-agent shape, and changeset-scope derivation. The implementation-audit orchestration dispatches only the selected skills that follow the concern contract — for a language, its code, tests, and architecture concerns — and never runs deterministic validation, test, or eval commands, which remain the main agent's changeset responsibility and CI's responsibility over the CI scope per [`spx/31-outcomeeng.enabler/31-verification.enabler/14-verification.pdr.md`](spx/31-outcomeeng.enabler/31-verification.enabler/14-verification.pdr.md). Eval-evidence audits run through a separate artifact-type auditor, not as a fourth implementation-audit phase.
  new: The marketplace ships one implementation-audit wrapper surface in the product-tree plugin: an `implementation-auditor` agent invoking skill-owned orchestration that resolves, for each changed path, the registered artifacts whose detection matches it and the audit skills they name, from the artifact registry the build renders beside its provider skill's reader, which the scope resolver imports; validates that each selected skill is installed; passes the supplied scope unchanged to each selected skill that follows the concern contract; aggregates their projections; and records one audit verification run. Each concern skill owns language-specific applicability and claims the subject paths it audits or returns not applicable; a resolved path no registered artifact matches, a matched path whose selected skill returns not applicable, and a path whose registered artifact's audit skill follows another contract remain outside implementation-audit coverage and stay with their artifact-type auditor and the whole-changeset review, while the run records each as an accounting record — an optional, skipped coverage-gap unit carrying no language partition and, for a path whose registered artifact's audit skill follows another contract, naming that skill — so a sealed run's recorded path subjects equal the changed-path inventory its own start input carries, while a missing selected skill is recorded as a required unit naming that skill rather than a path. Audit consumes the shared agentic-verification run journal and projection governed by [`spx/21-product-tree.enabler/16-verification.enabler/13-run-journal.adr.md`](spx/21-product-tree.enabler/16-verification.enabler/13-run-journal.adr.md) and `spx/21-product-tree.enabler/16-verification.enabler/18-journal-projection.enabler`; those shared layers own storage, backend selection, event ordering, streaming, sealing, projection rendering, wrapper-agent shape, and changeset-scope derivation. The implementation-audit orchestration dispatches only the selected skills that follow the concern contract — for a language, its code, tests, and architecture concerns — and never runs deterministic validation, test, or eval commands, which remain the main agent's changeset responsibility and CI's responsibility over the CI scope per [`spx/31-outcomeeng.enabler/31-verification.enabler/14-verification.pdr.md`](spx/31-outcomeeng.enabler/31-verification.enabler/14-verification.pdr.md). Eval-evidence audits run through a separate artifact-type auditor, not as a fourth implementation-audit phase.
  ```

- [x] line 5

  ```text
  old: A plugin that ships `author-{lang}-code` ships `audit-{lang}-code`, `audit-{lang}-test` and `audit-{lang}-architecture` as skills; no language-specific auditor agent exists. This is the audit case of the rule in [`spx/15-subagent-execution.pdr.md`](spx/15-subagent-execution.pdr.md) that every subagent definition is language-neutral. The implementation-audit surface is one spec-tree-owned `implementation-auditor` wrapper agent that owns the isolated verifier context and invokes those skills inside that one subagent invocation. The launcher exposes one subagent level, so nested composition happens by invoking skills from the dispatched implementation-auditor context rather than by launching a second layer of agents. The implementation-auditor composes the validated projections of the `audit-{lang}-code`, `audit-{lang}-test` and `audit-{lang}-architecture` skills it invokes into one audit verification run. Keeping composition inside that one verifier context avoids an unmaintainable fleet of single-skill agents such as `{lang}-code-auditor`, `{lang}-test-auditor`, or `{lang}-architecture-auditor`.
  new: A plugin that ships `author-{lang}-code` ships `audit-{lang}-code`, `audit-{lang}-test` and `audit-{lang}-architecture` as skills; no language-specific auditor agent exists. This is the audit case of the rule in [`spx/15-subagent-execution.pdr.md`](spx/15-subagent-execution.pdr.md) that every subagent definition is language-neutral. The implementation-audit surface is one product-tree-owned `implementation-auditor` wrapper agent that owns the isolated verifier context and invokes those skills inside that one subagent invocation. The launcher exposes one subagent level, so nested composition happens by invoking skills from the dispatched implementation-auditor context rather than by launching a second layer of agents. The implementation-auditor composes the validated projections of the `audit-{lang}-code`, `audit-{lang}-test` and `audit-{lang}-architecture` skills it invokes into one audit verification run. Keeping composition inside that one verifier context avoids an unmaintainable fleet of single-skill agents such as `{lang}-code-auditor`, `{lang}-test-auditor`, or `{lang}-architecture-auditor`.
  ```

- [x] line 13

  ```text
  old: The audit-specific decision lives here because neither shared verification nor review decides how audit partitions scope, which language skill names must exist, which artifact-type auditors compose language concerns, or which wrapper agents expose audit surfaces. Keeping those rules in the audit decision leaves the shared run-journal and projection architecture in `spx/21-spec-tree.enabler/16-verification.enabler/` and keeps review free to consume the same architecture with its own policy.
  new: The audit-specific decision lives here because neither shared verification nor review decides how audit partitions scope, which language skill names must exist, which artifact-type auditors compose language concerns, or which wrapper agents expose audit surfaces. Keeping those rules in the audit decision leaves the shared run-journal and projection architecture in `spx/21-product-tree.enabler/16-verification.enabler/` and keeps review free to consume the same architecture with its own policy.
  ```

- [x] line 28

  ```text
  old: - NEVER: the spec-tree plugin ships multiple implementation-audit wrapper agents; implementation audit has one wrapper, `implementation-auditor` ([audit])
  new: - NEVER: the product-tree plugin ships multiple implementation-audit wrapper agents; implementation audit has one wrapper, `implementation-auditor` ([audit])
  ```

- [x] line 29

  ```text
  old: - ALWAYS: every auditor agent is generic and artifact-type-scoped, never language-scoped — the one spec-tree-owned `implementation-auditor` composes the per-language implementation code, test, and architecture skills, and every other artifact type is covered by a single artifact-type auditor owned by the plugin that governs that artifact type; language audits ship as skills with no language-specific auditor agent ([audit])
  new: - ALWAYS: every auditor agent is generic and artifact-type-scoped, never language-scoped — the one product-tree-owned `implementation-auditor` composes the per-language implementation code, test, and architecture skills, and every other artifact type is covered by a single artifact-type auditor owned by the plugin that governs that artifact type; language audits ship as skills with no language-specific auditor agent ([audit])
  ```

### [`spx/21-spec-tree.enabler/18-context-loading.enabler/13-context-enumeration.adr.md`](spx/21-product-tree.enabler/18-context-loading.enabler/13-context-enumeration.adr.md), moving with its node under `spx/21-product-tree.enabler/`

- [x] line 19

  ```text
  old: - Instruction files — the active root harness instruction file (`CLAUDE.md` for Claude Code, `AGENTS.md` for Codex), plus any on-path subdirectory instruction file with that harness's instruction filename, in path order from the root — are enumerated as a distinct set outside the ordered read order. The root instruction file's managed Spec Tree instruction block carries the product-root methodology instructions; `spx/CLAUDE.md` and `spx/AGENTS.md` are not instruction inputs.
  new: - Instruction files — the active root harness instruction file (`CLAUDE.md` for Claude Code, `AGENTS.md` for Codex), plus any on-path subdirectory instruction file with that harness's instruction filename, in path order from the root — are enumerated as a distinct set outside the ordered read order. The root instruction file's managed Product Tree instruction block carries the product-root methodology instructions; `spx/CLAUDE.md` and `spx/AGENTS.md` are not instruction inputs.
  ```

### [`spx/21-spec-tree.enabler/18-context-loading.enabler/15-foundation-manifest.adr.md`](spx/21-product-tree.enabler/18-context-loading.enabler/15-foundation-manifest.adr.md), moving with its node under `spx/21-product-tree.enabler/`

- [x] line 3

  ```text
  old: The spec-tree plugin package identifies its methodology resource surface through an authored machine-readable manifest at the package-relative path `skills/understand/manifest.json`: JSON carrying an integer `schema_version`, exactly one package-relative core entry naming the consolidated foundation document `skills/understand/SKILL.md`, and three deterministically ordered, duplicate-free catalogs of package-relative extended resource paths — references, templates, and examples — in curated reading order. The manifest is metadata only and never duplicates, summarizes, or restructures the foundation document body; within a schema version the shape evolves additively, and a breaking shape change increments `schema_version`. Package checks validate the shipped manifest in every generated tree so every declared path exists and every shipped extended resource is declared.
  new: The product-tree plugin package identifies its methodology resource surface through an authored machine-readable manifest at the package-relative path `skills/understand/manifest.json`: JSON carrying an integer `schema_version`, exactly one package-relative core entry naming the consolidated foundation document `skills/understand/SKILL.md`, and three deterministically ordered, duplicate-free catalogs of package-relative extended resource paths — references, templates, and examples — in curated reading order. The manifest is metadata only and never duplicates, summarizes, or restructures the foundation document body; within a schema version the shape evolves additively, and a breaking shape change increments `schema_version`. Package checks validate the shipped manifest in every generated tree so every declared path exists and every shipped extended resource is declared.
  ```

- [x] line 7

  ```text
  old: The SPX CLI consumes the package's resource surface as structured package data — the same trusted-third-party structured-data boundary [`spx/21-spec-tree.enabler/18-context-loading.enabler/13-context-enumeration.adr.md`](spx/21-spec-tree.enabler/18-context-loading.enabler/13-context-enumeration.adr.md) establishes for tree enumeration — rather than parsing skill prose or inferring resource groups from directory layout, while authored curation keeps catalog order meaningful and package-check validation closes the drift between the manifest and the shipped files.
  new: The SPX CLI consumes the package's resource surface as structured package data — the same trusted-third-party structured-data boundary [`spx/21-product-tree.enabler/18-context-loading.enabler/13-context-enumeration.adr.md`](spx/21-product-tree.enabler/18-context-loading.enabler/13-context-enumeration.adr.md) establishes for tree enumeration — rather than parsing skill prose or inferring resource groups from directory layout, while authored curation keeps catalog order meaningful and package-check validation closes the drift between the manifest and the shipped files.
  ```

- [x] line 19

  ```text
  old: - ALWAYS: the spec-tree plugin ships `skills/understand/manifest.json` in every generated tree, declaring an integer `schema_version`, exactly one core entry naming the consolidated foundation document, and the references, templates, and examples catalogs as ordered arrays of package-relative paths ([conformance])
  new: - ALWAYS: the product-tree plugin ships `skills/understand/manifest.json` in every generated tree, declaring an integer `schema_version`, exactly one core entry naming the consolidated foundation document, and the references, templates, and examples catalogs as ordered arrays of package-relative paths ([conformance])
  ```

### [`spx/21-spec-tree.enabler/43-instruction-block.enabler/21-render-model.adr.md`](spx/21-product-tree.enabler/43-instruction-block.enabler/21-render-model.adr.md), moving with its node under `spx/21-product-tree.enabler/`

- [x] line 3

  ```text
  old: The product's Spec Tree instructions live as a generated **router block** at the top of each root agent-harness instruction file — `CLAUDE.md` for Claude Code and `AGENTS.md` for Codex — because root instruction files are retained across context compaction while `spx/` subdirectory instruction files disappear from the compacted conversation. Each root file is three content kinds: the generated router block, always first; **`shared` regions** kept byte-identical across both files; and **independent content** free to differ between the files. The router carries the product-neutral WHEN-to-invoke routing and a concrete instruction to read the whole file, so a product's own phase commands survive compaction as content the agent reads rather than as data the router resolves. The writer removes `spx/CLAUDE.md` and `spx/AGENTS.md` so the root surface is the only instruction surface, and preserves every root instruction-file content outside the router block and the shared regions.
  new: The product's Product Tree instructions live as a generated **router block** at the top of each root agent-harness instruction file — `CLAUDE.md` for Claude Code and `AGENTS.md` for Codex — because root instruction files are retained across context compaction while `spx/` subdirectory instruction files disappear from the compacted conversation. Each root file is three content kinds: the generated router block, always first; **`shared` regions** kept byte-identical across both files; and **independent content** free to differ between the files. The router carries the product-neutral WHEN-to-invoke routing and a concrete instruction to read the whole file, so a product's own phase commands survive compaction as content the agent reads rather than as data the router resolves. The writer removes `spx/CLAUDE.md` and `spx/AGENTS.md` so the root surface is the only instruction surface, and preserves every root instruction-file content outside the router block and the shared regions.
  ```

- [x] line 5

  ```text
  old: The **router block** is delimited by a single opening marker `<!-- SPEC-TREE v{template_version} langs:{enabled-languages} -->` and a closing `<!-- /SPEC-TREE -->`, rendered from the harness templates committed under `dist/claude/` and `dist/codex/`, filtered to the product's enabled languages and to the reading harness — one authored template, two per-harness renders differing only in the spans the template marks for a harness and each file's own filename. Its opening marker carries only the two fields staleness reads: the dotted template version and the recorded enabled-language list. The router is regenerated in full on every update; a re-render overwrites any hand-edit inside it. It carries no product-specific string and references no per-product command by name; because its instruction is to read the entire file, the agent reaches the product's commands wherever the product writes them, so the router needs no slot to point at.
  new: The **router block** is delimited by a single opening marker `<!-- PRODUCT-TREE v{template_version} langs:{enabled-languages} -->` and a closing `<!-- /PRODUCT-TREE -->`, rendered from the harness templates committed under `dist/claude/` and `dist/codex/`, filtered to the product's enabled languages and to the reading harness — one authored template, two per-harness renders differing only in the spans the template marks for a harness and each file's own filename. Its opening marker carries only the two fields staleness reads: the dotted template version and the recorded enabled-language list. The router is regenerated in full on every update; a re-render overwrites any hand-edit inside it. It carries no product-specific string and references no per-product command by name; because its instruction is to read the entire file, the agent reaches the product's commands wherever the product writes them, so the router needs no slot to point at.
  ```

- [x] line 7

  ```text
  old: A **`shared` region** is delimited by `<!-- SPEC-TREE:shared {name} -->` and `<!-- /SPEC-TREE:shared {name} -->`, present in both root files under the same name with byte-identical bodies. Shared regions are the dominant content because in almost all repositories the two root files are identical. When a shared region's two bodies diverge, the region is reconciled by **whole-side replacement**: the side whose region was committed more recently — decided by that region's own line-range history, not the whole file's last commit, so a later commit to a file's independent content never carries a stale region — is written whole into the other file. The reconciler never merges the two bodies — a content merge needs semantic judgment a deterministic step cannot supply, so whole-side replacement is the rule that keeps every step reducible to a hook. **Independent content** is every part of a root file outside the router block and every shared region; it is per-file, may differ between the two files, and the writer preserves it verbatim.
  new: A **`shared` region** is delimited by `<!-- PRODUCT-TREE:shared {name} -->` and `<!-- /PRODUCT-TREE:shared {name} -->`, present in both root files under the same name with byte-identical bodies. Shared regions are the dominant content because in almost all repositories the two root files are identical. When a shared region's two bodies diverge, the region is reconciled by **whole-side replacement**: the side whose region was committed more recently — decided by that region's own line-range history, not the whole file's last commit, so a later commit to a file's independent content never carries a stale region — is written whole into the other file. The reconciler never merges the two bodies — a content merge needs semantic judgment a deterministic step cannot supply, so whole-side replacement is the rule that keeps every step reducible to a hook. **Independent content** is every part of a root file outside the router block and every shared region; it is per-file, may differ between the two files, and the writer preserves it verbatim.
  ```

- [x] line 54

  ```text
  old: The behavioral rules of the three content kinds — router marker format, full router regeneration, shared-region byte-identity and git-recency reconciliation, independent-content preservation, bootstrap wrapping, the five initial situations, legacy-block and symlink migration, obsolete `spx/` removal, and unresolved-delimiter refusal — are declared and tested as `[test]` assertions on the sibling spec `spx/21-spec-tree.enabler/43-instruction-block.enabler/instruction-block.md`. The `### Audit` rules below are the architectural constraints no deterministic test falsifies.
  new: The behavioral rules of the three content kinds — router marker format, full router regeneration, shared-region byte-identity and git-recency reconciliation, independent-content preservation, bootstrap wrapping, the five initial situations, legacy-block and symlink migration, obsolete `spx/` removal, and unresolved-delimiter refusal — are declared and tested as `[test]` assertions on the sibling spec `spx/21-product-tree.enabler/43-instruction-block.enabler/instruction-block.md`. The `### Audit` rules below are the architectural constraints no deterministic test falsifies.
  ```

- [x] line 66

  ```text
  old: - ALWAYS: the product's Spec Tree instructions are a generated router block at the top of each root harness instruction file — `CLAUDE.md` for Claude Code and `AGENTS.md` for Codex — because each harness retains its root instruction file across compaction ([audit])
  new: - ALWAYS: the product's Product Tree instructions are a generated router block at the top of each root harness instruction file — `CLAUDE.md` for Claude Code and `AGENTS.md` for Codex — because each harness retains its root instruction file across compaction ([audit])
  ```

### [`spx/21-spec-tree.enabler/68-reviewing.enabler/21-reviewing-changes.enabler/21-script-decomposition.adr.md`](spx/21-product-tree.enabler/68-reviewing.enabler/21-reviewing-changes.enabler/21-script-decomposition.adr.md), moving with its node under `spx/21-product-tree.enabler/`

- [x] line 24

  ```text
  old: - NEVER: scripts under `plugins/spec-tree/skills/review-changes/scripts/` import third-party packages, depend on `uv` at runtime, or import `outcomeeng_*` modules ([test](tests/test_reviewing_changes.compliance.l1.py))
  new: - NEVER: scripts under `plugins/product-tree/skills/review-changes/scripts/` import third-party packages, depend on `uv` at runtime, or import `outcomeeng_*` modules ([test](tests/test_reviewing_changes.compliance.l1.py))
  ```

### [`spx/21-spec-tree.enabler/79-diagnostics.enabler/13-diagnose-engine.adr.md`](spx/21-product-tree.enabler/79-diagnostics.enabler/13-diagnose-engine.adr.md), moving with its node under `spx/21-product-tree.enabler/`

- [x] line 21

  ```text
  old: The manifest is declarative because the facts that vary by consumer — the floor the installed plugin requires, the marketplace it depends on, and the checks it runs — are the plugin's, not the `spx` CLI's. The plugin declares them; `spx diagnose` executes against them, keeping the CLI generic across the consumers a methodology marketplace installs into. Expected plugin state is not one of those manifest facts. Claude Code selection belongs to the inventory recorded for the invocation checkout at project or local scope. Codex selection belongs to the raw selected `CODEX_HOME/config.toml` declarations, including disabled plugins and plugins whose cache is absent. The committed per-agent marketplace catalogs bound membership; neither catalog membership alone nor trusted product activation selects the expected installed set. Diagnosis reads selected-home declarations independently of product overrides and inspects native Codex state outside trusted product configuration discovery. A product that enables fewer plugins than its home selects therefore remains a valid selective installation. An absent cache is observable installation drift for a selected plugin, rather than evidence that the plugin was unselected. The floor stays a single source of truth: the build renders the product's `REQUIRED_SPX_VERSION` into the manifest, exactly as [`spx/21-spec-tree.enabler/79-diagnostics.enabler/15-version-floor.adr.md`](spx/21-spec-tree.enabler/79-diagnostics.enabler/15-version-floor.adr.md) requires the floor rendered into the shipped tree, so the shipped floor cannot drift from the floor the product enforces in CI. The manifest is a product-owned data file the skill passes by path; the field that [`spx/21-spec-tree.enabler/79-diagnostics.enabler/15-version-floor.adr.md`](spx/21-spec-tree.enabler/79-diagnostics.enabler/15-version-floor.adr.md) rejects is a field in the *agent's* plugin manifest, whose schema the agent owns and validates — a different artifact from this contract.
  new: The manifest is declarative because the facts that vary by consumer — the floor the installed plugin requires, the marketplace it depends on, and the checks it runs — are the plugin's, not the `spx` CLI's. The plugin declares them; `spx diagnose` executes against them, keeping the CLI generic across the consumers a methodology marketplace installs into. Expected plugin state is not one of those manifest facts. Claude Code selection belongs to the inventory recorded for the invocation checkout at project or local scope. Codex selection belongs to the raw selected `CODEX_HOME/config.toml` declarations, including disabled plugins and plugins whose cache is absent. The committed per-agent marketplace catalogs bound membership; neither catalog membership alone nor trusted product activation selects the expected installed set. Diagnosis reads selected-home declarations independently of product overrides and inspects native Codex state outside trusted product configuration discovery. A product that enables fewer plugins than its home selects therefore remains a valid selective installation. An absent cache is observable installation drift for a selected plugin, rather than evidence that the plugin was unselected. The floor stays a single source of truth: the build renders the product's `REQUIRED_SPX_VERSION` into the manifest, exactly as [`spx/21-product-tree.enabler/79-diagnostics.enabler/15-version-floor.adr.md`](spx/21-product-tree.enabler/79-diagnostics.enabler/15-version-floor.adr.md) requires the floor rendered into the shipped tree, so the shipped floor cannot drift from the floor the product enforces in CI. The manifest is a product-owned data file the skill passes by path; the field that [`spx/21-product-tree.enabler/79-diagnostics.enabler/15-version-floor.adr.md`](spx/21-product-tree.enabler/79-diagnostics.enabler/15-version-floor.adr.md) rejects is a field in the *agent's* plugin manifest, whose schema the agent owns and validates — a different artifact from this contract.
  ```

- [x] line 46

  ```text
  old: - ALWAYS: the consumer-varying inputs — the spx-version floor, the marketplace identity, and the check set — reach `spx diagnose` through a plugin-shipped declarative manifest the skill passes by path, the floor build-rendered from the product's single source of truth per [`spx/21-spec-tree.enabler/79-diagnostics.enabler/15-version-floor.adr.md`](spx/21-spec-tree.enabler/79-diagnostics.enabler/15-version-floor.adr.md) ([audit])
  new: - ALWAYS: the consumer-varying inputs — the spx-version floor, the marketplace identity, and the check set — reach `spx diagnose` through a plugin-shipped declarative manifest the skill passes by path, the floor build-rendered from the product's single source of truth per [`spx/21-product-tree.enabler/79-diagnostics.enabler/15-version-floor.adr.md`](spx/21-product-tree.enabler/79-diagnostics.enabler/15-version-floor.adr.md) ([audit])
  ```

### [`spx/31-outcomeeng.enabler/31-verification.enabler/14-verification.pdr.md`](spx/31-outcomeeng.enabler/31-verification.enabler/14-verification.pdr.md)

- [x] line 7

  ```text
  old: This product adopts the marketplace verification taxonomy rather than defining its own, so every node's evidence reads the same way across the spec tree and the two agentic types — audit and review — are themselves verified by graded eval cases. The Attested mode exists for the claim only observation settles: a probe records the Author's verdict together with the inspectable artifacts of an executed protocol, so a prototype's fidelity to its spec is evidence rather than an opinion, and the mode names how the verdict is produced, never who produced the subject. An audit verdict is produced in a Verifier's agent session isolated from the Author's agent session that produced the work under audit, so the judgment stays free of the bias an agent session accumulates while producing the work it would otherwise grade. The isolation separates Author from Verifier, never one Verifier from another: the Author's agent session dispatches the audit to a separate Verifier's agent session rather than grading its own work in place, and a Verifier already free of Author bias may compose further verification without reintroducing it.
  new: This product adopts the marketplace verification taxonomy rather than defining its own, so every node's evidence reads the same way across the product tree and the two agentic types — audit and review — are themselves verified by graded eval cases. The Attested mode exists for the claim only observation settles: a probe records the Author's verdict together with the inspectable artifacts of an executed protocol, so a prototype's fidelity to its spec is evidence rather than an opinion, and the mode names how the verdict is produced, never who produced the subject. An audit verdict is produced in a Verifier's agent session isolated from the Author's agent session that produced the work under audit, so the judgment stays free of the bias an agent session accumulates while producing the work it would otherwise grade. The isolation separates Author from Verifier, never one Verifier from another: the Author's agent session dispatches the audit to a separate Verifier's agent session rather than grading its own work in place, and a Verifier already free of Author bias may compose further verification without reintroducing it.
  ```

- [x] line 13

  ```text
  old: **The changeset** is the files changed between the base ref and HEAD (`git diff <base>...<head>`) and the spec-tree node(s) that govern them. When changed files span several nodes, their lowest common ancestor governs the combined verification scope.
  new: **The changeset** is the files changed between the base ref and HEAD (`git diff <base>...<head>`) and the product-tree node(s) that govern them. When changed files span several nodes, their lowest common ancestor governs the combined verification scope.
  ```

### [`spx/31-outcomeeng.enabler/31-verification.enabler/18-verification-component.adr.md`](spx/31-outcomeeng.enabler/31-verification.enabler/18-verification-component.adr.md)

- [x] line 3

  ```text
  old: The verification toolchain's runtime machinery — the trace event schema implementation, contract schema, conformance checker, contract inference, run aggregation, eval-harness runners, and coding-agent runtime adapters — is implemented in a separately versioned component outside this repository, released independently and consumed as a pinned third-party dependency. The spec tree under `spx/31-outcomeeng.enabler/31-verification.enabler/` stays authoritative for the semantics; the component complies. The one in-consumer exception is the trace emitter shipped inside plugins, which is standard-library-only Python rendered into the plugin trees because shipped plugin scripts import no third-party package.
  new: The verification toolchain's runtime machinery — the trace event schema implementation, contract schema, conformance checker, contract inference, run aggregation, eval-harness runners, and coding-agent runtime adapters — is implemented in a separately versioned component outside this repository, released independently and consumed as a pinned third-party dependency. The product tree under `spx/31-outcomeeng.enabler/31-verification.enabler/` stays authoritative for the semantics; the component complies. The one in-consumer exception is the trace emitter shipped inside plugins, which is standard-library-only Python rendered into the plugin trees because shipped plugin scripts import no third-party package.
  ```

### [`spx/31-outcomeeng.enabler/31-verification.enabler/31-eval-verification.enabler/15-adapter-derived-evals.adr.md`](spx/31-outcomeeng.enabler/31-verification.enabler/31-eval-verification.enabler/15-adapter-derived-evals.adr.md)

- [x] line 13

  ```text
  old: This governance supersedes, methodology-wide for skill, agent, and command behavior, the producer-coupling verdict model that the shipped `spx/21-spec-tree.enabler/68-audit.enabler/32-audit-eval-evidence.enabler/audit-eval-evidence.md` methodology records — where a producer-derived prompt earns a Proceed verdict. That auditor is a lower surface this decision governs; its re-derivation to the adapter-invoked coupling model is eval-verification cutover work tracked at its node, and it stays authoritative for its current consumers until that cutover completes, exactly as [`spx/13-infrastructure.enabler/25-eval-harness.enabler/57-producer-coupled-skill-evals.adr.md`](spx/13-infrastructure.enabler/25-eval-harness.enabler/57-producer-coupled-skill-evals.adr.md) stays authoritative for the shipped `outcomeeng_evals` harness until the same cutover.
  new: This governance supersedes, methodology-wide for skill, agent, and command behavior, the producer-coupling verdict model that the shipped `spx/21-product-tree.enabler/68-audit.enabler/32-audit-eval-evidence.enabler/audit-eval-evidence.md` methodology records — where a producer-derived prompt earns a Proceed verdict. That auditor is a lower surface this decision governs; its re-derivation to the adapter-invoked coupling model is eval-verification cutover work tracked at its node, and it stays authoritative for its current consumers until that cutover completes, exactly as [`spx/13-infrastructure.enabler/25-eval-harness.enabler/57-producer-coupled-skill-evals.adr.md`](spx/13-infrastructure.enabler/25-eval-harness.enabler/57-producer-coupled-skill-evals.adr.md) stays authoritative for the shipped `outcomeeng_evals` harness until the same cutover.
  ```

### [`spx/31-outcomeeng.enabler/31-verification.enabler/31-test-verification.enabler/15-test-infrastructure.pdr.md`](spx/31-outcomeeng.enabler/31-verification.enabler/31-test-verification.enabler/15-test-infrastructure.pdr.md)

- [x] line 3

  ```text
  old: Every spec tree governed by the Spec Tree methodology governs harnesses, generators, and inert fixtures as infrastructure that is crucial to delivering value; places their implementations at predictable per-language homes outside `spx/` and outside any `tests/` directory; and audits the full evidence chain from a spec assertion through every imported test-infrastructure artifact. Methodology users rely on this as a product-surface guarantee: predictable implementation homes per language, consistent category semantics, and every test-infrastructure artifact governed as production code by a naturally placed spec node.
  new: Every product tree governed by the Product Tree methodology governs harnesses, generators, and inert fixtures as infrastructure that is crucial to delivering value; places their implementations at predictable per-language homes outside `spx/` and outside any `tests/` directory; and audits the full evidence chain from a spec assertion through every imported test-infrastructure artifact. Methodology users rely on this as a product-surface guarantee: predictable implementation homes per language, consistent category semantics, and every test-infrastructure artifact governed as production code by a naturally placed spec node.
  ```

- [x] line 8

  ```text
  old: - The artifact's governing spec node sits wherever the product's Spec Tree naturally places that concern: a shared infrastructure node when category-wide policy is a real product concern, the node whose assertions depend on the artifact when the behavior is local to that node, or another ancestor or descendant selected by normal decomposition.
  new: - The artifact's governing spec node sits wherever the product's Product Tree naturally places that concern: a shared infrastructure node when category-wide policy is a real product concern, the node whose assertions depend on the artifact when the behavior is local to that node, or another ancestor or descendant selected by normal decomposition.
  ```

- [x] line 98

  ```text
  old: A test-infrastructure artifact is traceable to the spec tree through the same declaration path as any other infrastructure artifact. Category names are semantics, not required node slugs. A test-infrastructure artifact is traceable in one of two ways:
  new: A test-infrastructure artifact is traceable to the product tree through the same declaration path as any other infrastructure artifact. Category names are semantics, not required node slugs. A test-infrastructure artifact is traceable in one of two ways:
  ```

- [x] line 107

  ```text
  old: Methodology users rely on four predictable properties: where implementation files live, what category of artifact each file is, who owns the values it carries, and how audits judge the evidence chain. The decision gives those properties one answer that holds across products and languages while preserving natural Spec Tree placement for the governing node. Leaving implementation homes, ownership, or artifact semantics to local convention would make every product invent its own answer, defeat drift detection across audits, and produce contradictory skill-driven guidance across languages; forcing every product into the same root subtree would make the tree less true by moving local or shared evidence concerns away from the product area they actually serve. Natural placement keeps the truth hierarchy intact while category semantics and audit traversal give audits the authority to reject literal laundering, severed coupling, and helper directories masquerading as evidence.
  new: Methodology users rely on four predictable properties: where implementation files live, what category of artifact each file is, who owns the values it carries, and how audits judge the evidence chain. The decision gives those properties one answer that holds across products and languages while preserving natural Product Tree placement for the governing node. Leaving implementation homes, ownership, or artifact semantics to local convention would make every product invent its own answer, defeat drift detection across audits, and produce contradictory skill-driven guidance across languages; forcing every product into the same root subtree would make the tree less true by moving local or shared evidence concerns away from the product area they actually serve. Natural placement keeps the truth hierarchy intact while category semantics and audit traversal give audits the authority to reject literal laundering, severed coupling, and helper directories masquerading as evidence.
  ```

- [x] line 149

  ```text
  old: - NEVER: require or fabricate a top-level `infrastructure → testing → {generators, fixtures, harnesses}` subtree solely to govern test infrastructure — nodes with those slugs exist only when normal Spec Tree composition selects them for a real product concern ([audit])
  new: - NEVER: require or fabricate a top-level `infrastructure → testing → {generators, fixtures, harnesses}` subtree solely to govern test infrastructure — nodes with those slugs exist only when normal Product Tree composition selects them for a real product concern ([audit])
  ```

- [x] line 150

  ```text
  old: - NEVER: a `tests/` directory at any level of any spec tree contains a test harness, generator, fixture, or any non-test-assertion code — `tests/` contains only typed assertion files per [`spx/31-outcomeeng.enabler/31-verification.enabler/31-test-verification.enabler/21-evidence-types.pdr.md`](spx/31-outcomeeng.enabler/31-verification.enabler/31-test-verification.enabler/21-evidence-types.pdr.md) ([audit])
  new: - NEVER: a `tests/` directory at any level of any product tree contains a test harness, generator, fixture, or any non-test-assertion code — `tests/` contains only typed assertion files per [`spx/31-outcomeeng.enabler/31-verification.enabler/31-test-verification.enabler/21-evidence-types.pdr.md`](spx/31-outcomeeng.enabler/31-verification.enabler/31-test-verification.enabler/21-evidence-types.pdr.md) ([audit])
  ```

### [`spx/31-outcomeeng.enabler/31-verification.enabler/31-test-verification.enabler/21-evidence-types.pdr.md`](spx/31-outcomeeng.enabler/31-verification.enabler/31-test-verification.enabler/21-evidence-types.pdr.md)

- [x] line 50

  ```text
  old: 9. The scenario's case tuple relocated to a production constant so the test can cite a production address — source laundering (the production-address `NEVER` assertion in `spx/31-outcomeeng.enabler/31-verification.enabler/31-test-verification.enabler/test-verification.md`; the litmus-first assertion in `spx/21-spec-tree.enabler/68-audit.enabler/32-audit-tests.enabler/audit-tests.md`).
  new: 9. The scenario's case tuple relocated to a production constant so the test can cite a production address — source laundering (the production-address `NEVER` assertion in `spx/31-outcomeeng.enabler/31-verification.enabler/31-test-verification.enabler/test-verification.md`; the litmus-first assertion in `spx/21-product-tree.enabler/68-audit.enabler/32-audit-tests.enabler/audit-tests.md`).
  ```

### [`spx/32-distribution.enabler/21-installation.enabler/21-repository-installation.enabler/21-installation-architecture.adr.md`](spx/32-distribution.enabler/21-installation.enabler/21-repository-installation.enabler/21-installation-architecture.adr.md)

- [x] line 5

  ```text
  old: Persistent preflight reads each agent's marketplace registry through the agent's own listing command, taking the entry that carries the committed catalog's name as the source the run refreshes from; the catalogs supply the name and no constant supplies the source. It reads Claude Code's complete install-record listing and the selected Codex home's raw plugin declarations, including disabled entries whose cache or marketplace snapshot is missing. From the Claude Code listing it derives two things: the invocation checkout's project- and local-scope inventory, which selects the bootstrap set and the native-update set, and every other project- or local-scope install record of a cataloged plugin on the machine — one per plugin, scope, and project path — which the plan brings to the target by rewriting its install-record entry. It validates every nonempty catalog-bounded selection contains `spec-tree`, derives empty state as the `spec-tree` bootstrap selection, and orders names through the committed catalog. An empty inventory proposes that bootstrap; the plan decides it. Every entry the run reports — each warning, each plugin it names as installed — therefore reads the plan rather than the observation that proposed it, because the two diverge wherever a later condition suppresses an operation the observation implied: the first-install warning accompanies the bootstrap install the plan carries, and the installed set the report names for an agent is the plugins its plan carries an install or a native update for, less the pending ones. Unreadable invocation settings and a withheld registration are two such conditions, and under either the agent announces nothing and is named as installing nothing. Read-only activation observations retain the pre-run declarations for comparison. Selected subsets and agent-definition collisions validate before the first state-changing operation. A missing registration is the bootstrap case: the run registers the source the invocation checkout's own settings declare. A checkout that declares no readable source withholds that agent's registration and, with it, every operation of that agent's plan that names the marketplace the run never registered — including a closing listing that names it and the native update of each record the invocation checkout holds — while a closing listing over the machine's own records, which names no registration, still runs. A withheld registration also leaves no clone to read a target from, so no record of that agent moves: every project- or local-scope record of a cataloged plugin, the invocation checkout's own included, is reported as unrefreshed at its listed version. The withholding is a blocking warning, so the exit is nonzero. No clone exists when a bootstrap plan is built, so it carries no target; every other checkout's record is reported as unrefreshed with its listed version, the exit is nonzero, and the next run, which finds the registration, brings them to the target.
  new: Persistent preflight reads each agent's marketplace registry through the agent's own listing command, taking the entry that carries the committed catalog's name as the source the run refreshes from; the catalogs supply the name and no constant supplies the source. It reads Claude Code's complete install-record listing and the selected Codex home's raw plugin declarations, including disabled entries whose cache or marketplace snapshot is missing. From the Claude Code listing it derives two things: the invocation checkout's project- and local-scope inventory, which selects the bootstrap set and the native-update set, and every other project- or local-scope install record of a cataloged plugin on the machine — one per plugin, scope, and project path — which the plan brings to the target by rewriting its install-record entry. It validates every nonempty catalog-bounded selection contains `product-tree`, derives empty state as the `product-tree` bootstrap selection, and orders names through the committed catalog. An empty inventory proposes that bootstrap; the plan decides it. Every entry the run reports — each warning, each plugin it names as installed — therefore reads the plan rather than the observation that proposed it, because the two diverge wherever a later condition suppresses an operation the observation implied: the first-install warning accompanies the bootstrap install the plan carries, and the installed set the report names for an agent is the plugins its plan carries an install or a native update for, less the pending ones. Unreadable invocation settings and a withheld registration are two such conditions, and under either the agent announces nothing and is named as installing nothing. Read-only activation observations retain the pre-run declarations for comparison. Selected subsets and agent-definition collisions validate before the first state-changing operation. A missing registration is the bootstrap case: the run registers the source the invocation checkout's own settings declare. A checkout that declares no readable source withholds that agent's registration and, with it, every operation of that agent's plan that names the marketplace the run never registered — including a closing listing that names it and the native update of each record the invocation checkout holds — while a closing listing over the machine's own records, which names no registration, still runs. A withheld registration also leaves no clone to read a target from, so no record of that agent moves: every project- or local-scope record of a cataloged plugin, the invocation checkout's own included, is reported as unrefreshed at its listed version. The withholding is a blocking warning, so the exit is nonzero. No clone exists when a bootstrap plan is built, so it carries no target; every other checkout's record is reported as unrefreshed with its listed version, the exit is nonzero, and the next run, which finds the registration, brings them to the target.
  ```

- [x] line 7

  ```text
  old: The plan distinguishes native refresh from bootstrap and recovery. Native refresh updates selected plugin content without activating disabled plugins; activating install or enable commands do not implement routine refresh. The native marketplace refresh moves the registered clone to the head of its source's default branch; that commit is the target, and for each cataloged plugin the target version is its manifest version at that commit and the target install path is the cache directory that version names. The head is read by running git in the location the registry records for the marketplace, so the target presupposes that location is a git working tree. A GitHub or git registration records a clone and satisfies it; a directory registration records whatever path was added, which the agent accepts without it being a repository, and a plain directory resolves no head — nor does a clone the read fails against for any other reason. That failure is the one planned command whose nonzero exit is a reported disposition rather than a terminal failure, because stopping there would abandon the machine-wide refresh with nothing reported about any record on the machine. A run with no head reaches no target, which is the condition the bootstrap and withheld-registration cases already carry: no record moves through the rewrite, every project- or local-scope record of a cataloged plugin the run carries — the invocation checkout's own, whose native update has already run, included — is reported against no target with a blocking warning, and the exit is nonzero. A cataloged plugin the clone's catalog names no source for, or whose manifest the clone cannot supply or does not version, resolves to no target version; every project- or local-scope record of that plugin is reported as unresolved and the exit is nonzero, while every other plugin's records still move. The domain is every such record the run carries, the invocation checkout's own included, because the condition belongs to the plugin's supply in the clone rather than to the way one record would have moved: a record outside the invocation checkout is left unchanged, since the rewrite is what would have moved it, while the invocation checkout's own record has already received its native update by the time the clone is read, so the run reports it at the version the closing listing carries. Either way no target version exists for the comparison to judge that record against, so its condition reaches the exit code through the report's warning rather than through the drift comparison. For Claude Code, the invocation checkout's own records receive one `plugin update` each at their scope, executed with the invocation checkout as working directory, which fetches the target into the shared plugin cache. After the native marketplace refresh and the native updates of the invocation checkout's records, and before rewrite planning, the run reads the plugin cache once; for each cataloged plugin that no invocation-checkout record names, that another project- or local-scope record names, and whose target version has no cache directory, it issues one native `plugin install` at project scope with a run-owned temporary project as its working directory and the persistent environment, so the agent writes that version into the shared plugin cache under its own configuration directory. The run creates that project from a unique-per-invocation temporary directory outside every checkout and removes it on every exit path. Every other project- or local-scope record of a cataloged plugin is brought to the target by a rewrite of its entry in the install-record file — install path, version, and commit — planned as a pure function from the opening listing and the target entries and performed once, atomically, by the single writer at the execution boundary, before the closing listing read the run's postcondition depends on, preserving every entry and field the plan does not set. The single install-record writer removes every entry whose project path is the run-owned temporary project in the same atomic replace that rewrites the other records, before the closing listing read; a run that a later failed operation stops after a fetch still runs the writer for that removal alone and rewrites no other record, so no record of that project outlives the run and the closing comparison never reads one. A native uninstall does not drop that record, because the agent may prune the cache version the rewrite is about to name, and the writer is already the run's single install-record writer. The document that write replaces is the document as it stands at the write boundary, not a copy read before it: the writer reads the document, applies the planned set to it as a pure function of text and write set, and reads the document once more immediately before the replace, applying the same set again when the store moved under it. The run does not own that document, and the agent admits no lock over it, so a write landing there while the run is in flight is the ordinary case rather than an anomaly: the second read is what carries such a write into the replacement instead of discarding it. It is one read at the write boundary, not a lock, a wait, or a loop — the run still neither waits for another session nor chases a record it observes, and the record another session wrote reaches the closing comparison, which reports it. The rewrite runs no command in any other checkout and does not depend on the record's project directory existing. A record whose plugin the catalog does not carry, or whose scope is neither project nor local, is reported as a warning and left unchanged. A listing entry at project or local scope that names no project path, or that reports no version, is reported as a listing defect; the run continues and its exit is nonzero. The listing is the only source for what a record holds and the only address a rewrite can reach, so an entry missing either carries too little for the run to move it, and neither defect settles anything about the rest of the machine's records. Install and enable are suppressed for every plugin the invocation checkout records at project or local scope; they run in the invocation checkout only in the bootstrap case, where the checkout records none, and only there do the invocation checkout's own settings matter: unreadable settings stop bootstrap and nothing else; the uncached-target fetch's install runs in the run-owned temporary project and touches no checkout's settings. A record of a cataloged plugin whose target version still has no cache directory after the fetch is reported as unrefreshable, its record untouched, and the exit is nonzero. A failed fetch install stops the run like any other failed operation; the pending-publication carve-out covers selected plugins only, and a plugin whose target version the clone resolves is published. The run never writes the plugin cache itself; the agent's native install does. An empty Codex home receives a disabled `spec-tree` declaration. Cache recovery preserves existing activation, including explicit home enablement, and never treats an unchanged marketplace snapshot as proof that each selected plugin cache exists. After execution, native state inspection and declaration comparison establish the selected set, activation, and refreshed or pending status of every selected plugin. Unexpected changes are terminal diagnostics, with no snapshot restoration or compensating activation writes. That postcondition is bounded to the invocation checkout and the selected home, whose bootstrap install and enable are the only operations that write an activation entry; a recorded checkout elsewhere receives the install-record rewrite alone, which touches no settings document, so its settings carry no postcondition. The machine-wide refresh carries its own postcondition read: the plan is built from one install-record listing taken in preflight, and after execution the run takes a second listing and compares every project- or local-scope record of a cataloged plugin with the target, reporting each record's version before and after and exiting nonzero when any such record — planned, or written by another session between the two reads — is off the target. The run neither locks the agent's record store nor issues a further update or rewrite; the comparison and the exit code are its complete response. The exit is nonzero when that comparison leaves any record off the target and when the run raises a blocking warning, which is how every condition the comparison cannot reach gets to the exit code: a condition no record carries — a listing entry with no project path or no version, a bootstrap run with no registered clone, an agent whose registration the run withheld, a cataloged plugin whose target version has no cache directory — and a condition a record carries that the comparison has no target to judge, which is a record of a plugin the clone resolves no target version for and every record of a cataloged plugin in a run whose head read resolved no target at all.
  new: The plan distinguishes native refresh from bootstrap and recovery. Native refresh updates selected plugin content without activating disabled plugins; activating install or enable commands do not implement routine refresh. The native marketplace refresh moves the registered clone to the head of its source's default branch; that commit is the target, and for each cataloged plugin the target version is its manifest version at that commit and the target install path is the cache directory that version names. The head is read by running git in the location the registry records for the marketplace, so the target presupposes that location is a git working tree. A GitHub or git registration records a clone and satisfies it; a directory registration records whatever path was added, which the agent accepts without it being a repository, and a plain directory resolves no head — nor does a clone the read fails against for any other reason. That failure is the one planned command whose nonzero exit is a reported disposition rather than a terminal failure, because stopping there would abandon the machine-wide refresh with nothing reported about any record on the machine. A run with no head reaches no target, which is the condition the bootstrap and withheld-registration cases already carry: no record moves through the rewrite, every project- or local-scope record of a cataloged plugin the run carries — the invocation checkout's own, whose native update has already run, included — is reported against no target with a blocking warning, and the exit is nonzero. A cataloged plugin the clone's catalog names no source for, or whose manifest the clone cannot supply or does not version, resolves to no target version; every project- or local-scope record of that plugin is reported as unresolved and the exit is nonzero, while every other plugin's records still move. The domain is every such record the run carries, the invocation checkout's own included, because the condition belongs to the plugin's supply in the clone rather than to the way one record would have moved: a record outside the invocation checkout is left unchanged, since the rewrite is what would have moved it, while the invocation checkout's own record has already received its native update by the time the clone is read, so the run reports it at the version the closing listing carries. Either way no target version exists for the comparison to judge that record against, so its condition reaches the exit code through the report's warning rather than through the drift comparison. For Claude Code, the invocation checkout's own records receive one `plugin update` each at their scope, executed with the invocation checkout as working directory, which fetches the target into the shared plugin cache. After the native marketplace refresh and the native updates of the invocation checkout's records, and before rewrite planning, the run reads the plugin cache once; for each cataloged plugin that no invocation-checkout record names, that another project- or local-scope record names, and whose target version has no cache directory, it issues one native `plugin install` at project scope with a run-owned temporary project as its working directory and the persistent environment, so the agent writes that version into the shared plugin cache under its own configuration directory. The run creates that project from a unique-per-invocation temporary directory outside every checkout and removes it on every exit path. Every other project- or local-scope record of a cataloged plugin is brought to the target by a rewrite of its entry in the install-record file — install path, version, and commit — planned as a pure function from the opening listing and the target entries and performed once, atomically, by the single writer at the execution boundary, before the closing listing read the run's postcondition depends on, preserving every entry and field the plan does not set. The single install-record writer removes every entry whose project path is the run-owned temporary project in the same atomic replace that rewrites the other records, before the closing listing read; a run that a later failed operation stops after a fetch still runs the writer for that removal alone and rewrites no other record, so no record of that project outlives the run and the closing comparison never reads one. A native uninstall does not drop that record, because the agent may prune the cache version the rewrite is about to name, and the writer is already the run's single install-record writer. The document that write replaces is the document as it stands at the write boundary, not a copy read before it: the writer reads the document, applies the planned set to it as a pure function of text and write set, and reads the document once more immediately before the replace, applying the same set again when the store moved under it. The run does not own that document, and the agent admits no lock over it, so a write landing there while the run is in flight is the ordinary case rather than an anomaly: the second read is what carries such a write into the replacement instead of discarding it. It is one read at the write boundary, not a lock, a wait, or a loop — the run still neither waits for another session nor chases a record it observes, and the record another session wrote reaches the closing comparison, which reports it. The rewrite runs no command in any other checkout and does not depend on the record's project directory existing. A record whose plugin the catalog does not carry, or whose scope is neither project nor local, is reported as a warning and left unchanged. A listing entry at project or local scope that names no project path, or that reports no version, is reported as a listing defect; the run continues and its exit is nonzero. The listing is the only source for what a record holds and the only address a rewrite can reach, so an entry missing either carries too little for the run to move it, and neither defect settles anything about the rest of the machine's records. Install and enable are suppressed for every plugin the invocation checkout records at project or local scope; they run in the invocation checkout only in the bootstrap case, where the checkout records none, and only there do the invocation checkout's own settings matter: unreadable settings stop bootstrap and nothing else; the uncached-target fetch's install runs in the run-owned temporary project and touches no checkout's settings. A record of a cataloged plugin whose target version still has no cache directory after the fetch is reported as unrefreshable, its record untouched, and the exit is nonzero. A failed fetch install stops the run like any other failed operation; the pending-publication carve-out covers selected plugins only, and a plugin whose target version the clone resolves is published. The run never writes the plugin cache itself; the agent's native install does. An empty Codex home receives a disabled `product-tree` declaration. Cache recovery preserves existing activation, including explicit home enablement, and never treats an unchanged marketplace snapshot as proof that each selected plugin cache exists. After execution, native state inspection and declaration comparison establish the selected set, activation, and refreshed or pending status of every selected plugin. Unexpected changes are terminal diagnostics, with no snapshot restoration or compensating activation writes. That postcondition is bounded to the invocation checkout and the selected home, whose bootstrap install and enable are the only operations that write an activation entry; a recorded checkout elsewhere receives the install-record rewrite alone, which touches no settings document, so its settings carry no postcondition. The machine-wide refresh carries its own postcondition read: the plan is built from one install-record listing taken in preflight, and after execution the run takes a second listing and compares every project- or local-scope record of a cataloged plugin with the target, reporting each record's version before and after and exiting nonzero when any such record — planned, or written by another session between the two reads — is off the target. The run neither locks the agent's record store nor issues a further update or rewrite; the comparison and the exit code are its complete response. The exit is nonzero when that comparison leaves any record off the target and when the run raises a blocking warning, which is how every condition the comparison cannot reach gets to the exit code: a condition no record carries — a listing entry with no project path or no version, a bootstrap run with no registered clone, an agent whose registration the run withheld, a cataloged plugin whose target version has no cache directory — and a condition a record carries that the comparison has no target to judge, which is a record of a plugin the clone resolves no target version for and every record of a cataloged plugin in a run whose head read resolved no target at all.
  ```

- [x] line 41

  ```text
  old: - An empty persistent selection maps to `spec-tree` plus one warning and disabled activation where no activation is declared; every nonempty selection is valid only when it contains `spec-tree`. The warning is raised from the plan's bootstrap install, so an agent whose bootstrap the run withholds raises none.
  new: - An empty persistent selection maps to `product-tree` plus one warning and disabled activation where no activation is declared; every nonempty selection is valid only when it contains `product-tree`. The warning is raised from the plan's bootstrap install, so an agent whose bootstrap the run withholds raises none.
  ```

- [x] line 73

  ```text
  old: - ALWAYS: empty selection produces only the `spec-tree` bootstrap plan, preserving declared activation and choosing disabled activation when absent; an empty Codex home declares it disabled. The first-install warning is raised from the bootstrap install that plan carries, so an agent whose bootstrap the run withholds raises none.
  new: - ALWAYS: empty selection produces only the `product-tree` bootstrap plan, preserving declared activation and choosing disabled activation when absent; an empty Codex home declares it disabled. The first-install warning is raised from the bootstrap install that plan carries, so an agent whose bootstrap the run withholds raises none.
  ```

### [`spx/43-coding-agents.enabler/21-agent-communication.enabler/21-message-record.adr.md`](spx/43-coding-agents.enabler/21-agent-communication.enabler/21-message-record.adr.md)

- [x] line 7

  ```text
  old: The record is the unit of meaning and the store is the unit of delivery, so the node that owns communication semantics declares the record and the capability that owns the store maps it. The declaration lives in this node's script as named constants because the field names and kinds are values the spec tree declares; the adapter's mapping table carries the same names as its compliance with that declaration, and their agreement is audit evidence under [`spx/12-shipped-scripting.adr.md`](spx/12-shipped-scripting.adr.md), never a second declaration a test could restate. A `__file__`-relative import of the adapter is rejected: [`spx/43-coding-agents.enabler/18-agent-mail.enabler/21-agent-mail-adapter.adr.md`](spx/43-coding-agents.enabler/18-agent-mail.enabler/21-agent-mail-adapter.adr.md) makes `/operate-agent-mail` the owner of all bundled-script access, and a script that reaches across skill directories manufactures the cross-skill path that decision forbids. The script validates the agent-mail `send` result and the Prowl `send` result by the same means, its own field constants over each capability's public result, so both routes are checked the same way and neither route needs a subprocess, a store handle, or a mock.
  new: The record is the unit of meaning and the store is the unit of delivery, so the node that owns communication semantics declares the record and the capability that owns the store maps it. The declaration lives in this node's script as named constants because the field names and kinds are values the product tree declares; the adapter's mapping table carries the same names as its compliance with that declaration, and their agreement is audit evidence under [`spx/12-shipped-scripting.adr.md`](spx/12-shipped-scripting.adr.md), never a second declaration a test could restate. A `__file__`-relative import of the adapter is rejected: [`spx/43-coding-agents.enabler/18-agent-mail.enabler/21-agent-mail-adapter.adr.md`](spx/43-coding-agents.enabler/18-agent-mail.enabler/21-agent-mail-adapter.adr.md) makes `/operate-agent-mail` the owner of all bundled-script access, and a script that reaches across skill directories manufactures the cross-skill path that decision forbids. The script validates the agent-mail `send` result and the Prowl `send` result by the same means, its own field constants over each capability's public result, so both routes are checked the same way and neither route needs a subprocess, a store handle, or a mock.
  ```

## Nodes

Each node the Change's Spec mutations name, by what the rename changes in it. A node's path is given as it reads after the move.

- Nodes whose assertions change: 39
- Nodes whose spec changes only outside its assertions: 25
- Nodes whose spec is unchanged and whose tests, evals, or probes change: 7
- Nodes that change only by moving with `spx/21-spec-tree.enabler`: 48

### `spx/21-spec-tree.enabler` -> `spx/21-product-tree.enabler`

- [x] spec file `spec-tree.md` -> `product-tree.md`
      `product-tree.md` assertions replaced:

- [x] line 19

  ```text
  old: - Given a spec-tree enabler directory, when its contents are listed, then a spec file named `{slug}.md` exists ([test](tests/test_spec_tree.scenario.l1.py))
  new: - Given a product-tree enabler directory, when its contents are listed, then a spec file named `{slug}.md` exists ([test](tests/test_product_tree.scenario.l1.py))
  ```

- [x] line 20

  ```text
  old: - Given a node directory with a numeric prefix, when validated, then the prefix is an integer between 10 and 99 ([test](tests/test_spec_tree.scenario.l1.py))
  new: - Given a node directory with a numeric prefix, when validated, then the prefix is an integer between 10 and 99 ([test](tests/test_product_tree.scenario.l1.py))
  ```

- [x] line 21

  ```text
  old: - Given a test file nested under a consumer `pyproject.toml`, when the marketplace root is detected, then the detector returns the root that also contains the marketplace plugin marker ([test](tests/test_spec_tree.scenario.l1.py))
  new: - Given a test file nested under a consumer `pyproject.toml`, when the marketplace root is detected, then the detector returns the root that also contains the marketplace plugin marker ([test](tests/test_product_tree.scenario.l1.py))
  ```

- [x] line 22

  ```text
  old: - Given a test file outside the marketplace tree, when marketplace root detection exhausts the path, then the detector reports a configuration error ([test](tests/test_spec_tree.scenario.l1.py))
  new: - Given a test file outside the marketplace tree, when marketplace root detection exhausts the path, then the detector reports a configuration error ([test](tests/test_product_tree.scenario.l1.py))
  ```

- [x] line 26

  ```text
  old: - A node directory name matching `{index}-{slug}.{kind}` maps to parsed index, slug, and kind fields ([test](tests/test_spec_tree.mapping.l1.py))
  new: - A node directory name matching `{index}-{slug}.{kind}` maps to parsed index, slug, and kind fields ([test](tests/test_product_tree.mapping.l1.py))
  ```

- [x] line 27

  ```text
  old: - A node directory name outside the node grammar maps to an absent parse result ([test](tests/test_spec_tree.mapping.l1.py))
  new: - A node directory name outside the node grammar maps to an absent parse result ([test](tests/test_product_tree.mapping.l1.py))
  ```

- [x] line 28

  ```text
  old: - A node index maps to valid when it is between 10 and 99 and invalid otherwise ([test](tests/test_spec_tree.mapping.l1.py))
  new: - A node index maps to valid when it is between 10 and 99 and invalid otherwise ([test](tests/test_product_tree.mapping.l1.py))
  ```

- [x] line 29

  ```text
  old: - Formatting a node directory name maps invalid indexes to a rejected operation ([test](tests/test_spec_tree.mapping.l1.py))
  new: - Formatting a node directory name maps invalid indexes to a rejected operation ([test](tests/test_product_tree.mapping.l1.py))
  ```

- [x] line 30

  ```text
  old: - A node directory maps to its `{slug}.md` spec file path ([test](tests/test_spec_tree.mapping.l1.py))
  new: - A node directory maps to its `{slug}.md` spec file path ([test](tests/test_product_tree.mapping.l1.py))
  ```

- [x] line 31

  ```text
  old: - Prepared tree directory traversal maps symlinked duplicate node paths to a single yielded node directory ([test](tests/test_spec_tree.mapping.l1.py))
  new: - Prepared tree directory traversal maps symlinked duplicate node paths to a single yielded node directory ([test](tests/test_product_tree.mapping.l1.py))
  ```

- [x] line 35

  ```text
  old: - Every node directory in the tree contains exactly one spec file matching `{slug}.md` — no orphan directories exist ([test](tests/test_spec_tree.conformance.l1.py))
  new: - Every node directory in the tree contains exactly one spec file matching `{slug}.md` — no orphan directories exist ([test](tests/test_product_tree.conformance.l1.py))
  ```

- [x] line 50

  ```text
  old: - ALWAYS: load complete spec-tree context before any implementation work ([audit])
  new: - ALWAYS: load complete product-tree context before any implementation work ([audit])
  ```

`product-tree.md` other lines replaced:

- [x] line 6

  ```text
  old: # Spec Tree
  new: # Product Tree
  ```

- [x] line 8

  ```text
  old: PROVIDES the Spec Tree methodology — context loading, spec authoring, testing, implementation, and commit workflows
  new: PROVIDES the Product Tree methodology — context loading, spec authoring, testing, implementation, and commit workflows
  ```

Evidence files carrying the term:

- [x] `spx/21-spec-tree.enabler/tests/test_spec_tree.conformance.l1.py` -> `spx/21-product-tree.enabler/tests/test_product_tree.conformance.l1.py` (3 lines)
- [x] `spx/21-spec-tree.enabler/tests/test_spec_tree.mapping.l1.py` -> `spx/21-product-tree.enabler/tests/test_product_tree.mapping.l1.py` (12 lines)
- [x] `spx/21-spec-tree.enabler/tests/test_spec_tree.scenario.l1.py` -> `spx/21-product-tree.enabler/tests/test_product_tree.scenario.l1.py` (10 lines)

### `spx/21-spec-tree.enabler/12-worktree-provisioning.enabler` -> `spx/21-product-tree.enabler/12-worktree-provisioning.enabler`

`worktree-provisioning.md` other lines replaced:

- [x] line 8

  ```text
  old: PROVIDES the `init-worktrees` provisioning flow that classifies a checkout's git layout and brings a single or non-compliant checkout into the bare-repository worktree pool of [`spx/21-spec-tree.enabler/11-repository-layout.pdr.md`](spx/21-spec-tree.enabler/11-repository-layout.pdr.md), pushing every local ref to the remote and carrying a prior checkout's gitignored state across
  new: PROVIDES the `init-worktrees` provisioning flow that classifies a checkout's git layout and brings a single or non-compliant checkout into the bare-repository worktree pool of [`spx/21-product-tree.enabler/11-repository-layout.pdr.md`](spx/21-product-tree.enabler/11-repository-layout.pdr.md), pushing every local ref to the remote and carrying a prior checkout's gitignored state across
  ```

### `spx/21-spec-tree.enabler/13-agent-environment.enabler` -> `spx/21-product-tree.enabler/13-agent-environment.enabler`

`agent-environment.md` assertions replaced:

- [x] line 19

  ```text
  old: - Given the kill switch `SPECTREE_SESSION_HOOK_DISABLED=1`, when the shipped hook command runs, then it exits with a valid empty result and writes nothing — no identity, no claim, no `.spx/` state ([test](tests/test_agent_environment.scenario.l1.py))
  new: - Given the kill switch `PRODUCT_TREE_SESSION_HOOK_DISABLED=1`, when the shipped hook command runs, then it exits with a valid empty result and writes nothing — no identity, no claim, no `.spx/` state ([test](tests/test_agent_environment.scenario.l1.py))
  ```

- [x] line 25

  ```text
  old: - The spec-tree plugin's `hooks.json` declares exactly one hook event — `SessionStart` — whose command delegates to `spx hook run session-start` and names no plugin-shipped script path ([test](tests/test_agent_environment.conformance.l1.py))
  new: - The product-tree plugin's `hooks.json` declares exactly one hook event — `SessionStart` — whose command delegates to `spx hook run session-start` and names no plugin-shipped script path ([test](tests/test_agent_environment.conformance.l1.py))
  ```

- [x] line 29

  ```text
  old: - ALWAYS: the `SessionStart` hook delegates session-identity, project-dir, and worktree-occupancy work to the `spx` CLI hook runner and embeds no `.spx/`, git, transcript, or session logic of its own; on the disabled-or-absent path it exits with a valid empty result, per [`spx/21-spec-tree.enabler/15-hook-state-delegation.adr.md`](spx/21-spec-tree.enabler/15-hook-state-delegation.adr.md) ([audit])
  new: - ALWAYS: the `SessionStart` hook delegates session-identity, project-dir, and worktree-occupancy work to the `spx` CLI hook runner and embeds no `.spx/`, git, transcript, or session logic of its own; on the disabled-or-absent path it exits with a valid empty result, per [`spx/21-product-tree.enabler/15-hook-state-delegation.adr.md`](spx/21-product-tree.enabler/15-hook-state-delegation.adr.md) ([audit])
  ```

`agent-environment.md` other lines replaced:

- [x] line 12

  ```text
  old: The spec-tree plugin's only runtime hook is a `SessionStart` hook that delegates to the `spx` CLI hook runner — `spx hook run <hook-name-kebab-case>`, here `spx hook run session-start` — through a hook-safety-compliant inline guard. On the normal path the `spx` hook runner delivers the session environment: it writes the agent session identity and project directories into the harness-provided `$CLAUDE_ENV_FILE` and records the worktree-occupancy claim. On the disabled-or-absent path the guard exits with a valid empty result and writes nothing. The plugin owns only the hook's wiring and its fail-open guard; it embeds no `.spx/`, git, transcript, or session logic of its own, per [`spx/21-spec-tree.enabler/15-hook-state-delegation.adr.md`](spx/21-spec-tree.enabler/15-hook-state-delegation.adr.md) and [`spx/15-hook-safety.pdr.md`](spx/15-hook-safety.pdr.md). The identity's distinctness and the per-session directory the `spx` CLI realizes are its own contract, verified by its suite; this node verifies the plugin's integration with it. This node holds the hook-wide constraint that spans its children.
  new: The product-tree plugin's only runtime hook is a `SessionStart` hook that delegates to the `spx` CLI hook runner — `spx hook run <hook-name-kebab-case>`, here `spx hook run session-start` — through a hook-safety-compliant inline guard. On the normal path the `spx` hook runner delivers the session environment: it writes the agent session identity and project directories into the harness-provided `$CLAUDE_ENV_FILE` and records the worktree-occupancy claim. On the disabled-or-absent path the guard exits with a valid empty result and writes nothing. The plugin owns only the hook's wiring and its fail-open guard; it embeds no `.spx/`, git, transcript, or session logic of its own, per [`spx/21-product-tree.enabler/15-hook-state-delegation.adr.md`](spx/21-product-tree.enabler/15-hook-state-delegation.adr.md) and [`spx/15-hook-safety.pdr.md`](spx/15-hook-safety.pdr.md). The identity's distinctness and the per-session directory the `spx` CLI realizes are its own contract, verified by its suite; this node verifies the plugin's integration with it. This node holds the hook-wide constraint that spans its children.
  ```

Evidence files carrying the term:

- [x] `spx/21-spec-tree.enabler/13-agent-environment.enabler/tests/test_agent_environment.conformance.l1.py` -> `spx/21-product-tree.enabler/13-agent-environment.enabler/tests/test_agent_environment.conformance.l1.py` (1 lines)

### `spx/21-spec-tree.enabler/13-agent-environment.enabler/21-identity.enabler` -> `spx/21-product-tree.enabler/13-agent-environment.enabler/21-identity.enabler`

`identity.md` other lines replaced:

- [x] line 12

  ```text
  old: The scenario, property, and mapping assertions below verify the `$CLAUDE_SESSION_ID` env-file export the `spx` hook runner writes at the pinned floor; consumers never resolve identity from that export — the compliance assertions name the agent-published variables they read. `spx/21-spec-tree.enabler/13-agent-environment.enabler/ISSUES.md` records the export's retirement, gated on the published `spx` floor advancing past the removal.
  new: The scenario, property, and mapping assertions below verify the `$CLAUDE_SESSION_ID` env-file export the `spx` hook runner writes at the pinned floor; consumers never resolve identity from that export — the compliance assertions name the agent-published variables they read. `spx/21-product-tree.enabler/13-agent-environment.enabler/ISSUES.md` records the export's retirement, gated on the published `spx` floor advancing past the removal.
  ```

### `spx/21-spec-tree.enabler/13-infrastructure.enabler` -> `spx/21-product-tree.enabler/13-infrastructure.enabler`

`infrastructure.md` other lines replaced:

- [x] line 9

  ```text
  old: SO THAT spec-tree methodology skills and downstream language plugins
  new: SO THAT product-tree methodology skills and downstream language plugins
  ```

### `spx/21-spec-tree.enabler/13-infrastructure.enabler/21-github-actions.enabler` -> `spx/21-product-tree.enabler/13-infrastructure.enabler/21-github-actions.enabler`

`github-actions.md` other lines replaced:

- [x] line 9

  ```text
  old: SO THAT spec-tree plugin users and marketplace maintainers
  new: SO THAT product-tree plugin users and marketplace maintainers
  ```

### `spx/21-spec-tree.enabler/13-infrastructure.enabler/21-github-actions.enabler/32-workflow-observability.enabler` -> `spx/21-product-tree.enabler/13-infrastructure.enabler/21-github-actions.enabler/32-workflow-observability.enabler`

Evidence files carrying the term:

- [x] `spx/21-spec-tree.enabler/13-infrastructure.enabler/21-github-actions.enabler/32-workflow-observability.enabler/tests/test_workflow_observability.compliance.l1.py` -> `spx/21-product-tree.enabler/13-infrastructure.enabler/21-github-actions.enabler/32-workflow-observability.enabler/tests/test_workflow_observability.compliance.l1.py` (2 lines)
- [x] `spx/21-spec-tree.enabler/13-infrastructure.enabler/21-github-actions.enabler/32-workflow-observability.enabler/tests/test_workflow_observability.property.l1.py` -> `spx/21-product-tree.enabler/13-infrastructure.enabler/21-github-actions.enabler/32-workflow-observability.enabler/tests/test_workflow_observability.property.l1.py` (2 lines)
- [x] `spx/21-spec-tree.enabler/13-infrastructure.enabler/21-github-actions.enabler/32-workflow-observability.enabler/tests/test_workflow_observability.scenario.l1.py` -> `spx/21-product-tree.enabler/13-infrastructure.enabler/21-github-actions.enabler/32-workflow-observability.enabler/tests/test_workflow_observability.scenario.l1.py` (2 lines)
- [x] `spx/21-spec-tree.enabler/13-infrastructure.enabler/21-github-actions.enabler/32-workflow-observability.enabler/tests/test_workflow_observability.scenario.l3.py` -> `spx/21-product-tree.enabler/13-infrastructure.enabler/21-github-actions.enabler/32-workflow-observability.enabler/tests/test_workflow_observability.scenario.l3.py` (2 lines)

### `spx/21-spec-tree.enabler/13-infrastructure.enabler/21-github-actions.enabler/32-workflow-safety.enabler` -> `spx/21-product-tree.enabler/13-infrastructure.enabler/21-github-actions.enabler/32-workflow-safety.enabler`

`workflow-safety.md` assertions replaced:

- [x] line 23

  ```text
  old: - NEVER: keep generic Claude caller workflows (`claude.yml`, `claude-code-review.yml`) active in this repository's `.github/workflows/` directory alongside the spec-tree callers — duplicate agent workflows spend tokens for the same issue and pull-request events ([test](tests/test_workflow_safety.compliance.l1.py))
  new: - NEVER: keep generic Claude caller workflows (`claude.yml`, `claude-code-review.yml`) active in this repository's `.github/workflows/` directory alongside the product-tree callers — duplicate agent workflows spend tokens for the same issue and pull-request events ([test](tests/test_workflow_safety.compliance.l1.py))
  ```

### `spx/21-spec-tree.enabler/13-infrastructure.enabler/21-github-actions.enabler/54-runtime-operations.enabler` -> `spx/21-product-tree.enabler/13-infrastructure.enabler/21-github-actions.enabler/54-runtime-operations.enabler`

`runtime-operations.md` assertions replaced:

- [x] line 21

  ```text
  old: - ALWAYS: a failure diagnosis names the local Spec Tree or repository command that verifies the same concern when the repository provides one — local-runnable equivalents make the failure reproducible without GitHub ([audit])
  new: - ALWAYS: a failure diagnosis names the local Product Tree or repository command that verifies the same concern when the repository provides one — local-runnable equivalents make the failure reproducible without GitHub ([audit])
  ```

### `spx/21-spec-tree.enabler/14-version-control.enabler/32-sync-base.enabler` -> `spx/21-product-tree.enabler/14-version-control.enabler/32-sync-base.enabler`

`sync-base.md` assertions replaced:

- [x] line 43

  ```text
  old: - NEVER: the synchronization primitive brings a behind-base branch current with `git reset` in any mode — it rebases, preserving the branch's commits, per [`spx/21-spec-tree.enabler/14-version-control.enabler/32-sync-base.enabler/13-base-sync-mechanism.adr.md`](spx/21-spec-tree.enabler/14-version-control.enabler/32-sync-base.enabler/13-base-sync-mechanism.adr.md) ([test](tests/test_sync_base.compliance.l1.py))
  new: - NEVER: the synchronization primitive brings a behind-base branch current with `git reset` in any mode — it rebases, preserving the branch's commits, per [`spx/21-product-tree.enabler/14-version-control.enabler/32-sync-base.enabler/13-base-sync-mechanism.adr.md`](spx/21-product-tree.enabler/14-version-control.enabler/32-sync-base.enabler/13-base-sync-mechanism.adr.md) ([test](tests/test_sync_base.compliance.l1.py))
  ```

- [x] line 45

  ```text
  old: - NEVER: the synchronization primitive commits or stashes the working tree, aborts a conflicted rebase at operator handoff, or surfaces a dirty tree as a conflict — a dirty tree is a distinct precondition the skill resolves through the commit workflow, per [`spx/21-spec-tree.enabler/14-version-control.enabler/32-sync-base.enabler/13-base-sync-mechanism.adr.md`](spx/21-spec-tree.enabler/14-version-control.enabler/32-sync-base.enabler/13-base-sync-mechanism.adr.md) ([test](tests/test_sync_base.compliance.l1.py))
  new: - NEVER: the synchronization primitive commits or stashes the working tree, aborts a conflicted rebase at operator handoff, or surfaces a dirty tree as a conflict — a dirty tree is a distinct precondition the skill resolves through the commit workflow, per [`spx/21-product-tree.enabler/14-version-control.enabler/32-sync-base.enabler/13-base-sync-mechanism.adr.md`](spx/21-product-tree.enabler/14-version-control.enabler/32-sync-base.enabler/13-base-sync-mechanism.adr.md) ([test](tests/test_sync_base.compliance.l1.py))
  ```

- [x] line 46

  ```text
  old: - ALWAYS: `src/plugins/spec-tree/skills/sync-base/SKILL.md` assigns authorized dirty-tree recovery to `/sync-base`: objective work stays on its owning branch, unrelated coordination work follows its own merge route, and `/commit-changes` owns checkpoint policy and proof of success before the primitive is retried within the same invocation ([audit])
  new: - ALWAYS: `src/plugins/product-tree/skills/sync-base/SKILL.md` assigns authorized dirty-tree recovery to `/sync-base`: objective work stays on its owning branch, unrelated coordination work follows its own merge route, and `/commit-changes` owns checkpoint policy and proof of success before the primitive is retried within the same invocation ([audit])
  ```

- [x] line 50

  ```text
  old: - ALWAYS: `src/plugins/spec-tree/skills/sync-base/SKILL.md` finishes a conflicted rebase by default and, when another route takes less work or evidence cannot decide product intent, sends its superior an assessment with a recommended route and acts on the superior's decision; it aborts a rebase only on that decision and never ends its work with a rebase active and no decision asked, per [`spx/21-spec-tree.enabler/14-version-control.enabler/32-sync-base.enabler/13-base-sync-mechanism.adr.md`](spx/21-spec-tree.enabler/14-version-control.enabler/32-sync-base.enabler/13-base-sync-mechanism.adr.md) ([audit])
  new: - ALWAYS: `src/plugins/product-tree/skills/sync-base/SKILL.md` finishes a conflicted rebase by default and, when another route takes less work or evidence cannot decide product intent, sends its superior an assessment with a recommended route and acts on the superior's decision; it aborts a rebase only on that decision and never ends its work with a rebase active and no decision asked, per [`spx/21-product-tree.enabler/14-version-control.enabler/32-sync-base.enabler/13-base-sync-mechanism.adr.md`](spx/21-product-tree.enabler/14-version-control.enabler/32-sync-base.enabler/13-base-sync-mechanism.adr.md) ([audit])
  ```

- [x] line 51

  ```text
  old: - ALWAYS: the synchronization primitive brings a clean detached HEAD whose commit is an ancestor of the fetched base current by advancing the worktree to `origin/<base>`, never waving it through as a hard failure, per [`spx/21-spec-tree.enabler/14-version-control.enabler/32-sync-base.enabler/13-base-sync-mechanism.adr.md`](spx/21-spec-tree.enabler/14-version-control.enabler/32-sync-base.enabler/13-base-sync-mechanism.adr.md) ([test](tests/test_sync_base.compliance.l1.py))
  new: - ALWAYS: the synchronization primitive brings a clean detached HEAD whose commit is an ancestor of the fetched base current by advancing the worktree to `origin/<base>`, never waving it through as a hard failure, per [`spx/21-product-tree.enabler/14-version-control.enabler/32-sync-base.enabler/13-base-sync-mechanism.adr.md`](spx/21-product-tree.enabler/14-version-control.enabler/32-sync-base.enabler/13-base-sync-mechanism.adr.md) ([test](tests/test_sync_base.compliance.l1.py))
  ```

- [x] line 53

  ```text
  old: - NEVER: the synchronization primitive advances a diverged detached HEAD — one carrying commits the base lacks — it reports `git_failure` and preserves those commits rather than orphaning them, per [`spx/21-spec-tree.enabler/14-version-control.enabler/32-sync-base.enabler/13-base-sync-mechanism.adr.md`](spx/21-spec-tree.enabler/14-version-control.enabler/32-sync-base.enabler/13-base-sync-mechanism.adr.md) ([test](tests/test_sync_base.compliance.l1.py))
  new: - NEVER: the synchronization primitive advances a diverged detached HEAD — one carrying commits the base lacks — it reports `git_failure` and preserves those commits rather than orphaning them, per [`spx/21-product-tree.enabler/14-version-control.enabler/32-sync-base.enabler/13-base-sync-mechanism.adr.md`](spx/21-product-tree.enabler/14-version-control.enabler/32-sync-base.enabler/13-base-sync-mechanism.adr.md) ([test](tests/test_sync_base.compliance.l1.py))
  ```

- [x] line 54

  ```text
  old: - ALWAYS: the readiness-preservation proof carries a schema version and reports the old and new base and branch OIDs as full unabbreviated hashes, and carries no project-specific validation-lane name — lane mapping is the project overlay's, per [`spx/21-spec-tree.enabler/14-version-control.enabler/32-sync-base.enabler/13-base-sync-mechanism.adr.md`](spx/21-spec-tree.enabler/14-version-control.enabler/32-sync-base.enabler/13-base-sync-mechanism.adr.md) ([test](tests/test_sync_base_preservation.compliance.l1.py))
  new: - ALWAYS: the readiness-preservation proof carries a schema version and reports the old and new base and branch OIDs as full unabbreviated hashes, and carries no project-specific validation-lane name — lane mapping is the project overlay's, per [`spx/21-product-tree.enabler/14-version-control.enabler/32-sync-base.enabler/13-base-sync-mechanism.adr.md`](spx/21-product-tree.enabler/14-version-control.enabler/32-sync-base.enabler/13-base-sync-mechanism.adr.md) ([test](tests/test_sync_base_preservation.compliance.l1.py))
  ```

### `spx/21-spec-tree.enabler/16-verification.enabler` -> `spx/21-product-tree.enabler/16-verification.enabler`

`verification.md` assertions replaced:

- [x] line 18

  ```text
  old: - ALWAYS: a run finished with one or more units marked unread seals `failed`, and its terminal event lists each unread unit, per [`spx/21-spec-tree.enabler/16-verification.enabler/13-run-journal.adr.md`](spx/21-spec-tree.enabler/16-verification.enabler/13-run-journal.adr.md) ([test](tests/test_unread_scope.compliance.l1.py))
  new: - ALWAYS: a run finished with one or more units marked unread seals `failed`, and its terminal event lists each unread unit, per [`spx/21-product-tree.enabler/16-verification.enabler/13-run-journal.adr.md`](spx/21-product-tree.enabler/16-verification.enabler/13-run-journal.adr.md) ([test](tests/test_unread_scope.compliance.l1.py))
  ```

- [x] line 19

  ```text
  old: - NEVER: a run seals approved while a unit of its scope carries no scope-advanced event or is marked unread, per [`spx/21-spec-tree.enabler/16-verification.enabler/13-run-journal.adr.md`](spx/21-spec-tree.enabler/16-verification.enabler/13-run-journal.adr.md) ([test](tests/test_unread_scope.compliance.l1.py))
  new: - NEVER: a run seals approved while a unit of its scope carries no scope-advanced event or is marked unread, per [`spx/21-product-tree.enabler/16-verification.enabler/13-run-journal.adr.md`](spx/21-product-tree.enabler/16-verification.enabler/13-run-journal.adr.md) ([test](tests/test_unread_scope.compliance.l1.py))
  ```

- [x] line 33

  ```text
  old: - ALWAYS: a thin wrapper agent under `src/plugins/spec-tree/agents/` drives each agentic verification skill, holds no verification or I/O policy, and declares an explicit non-inherited verification model plus its required skill set; target conversion emits each runtime's native model, sandbox, tool, and skill-enablement configuration ([audit])
  new: - ALWAYS: a thin wrapper agent under `src/plugins/product-tree/agents/` drives each agentic verification skill, holds no verification or I/O policy, and declares an explicit non-inherited verification model plus its required skill set; target conversion emits each runtime's native model, sandbox, tool, and skill-enablement configuration ([audit])
  ```

- [x] line 34

  ```text
  old: - ALWAYS: every agentic verification skill derives its changeset scope through the shared changeset-scope primitives (`spx/21-spec-tree.enabler/14-version-control.enabler/15-changeset-scope.enabler/changeset-scope.md`) ([audit])
  new: - ALWAYS: every agentic verification skill derives its changeset scope through the shared changeset-scope primitives (`spx/21-product-tree.enabler/14-version-control.enabler/15-changeset-scope.enabler/changeset-scope.md`) ([audit])
  ```

`verification.md` other lines replaced:

- [x] line 14

  ```text
  old: The six verification types and the two axes that classify them — verdict mode and purpose — are declared in the inline `/understand` `<verification_model>` and grounded for this product in [`spx/31-outcomeeng.enabler/31-verification.enabler/14-verification.pdr.md`](spx/31-outcomeeng.enabler/31-verification.enabler/14-verification.pdr.md). This enabler is the home of the agentic types' shared architecture, decided in [`spx/21-spec-tree.enabler/16-verification.enabler/13-run-journal.adr.md`](spx/21-spec-tree.enabler/16-verification.enabler/13-run-journal.adr.md); review and audit implement it.
  new: The six verification types and the two axes that classify them — verdict mode and purpose — are declared in the inline `/understand` `<verification_model>` and grounded for this product in [`spx/31-outcomeeng.enabler/31-verification.enabler/14-verification.pdr.md`](spx/31-outcomeeng.enabler/31-verification.enabler/14-verification.pdr.md). This enabler is the home of the agentic types' shared architecture, decided in [`spx/21-product-tree.enabler/16-verification.enabler/13-run-journal.adr.md`](spx/21-product-tree.enabler/16-verification.enabler/13-run-journal.adr.md); review and audit implement it.
  ```

- [x] line 23

  ```text
  old: Each rule enforces a guarantee of [`spx/21-spec-tree.enabler/16-verification.enabler/13-run-journal.adr.md`](spx/21-spec-tree.enabler/16-verification.enabler/13-run-journal.adr.md).
  new: Each rule enforces a guarantee of [`spx/21-product-tree.enabler/16-verification.enabler/13-run-journal.adr.md`](spx/21-product-tree.enabler/16-verification.enabler/13-run-journal.adr.md).
  ```

Evidence files carrying the term:

- [x] `spx/21-spec-tree.enabler/16-verification.enabler/tests/test_agent_model_field.mapping.l1.py` -> `spx/21-product-tree.enabler/16-verification.enabler/tests/test_agent_model_field.mapping.l1.py` (4 lines)

### `spx/21-spec-tree.enabler/16-verification.enabler/15-verdict-toolchain.enabler` -> `spx/21-product-tree.enabler/16-verification.enabler/15-verdict-toolchain.enabler`

`verdict-toolchain.md` assertions replaced:

- [x] line 21

  ```text
  old: - NEVER: the spec-tree plugin ships `verdict.py`, `aggregate_verdicts.py`, `pass_results.py`, `journal_emit.py`, or `audit_orchestrator.py` under the audit skill ([test](tests/test_verification_run_payload_contract.compliance.l1.py))
  new: - NEVER: the product-tree plugin ships `verdict.py`, `aggregate_verdicts.py`, `pass_results.py`, `journal_emit.py`, or `audit_orchestrator.py` under the audit skill ([test](tests/test_verification_run_payload_contract.compliance.l1.py))
  ```

### `spx/21-spec-tree.enabler/16-verification.enabler/18-journal-projection.enabler` -> `spx/21-product-tree.enabler/16-verification.enabler/18-journal-projection.enabler`

`journal-projection.md` assertions replaced:

- [x] line 28

  ```text
  old: - NEVER: the projection exposes a builder that emits a whole run's events from a finished result — it offers one builder per domain event so the consuming skill appends each as the run advances, never a batch dump, per [`spx/21-spec-tree.enabler/16-verification.enabler/13-run-journal.adr.md`](spx/21-spec-tree.enabler/16-verification.enabler/13-run-journal.adr.md) ([audit])
  new: - NEVER: the projection exposes a builder that emits a whole run's events from a finished result — it offers one builder per domain event so the consuming skill appends each as the run advances, never a batch dump, per [`spx/21-product-tree.enabler/16-verification.enabler/13-run-journal.adr.md`](spx/21-product-tree.enabler/16-verification.enabler/13-run-journal.adr.md) ([audit])
  ```

### `spx/21-spec-tree.enabler/18-context-loading.enabler` -> `spx/21-product-tree.enabler/18-context-loading.enabler`

`context-loading.md` assertions replaced:

- [x] line 16

  ```text
  old: - The spec-tree plugin package ships the foundation-resource manifest governed by [`spx/21-spec-tree.enabler/18-context-loading.enabler/15-foundation-manifest.adr.md`](spx/21-spec-tree.enabler/18-context-loading.enabler/15-foundation-manifest.adr.md) at `skills/understand/manifest.json` in every generated tree, naming exactly one core foundation document and the ordered references, templates, and examples catalogs as package-relative paths ([test](tests/test_foundation_manifest.conformance.l1.py))
  new: - The product-tree plugin package ships the foundation-resource manifest governed by [`spx/21-product-tree.enabler/18-context-loading.enabler/15-foundation-manifest.adr.md`](spx/21-product-tree.enabler/18-context-loading.enabler/15-foundation-manifest.adr.md) at `skills/understand/manifest.json` in every generated tree, naming exactly one core foundation document and the ordered references, templates, and examples catalogs as package-relative paths ([test](tests/test_foundation_manifest.conformance.l1.py))
  ```

- [x] line 17

  ```text
  old: - NEVER: the authored foundation-resource manifest and its generated-tree copies diverge, per [`spx/21-spec-tree.enabler/18-context-loading.enabler/15-foundation-manifest.adr.md`](spx/21-spec-tree.enabler/18-context-loading.enabler/15-foundation-manifest.adr.md) ([test](tests/test_foundation_manifest.conformance.l1.py))
  new: - NEVER: the authored foundation-resource manifest and its generated-tree copies diverge, per [`spx/21-product-tree.enabler/18-context-loading.enabler/15-foundation-manifest.adr.md`](spx/21-product-tree.enabler/18-context-loading.enabler/15-foundation-manifest.adr.md) ([test](tests/test_foundation_manifest.conformance.l1.py))
  ```

- [x] line 26

  ```text
  old: - NEVER: the foundation-resource manifest carries content beyond paths and schema metadata, per [`spx/21-spec-tree.enabler/18-context-loading.enabler/15-foundation-manifest.adr.md`](spx/21-spec-tree.enabler/18-context-loading.enabler/15-foundation-manifest.adr.md) — package checks reject a content-bearing field ([test](tests/test_foundation_manifest.compliance.l1.py))
  new: - NEVER: the foundation-resource manifest carries content beyond paths and schema metadata, per [`spx/21-product-tree.enabler/18-context-loading.enabler/15-foundation-manifest.adr.md`](spx/21-product-tree.enabler/18-context-loading.enabler/15-foundation-manifest.adr.md) — package checks reject a content-bearing field ([test](tests/test_foundation_manifest.compliance.l1.py))
  ```

- [x] line 27

  ```text
  old: - ALWAYS: a foundation-resource manifest shape change within a schema version is additive, and a breaking shape change increments `schema_version`, per [`spx/21-spec-tree.enabler/18-context-loading.enabler/15-foundation-manifest.adr.md`](spx/21-spec-tree.enabler/18-context-loading.enabler/15-foundation-manifest.adr.md) ([audit])
  new: - ALWAYS: a foundation-resource manifest shape change within a schema version is additive, and a breaking shape change increments `schema_version`, per [`spx/21-product-tree.enabler/18-context-loading.enabler/15-foundation-manifest.adr.md`](spx/21-product-tree.enabler/18-context-loading.enabler/15-foundation-manifest.adr.md) ([audit])
  ```

- [x] line 28

  ```text
  old: - ALWAYS: the `/contextualize` skill brings a behind-base branch current through sync-base (`spx/21-spec-tree.enabler/14-version-control.enabler/32-sync-base.enabler/sync-base.md`) before reading product or spec context, so loaded context reflects current product truth rather than a stale branch ([audit])
  new: - ALWAYS: the `/contextualize` skill brings a behind-base branch current through sync-base (`spx/21-product-tree.enabler/14-version-control.enabler/32-sync-base.enabler/sync-base.md`) before reading product or spec context, so loaded context reflects current product truth rather than a stale branch ([audit])
  ```

- [x] line 33

  ```text
  old: - ALWAYS: the `/contextualize` skill derives the target read-set from the deterministic enumeration decided in [`spx/21-spec-tree.enabler/18-context-loading.enabler/13-context-enumeration.adr.md`](spx/21-spec-tree.enabler/18-context-loading.enabler/13-context-enumeration.adr.md), reads the ordered read-set in its enumerated order, reads the guides and the lifecycle overlay outside that order, and lists the remaining local overlays without reading them ([audit])
  new: - ALWAYS: the `/contextualize` skill derives the target read-set from the deterministic enumeration decided in [`spx/21-product-tree.enabler/18-context-loading.enabler/13-context-enumeration.adr.md`](spx/21-product-tree.enabler/18-context-loading.enabler/13-context-enumeration.adr.md), reads the ordered read-set in its enumerated order, reads the guides and the lifecycle overlay outside that order, and lists the remaining local overlays without reading them ([audit])
  ```

- [x] line 34

  ```text
  old: - ALWAYS: the `/contextualize` context manifest states the methodology source and exact version the repository follows, taken from the `methodology` block of the SPX CLI's context bundle (`spx spec context show --json`), so every session applies the declared methodology and its rules for the node under work, per [`spx/21-spec-tree.enabler/18-context-loading.enabler/13-context-enumeration.adr.md`](spx/21-spec-tree.enabler/18-context-loading.enabler/13-context-enumeration.adr.md) ([audit])
  new: - ALWAYS: the `/contextualize` context manifest states the methodology source and exact version the repository follows, taken from the `methodology` block of the SPX CLI's context bundle (`spx spec context show --json`), so every session applies the declared methodology and its rules for the node under work, per [`spx/21-product-tree.enabler/18-context-loading.enabler/13-context-enumeration.adr.md`](spx/21-product-tree.enabler/18-context-loading.enabler/13-context-enumeration.adr.md) ([audit])
  ```

- [x] line 44

  ```text
  old: - ALWAYS: the `/contextualize` skill treats the `SPEC_TREE_FOUNDATION` marker as absent after every compaction event until `/understand` re-emits it in the resuming conversation ([audit])
  new: - ALWAYS: the `/contextualize` skill treats the `PRODUCT_TREE_FOUNDATION` marker as absent after every compaction event until `/understand` re-emits it in the resuming conversation ([audit])
  ```

- [x] line 45

  ```text
  old: - ALWAYS: the `/contextualize` skill requires a live `SPEC_TREE_FOUNDATION` marker before direct filesystem access to any path under `spx/`, or before reading, searching, listing, or changing any other product content — source or test files, generated output, evals, spec-declared configuration; operational-state commands under `spx session`, `spx worktree status`, `spx diagnose`, and no-patch Git status, history, and topology, and a skill's read of the `spx/local/` overlay or the passing-scope list it declares, remain available without the marker until their output is followed into product content ([audit])
  new: - ALWAYS: the `/contextualize` skill requires a live `PRODUCT_TREE_FOUNDATION` marker before direct filesystem access to any path under `spx/`, or before reading, searching, listing, or changing any other product content — source or test files, generated output, evals, spec-declared configuration; operational-state commands under `spx session`, `spx worktree status`, `spx diagnose`, and no-patch Git status, history, and topology, and a skill's read of the `spx/local/` overlay or the passing-scope list it declares, remain available without the marker until their output is followed into product content ([audit])
  ```

- [x] line 50

  ```text
  old: - NEVER: the `/contextualize` skill accepts a `SPEC_TREE_FOUNDATION` mention in a compaction summary, Handoff, prior-run description, or statement that `/understand` ran as evidence that the marker is live ([audit])
  new: - NEVER: the `/contextualize` skill accepts a `PRODUCT_TREE_FOUNDATION` mention in a compaction summary, Handoff, prior-run description, or statement that `/understand` ran as evidence that the marker is live ([audit])
  ```

Evidence files carrying the term:

- [x] `spx/21-spec-tree.enabler/18-context-loading.enabler/tests/test_foundation_manifest.conformance.l1.py` -> `spx/21-product-tree.enabler/18-context-loading.enabler/tests/test_foundation_manifest.conformance.l1.py` (4 lines)

### `spx/21-spec-tree.enabler/19-worktree-occupancy.enabler` -> `spx/21-product-tree.enabler/19-worktree-occupancy.enabler`

`worktree-occupancy.md` assertions replaced:

- [x] line 23

  ```text
  old: - ALWAYS: the spec-tree plugin's `SessionStart` hook records the worktree-occupancy claim by delegating to `spx hook run session-start` (`spx/21-spec-tree.enabler/13-agent-environment.enabler/`); the hook embeds no claim logic of its own ([audit])
  new: - ALWAYS: the product-tree plugin's `SessionStart` hook records the worktree-occupancy claim by delegating to `spx hook run session-start` (`spx/21-product-tree.enabler/13-agent-environment.enabler/`); the hook embeds no claim logic of its own ([audit])
  ```

`worktree-occupancy.md` other lines replaced:

- [x] line 12

  ```text
  old: The `SessionStart` hook records the running session's worktree-occupancy claim by delegating to `spx hook run session-start`; `claim-change` then brings a Handoff's work branch into that assigned, hook-claimed worktree, reading occupancy through `spx worktree status` only as a read-only check and recording no claim of its own, and `release-change` preserves the live runtime claim while freeing the Git branch by stepping the checkout off it after the push. These surfaces reach occupancy entirely through the `spx` CLI and never read or write the `.spx/worktrees/` claim store directly. How `spx` records a claim and decides whether a worktree is held by a live agent is `spx`'s concern, specified in the `spx` CLI's own spec tree; this node specifies only the plugins' use of that capability. The assigned-worktree discipline the Lifecycle skills follow — each agent conducts its git work in the assigned, hook-claimed worktree, never entering or creating another — is governed by [`spx/15-merging.pdr.md`](spx/15-merging.pdr.md), and the hook's claim delegation by `spx/21-spec-tree.enabler/13-agent-environment.enabler/` and [`spx/21-spec-tree.enabler/15-hook-state-delegation.adr.md`](spx/21-spec-tree.enabler/15-hook-state-delegation.adr.md). The bare-repository pool these skills operate within is governed by [`spx/21-spec-tree.enabler/11-repository-layout.pdr.md`](spx/21-spec-tree.enabler/11-repository-layout.pdr.md) and provisioned by `spx/21-spec-tree.enabler/12-worktree-provisioning.enabler`.
  new: The `SessionStart` hook records the running session's worktree-occupancy claim by delegating to `spx hook run session-start`; `claim-change` then brings a Handoff's work branch into that assigned, hook-claimed worktree, reading occupancy through `spx worktree status` only as a read-only check and recording no claim of its own, and `release-change` preserves the live runtime claim while freeing the Git branch by stepping the checkout off it after the push. These surfaces reach occupancy entirely through the `spx` CLI and never read or write the `.spx/worktrees/` claim store directly. How `spx` records a claim and decides whether a worktree is held by a live agent is `spx`'s concern, specified in the `spx` CLI's own product tree; this node specifies only the plugins' use of that capability. The assigned-worktree discipline the Lifecycle skills follow — each agent conducts its git work in the assigned, hook-claimed worktree, never entering or creating another — is governed by [`spx/15-merging.pdr.md`](spx/15-merging.pdr.md), and the hook's claim delegation by `spx/21-product-tree.enabler/13-agent-environment.enabler/` and [`spx/21-product-tree.enabler/15-hook-state-delegation.adr.md`](spx/21-product-tree.enabler/15-hook-state-delegation.adr.md). The bare-repository pool these skills operate within is governed by [`spx/21-product-tree.enabler/11-repository-layout.pdr.md`](spx/21-product-tree.enabler/11-repository-layout.pdr.md) and provisioned by `spx/21-product-tree.enabler/12-worktree-provisioning.enabler`.
  ```

### `spx/21-spec-tree.enabler/21-templates.enabler` -> `spx/21-product-tree.enabler/21-templates.enabler`

`templates.md` other lines replaced:

- [x] line 8

  ```text
  old: PROVIDES the artifact type templates — product spec, ADR, PDR, the five output-kind specs, the variant spec, the outcome record, and the probe protocol — that define what each spec-tree artifact must contain
  new: PROVIDES the artifact type templates — product spec, ADR, PDR, the five output-kind specs, the variant spec, the outcome record, and the probe protocol — that define what each product-tree artifact must contain
  ```

### `spx/21-spec-tree.enabler/32-decisions.enabler` -> `spx/21-product-tree.enabler/32-decisions.enabler`

`decisions.md` other lines replaced:

- [x] line 9

  ```text
  old: SO THAT all spec-tree projects
  new: SO THAT all product-tree projects
  ```

### `spx/21-spec-tree.enabler/32-decisions.enabler/21-adr-auditing.enabler` -> `spx/21-product-tree.enabler/32-decisions.enabler/21-adr-auditing.enabler`

`adr-auditing.md` other lines replaced:

- [x] line 9

  ```text
  old: SO THAT all spec-tree projects
  new: SO THAT all product-tree projects
  ```

- [x] line 22

  ```text
  old: Section structure, atemporal voice, and tag validity are judged from the canonical decision template (`spx/21-spec-tree.enabler/21-templates.enabler`), never a transcribed copy of it. Language-specific ADR concerns — testability-in-Verification (dependency injection, no-mocking), execution-level accuracy — are composed by invoking `audit-{lang}-architecture` for the language detected in scope; that skill carries only those language-specific concerns and never re-judges structure, voice, or tags.
  new: Section structure, atemporal voice, and tag validity are judged from the canonical decision template (`spx/21-product-tree.enabler/21-templates.enabler`), never a transcribed copy of it. Language-specific ADR concerns — testability-in-Verification (dependency injection, no-mocking), execution-level accuracy — are composed by invoking `audit-{lang}-architecture` for the language detected in scope; that skill carries only those language-specific concerns and never re-judges structure, voice, or tags.
  ```

- [x] line 26

  ```text
  old: A `### Testing` rule's assertion-type tag is chosen from the rule's claim shape via `/test` after `/verify` selects test (see `spx/21-spec-tree.enabler/35-evidence.enabler/evidence.md`). `/test` selects the assertion type; the audit verifies the selection is correct against the claim's shape — the decisive check is the quantifier: a universal claim (ALWAYS/NEVER) is never `scenario`, because a scenario proves one case and cannot establish a claim about every case. The audit does not relitigate a choice the router leaves open between equally-valid types. A missing tag inside a routed subsection, a bare mechanism tag (`[review]`/`[test]`), a tag that disagrees with its subsection, more than one tag, or an assertion type the `/test` router would not produce for the claim is a finding. Untagged rules directly under `## Verification` receive declaration-quality checks without a missing-tag finding; their approval establishes no evidence result.
  new: A `### Testing` rule's assertion-type tag is chosen from the rule's claim shape via `/test` after `/verify` selects test (see `spx/21-product-tree.enabler/35-evidence.enabler/evidence.md`). `/test` selects the assertion type; the audit verifies the selection is correct against the claim's shape — the decisive check is the quantifier: a universal claim (ALWAYS/NEVER) is never `scenario`, because a scenario proves one case and cannot establish a claim about every case. The audit does not relitigate a choice the router leaves open between equally-valid types. A missing tag inside a routed subsection, a bare mechanism tag (`[review]`/`[test]`), a tag that disagrees with its subsection, more than one tag, or an assertion type the `/test` router would not produce for the claim is a finding. Untagged rules directly under `## Verification` receive declaration-quality checks without a missing-tag finding; their approval establishes no evidence result.
  ```

Evidence files carrying the term:

- [x] `spx/21-spec-tree.enabler/32-decisions.enabler/21-adr-auditing.enabler/evals/structure/eval.toml` -> `spx/21-product-tree.enabler/32-decisions.enabler/21-adr-auditing.enabler/evals/structure/eval.toml` (6 lines)
- [x] `spx/21-spec-tree.enabler/32-decisions.enabler/21-adr-auditing.enabler/evals/structure/prompt.md` -> `spx/21-product-tree.enabler/32-decisions.enabler/21-adr-auditing.enabler/evals/structure/prompt.md` (4 lines)
- [x] `spx/21-spec-tree.enabler/32-decisions.enabler/21-adr-auditing.enabler/evals/tag-validity/eval.toml` -> `spx/21-product-tree.enabler/32-decisions.enabler/21-adr-auditing.enabler/evals/tag-validity/eval.toml` (6 lines)
- [x] `spx/21-spec-tree.enabler/32-decisions.enabler/21-adr-auditing.enabler/evals/tag-validity/prompt.md` -> `spx/21-product-tree.enabler/32-decisions.enabler/21-adr-auditing.enabler/evals/tag-validity/prompt.md` (4 lines)
- [x] `spx/21-spec-tree.enabler/32-decisions.enabler/21-adr-auditing.enabler/evals/voice/eval.toml` -> `spx/21-product-tree.enabler/32-decisions.enabler/21-adr-auditing.enabler/evals/voice/eval.toml` (6 lines)
- [x] `spx/21-spec-tree.enabler/32-decisions.enabler/21-adr-auditing.enabler/evals/voice/prompt.md` -> `spx/21-product-tree.enabler/32-decisions.enabler/21-adr-auditing.enabler/evals/voice/prompt.md` (4 lines)

### `spx/21-spec-tree.enabler/32-decisions.enabler/32-pdr-auditing.enabler` -> `spx/21-product-tree.enabler/32-decisions.enabler/32-pdr-auditing.enabler`

`pdr-auditing.md` other lines replaced:

- [x] line 9

  ```text
  old: SO THAT all spec-tree projects
  new: SO THAT all product-tree projects
  ```

- [x] line 28

  ```text
  old: The `/audit-pdr` skill in the spec-tree plugin classifies every statement in the PDR:
  new: The `/audit-pdr` skill in the product-tree plugin classifies every statement in the PDR:
  ```

Evidence files carrying the term:

- [x] `spx/21-spec-tree.enabler/32-decisions.enabler/32-pdr-auditing.enabler/evals/structure/eval.toml` -> `spx/21-product-tree.enabler/32-decisions.enabler/32-pdr-auditing.enabler/evals/structure/eval.toml` (7 lines)
- [x] `spx/21-spec-tree.enabler/32-decisions.enabler/32-pdr-auditing.enabler/evals/structure/prompt.md` -> `spx/21-product-tree.enabler/32-decisions.enabler/32-pdr-auditing.enabler/evals/structure/prompt.md` (8 lines)
- [x] `spx/21-spec-tree.enabler/32-decisions.enabler/32-pdr-auditing.enabler/evals/tag-validity/eval.toml` -> `spx/21-product-tree.enabler/32-decisions.enabler/32-pdr-auditing.enabler/evals/tag-validity/eval.toml` (7 lines)
- [x] `spx/21-spec-tree.enabler/32-decisions.enabler/32-pdr-auditing.enabler/evals/tag-validity/prompt.md` -> `spx/21-product-tree.enabler/32-decisions.enabler/32-pdr-auditing.enabler/evals/tag-validity/prompt.md` (8 lines)
- [x] `spx/21-spec-tree.enabler/32-decisions.enabler/32-pdr-auditing.enabler/evals/voice/eval.toml` -> `spx/21-product-tree.enabler/32-decisions.enabler/32-pdr-auditing.enabler/evals/voice/eval.toml` (7 lines)
- [x] `spx/21-spec-tree.enabler/32-decisions.enabler/32-pdr-auditing.enabler/evals/voice/prompt.md` -> `spx/21-product-tree.enabler/32-decisions.enabler/32-pdr-auditing.enabler/evals/voice/prompt.md` (8 lines)

### `spx/21-spec-tree.enabler/35-evidence.enabler` -> `spx/21-product-tree.enabler/35-evidence.enabler`

`evidence.md` other lines replaced:

- [x] line 9

  ```text
  old: SO THAT all spec-tree projects
  new: SO THAT all product-tree projects
  ```

### `spx/21-spec-tree.enabler/35-evidence.enabler/69-verify-skill.enabler` -> `spx/21-product-tree.enabler/35-evidence.enabler/69-verify-skill.enabler`

`verify-skill.md` other lines replaced:

- [x] line 8

  ```text
  old: PROVIDES verification-type selection and evidence-work orchestration from one assertion or canonical spec-tree scope
  new: PROVIDES verification-type selection and evidence-work orchestration from one assertion or canonical product-tree scope
  ```

Evidence files carrying the term:

- [x] `spx/21-spec-tree.enabler/35-evidence.enabler/69-verify-skill.enabler/evals/routing/eval.toml` -> `spx/21-product-tree.enabler/35-evidence.enabler/69-verify-skill.enabler/evals/routing/eval.toml` (7 lines)
- [x] `spx/21-spec-tree.enabler/35-evidence.enabler/69-verify-skill.enabler/evals/routing/prompt.md` -> `spx/21-product-tree.enabler/35-evidence.enabler/69-verify-skill.enabler/evals/routing/prompt.md` (18 lines)

### `spx/21-spec-tree.enabler/43-instruction-block.enabler` -> `spx/21-product-tree.enabler/43-instruction-block.enabler`

`instruction-block.md` assertions replaced:

- [x] line 21

  ```text
  old: - Given the router block, when it is written, then its opening marker is `<!-- SPEC-TREE v{template_version} langs:{enabled-languages} -->` carrying only the version and the recorded enabled-language list, its closing marker is `<!-- /SPEC-TREE -->`, and no template-source field is recorded ([test](tests/test_instruction_block.scenario.l1.py))
  new: - Given the router block, when it is written, then its opening marker is `<!-- PRODUCT-TREE v{template_version} langs:{enabled-languages} -->` carrying only the version and the recorded enabled-language list, its closing marker is `<!-- /PRODUCT-TREE -->`, and no template-source field is recorded ([test](tests/test_instruction_block.scenario.l1.py))
  ```

- [x] line 28

  ```text
  old: - Given a root instruction file contains a markerless full-file Spec Tree instruction surface, when the managed surface is updated, then the generated full-file body is replaced rather than preserved ahead of the router block ([test](tests/test_instruction_block.scenario.l1.py))
  new: - Given a root instruction file contains a markerless full-file Product Tree instruction surface, when the managed surface is updated, then the generated full-file body is replaced rather than preserved ahead of the router block ([test](tests/test_instruction_block.scenario.l1.py))
  ```

- [x] line 38

  ```text
  old: - Given a router block whose body or following independent content quotes the literal `<!-- /SPEC-TREE -->` closing marker inline, when the managed surface is updated, then only the standalone-line closing fence bounds the router block, so the inline-quoted marker and the content around it are preserved rather than swallowed at the quote ([test](tests/test_instruction_block.scenario.l1.py))
  new: - Given a router block whose body or following independent content quotes the literal `<!-- /PRODUCT-TREE -->` closing marker inline, when the managed surface is updated, then only the standalone-line closing fence bounds the router block, so the inline-quoted marker and the content around it are preserved rather than swallowed at the quote ([test](tests/test_instruction_block.scenario.l1.py))
  ```

- [x] line 54

  ```text
  old: - Generation and the `--check` verb measure each rendered root instruction file's byte size against the 32768-byte combined Codex project-doc ceiling declared in [`spx/21-spec-tree.enabler/43-instruction-block.enabler/21-render-model.adr.md`](spx/21-spec-tree.enabler/43-instruction-block.enabler/21-render-model.adr.md) and map it to a per-file report carrying the exact size and breach state ([test](tests/test_budget_measurement.mapping.l1.py))
  new: - Generation and the `--check` verb measure each rendered root instruction file's byte size against the 32768-byte combined Codex project-doc ceiling declared in [`spx/21-product-tree.enabler/43-instruction-block.enabler/21-render-model.adr.md`](spx/21-product-tree.enabler/43-instruction-block.enabler/21-render-model.adr.md) and map it to a per-file report carrying the exact size and breach state ([test](tests/test_budget_measurement.mapping.l1.py))
  ```

- [x] line 104

  ```text
  old: - NEVER: generation permits code comments or docstrings to reference Spec Tree specs or decisions through `spx/...` paths, ADR/PDR identifiers, or decision-file references ([test](tests/test_instruction_block.compliance.l1.py))
  new: - NEVER: generation permits code comments or docstrings to reference Product Tree specs or decisions through `spx/...` paths, ADR/PDR identifiers, or decision-file references ([test](tests/test_instruction_block.compliance.l1.py))
  ```

- [x] line 110

  ```text
  old: - ALWAYS: generation emits and validates a managed router that requires a live `SPEC_TREE_FOUNDATION` marker before direct filesystem access under `spx/` or access to source and test content, while exempting `spx session` operations — including inspection, archive, and release — `spx worktree status`, `spx diagnose`, and no-patch Git status, history, and topology until their output is followed into product content ([test](tests/test_instruction_block.compliance.l1.py))
  new: - ALWAYS: generation emits and validates a managed router that requires a live `PRODUCT_TREE_FOUNDATION` marker before direct filesystem access under `spx/` or access to source and test content, while exempting `spx session` operations — including inspection, archive, and release — `spx worktree status`, `spx diagnose`, and no-patch Git status, history, and topology until their output is followed into product content ([test](tests/test_instruction_block.compliance.l1.py))
  ```

- [x] line 111

  ```text
  old: - ALWAYS: the Codex router block begins with the operator-override rule as its first rendered body content, before the `Spec Tree Instructions` heading, while the Claude router block omits that Codex-only rule ([audit])
  new: - ALWAYS: the Codex router block begins with the operator-override rule as its first rendered body content, before the `Product Tree Instructions` heading, while the Claude router block omits that Codex-only rule ([audit])
  ```

- [x] line 116

  ```text
  old: - ALWAYS: generation emits, in the `/understand` section, the instruction to read the methodology source and version the repository follows from `spx.config.yaml` at the repository root, to read it again whenever `/understand` runs, and to treat an absent file, a missing `methodology` block, or a `methodology.version` of the sentinel `installed` as no declared methodology version, never inferring one from a plugin's distribution version, a changelog, or prose; the instruction reads the same declaration the SPX CLI resolves, as the reader's stand-in for the methodology declaration context loading delivers per `spx/21-spec-tree.enabler/18-context-loading.enabler/context-loading.md` ([test](tests/test_methodology_declaration.compliance.l1.py))
  new: - ALWAYS: generation emits, in the `/understand` section, the instruction to read the methodology source and version the repository follows from `spx.config.yaml` at the repository root, to read it again whenever `/understand` runs, and to treat an absent file, a missing `methodology` block, or a `methodology.version` of the sentinel `installed` as no declared methodology version, never inferring one from a plugin's distribution version, a changelog, or prose; the instruction reads the same declaration the SPX CLI resolves, as the reader's stand-in for the methodology declaration context loading delivers per `spx/21-product-tree.enabler/18-context-loading.enabler/context-loading.md` ([test](tests/test_methodology_declaration.compliance.l1.py))
  ```

- [x] line 130

  ```text
  old: - NEVER: the generator recognizes a `SPEC-TREE:{name}` slot fence as a managed command slot — the fence is ordinary independent content, never a slot the router resolves by name ([test](tests/test_instruction_block.compliance.l1.py))
  new: - NEVER: the generator recognizes a `PRODUCT-TREE:{name}` slot fence as a managed command slot — the fence is ordinary independent content, never a slot the router resolves by name ([test](tests/test_instruction_block.compliance.l1.py))
  ```

`instruction-block.md` other lines replaced:

- [x] line 8

  ```text
  old: PROVIDES deterministic generation and validation of a managed Spec Tree instruction surface in a product's root agent-harness instruction files — `CLAUDE.md` for Claude Code and `AGENTS.md` for Codex — composed of a generated router block rendered from the harness templates committed under `dist/`, `shared` regions kept byte-identical across both files, and independent product content free to differ per file, scoped to the project's enabled languages and rendered per agent harness
  new: PROVIDES deterministic generation and validation of a managed Product Tree instruction surface in a product's root agent-harness instruction files — `CLAUDE.md` for Claude Code and `AGENTS.md` for Codex — composed of a generated router block rendered from the harness templates committed under `dist/`, `shared` regions kept byte-identical across both files, and independent product content free to differ per file, scoped to the project's enabled languages and rendered per agent harness
  ```

- [x] line 9

  ```text
  old: SO THAT every agent working a spec-tree project
  new: SO THAT every agent working a product-tree project
  ```

- [x] line 10

  ```text
  old: CAN retain the Spec Tree routing instructions and reach the product's own phase commands across compaction while preserving the product's other root instructions and keeping the two root files consistent
  new: CAN retain the Product Tree routing instructions and reach the product's own phase commands across compaction while preserving the product's other root instructions and keeping the two root files consistent
  ```

### `spx/21-spec-tree.enabler/43-instruction-block.enabler/54-instruction-block-harness.enabler` -> `spx/21-product-tree.enabler/43-instruction-block.enabler/54-instruction-block-harness.enabler`

`instruction-block-harness.md` other lines replaced:

- [x] line 9

  ```text
  old: SO THAT `spx/21-spec-tree.enabler/43-instruction-block.enabler`
  new: SO THAT `spx/21-product-tree.enabler/43-instruction-block.enabler`
  ```

### `spx/21-spec-tree.enabler/54-aligning.enabler` -> `spx/21-product-tree.enabler/54-aligning.enabler`

`aligning.md` assertions replaced:

- [x] line 20

  ```text
  old: - ALWAYS: when checking a changeset, report a product spec, ADR, PDR, or ancestor spec change that lacks both aligned first affected lower specs and first-affected-node `PLAN.md` grounding, deriving the changed-file set through `spx/21-spec-tree.enabler/14-version-control.enabler/15-changeset-scope.enabler` rather than ad hoc git diff logic ([audit])
  new: - ALWAYS: when checking a changeset, report a product spec, ADR, PDR, or ancestor spec change that lacks both aligned first affected lower specs and first-affected-node `PLAN.md` grounding, deriving the changed-file set through `spx/21-product-tree.enabler/14-version-control.enabler/15-changeset-scope.enabler` rather than ad hoc git diff logic ([audit])
  ```

`aligning.md` other lines replaced:

- [x] line 8

  ```text
  old: PROVIDES systematic consistency checking across the spec tree — structural conformance, atemporal voice, and content placement
  new: PROVIDES systematic consistency checking across the product tree — structural conformance, atemporal voice, and content placement
  ```

### `spx/21-spec-tree.enabler/54-authoring.enabler/39-artifact-authoring.enabler` -> `spx/21-product-tree.enabler/54-authoring.enabler/39-artifact-authoring.enabler`

`artifact-authoring.md` other lines replaced:

- [x] line 8

  ```text
  old: PROVIDES deterministic creation and modification of decision-ready Spec Tree artifacts
  new: PROVIDES deterministic creation and modification of decision-ready Product Tree artifacts
  ```

### `spx/21-spec-tree.enabler/54-authoring.enabler/69-spec-workflow.enabler` -> `spx/21-product-tree.enabler/54-authoring.enabler/69-spec-workflow.enabler`

`spec-workflow.md` other lines replaced:

- [x] line 10

  ```text
  old: CAN move from intent to aligned Spec Tree truth through one interactive, context-complete workflow
  new: CAN move from intent to aligned Product Tree truth through one interactive, context-complete workflow
  ```

### `spx/21-spec-tree.enabler/54-bootstrapping.enabler` -> `spx/21-product-tree.enabler/54-bootstrapping.enabler`

`bootstrapping.md` assertions replaced:

- [x] line 16

  ```text
  old: - ALWAYS: bootstrapping a product with no `spx/` directory creates a product spec and a managed Spec Tree instruction block in root `CLAUDE.md` and `AGENTS.md` ([audit])
  new: - ALWAYS: bootstrapping a product with no `spx/` directory creates a product spec and a managed Product Tree instruction block in root `CLAUDE.md` and `AGENTS.md` ([audit])
  ```

- [x] line 18

  ```text
  old: - ALWAYS: bootstrapping writes a root `CLAUDE.md` and `AGENTS.md` managed Spec Tree instruction block whose `template_version` matches the installed spec-tree plugin ([audit])
  new: - ALWAYS: bootstrapping writes a root `CLAUDE.md` and `AGENTS.md` managed Product Tree instruction block whose `template_version` matches the installed product-tree plugin ([audit])
  ```

- [x] line 23

  ```text
  old: - ALWAYS: create the product spec and the root `CLAUDE.md` and `AGENTS.md` managed Spec Tree instruction block before any top-level child nodes — the root must exist before composition ([audit])
  new: - ALWAYS: create the product spec and the root `CLAUDE.md` and `AGENTS.md` managed Product Tree instruction block before any top-level child nodes — the root must exist before composition ([audit])
  ```

- [x] line 26

  ```text
  old: - NEVER: create a spec tree without a product spec — the product spec is the root of all context ([audit])
  new: - NEVER: create a product tree without a product spec — the product spec is the root of all context ([audit])
  ```

`bootstrapping.md` other lines replaced:

- [x] line 8

  ```text
  old: PROVIDES an interactive bootstrapping flow that scaffolds a product-root spec tree from user interviews
  new: PROVIDES an interactive bootstrapping flow that scaffolds a product-root product tree from user interviews
  ```

- [x] line 10

  ```text
  old: CAN adopt the Spec Tree methodology while delegating top-level structure to `/decompose spx/`
  new: CAN adopt the Product Tree methodology while delegating top-level structure to `/decompose spx/`
  ```

### `spx/21-spec-tree.enabler/54-interview.enabler` -> `spx/21-product-tree.enabler/54-interview.enabler`

`interview.md` other lines replaced:

- [x] line 9

  ```text
  old: SO THAT every spec-tree skill that gathers requirements
  new: SO THAT every product-tree skill that gathers requirements
  ```

### `spx/21-spec-tree.enabler/54-migrating.enabler` -> `spx/21-product-tree.enabler/54-migrating.enabler`

`migrating.md` other lines replaced:

- [x] line 8

  ```text
  old: PROVIDES conversion of every citation in a spec tree to the tree-absolute link form the 4.0 methodology declares
  new: PROVIDES conversion of every citation in a product tree to the tree-absolute link form the 4.0 methodology declares
  ```

Evidence files carrying the term:

- [x] `spx/21-spec-tree.enabler/54-migrating.enabler/tests/test_migrating.compliance.l1.py` -> `spx/21-product-tree.enabler/54-migrating.enabler/tests/test_migrating.compliance.l1.py` (5 lines)
- [x] `spx/21-spec-tree.enabler/54-migrating.enabler/tests/test_migrating.scenario.l1.py` -> `spx/21-product-tree.enabler/54-migrating.enabler/tests/test_migrating.scenario.l1.py` (3 lines)

### `spx/21-spec-tree.enabler/54-refactoring.enabler` -> `spx/21-product-tree.enabler/54-refactoring.enabler`

`refactoring.md` other lines replaced:

- [x] line 10

  ```text
  old: CAN reorganize the spec tree without losing context, breaking references, or duplicating composition logic
  new: CAN reorganize the product tree without losing context, breaking references, or duplicating composition logic
  ```

### `spx/21-spec-tree.enabler/65-apply.enabler` -> `spx/21-product-tree.enabler/65-apply.enabler`

`apply.md` assertions replaced:

- [x] line 26

  ```text
  old: - NEVER: a runtime hook enforces the audit gates — the gate reminders are skill prose, and the spec-tree plugin ships no `PostToolUse` hook (`spx/21-spec-tree.enabler/13-agent-environment.enabler/`); enforcement is the flow's own discipline, not a hook ([audit])
  new: - NEVER: a runtime hook enforces the audit gates — the gate reminders are skill prose, and the product-tree plugin ships no `PostToolUse` hook (`spx/21-product-tree.enabler/13-agent-environment.enabler/`); enforcement is the flow's own discipline, not a hook ([audit])
  ```

### `spx/21-spec-tree.enabler/65-apply.enabler/21-plan-slice.enabler` -> `spx/21-product-tree.enabler/65-apply.enabler/21-plan-slice.enabler`

`plan-slice.md` assertions replaced:

- [x] line 17

  ```text
  old: - ALWAYS: express the selected slice as a path through existing spec-tree nodes, addressable by full path from `spx/`, rather than as an ad hoc list of files — the slice is located in the durable map ([audit])
  new: - ALWAYS: express the selected slice as a path through existing product-tree nodes, addressable by full path from `spx/`, rather than as an ad hoc list of files — the slice is located in the durable map ([audit])
  ```

- [x] line 21

  ```text
  old: - ALWAYS: hand the selected slice's node set to the per-node TDD flow as its work queue — slice selection feeds `spx/21-spec-tree.enabler/65-apply.enabler/54-node-flow.enabler`, which runs each node in ascending index order ([audit])
  new: - ALWAYS: hand the selected slice's node set to the per-node TDD flow as its work queue — slice selection feeds `spx/21-product-tree.enabler/65-apply.enabler/54-node-flow.enabler`, which runs each node in ascending index order ([audit])
  ```

`plan-slice.md` other lines replaced:

- [x] line 9

  ```text
  old: SO THAT the per-node TDD flow (`spx/21-spec-tree.enabler/65-apply.enabler/54-node-flow.enabler`)
  new: SO THAT the per-node TDD flow (`spx/21-product-tree.enabler/65-apply.enabler/54-node-flow.enabler`)
  ```

### `spx/21-spec-tree.enabler/65-apply.enabler/54-node-flow.enabler` -> `spx/21-product-tree.enabler/65-apply.enabler/54-node-flow.enabler`

`node-flow.md` assertions replaced:

- [x] line 21

  ```text
  old: - ALWAYS: when an audit gate's verdict rejects, whether as `REJECTED` or `UNKNOWN`, as a sealed run whose terminal status is `rejected`, or as a complete blocked diagnostic, attempt remediation within the gate cap [`spx/21-spec-tree.enabler/65-apply.enabler/apply.md`](spx/21-spec-tree.enabler/65-apply.enabler/apply.md) states, and stop on a failed launch or unusable result without remediation — the gate verdict governs progression ([audit])
  new: - ALWAYS: when an audit gate's verdict rejects, whether as `REJECTED` or `UNKNOWN`, as a sealed run whose terminal status is `rejected`, or as a complete blocked diagnostic, attempt remediation within the gate cap [`spx/21-product-tree.enabler/65-apply.enabler/apply.md`](spx/21-product-tree.enabler/65-apply.enabler/apply.md) states, and stop on a failed launch or unusable result without remediation — the gate verdict governs progression ([audit])
  ```

### `spx/21-spec-tree.enabler/68-audit.enabler` -> `spx/21-product-tree.enabler/68-audit.enabler`

`audit.md` assertions replaced:

- [x] line 25

  ```text
  old: - ALWAYS: the `spec-tree:audit-implementation` prompt contract admits only `audited`, `not-applicable`, `missing-skill`, or `unsupported` as a required coverage unit's final status, and requires a run that reaches none of those to return the blocked diagnostic naming the concrete failed operation or absent prerequisite ([audit])
  new: - ALWAYS: the `product-tree:audit-implementation` prompt contract admits only `audited`, `not-applicable`, `missing-skill`, or `unsupported` as a required coverage unit's final status, and requires a run that reaches none of those to return the blocked diagnostic naming the concrete failed operation or absent prerequisite ([audit])
  ```

- [x] line 26

  ```text
  old: - ALWAYS: the `spec-tree:audit-implementation` prompt contract requires every required unit to carry a final status, every unclaimed resolved path to carry its accounting record, and every recorded finding to reference an accepted unit before the run finishes, and continues the run when that reconciliation fails ([audit])
  new: - ALWAYS: the `product-tree:audit-implementation` prompt contract requires every required unit to carry a final status, every unclaimed resolved path to carry its accounting record, and every recorded finding to reference an accepted unit before the run finishes, and continues the run when that reconciliation fails ([audit])
  ```

- [x] line 27

  ```text
  old: - ALWAYS: the `spec-tree:audit-implementation` prompt contract requires each subject body to be inspected completely from the resolved base-to-head scope, re-issuing a truncated or partial read in bounded ranges until the body is complete ([audit])
  new: - ALWAYS: the `product-tree:audit-implementation` prompt contract requires each subject body to be inspected completely from the resolved base-to-head scope, re-issuing a truncated or partial read in bounded ranges until the body is complete ([audit])
  ```

- [x] line 28

  ```text
  old: - ALWAYS: the `spec-tree:audit-implementation` prompt contract requires each concern's governing standards and the audited repository's declared `spx/local/` overlays to load before a finding is accepted ([audit])
  new: - ALWAYS: the `product-tree:audit-implementation` prompt contract requires each concern's governing standards and the audited repository's declared `spx/local/` overlays to load before a finding is accepted ([audit])
  ```

- [x] line 29

  ```text
  old: - NEVER: the `spec-tree:audit-implementation` prompt contract admits remaining work, elapsed time, context pressure, or unfinished reading as a cause for ending a run, or derives a subject body from a single commit's patch rather than the resolved base-to-head scope ([audit])
  new: - NEVER: the `product-tree:audit-implementation` prompt contract admits remaining work, elapsed time, context pressure, or unfinished reading as a cause for ending a run, or derives a subject body from a single commit's patch rather than the resolved base-to-head scope ([audit])
  ```

- [x] line 31

  ```text
  old: - ALWAYS: the `spec-tree:audit-implementation` prompt contract gives every selected concern skill the complete resolved changed-path set and records one scope unit per path a concern returns, narrowing neither set ([audit])
  new: - ALWAYS: the `product-tree:audit-implementation` prompt contract gives every selected concern skill the complete resolved changed-path set and records one scope unit per path a concern returns, narrowing neither set ([audit])
  ```

- [x] line 32

  ```text
  old: - ALWAYS: the `spec-tree:audit-implementation` prompt contract dispatches the scope resolver's registry selection for each resolved path, never selects from the installed skill inventory its own context carries, never invokes a skill to probe whether one is installed, and records a selected skill absent from that inventory as a `missing-skill` unit ([audit])
  new: - ALWAYS: the `product-tree:audit-implementation` prompt contract dispatches the scope resolver's registry selection for each resolved path, never selects from the installed skill inventory its own context carries, never invokes a skill to probe whether one is installed, and records a selected skill absent from that inventory as a `missing-skill` unit ([audit])
  ```

- [x] line 33

  ```text
  old: - ALWAYS: the `spec-tree:audit-implementation` prompt contract binds the target selector from the configured subagent's task message when the skill was preloaded, treats an empty substituted argument as binding nothing, and returns the missing-input diagnostic only when the task message itself carries no selector ([audit])
  new: - ALWAYS: the `product-tree:audit-implementation` prompt contract binds the target selector from the configured subagent's task message when the skill was preloaded, treats an empty substituted argument as binding nothing, and returns the missing-input diagnostic only when the task message itself carries no selector ([audit])
  ```

- [x] line 34

  ```text
  old: - ALWAYS: the `spec-tree:audit-implementation` prompt contract records a concern's complete claimed-path coverage before recording any finding for that concern, so a finding never stands in for the coverage of the paths it does not name ([audit])
  new: - ALWAYS: the `product-tree:audit-implementation` prompt contract records a concern's complete claimed-path coverage before recording any finding for that concern, so a finding never stands in for the coverage of the paths it does not name ([audit])
  ```

- [x] line 35

  ```text
  old: - ALWAYS: the `spec-tree:audit-implementation` prompt contract reconciles before finishing by running the bundled reconciler over the run's own sealed inventory and recorded units, and treats its nonzero exit as a failed reconciliation — to the blocked diagnostic whenever the selector no longer resolves to the sealed inventory, a recorded subject lies outside it, or a required unit rests at a status the append-only run cannot revise, since no inspection repairs those, and back to inspection only for sealed paths that carry no unit yet ([audit])
  new: - ALWAYS: the `product-tree:audit-implementation` prompt contract reconciles before finishing by running the bundled reconciler over the run's own sealed inventory and recorded units, and treats its nonzero exit as a failed reconciliation — to the blocked diagnostic whenever the selector no longer resolves to the sealed inventory, a recorded subject lies outside it, or a required unit rests at a status the append-only run cannot revise, since no inspection repairs those, and back to inspection only for sealed paths that carry no unit yet ([audit])
  ```

- [x] line 36

  ```text
  old: - NEVER: the `spec-tree:audit-implementation` prompt contract authorizes finishing from a reconciliation against the run's own planned inventory alone — a plan narrowed before enumeration reconciles with itself ([audit])
  new: - NEVER: the `product-tree:audit-implementation` prompt contract authorizes finishing from a reconciliation against the run's own planned inventory alone — a plan narrowed before enumeration reconciles with itself ([audit])
  ```

- [x] line 37

  ```text
  old: - NEVER: the `spec-tree:audit-implementation` prompt contract admits a raised finding or a rejected terminal status as a reason to leave a remaining concern or resolved path uninspected or unrecorded ([audit])
  new: - NEVER: the `product-tree:audit-implementation` prompt contract admits a raised finding or a rejected terminal status as a reason to leave a remaining concern or resolved path uninspected or unrecorded ([audit])
  ```

- [x] line 55

  ```text
  old: - ALWAYS: the `implementation-auditor` wrapper is a thin projection relay that invokes `spec-tree:audit-implementation` with the caller's raw scope selector, supplies its own run-driver producer identity as internal request data, owns no audit policy, and relays the exact `spx verification run` token, the run file, and the rendered projection; the invoked skill discovers repository, governing nodes, verification context, and the complete live file set for an explicitly advisory target ([audit])
  new: - ALWAYS: the `implementation-auditor` wrapper is a thin projection relay that invokes `product-tree:audit-implementation` with the caller's raw scope selector, supplies its own run-driver producer identity as internal request data, owns no audit policy, and relays the exact `spx verification run` token, the run file, and the rendered projection; the invoked skill discovers repository, governing nodes, verification context, and the complete live file set for an explicitly advisory target ([audit])
  ```

- [x] line 56

  ```text
  old: - ALWAYS: the `spec-tree:audit-implementation` prompt contract requires request validation including generic run-driver identity, one audit run started before concern analysis, registry selection of the audit skills each resolved path names, required `audit-{lang}-{code|test|architecture}` concern dispatch for each selected implementation partition, accounting of a path whose registered artifact's audit skill follows another contract under that skill's name rather than as missing-skill coverage, scope and finding recording through `spx verification run` with the published audit payload field names, missing-skill rejection before dispatch, terminal status derived from accepted evidence, final projection relay, and complete blocked-command relay carrying the run token when started, exact command, payload source and key, exit code, and stderr ([audit])
  new: - ALWAYS: the `product-tree:audit-implementation` prompt contract requires request validation including generic run-driver identity, one audit run started before concern analysis, registry selection of the audit skills each resolved path names, required `audit-{lang}-{code|test|architecture}` concern dispatch for each selected implementation partition, accounting of a path whose registered artifact's audit skill follows another contract under that skill's name rather than as missing-skill coverage, scope and finding recording through `spx verification run` with the published audit payload field names, missing-skill rejection before dispatch, terminal status derived from accepted evidence, final projection relay, and complete blocked-command relay carrying the run token when started, exact command, payload source and key, exit code, and stderr ([audit])
  ```

- [x] line 60

  ```text
  old: - NEVER: the spec-tree plugin ships implementation-audit agents named `auditor` or `audit-orchestrator`; implementation audit has one wrapper agent, `implementation-auditor` ([test](tests/test_implementation_audit_contract.compliance.l1.py))
  new: - NEVER: the product-tree plugin ships implementation-audit agents named `auditor` or `audit-orchestrator`; implementation audit has one wrapper agent, `implementation-auditor` ([test](tests/test_implementation_audit_contract.compliance.l1.py))
  ```

`audit.md` other lines replaced:

- [x] line 8

  ```text
  old: PROVIDES implementation-audit orchestration through one spec-tree-owned `implementation-auditor` wrapper agent that records audit coverage, findings, terminal state, and the rendered projection through `spx verification run`
  new: PROVIDES implementation-audit orchestration through one product-tree-owned `implementation-auditor` wrapper agent that records audit coverage, findings, terminal state, and the rendered projection through `spx verification run`
  ```

Evidence files carrying the term:

- [x] `spx/21-spec-tree.enabler/68-audit.enabler/tests/test_implementation_audit_contract.compliance.l1.py` -> `spx/21-product-tree.enabler/68-audit.enabler/tests/test_implementation_audit_contract.compliance.l1.py` (3 lines)

### `spx/21-spec-tree.enabler/68-audit.enabler/32-audit-eval-evidence.enabler` -> `spx/21-product-tree.enabler/68-audit.enabler/32-audit-eval-evidence.enabler`

`audit-eval-evidence.md` assertions replaced:

- [x] line 17

  ```text
  old: - ALWAYS: the `eval-evidence-auditor` agent is a thin wrapper that carries no independent audit policy beyond invoking `spec-tree:audit-eval-evidence` with the raw target and its run-driver identity, and relays the run token, the run file, and the rendered projection unchanged ([audit])
  new: - ALWAYS: the `eval-evidence-auditor` agent is a thin wrapper that carries no independent audit policy beyond invoking `product-tree:audit-eval-evidence` with the raw target and its run-driver identity, and relays the run token, the run file, and the rendered projection unchanged ([audit])
  ```

`audit-eval-evidence.md` other lines replaced:

- [x] line 9

  ```text
  old: SO THAT spec-tree projects can rely on eval runs as evidence about the producing skill, agent, or classifier rather than about a copied prompt simulation
  new: SO THAT product-tree projects can rely on eval runs as evidence about the producing skill, agent, or classifier rather than about a copied prompt simulation
  ```

### `spx/21-spec-tree.enabler/68-audit.enabler/32-audit-specs.enabler` -> `spx/21-product-tree.enabler/68-audit.enabler/32-audit-specs.enabler`

`audit-specs.md` other lines replaced:

- [x] line 9

  ```text
  old: SO THAT all spec-tree projects
  new: SO THAT all product-tree projects
  ```

- [x] line 24

  ```text
  old: A `[test]` assertion's assertion type is chosen from the claim's shape via `/test` (see `spx/21-spec-tree.enabler/35-evidence.enabler/evidence.md`). The audit verifies the selection fits the claim and does not relitigate a choice the router leaves open between equally valid types. A routed heading describes the claim's shape for every verification type: a universal audit-backed rule remains under `### Compliance` without acquiring the test-only compliance assertion type. A required tag missing inside a routed subsection, a bare mechanism tag, more than one tag, a claim whose shape disagrees with its heading, or an assertion type the router would not produce for a `[test]` claim is a finding. Untagged assertions directly under `## Assertions` receive declaration-quality checks without a missing-tag or missing-heading finding; their approval establishes no evidence result.
  new: A `[test]` assertion's assertion type is chosen from the claim's shape via `/test` (see `spx/21-product-tree.enabler/35-evidence.enabler/evidence.md`). The audit verifies the selection fits the claim and does not relitigate a choice the router leaves open between equally valid types. A routed heading describes the claim's shape for every verification type: a universal audit-backed rule remains under `### Compliance` without acquiring the test-only compliance assertion type. A required tag missing inside a routed subsection, a bare mechanism tag, more than one tag, a claim whose shape disagrees with its heading, or an assertion type the router would not produce for a `[test]` claim is a finding. Untagged assertions directly under `## Assertions` receive declaration-quality checks without a missing-tag or missing-heading finding; their approval establishes no evidence result.
  ```

Evidence files carrying the term:

- [x] `spx/21-spec-tree.enabler/68-audit.enabler/32-audit-specs.enabler/evals/structure/cases.jsonl` -> `spx/21-product-tree.enabler/68-audit.enabler/32-audit-specs.enabler/evals/structure/cases.jsonl` (1 lines)
- [x] `spx/21-spec-tree.enabler/68-audit.enabler/32-audit-specs.enabler/evals/structure/eval.toml` -> `spx/21-product-tree.enabler/68-audit.enabler/32-audit-specs.enabler/evals/structure/eval.toml` (7 lines)
- [x] `spx/21-spec-tree.enabler/68-audit.enabler/32-audit-specs.enabler/evals/structure/prompt.md` -> `spx/21-product-tree.enabler/68-audit.enabler/32-audit-specs.enabler/evals/structure/prompt.md` (2 lines)

### `spx/21-spec-tree.enabler/68-audit.enabler/32-audit-tests.enabler` -> `spx/21-product-tree.enabler/68-audit.enabler/32-audit-tests.enabler`

`audit-tests.md` assertions replaced:

- [x] line 126

  ```text
  old: - NEVER: run the project's coverage command, test command, or any other deterministic verification inside the audit — re-running what the caller passed before dispatch is the duplication prohibited by [`spx/31-outcomeeng.enabler/31-verification.enabler/14-verification.pdr.md`](spx/31-outcomeeng.enabler/31-verification.enabler/14-verification.pdr.md) and [`spx/21-spec-tree.enabler/17-audit.adr.md`](spx/21-spec-tree.enabler/17-audit.adr.md); trace the exercised path by reading instead ([audit])
  new: - NEVER: run the project's coverage command, test command, or any other deterministic verification inside the audit — re-running what the caller passed before dispatch is the duplication prohibited by [`spx/31-outcomeeng.enabler/31-verification.enabler/14-verification.pdr.md`](spx/31-outcomeeng.enabler/31-verification.enabler/14-verification.pdr.md) and [`spx/21-product-tree.enabler/17-audit.adr.md`](spx/21-product-tree.enabler/17-audit.adr.md); trace the exercised path by reading instead ([audit])
  ```

`audit-tests.md` other lines replaced:

- [x] line 9

  ```text
  old: SO THAT all spec-tree projects
  new: SO THAT all product-tree projects
  ```

- [x] line 55

  ```text
  old: The Auditor establishes coverage by reading, never by running coverage tooling. A dispatched agentic audit runs no deterministic verification — the caller brings the project's tests and coverage gate to passing on the changeset before dispatch, and CI re-runs them over the CI scope, per [`spx/31-outcomeeng.enabler/31-verification.enabler/14-verification.pdr.md`](spx/31-outcomeeng.enabler/31-verification.enabler/14-verification.pdr.md) and [`spx/21-spec-tree.enabler/17-audit.adr.md`](spx/21-spec-tree.enabler/17-audit.adr.md). Re-running the project's coverage command inside the audit re-pays a cost already paid and is the duplication that rule prohibits.
  new: The Auditor establishes coverage by reading, never by running coverage tooling. A dispatched agentic audit runs no deterministic verification — the caller brings the project's tests and coverage gate to passing on the changeset before dispatch, and CI re-runs them over the CI scope, per [`spx/31-outcomeeng.enabler/31-verification.enabler/14-verification.pdr.md`](spx/31-outcomeeng.enabler/31-verification.enabler/14-verification.pdr.md) and [`spx/21-product-tree.enabler/17-audit.adr.md`](spx/21-product-tree.enabler/17-audit.adr.md). Re-running the project's coverage command inside the audit re-pays a cost already paid and is the duplication that rule prohibits.
  ```

Evidence files carrying the term:

- [x] `spx/21-spec-tree.enabler/68-audit.enabler/32-audit-tests.enabler/evals/full-chain-ownership/eval.toml` -> `spx/21-product-tree.enabler/68-audit.enabler/32-audit-tests.enabler/evals/full-chain-ownership/eval.toml` (8 lines)
- [x] `spx/21-spec-tree.enabler/68-audit.enabler/32-audit-tests.enabler/evals/full-chain-ownership/prompt.md` -> `spx/21-product-tree.enabler/68-audit.enabler/32-audit-tests.enabler/evals/full-chain-ownership/prompt.md` (4 lines)
- [x] `spx/21-spec-tree.enabler/68-audit.enabler/32-audit-tests.enabler/evals/full-chain-ownership-codex/eval.toml` -> `spx/21-product-tree.enabler/68-audit.enabler/32-audit-tests.enabler/evals/full-chain-ownership-codex/eval.toml` (7 lines)
- [x] `spx/21-spec-tree.enabler/68-audit.enabler/32-audit-tests.enabler/evals/full-chain-ownership-codex/prompt.md` -> `spx/21-product-tree.enabler/68-audit.enabler/32-audit-tests.enabler/evals/full-chain-ownership-codex/prompt.md` (4 lines)

### `spx/21-spec-tree.enabler/68-audit.enabler/32-changeset-coherence.enabler` -> `spx/21-product-tree.enabler/68-audit.enabler/32-changeset-coherence.enabler`

Evidence files carrying the term:

- [x] `spx/21-spec-tree.enabler/68-audit.enabler/32-changeset-coherence.enabler/evals/coherence-verdict/cases.jsonl` -> `spx/21-product-tree.enabler/68-audit.enabler/32-changeset-coherence.enabler/evals/coherence-verdict/cases.jsonl` (3 lines)
- [x] `spx/21-spec-tree.enabler/68-audit.enabler/32-changeset-coherence.enabler/evals/coherence-verdict/eval.toml` -> `spx/21-product-tree.enabler/68-audit.enabler/32-changeset-coherence.enabler/evals/coherence-verdict/eval.toml` (9 lines)
- [x] `spx/21-spec-tree.enabler/68-audit.enabler/32-changeset-coherence.enabler/evals/coherence-verdict/prompt.md` -> `spx/21-product-tree.enabler/68-audit.enabler/32-changeset-coherence.enabler/evals/coherence-verdict/prompt.md` (1 lines)

### `spx/21-spec-tree.enabler/68-reviewing.enabler` -> `spx/21-product-tree.enabler/68-reviewing.enabler`

`reviewing.md` assertions replaced:

- [x] line 16

  ```text
  old: - ALWAYS: a review skill conforms to the verification contract in `spx/21-spec-tree.enabler/16-verification.enabler/verification.md` — one persistence model, one verification discipline, one wrapper-agent shape — so review composes against the same machinery as every other verification kind ([audit])
  new: - ALWAYS: a review skill conforms to the verification contract in `spx/21-product-tree.enabler/16-verification.enabler/verification.md` — one persistence model, one verification discipline, one wrapper-agent shape — so review composes against the same machinery as every other verification kind ([audit])
  ```

### `spx/21-spec-tree.enabler/68-reviewing.enabler/21-reviewing-changes.enabler` -> `spx/21-product-tree.enabler/68-reviewing.enabler/21-reviewing-changes.enabler`

`reviewing-changes.md` assertions replaced:

- [x] line 15

  ```text
  old: - ALWAYS: the review skill advances a changed file's scope only after reading the file, and marks every changed file it does not read as unread before it finishes, per [`spx/21-spec-tree.enabler/16-verification.enabler/13-run-journal.adr.md`](spx/21-spec-tree.enabler/16-verification.enabler/13-run-journal.adr.md) ([audit])
  new: - ALWAYS: the review skill advances a changed file's scope only after reading the file, and marks every changed file it does not read as unread before it finishes, per [`spx/21-product-tree.enabler/16-verification.enabler/13-run-journal.adr.md`](spx/21-product-tree.enabler/16-verification.enabler/13-run-journal.adr.md) ([audit])
  ```

- [x] line 16

  ```text
  old: - ALWAYS: a review whose branch value names a commit rather than a branch records the checked-out branch as its branch identity and slug, per [`spx/21-spec-tree.enabler/16-verification.enabler/13-run-journal.adr.md`](spx/21-spec-tree.enabler/16-verification.enabler/13-run-journal.adr.md) ([test](tests/test_review_branch_identity.compliance.l2.py))
  new: - ALWAYS: a review whose branch value names a commit rather than a branch records the checked-out branch as its branch identity and slug, per [`spx/21-product-tree.enabler/16-verification.enabler/13-run-journal.adr.md`](spx/21-product-tree.enabler/16-verification.enabler/13-run-journal.adr.md) ([test](tests/test_review_branch_identity.compliance.l2.py))
  ```

- [x] line 17

  ```text
  old: - NEVER: the reviewer agent exports a commit as the branch identity for a commit-range input, per [`spx/21-spec-tree.enabler/16-verification.enabler/13-run-journal.adr.md`](spx/21-spec-tree.enabler/16-verification.enabler/13-run-journal.adr.md) ([audit])
  new: - NEVER: the reviewer agent exports a commit as the branch identity for a commit-range input, per [`spx/21-product-tree.enabler/16-verification.enabler/13-run-journal.adr.md`](spx/21-product-tree.enabler/16-verification.enabler/13-run-journal.adr.md) ([audit])
  ```

- [x] line 61

  ```text
  old: - ALWAYS: scripts under `plugins/spec-tree/skills/review-changes/scripts/` write no durable review state directly; `compute_diff.py` may write only the caller-owned scratch review-input bundle files, and `review_run.py` may write and remove runner-owned scratch state ([test](tests/test_reviewing_changes.compliance.l1.py))
  new: - ALWAYS: scripts under `plugins/product-tree/skills/review-changes/scripts/` write no durable review state directly; `compute_diff.py` may write only the caller-owned scratch review-input bundle files, and `review_run.py` may write and remove runner-owned scratch state ([test](tests/test_reviewing_changes.compliance.l1.py))
  ```

- [x] line 62

  ```text
  old: - ALWAYS: the swappable review prompt template lives at `plugins/spec-tree/skills/review-changes/references/review-prompt.md` and the skill prose loads it via `${CLAUDE_SKILL_DIR}/references/review-prompt.md` ([audit])
  new: - ALWAYS: the swappable review prompt template lives at `plugins/product-tree/skills/review-changes/references/review-prompt.md` and the skill prose loads it via `${CLAUDE_SKILL_DIR}/references/review-prompt.md` ([audit])
  ```

- [x] line 63

  ```text
  old: - ALWAYS: `Finding.rule` is a non-empty string whose form is a path-style citation into an existing rule in the spec-tree or skill ecosystem, from one of the declared citation families — `spx/<path>:<MUST\|NEVER\|ALWAYS\|SCENARIO\|MAPPING\|CONFORMANCE\|PROPERTY\|AUDIT>:<n>`, a path to a spec-tree ADR/PDR, `plugins/<plugin>/skills/<skill>/SKILL.md:<rule-slug>`, `AGENTS.md:<rule-slug>`, or `CLAUDE.md:<rule-slug>` ([test](tests/test_review_result.mapping.l1.py))
  new: - ALWAYS: `Finding.rule` is a non-empty string whose form is a path-style citation into an existing rule in the product-tree or skill ecosystem, from one of the declared citation families — `spx/<path>:<MUST\|NEVER\|ALWAYS\|SCENARIO\|MAPPING\|CONFORMANCE\|PROPERTY\|AUDIT>:<n>`, a path to a product-tree ADR/PDR, `plugins/<plugin>/skills/<skill>/SKILL.md:<rule-slug>`, `AGENTS.md:<rule-slug>`, or `CLAUDE.md:<rule-slug>` ([test](tests/test_review_result.mapping.l1.py))
  ```

- [x] line 68

  ```text
  old: - ALWAYS: finding `severity` matches the rubric in `plugins/spec-tree/skills/review-changes/references/review-prompt.md` — `blocking` for merge-safety defects, `debt` for real defects that do not jeopardize merge safety ([audit])
  new: - ALWAYS: finding `severity` matches the rubric in `plugins/product-tree/skills/review-changes/references/review-prompt.md` — `blocking` for merge-safety defects, `debt` for real defects that do not jeopardize merge safety ([audit])
  ```

- [x] line 72

  ```text
  old: - NEVER: any script under `plugins/spec-tree/skills/review-changes/scripts/` imports a third-party package, depends on `uv` at runtime, or imports any `outcomeeng_*` module — stdlib only per the Plugin Portability Constraints in `AGENTS.md` ([test](tests/test_reviewing_changes.compliance.l1.py))
  new: - NEVER: any script under `plugins/product-tree/skills/review-changes/scripts/` imports a third-party package, depends on `uv` at runtime, or imports any `outcomeeng_*` module — stdlib only per the Plugin Portability Constraints in `AGENTS.md` ([test](tests/test_reviewing_changes.compliance.l1.py))
  ```

Evidence files carrying the term:

- [x] `spx/21-spec-tree.enabler/68-reviewing.enabler/21-reviewing-changes.enabler/tests/test_review_journal_emit.mapping.l1.py` -> `spx/21-product-tree.enabler/68-reviewing.enabler/21-reviewing-changes.enabler/tests/test_review_journal_emit.mapping.l1.py` (5 lines)
- [x] `spx/21-spec-tree.enabler/68-reviewing.enabler/21-reviewing-changes.enabler/tests/test_review_result.scenario.l1.py` -> `spx/21-product-tree.enabler/68-reviewing.enabler/21-reviewing-changes.enabler/tests/test_review_result.scenario.l1.py` (2 lines)

### `spx/21-spec-tree.enabler/73-committing.enabler` -> `spx/21-product-tree.enabler/73-committing.enabler`

`committing.md` other lines replaced:

- [x] line 10

  ```text
  old: CAN produce atomic, well-described commits that map cleanly to spec tree changes
  new: CAN produce atomic, well-described commits that map cleanly to product tree changes
  ```

### `spx/21-spec-tree.enabler/76-merge.enabler` -> `spx/21-product-tree.enabler/76-merge.enabler`

`merge.md` assertions replaced:

- [x] line 32

  ```text
  old: - ALWAYS: the `/merge` dispatcher ships as a user-invocable `SKILL.md` under `plugins/spec-tree/skills/merge/`, with no command wrapper, so it activates on both runtimes per [`spx/13-plugin-and-runtime-conventions.adr.md`](spx/13-plugin-and-runtime-conventions.adr.md) ([audit])
  new: - ALWAYS: the `/merge` dispatcher ships as a user-invocable `SKILL.md` under `plugins/product-tree/skills/merge/`, with no command wrapper, so it activates on both runtimes per [`spx/13-plugin-and-runtime-conventions.adr.md`](spx/13-plugin-and-runtime-conventions.adr.md) ([audit])
  ```

- [x] line 35

  ```text
  old: - NEVER: the `/merge` dispatcher re-derives the base ref or diff range inline; its co-located classifier consumes the canonical `changeset_scope` primitives per [`spx/21-spec-tree.enabler/14-version-control.enabler/15-changeset-scope.enabler/13-changeset-derivation.adr.md`](spx/21-spec-tree.enabler/14-version-control.enabler/15-changeset-scope.enabler/13-changeset-derivation.adr.md) ([audit])
  new: - NEVER: the `/merge` dispatcher re-derives the base ref or diff range inline; its co-located classifier consumes the canonical `changeset_scope` primitives per [`spx/21-product-tree.enabler/14-version-control.enabler/15-changeset-scope.enabler/13-changeset-derivation.adr.md`](spx/21-product-tree.enabler/14-version-control.enabler/15-changeset-scope.enabler/13-changeset-derivation.adr.md) ([audit])
  ```

- [x] line 54

  ```text
  old: - ALWAYS: an Auditor verdict surfacing while the merging flow drives review feedback — a sealed run whose terminal status is `rejected`, with or without a finding — whose subject artifact text the changeset touches or invalidates is in-slice unresolved work the flow fixes or resolves before merge, never deferred `ISSUES.md` work; a verdict on any other text is returned `filed` under [`spx/31-outcomeeng.enabler/31-verification.enabler/14-verification.pdr.md`](spx/31-outcomeeng.enabler/31-verification.enabler/14-verification.pdr.md), tracked out of the PR in the owning node's `ISSUES.md` with the reason recorded, and never blocks the merge, per the verdict mapping above, `spx/21-spec-tree.enabler/16-verification.enabler/15-verdict-toolchain.enabler/verdict-toolchain.md`, and [`spx/15-merging.pdr.md`](spx/15-merging.pdr.md) ([audit])
  new: - ALWAYS: an Auditor verdict surfacing while the merging flow drives review feedback — a sealed run whose terminal status is `rejected`, with or without a finding — whose subject artifact text the changeset touches or invalidates is in-slice unresolved work the flow fixes or resolves before merge, never deferred `ISSUES.md` work; a verdict on any other text is returned `filed` under [`spx/31-outcomeeng.enabler/31-verification.enabler/14-verification.pdr.md`](spx/31-outcomeeng.enabler/31-verification.enabler/14-verification.pdr.md), tracked out of the PR in the owning node's `ISSUES.md` with the reason recorded, and never blocks the merge, per the verdict mapping above, `spx/21-product-tree.enabler/16-verification.enabler/15-verdict-toolchain.enabler/verdict-toolchain.md`, and [`spx/15-merging.pdr.md`](spx/15-merging.pdr.md) ([audit])
  ```

- [x] line 65

  ```text
  old: - ALWAYS: the merging skills require `/sync-base` (`spx/21-spec-tree.enabler/14-version-control.enabler/32-sync-base.enabler/sync-base.md`) to complete with `already_current` or `rebased` for the recorded checkout and selected base before continuing dependent work; `/sync-base` owns checkpointing only authorized paths through `/commit-changes` and retrying, while callers preserve the exact blocked action, paths, and evidence for distinct authority, checkpoint, Git-failure, and unresolved product-intent conflict conditions, involving the operator only when no authorized autonomous continuation remains and preserving active rebase state for an unresolved conflict, per [`spx/15-merging.pdr.md`](spx/15-merging.pdr.md) ([audit])
  new: - ALWAYS: the merging skills require `/sync-base` (`spx/21-product-tree.enabler/14-version-control.enabler/32-sync-base.enabler/sync-base.md`) to complete with `already_current` or `rebased` for the recorded checkout and selected base before continuing dependent work; `/sync-base` owns checkpointing only authorized paths through `/commit-changes` and retrying, while callers preserve the exact blocked action, paths, and evidence for distinct authority, checkpoint, Git-failure, and unresolved product-intent conflict conditions, involving the operator only when no authorized autonomous continuation remains and preserving active rebase state for an unresolved conflict, per [`spx/15-merging.pdr.md`](spx/15-merging.pdr.md) ([audit])
  ```

`merge.md` other lines replaced:

- [x] line 9

  ```text
  old: SO THAT every product that installs the spec-tree plugin
  new: SO THAT every product that installs the product-tree plugin
  ```

Evidence files carrying the term:

- [x] `spx/21-spec-tree.enabler/76-merge.enabler/evals/local-completion-boundary/eval.toml` -> `spx/21-product-tree.enabler/76-merge.enabler/evals/local-completion-boundary/eval.toml` (10 lines)
- [x] `spx/21-spec-tree.enabler/76-merge.enabler/evals/transport-selection/cases.jsonl` -> `spx/21-product-tree.enabler/76-merge.enabler/evals/transport-selection/cases.jsonl` (9 lines)
- [x] `spx/21-spec-tree.enabler/76-merge.enabler/evals/transport-selection/eval.toml` -> `spx/21-product-tree.enabler/76-merge.enabler/evals/transport-selection/eval.toml` (8 lines)
- [x] `spx/21-spec-tree.enabler/76-merge.enabler/evals/transport-selection/prompt.md` -> `spx/21-product-tree.enabler/76-merge.enabler/evals/transport-selection/prompt.md` (1 lines)
- [x] `spx/21-spec-tree.enabler/76-merge.enabler/probes/merge-gate-selection/probe.md` -> `spx/21-product-tree.enabler/76-merge.enabler/probes/merge-gate-selection/probe.md` (2 lines)
- [x] `spx/21-spec-tree.enabler/76-merge.enabler/probes/merge-gate-selection/transcript.jsonl` -> `spx/21-product-tree.enabler/76-merge.enabler/probes/merge-gate-selection/transcript.jsonl` (5 lines)

### `spx/21-spec-tree.enabler/76-merge.enabler/32-github-pr.enabler` -> `spx/21-product-tree.enabler/76-merge.enabler/32-github-pr.enabler`

`github-pr.md` assertions replaced:

- [x] line 27

  ```text
  old: - ALWAYS: `/manage-github-pr` ships as a user-invocable `SKILL.md` under `plugins/spec-tree/skills/manage-github-pr/`, with no command wrapper, so it activates on both runtimes per [`spx/13-plugin-and-runtime-conventions.adr.md`](spx/13-plugin-and-runtime-conventions.adr.md) ([audit])
  new: - ALWAYS: `/manage-github-pr` ships as a user-invocable `SKILL.md` under `plugins/product-tree/skills/manage-github-pr/`, with no command wrapper, so it activates on both runtimes per [`spx/13-plugin-and-runtime-conventions.adr.md`](spx/13-plugin-and-runtime-conventions.adr.md) ([audit])
  ```

- [x] line 28

  ```text
  old: - ALWAYS: `/open-pr` ships as an internal `SKILL.md` under `plugins/spec-tree/skills/open-pr/`, with no direct command wrapper ([audit])
  new: - ALWAYS: `/open-pr` ships as an internal `SKILL.md` under `plugins/product-tree/skills/open-pr/`, with no direct command wrapper ([audit])
  ```

### `spx/21-spec-tree.enabler/76-merge.enabler/32-github-pr.enabler/32-opening-pr.enabler` -> `spx/21-product-tree.enabler/76-merge.enabler/32-github-pr.enabler/32-opening-pr.enabler`

`opening-pr.md` assertions replaced:

- [x] line 27

  ```text
  old: - ALWAYS: `/open-pr` runs each evidence-auditor predicate and the local review within the gate cap `spx/21-spec-tree.enabler/76-merge.enabler/merge.md` states ([audit])
  new: - ALWAYS: `/open-pr` runs each evidence-auditor predicate and the local review within the gate cap `spx/21-product-tree.enabler/76-merge.enabler/merge.md` states ([audit])
  ```

### `spx/21-spec-tree.enabler/76-merge.enabler/32-github-pr.enabler/54-managing-pr.enabler` -> `spx/21-product-tree.enabler/76-merge.enabler/32-github-pr.enabler/54-managing-pr.enabler`

`managing-pr.md` assertions replaced:

- [x] line 26

  ```text
  old: - ALWAYS: when the current-head CI review reports `conclusion: skipped` because the PR modifies the reviewer's own workflow file, `/manage-pr` fires the mention-triggered reviewer with the project's configured trigger phrase (default `@spec-tree`) and treats its posted findings as the current-head review, per [`spx/15-merging.pdr.md`](spx/15-merging.pdr.md) ([audit])
  new: - ALWAYS: when the current-head CI review reports `conclusion: skipped` because the PR modifies the reviewer's own workflow file, `/manage-pr` fires the mention-triggered reviewer with the project's configured trigger phrase (default `@spec-tree`) and treats its posted findings as the current-head review, per [`spx/15-merging.pdr.md`](spx/15-merging.pdr.md) ([audit])
  ```

- [x] line 34

  ```text
  old: - ALWAYS: `/manage-pr` runs each evidence-auditor predicate and the local review of a follow-up push within the gate cap `spx/21-spec-tree.enabler/76-merge.enabler/merge.md` states ([audit])
  new: - ALWAYS: `/manage-pr` runs each evidence-auditor predicate and the local review of a follow-up push within the gate cap `spx/21-product-tree.enabler/76-merge.enabler/merge.md` states ([audit])
  ```

### `spx/21-spec-tree.enabler/79-diagnostics.enabler` -> `spx/21-product-tree.enabler/79-diagnostics.enabler`

`diagnostics.md` assertions replaced:

- [x] line 24

  ```text
  old: - ALWAYS: the shipped skill reasons only about surfaces the agent harness exposes — the `spx` CLI, harness environment variables, worktree/session state, and install state — through `spx diagnose`, degrading a check to not-applicable where its surface is absent rather than misclassifying, and names no product-internal spec-tree node address ([audit])
  new: - ALWAYS: the shipped skill reasons only about surfaces the agent harness exposes — the `spx` CLI, harness environment variables, worktree/session state, and install state — through `spx diagnose`, degrading a check to not-applicable where its surface is absent rather than misclassifying, and names no product-internal product-tree node address ([audit])
  ```

`diagnostics.md` other lines replaced:

- [x] line 9

  ```text
  old: SO THAT a user or agent working any spec-tree product
  new: SO THAT a user or agent working any product-tree product
  ```

Evidence files carrying the term:

- [x] `spx/21-spec-tree.enabler/79-diagnostics.enabler/evals/diagnostic-remediation/cases.jsonl` -> `spx/21-product-tree.enabler/79-diagnostics.enabler/evals/diagnostic-remediation/cases.jsonl` (1 lines)
- [x] `spx/21-spec-tree.enabler/79-diagnostics.enabler/evals/diagnostic-remediation/eval.toml` -> `spx/21-product-tree.enabler/79-diagnostics.enabler/evals/diagnostic-remediation/eval.toml` (4 lines)

### `spx/13-infrastructure.enabler/21-test-infrastructure.enabler`

Evidence files carrying the term:

- [x] `spx/13-infrastructure.enabler/21-test-infrastructure.enabler/tests/test_infra_placement.compliance.l1.py` (1 lines)

### `spx/13-infrastructure.enabler/21-test-infrastructure.enabler/21-python-code-quality.enabler`

Evidence files carrying the term:

- [x] `spx/13-infrastructure.enabler/21-test-infrastructure.enabler/21-python-code-quality.enabler/tests/test_python_code_quality.conformance.l2.py` (1 lines)

### `spx/15-validation.enabler/32-hook-safety.enabler`

Evidence files carrying the term:

- [x] `spx/15-validation.enabler/32-hook-safety.enabler/tests/test_hook_safety.compliance.l1.py` (2 lines)
- [x] `spx/15-validation.enabler/32-hook-safety.enabler/tests/test_hook_safety.scenario.l1.py` (9 lines)

### `spx/15-validation.enabler/32-reference-portability.enabler`

`reference-portability.md` assertions replaced:

- [x] line 16

  ```text
  old: - NEVER: the validator passes a reference that points into this marketplace's own files — a spec-tree node or decision named by its sibling-local numeric prefix outside the illustrative `spx/55-example…` root sentinel (`spx/\d+-…`, such as `spx/15-validation.enabler/…` or [`spx/13-plugin-and-runtime-conventions.adr.md`](spx/13-plugin-and-runtime-conventions.adr.md)), the invalid `spx/NN-…` placeholder, the generated guide paths `spx/CLAUDE.md` and `spx/AGENTS.md`, or a path under one of this marketplace's own roots (`src/plugins/`, `dist/claude/`, `dist/codex/`, an `outcomeeng` toolchain package such as `outcomeeng/validation/…` or `outcomeeng_testing/…`, or a path under the marketplace's own GitHub repo slug such as `outcomeeng/plugins/AGENTS.md` or `outcomeeng/spx/src/types.ts`, caught even inside an absolute checkout path) — because none resolves in a consumer checkout ([test](tests/test_reference_portability.compliance.l1.py))
  new: - NEVER: the validator passes a reference that points into this marketplace's own files — a product-tree node or decision named by its sibling-local numeric prefix outside the illustrative `spx/55-example…` root sentinel (`spx/\d+-…`, such as `spx/15-validation.enabler/…` or [`spx/13-plugin-and-runtime-conventions.adr.md`](spx/13-plugin-and-runtime-conventions.adr.md)), the invalid `spx/NN-…` placeholder, the generated guide paths `spx/CLAUDE.md` and `spx/AGENTS.md`, or a path under one of this marketplace's own roots (`src/plugins/`, `dist/claude/`, `dist/codex/`, an `outcomeeng` toolchain package such as `outcomeeng/validation/…` or `outcomeeng_testing/…`, or a path under the marketplace's own GitHub repo slug such as `outcomeeng/plugins/AGENTS.md` or `outcomeeng/spx/src/types.ts`, caught even inside an absolute checkout path) — because none resolves in a consumer checkout ([test](tests/test_reference_portability.compliance.l1.py))
  ```

`reference-portability.md` other lines replaced:

- [x] line 3

  ```text
  old: PROVIDES a validator that flags a reference in plugin content under `src/plugins/` pointing into this marketplace's own files — which a consumer checkout does not hold — while passing references to the consumer's own spec tree or to the plugin's own files
  new: PROVIDES a validator that flags a reference in plugin content under `src/plugins/` pointing into this marketplace's own files — which a consumer checkout does not hold — while passing references to the consumer's own product tree or to the plugin's own files
  ```

### `spx/15-validation.enabler/65-gate.enabler`

`gate.md` assertions replaced:

- [x] line 32

  ```text
  old: - ALWAYS: the full gate step list includes a `fmt-check` (`dprint check`) step, a `ruff format --check` step, a `ruff check` step, a `mypy --strict` package step, a `pyright` package step, a `spx validation markdown` step, an evidence-link integrity step, and a hook-safety step — so repository formatting, Python formatting, lint, package type checking, Markdown link integrity, spec-tree `[test]` and `[eval]` link resolution, and shipped-hook safety are each enforced on every `just check-full` ([test](tests/test_gate.compliance.l1.py))
  new: - ALWAYS: the full gate step list includes a `fmt-check` (`dprint check`) step, a `ruff format --check` step, a `ruff check` step, a `mypy --strict` package step, a `pyright` package step, a `spx validation markdown` step, an evidence-link integrity step, and a hook-safety step — so repository formatting, Python formatting, lint, package type checking, Markdown link integrity, product-tree `[test]` and `[eval]` link resolution, and shipped-hook safety are each enforced on every `just check-full` ([test](tests/test_gate.compliance.l1.py))
  ```

### `spx/15-validation.enabler/65-gate.enabler/21-selected-gate.enabler`

Evidence files carrying the term:

- [x] `spx/15-validation.enabler/65-gate.enabler/21-selected-gate.enabler/tests/test_selected_gate.mapping.l1.py` (2 lines)

### `spx/16-interfaces.enabler`

`interfaces.md` assertions replaced:

- [x] line 15

  ```text
  old: - ALWAYS: source spec-tree structure and derived state from the SPX CLI's JSON projection — an interface surface never re-parses directory suffixes, assembles hierarchy, or derives node state itself ([audit])
  new: - ALWAYS: source product-tree structure and derived state from the SPX CLI's JSON projection — an interface surface never re-parses directory suffixes, assembles hierarchy, or derives node state itself ([audit])
  ```

- [x] line 16

  ```text
  old: - ALWAYS: present the node states and the node and decision categories the spec-tree methodology defines, so every surface reads the tree consistently ([audit])
  new: - ALWAYS: present the node states and the node and decision categories the product-tree methodology defines, so every surface reads the tree consistently ([audit])
  ```

`interfaces.md` other lines replaced:

- [x] line 7

  ```text
  old: PROVIDES the product's own user-facing surfaces over a spec-tree product
  new: PROVIDES the product's own user-facing surfaces over a product-tree product
  ```

### `spx/16-interfaces.enabler/21-browser.enabler`

`browser.md` other lines replaced:

- [x] line 3

  ```text
  old: PROVIDES a local, MCP-backed browser authoring surface that renders a spec-tree projection and live interview state into HTML
  new: PROVIDES a local, MCP-backed browser authoring surface that renders a product-tree projection and live interview state into HTML
  ```

### `spx/18-plugin-build.enabler`

`plugin-build.md` assertions replaced:

- [x] line 23

  ```text
  old: - ALWAYS: the build renders the agent tokens into a data file beside each spec-tree script that reads them, and the rendered file equals the declaration it renders ([test](tests/test_agent_token_rendering.mapping.l1.py))
  new: - ALWAYS: the build renders the agent tokens into a data file beside each product-tree script that reads them, and the rendered file equals the declaration it renders ([test](tests/test_agent_token_rendering.mapping.l1.py))
  ```

Evidence files carrying the term:

- [x] `spx/18-plugin-build.enabler/tests/test_agent_token_rendering.mapping.l1.py` (1 lines)

### `spx/18-plugin-build.enabler/54-conversion.enabler/21-agents.enabler/54-native-artifact.enabler`

Evidence files carrying the term:

- [x] `spx/18-plugin-build.enabler/54-conversion.enabler/21-agents.enabler/54-native-artifact.enabler/tests/test_native_artifact.scenario.l1.py` (2 lines)

### `spx/31-outcomeeng.enabler/32-changes.enabler/65-change-execution.enabler`

`change-execution.md` other lines replaced:

- [x] line 12

  ```text
  old: The spec-tree plugin ships one subagent definition per skill an Executor session or its rounds run: `change-executor` fronts `/execute-change`, `change-author` fronts `/author`, `change-verifier` fronts `/verify`, `change-tester` fronts `/test`, `change-implementer` fronts `/implement-change`, `change-skill-author` fronts `instructions:author-skill`, and `change-subagent-author` fronts `instructions:author-subagent`. Each Fixer is a fresh session of the definition its round's Author used, per [`spx/15-agent-terminology.pdr.md`](spx/15-agent-terminology.pdr.md).
  new: The product-tree plugin ships one subagent definition per skill an Executor session or its rounds run: `change-executor` fronts `/execute-change`, `change-author` fronts `/author`, `change-verifier` fronts `/verify`, `change-tester` fronts `/test`, `change-implementer` fronts `/implement-change`, `change-skill-author` fronts `instructions:author-skill`, and `change-subagent-author` fronts `instructions:author-subagent`. Each Fixer is a fresh session of the definition its round's Author used, per [`spx/15-agent-terminology.pdr.md`](spx/15-agent-terminology.pdr.md).
  ```

Evidence files carrying the term:

- [x] `spx/31-outcomeeng.enabler/32-changes.enabler/65-change-execution.enabler/probes/definition-invocation/change-author.result.json` (10 lines)
- [x] `spx/31-outcomeeng.enabler/32-changes.enabler/65-change-execution.enabler/probes/definition-invocation/change-executor.result.json` (9 lines)
- [x] `spx/31-outcomeeng.enabler/32-changes.enabler/65-change-execution.enabler/probes/definition-invocation/change-implementer.result.json` (9 lines)
- [x] `spx/31-outcomeeng.enabler/32-changes.enabler/65-change-execution.enabler/probes/definition-invocation/change-skill-author.result.json` (7 lines)
- [x] `spx/31-outcomeeng.enabler/32-changes.enabler/65-change-execution.enabler/probes/definition-invocation/change-subagent-author.result.json` (7 lines)
- [x] `spx/31-outcomeeng.enabler/32-changes.enabler/65-change-execution.enabler/probes/definition-invocation/change-tester.result.json` (9 lines)
- [x] `spx/31-outcomeeng.enabler/32-changes.enabler/65-change-execution.enabler/probes/definition-invocation/change-verifier.result.json` (9 lines)
- [x] `spx/31-outcomeeng.enabler/32-changes.enabler/65-change-execution.enabler/probes/definition-invocation/probe.md` (11 lines)

### `spx/32-distribution.enabler/21-installation.enabler`

`installation.md` assertions replaced:

- [x] line 9

  ```text
  old: - For each supported agent, isolated installation selects the complete committed catalog in catalog order, and persistent refresh selects the catalog-bounded members that agent reports installed in the invocation checkout or selected home, disabled entries included, in catalog order: an empty inventory bootstraps `spec-tree` alone, a nonempty Claude Code inventory is refreshed through native updates rather than installs, and a Codex inventory is refreshed through its native plugin operations. ([test](tests/test_installation.mapping.l1.py))
  new: - For each supported agent, isolated installation selects the complete committed catalog in catalog order, and persistent refresh selects the catalog-bounded members that agent reports installed in the invocation checkout or selected home, disabled entries included, in catalog order: an empty inventory bootstraps `product-tree` alone, a nonempty Claude Code inventory is refreshed through native updates rather than installs, and a Codex inventory is refreshed through its native plugin operations. ([test](tests/test_installation.mapping.l1.py))
  ```

- [x] line 19

  ```text
  old: - ALWAYS: persistent refresh preserves selection and activation through native update operations; an empty selection supplies only `spec-tree` with a warning and disabled activation where no activation is declared, and an agent whose bootstrap the run withholds supplies nothing, warns of no first install, and is reported as installing nothing; the repository-installation node declares and evidences those dispositions. ([test](tests/test_installation.compliance.l1.py))
  new: - ALWAYS: persistent refresh preserves selection and activation through native update operations; an empty selection supplies only `product-tree` with a warning and disabled activation where no activation is declared, and an agent whose bootstrap the run withholds supplies nothing, warns of no first install, and is reported as installing nothing; the repository-installation node declares and evidences those dispositions. ([test](tests/test_installation.compliance.l1.py))
  ```

- [x] line 22

  ```text
  old: - ALWAYS: persistent planning rejects every nonempty selected subset that omits `spec-tree` before a state-changing operation. ([test](tests/test_installation.compliance.l1.py))
  new: - ALWAYS: persistent planning rejects every nonempty selected subset that omits `product-tree` before a state-changing operation. ([test](tests/test_installation.compliance.l1.py))
  ```

Evidence files carrying the term:

- [x] `spx/32-distribution.enabler/21-installation.enabler/tests/test_installation.compliance.l1.py` (10 lines)
- [x] `spx/32-distribution.enabler/21-installation.enabler/tests/test_installation.mapping.l1.py` (2 lines)

### `spx/32-distribution.enabler/21-installation.enabler/21-repository-installation.enabler`

`repository-installation.md` assertions replaced:

- [x] line 10

  ```text
  old: - Given an invocation checkout with no install record of a cataloged plugin at project or local scope, when bootstrap runs, then only `spec-tree` is installed at project scope, declared project activation is preserved, and absent activation defaults to disabled with a warning; a checkout recording a plugin at either scope is refreshed through that record's native update and receives no install or enable.
  new: - Given an invocation checkout with no install record of a cataloged plugin at project or local scope, when bootstrap runs, then only `product-tree` is installed at project scope, declared project activation is preserved, and absent activation defaults to disabled with a warning; a checkout recording a plugin at either scope is refreshed through that record's native update and receives no install or enable.
  ```

- [x] line 19

  ```text
  old: - Given an empty selected Codex home, when persistent installation runs, then only `spec-tree` is registered and cached, its home activation is explicitly disabled, and the run warns that the operator can select additional plugins. ([test](tests/test_repository_installation.scenario.l3.py))
  new: - Given an empty selected Codex home, when persistent installation runs, then only `product-tree` is registered and cached, its home activation is explicitly disabled, and the run warns that the operator can select additional plugins. ([test](tests/test_repository_installation.scenario.l3.py))
  ```

- [x] line 23

  ```text
  old: - Given a nonempty selected subset that omits `spec-tree`, when persistent installation starts, then it reports the invalid selection and performs no state-changing operation. ([test](tests/test_repository_installation.scenario.l1.py))
  new: - Given a nonempty selected subset that omits `product-tree`, when persistent installation starts, then it reports the invalid selection and performs no state-changing operation. ([test](tests/test_repository_installation.scenario.l1.py))
  ```

- [x] line 26

  ```text
  old: - Given a generated subset omitting `spec-tree`, when isolated installation plans that selection, then it reports the invalid subset before an agent CLI mutates state. ([test](tests/test_repository_installation.scenario.l1.py))
  new: - Given a generated subset omitting `product-tree`, when isolated installation plans that selection, then it reports the invalid subset before an agent CLI mutates state. ([test](tests/test_repository_installation.scenario.l1.py))
  ```

- [x] line 53

  ```text
  old: - Each isolated verification selection — the complete committed catalogs and a generated valid subset containing `spec-tree` — maps to registration of the invocation checkout and exactly that selection reported as installed and enabled by the corresponding real agent CLI. ([test](tests/test_repository_installation.mapping.l3.py))
  new: - Each isolated verification selection — the complete committed catalogs and a generated valid subset containing `product-tree` — maps to registration of the invocation checkout and exactly that selection reported as installed and enabled by the corresponding real agent CLI. ([test](tests/test_repository_installation.mapping.l3.py))
  ```

Evidence files carrying the term:

- [x] `spx/32-distribution.enabler/21-installation.enabler/21-repository-installation.enabler/tests/test_repository_installation.compliance.l1.py` (4 lines)
- [x] `spx/32-distribution.enabler/21-installation.enabler/21-repository-installation.enabler/tests/test_repository_installation.scenario.l1.py` (23 lines)
- [x] `spx/32-distribution.enabler/21-installation.enabler/21-repository-installation.enabler/tests/test_repository_installation.scenario.l3.py` (15 lines)

### `spx/43-coding-agents.enabler/32-change-orchestration.enabler`

`change-orchestration.md` assertions replaced:

- [x] line 16

  ```text
  old: - ALWAYS: `/orchestrate-change` claims one Change for its Executor, naming the Executor's worktree root, and starts one Executor session for it in the root pane `spx/43-coding-agents.enabler/18-herdr-environment.enabler` returns when it creates the Executor's worktree, for a root absent from the pool, or opens the existing one, either grouped with the herdr workspace the invocation names; on Claude Code the session starts with the spec-tree definition `change-executor` selected ([audit])
  new: - ALWAYS: `/orchestrate-change` claims one Change for its Executor, naming the Executor's worktree root, and starts one Executor session for it in the root pane `spx/43-coding-agents.enabler/18-herdr-environment.enabler` returns when it creates the Executor's worktree, for a root absent from the pool, or opens the existing one, either grouped with the herdr workspace the invocation names; on Claude Code the session starts with the product-tree definition `change-executor` selected ([audit])
  ```

### `spx/43-coding-agents.enabler/32-same-worktree-coordination.enabler`

`same-worktree-coordination.md` assertions replaced:

- [x] line 14

  ```text
  old: - A same-worktree delegation records the sender as the tracked-file and Git owner and carries no write scope: the recipient reads the shared tree and returns its result in the mail record, and the mail body is the payload. The plugin validates that shape and writes nothing; a draft artifact home belongs to the `spx` CLI, whose `.spx/` state logic [`spx/21-spec-tree.enabler/15-hook-state-delegation.adr.md`](spx/21-spec-tree.enabler/15-hook-state-delegation.adr.md) keeps out of every plugin-shipped script.
  new: - A same-worktree delegation records the sender as the tracked-file and Git owner and carries no write scope: the recipient reads the shared tree and returns its result in the mail record, and the mail body is the payload. The plugin validates that shape and writes nothing; a draft artifact home belongs to the `spx` CLI, whose `.spx/` state logic [`spx/21-product-tree.enabler/15-hook-state-delegation.adr.md`](spx/21-product-tree.enabler/15-hook-state-delegation.adr.md) keeps out of every plugin-shipped script.
  ```

### `spx/43-coding-agents.enabler/43-position-direction.enabler/21-position-overrides.enabler`

`position-overrides.md` assertions replaced:

- [x] line 18

  ```text
  old: - ALWAYS: the keys and their shipped defaults are `mail.channel`, the mail project of the repository's own common Git directory; `mail.agent`, unset, so mail operations report unavailable; `positions`, empty, each entry naming a position's display name, environment, working directory, mail name, stall minutes, and context percent; `executor_groups`, empty, each naming a label, environment, working-directory prefix, and exclusions; `launchers`, empty, mapping a Product checkout path to the position that launches its Executors; `untouchable_panes`, empty; `advisor`, unset, so forwarding reports unavailable; `interval_seconds`, 1800; `compact_at_percent`, 30; `doorbell_start_delay_seconds`, 300; `pace`, unset, so no pacing applies; and `resume_line`, a line naming `/spec-tree:understand`, the resume note, the expectations, and the mail channel ([audit])
  new: - ALWAYS: the keys and their shipped defaults are `mail.channel`, the mail project of the repository's own common Git directory; `mail.agent`, unset, so mail operations report unavailable; `positions`, empty, each entry naming a position's display name, environment, working directory, mail name, stall minutes, and context percent; `executor_groups`, empty, each naming a label, environment, working-directory prefix, and exclusions; `launchers`, empty, mapping a Product checkout path to the position that launches its Executors; `untouchable_panes`, empty; `advisor`, unset, so forwarding reports unavailable; `interval_seconds`, 1800; `compact_at_percent`, 30; `doorbell_start_delay_seconds`, 300; `pace`, unset, so no pacing applies; and `resume_line`, a line naming `/product-tree:understand`, the resume note, the expectations, and the mail channel ([audit])
  ```

### `spx/43-go.enabler`

`go.md` other lines replaced:

- [x] line 8

  ```text
  old: SO THAT Go projects using spec-tree
  new: SO THAT Go projects using product-tree
  ```

- [x] line 11

  ```text
  old: The Go plugin composes foundational methodology with language-specific standards and workflows. The `audit-go-{code|test|architecture}` skills carry no language-specific auditor agent; `implementation-auditor` composes all three, `adr-auditor` composes `audit-go-architecture`, and `test-evidence-auditor` composes `audit-go-test`, per [`spx/21-spec-tree.enabler/17-audit.adr.md`](spx/21-spec-tree.enabler/17-audit.adr.md). Go concurrency soundness and `unsafe`/cgo boundary soundness are part of the Go code audit (`audit-go-code`). The Go test conventions the skills teach are decided in [`spx/43-go.enabler/15-go-testing.adr.md`](spx/43-go.enabler/15-go-testing.adr.md).
  new: The Go plugin composes foundational methodology with language-specific standards and workflows. The `audit-go-{code|test|architecture}` skills carry no language-specific auditor agent; `implementation-auditor` composes all three, `adr-auditor` composes `audit-go-architecture`, and `test-evidence-auditor` composes `audit-go-test`, per [`spx/21-product-tree.enabler/17-audit.adr.md`](spx/21-product-tree.enabler/17-audit.adr.md). Go concurrency soundness and `unsafe`/cgo boundary soundness are part of the Go code audit (`audit-go-code`). The Go test conventions the skills teach are decided in [`spx/43-go.enabler/15-go-testing.adr.md`](spx/43-go.enabler/15-go-testing.adr.md).
  ```

### `spx/43-prose.enabler`

`prose.md` other lines replaced:

- [x] line 7

  ```text
  old: The prose plugin exposes three workflow skills. `/author-prose-architecture` writes prose ADRs: structural decisions for the prose artifacts a spec node governs, driven by that node and located in the spec tree. `/author-prose` is the prose artifact's sole writer: it takes the kind, composes that kind's standards layers, and writes text that complies with the governing ADR. `/audit-prose` is the audit methodology: it takes the kind and judges the artifact, and the `prose-auditor` thin agent fronts it so a verdict is produced in a separate Verifier's agent session. No workflow skill dispatches another agent session; dispatch is the calling flow's. Chat responses to the user route to none of these — the plugin's rendered output style governs them. Operational prose — a code comment, a commit message, an agent-facing instruction — likewise stays outside the prose surface, with the workflow that owns it.
  new: The prose plugin exposes three workflow skills. `/author-prose-architecture` writes prose ADRs: structural decisions for the prose artifacts a spec node governs, driven by that node and located in the product tree. `/author-prose` is the prose artifact's sole writer: it takes the kind, composes that kind's standards layers, and writes text that complies with the governing ADR. `/audit-prose` is the audit methodology: it takes the kind and judges the artifact, and the `prose-auditor` thin agent fronts it so a verdict is produced in a separate Verifier's agent session. No workflow skill dispatches another agent session; dispatch is the calling flow's. Chat responses to the user route to none of these — the plugin's rendered output style governs them. Operational prose — a code comment, a commit message, an agent-facing instruction — likewise stays outside the prose surface, with the workflow that owns it.
  ```

### `spx/43-python.enabler`

`python.md` other lines replaced:

- [x] line 4

  ```text
  old: SO THAT Python projects using spec-tree
  new: SO THAT Python projects using product-tree
  ```

- [x] line 7

  ```text
  old: The python plugin contains 9 skills: `/python-code-standards` (reference), `/python-architecture-standards` (reference), `/python-test-standards` (reference), `/author-python-test`, `/author-python-code`, `/audit-python-code`, `/audit-python-test`, `/author-python-architecture`, `/audit-python-architecture`. The `audit-python-{code|test|architecture}` skills carry no Python-specific auditor agent; `implementation-auditor` composes all three, `adr-auditor` composes `audit-python-architecture`, and `test-evidence-auditor` composes `audit-python-test`, per [`spx/21-spec-tree.enabler/17-audit.adr.md`](spx/21-spec-tree.enabler/17-audit.adr.md).
  new: The python plugin contains 9 skills: `/python-code-standards` (reference), `/python-architecture-standards` (reference), `/python-test-standards` (reference), `/author-python-test`, `/author-python-code`, `/audit-python-code`, `/audit-python-test`, `/author-python-architecture`, `/audit-python-architecture`. The `audit-python-{code|test|architecture}` skills carry no Python-specific auditor agent; `implementation-auditor` composes all three, `adr-auditor` composes `audit-python-architecture`, and `test-evidence-auditor` composes `audit-python-test`, per [`spx/21-product-tree.enabler/17-audit.adr.md`](spx/21-product-tree.enabler/17-audit.adr.md).
  ```

### `spx/43-python.enabler/25-python-standards.enabler`

`python-standards.md` assertions replaced:

- [x] line 14

  ```text
  old: - ALWAYS: Python-specific standards live here, while marketplace-wide methodology (atemporal voice, ADR section structure, evidence mechanisms, and test-infrastructure semantics) lives at the spec-tree root or in cross-language decision records — duplication would force language-specific specs to restate methodology ([audit])
  new: - ALWAYS: Python-specific standards live here, while marketplace-wide methodology (atemporal voice, ADR section structure, evidence mechanisms, and test-infrastructure semantics) lives at the product-tree root or in cross-language decision records — duplication would force language-specific specs to restate methodology ([audit])
  ```

- [x] line 15

  ```text
  old: - NEVER: place execution-lane or methodology rules under this enabler — those are governed by product-level decisions and spec-tree methodology references; this enabler scopes only Python-specific concerns ([audit])
  new: - NEVER: place execution-lane or methodology rules under this enabler — those are governed by product-level decisions and product-tree methodology references; this enabler scopes only Python-specific concerns ([audit])
  ```

### `spx/43-python.enabler/25-python-standards.enabler/29-python-code.enabler`

`python-code.md` assertions replaced:

- [x] line 11

  ```text
  old: - ALWAYS: Python implementation work starts from complete spec-tree context, governing ADRs/PDRs, and lower-index Python standards — code follows declared product truth rather than local precedent ([audit])
  new: - ALWAYS: Python implementation work starts from complete product-tree context, governing ADRs/PDRs, and lower-index Python standards — code follows declared product truth rather than local precedent ([audit])
  ```

`python-code.md` other lines replaced:

- [x] line 4

  ```text
  old: SO THAT Python products using spec-tree
  new: SO THAT Python products using product-tree
  ```

### `spx/43-rust.enabler`

`rust.md` other lines replaced:

- [x] line 8

  ```text
  old: SO THAT Rust projects using spec-tree
  new: SO THAT Rust projects using product-tree
  ```

- [x] line 11

  ```text
  old: The Rust plugin composes foundational methodology with language-specific standards and workflows. The `audit-rust-{code|test|architecture}` skills carry no language-specific auditor agent; `implementation-auditor` composes all three, `adr-auditor` composes `audit-rust-architecture`, and `test-evidence-auditor` composes `audit-rust-test`, per [`spx/21-spec-tree.enabler/17-audit.adr.md`](spx/21-spec-tree.enabler/17-audit.adr.md). Rust `unsafe`/FFI soundness is part of the Rust code audit (`audit-rust-code`).
  new: The Rust plugin composes foundational methodology with language-specific standards and workflows. The `audit-rust-{code|test|architecture}` skills carry no language-specific auditor agent; `implementation-auditor` composes all three, `adr-auditor` composes `audit-rust-architecture`, and `test-evidence-auditor` composes `audit-rust-test`, per [`spx/21-product-tree.enabler/17-audit.adr.md`](spx/21-product-tree.enabler/17-audit.adr.md). Rust `unsafe`/FFI soundness is part of the Rust code audit (`audit-rust-code`).
  ```

### `spx/43-typescript.enabler`

`typescript.md` other lines replaced:

- [x] line 8

  ```text
  old: SO THAT TypeScript projects using spec-tree
  new: SO THAT TypeScript projects using product-tree
  ```

- [x] line 11

  ```text
  old: The TypeScript plugin composes foundational methodology with language-specific standards and workflows. The `audit-typescript-{code|test|architecture}` skills carry no language-specific auditor agent; `implementation-auditor` composes all three, `adr-auditor` composes `audit-typescript-architecture`, and `test-evidence-auditor` composes `audit-typescript-test`, per [`spx/21-spec-tree.enabler/17-audit.adr.md`](spx/21-spec-tree.enabler/17-audit.adr.md).
  new: The TypeScript plugin composes foundational methodology with language-specific standards and workflows. The `audit-typescript-{code|test|architecture}` skills carry no language-specific auditor agent; `implementation-auditor` composes all three, `adr-auditor` composes `audit-typescript-architecture`, and `test-evidence-auditor` composes `audit-typescript-test`, per [`spx/21-product-tree.enabler/17-audit.adr.md`](spx/21-product-tree.enabler/17-audit.adr.md).
  ```

### `spx/43-typescript.enabler/25-typescript-standards.enabler`

`typescript-standards.md` assertions replaced:

- [x] line 14

  ```text
  old: - ALWAYS: TypeScript-specific standards live here, while marketplace-wide methodology (atemporal voice, ADR section structure, evidence mechanisms) lives at the spec-tree root or under `spx/21-spec-tree.enabler/` — duplication would force language-specific specs to restate the methodology ([audit])
  new: - ALWAYS: TypeScript-specific standards live here, while marketplace-wide methodology (atemporal voice, ADR section structure, evidence mechanisms) lives at the product-tree root or under `spx/21-product-tree.enabler/` — duplication would force language-specific specs to restate the methodology ([audit])
  ```

- [x] line 15

  ```text
  old: - NEVER: place execution-lane or methodology rules under this enabler — those are governed by [`spx/31-outcomeeng.enabler/31-verification.enabler/14-verification.pdr.md`](spx/31-outcomeeng.enabler/31-verification.enabler/14-verification.pdr.md) and the spec-tree methodology references; this enabler scopes only TypeScript-specific concerns ([audit])
  new: - NEVER: place execution-lane or methodology rules under this enabler — those are governed by [`spx/31-outcomeeng.enabler/31-verification.enabler/14-verification.pdr.md`](spx/31-outcomeeng.enabler/31-verification.enabler/14-verification.pdr.md) and the product-tree methodology references; this enabler scopes only TypeScript-specific concerns ([audit])
  ```

### `spx/43-typescript.enabler/25-typescript-standards.enabler/29-typescript-code.enabler`

`typescript-code.md` assertions replaced:

- [x] line 11

  ```text
  old: - ALWAYS: TypeScript implementation work starts from complete spec-tree context, governing ADRs/PDRs, and lower-index TypeScript standards — code follows declared product truth rather than local precedent ([audit])
  new: - ALWAYS: TypeScript implementation work starts from complete product-tree context, governing ADRs/PDRs, and lower-index TypeScript standards — code follows declared product truth rather than local precedent ([audit])
  ```

`typescript-code.md` other lines replaced:

- [x] line 4

  ```text
  old: SO THAT TypeScript projects using spec-tree
  new: SO THAT TypeScript projects using product-tree
  ```

### Nodes that move without a content change

- [x] `spx/21-spec-tree.enabler/13-agent-environment.enabler/43-session-directory.enabler` -> `spx/21-product-tree.enabler/13-agent-environment.enabler/43-session-directory.enabler`
- [x] `spx/21-spec-tree.enabler/13-infrastructure.enabler/21-github-actions.enabler/21-platform-boundary.enabler` -> `spx/21-product-tree.enabler/13-infrastructure.enabler/21-github-actions.enabler/21-platform-boundary.enabler`
- [x] `spx/21-spec-tree.enabler/13-infrastructure.enabler/21-github-actions.enabler/43-workflow-design.enabler` -> `spx/21-product-tree.enabler/13-infrastructure.enabler/21-github-actions.enabler/43-workflow-design.enabler`
- [x] `spx/21-spec-tree.enabler/13-infrastructure.enabler/21-github-actions.enabler/54-workflow-review.enabler` -> `spx/21-product-tree.enabler/13-infrastructure.enabler/21-github-actions.enabler/54-workflow-review.enabler`
- [x] `spx/21-spec-tree.enabler/13-infrastructure.enabler/21-github-actions.enabler/65-workflow-evolution.enabler` -> `spx/21-product-tree.enabler/13-infrastructure.enabler/21-github-actions.enabler/65-workflow-evolution.enabler`
- [x] `spx/21-spec-tree.enabler/14-version-control.enabler` -> `spx/21-product-tree.enabler/14-version-control.enabler`
- [x] `spx/21-spec-tree.enabler/14-version-control.enabler/15-changeset-scope.enabler` -> `spx/21-product-tree.enabler/14-version-control.enabler/15-changeset-scope.enabler`
- [x] `spx/21-spec-tree.enabler/35-artifact-registry.enabler` -> `spx/21-product-tree.enabler/35-artifact-registry.enabler`
- [x] `spx/21-spec-tree.enabler/35-evidence.enabler/39-eval-skill.enabler` -> `spx/21-product-tree.enabler/35-evidence.enabler/39-eval-skill.enabler`
- [x] `spx/21-spec-tree.enabler/35-evidence.enabler/39-eval-skill.enabler/21-skill-eval.enabler` -> `spx/21-product-tree.enabler/35-evidence.enabler/39-eval-skill.enabler/21-skill-eval.enabler`
- [x] `spx/21-spec-tree.enabler/35-evidence.enabler/39-test-skill.enabler` -> `spx/21-product-tree.enabler/35-evidence.enabler/39-test-skill.enabler`
- [x] `spx/21-spec-tree.enabler/54-authoring.enabler` -> `spx/21-product-tree.enabler/54-authoring.enabler`
- [x] `spx/21-spec-tree.enabler/54-decomposing.enabler` -> `spx/21-product-tree.enabler/54-decomposing.enabler`
- [x] `spx/21-spec-tree.enabler/68-audit.enabler/21-state-surface.enabler` -> `spx/21-product-tree.enabler/68-audit.enabler/21-state-surface.enabler`
- [x] `spx/21-spec-tree.enabler/68-audit.enabler/32-audit-assertions.enabler` -> `spx/21-product-tree.enabler/68-audit.enabler/32-audit-assertions.enabler`
- [x] `spx/21-spec-tree.enabler/68-audit.enabler/32-pr-thread-state-surface.enabler` -> `spx/21-product-tree.enabler/68-audit.enabler/32-pr-thread-state-surface.enabler`
- [x] `spx/21-spec-tree.enabler/76-merge.enabler/32-direct-push.enabler` -> `spx/21-product-tree.enabler/76-merge.enabler/32-direct-push.enabler`
- [x] `spx/13-infrastructure.enabler/13-host-readiness.enabler` -> `spx/13-infrastructure.enabler/13-host-readiness.enabler`
- [x] `spx/13-infrastructure.enabler/25-eval-harness.enabler` -> `spx/13-infrastructure.enabler/25-eval-harness.enabler`
- [x] `spx/15-validation.enabler/32-plugin-manifest.enabler` -> `spx/15-validation.enabler/32-plugin-manifest.enabler`
- [x] `spx/15-validation.enabler/32-runtime-token.enabler` -> `spx/15-validation.enabler/32-runtime-token.enabler`
- [x] `spx/15-validation.enabler/32-scratch-path.enabler` -> `spx/15-validation.enabler/32-scratch-path.enabler`
- [x] `spx/18-plugin-build.enabler/21-source-and-templating.enabler` -> `spx/18-plugin-build.enabler/21-source-and-templating.enabler`
- [x] `spx/18-plugin-build.enabler/21-source-and-templating.enabler/21-runtime-parameterization.enabler` -> `spx/18-plugin-build.enabler/21-source-and-templating.enabler/21-runtime-parameterization.enabler`
- [x] `spx/18-plugin-build.enabler/43-target-emission.enabler` -> `spx/18-plugin-build.enabler/43-target-emission.enabler`
- [x] `spx/18-plugin-build.enabler/54-conversion.enabler/21-agents.enabler` -> `spx/18-plugin-build.enabler/54-conversion.enabler/21-agents.enabler`
- [x] `spx/18-plugin-build.enabler/54-conversion.enabler/21-agents.enabler/54-execution-policy.enabler` -> `spx/18-plugin-build.enabler/54-conversion.enabler/21-agents.enabler/54-execution-policy.enabler`
- [x] `spx/18-plugin-build.enabler/65-build-orchestration.enabler` -> `spx/18-plugin-build.enabler/65-build-orchestration.enabler`
- [x] `spx/21-catalog.enabler` -> `spx/21-catalog.enabler`
- [x] `spx/31-outcomeeng.enabler/31-verification.enabler` -> `spx/31-outcomeeng.enabler/31-verification.enabler`
- [x] `spx/31-outcomeeng.enabler/31-verification.enabler/31-eval-verification.enabler` -> `spx/31-outcomeeng.enabler/31-verification.enabler/31-eval-verification.enabler`
- [x] `spx/31-outcomeeng.enabler/31-verification.enabler/31-test-verification.enabler` -> `spx/31-outcomeeng.enabler/31-verification.enabler/31-test-verification.enabler`
- [x] `spx/31-outcomeeng.enabler/32-changes.enabler` -> `spx/31-outcomeeng.enabler/32-changes.enabler`
- [x] `spx/32-distribution.enabler` -> `spx/32-distribution.enabler`
- [x] `spx/32-distribution.enabler/21-bump.enabler` -> `spx/32-distribution.enabler/21-bump.enabler`
- [x] `spx/43-coding-agents.enabler` -> `spx/43-coding-agents.enabler`
- [x] `spx/43-coding-agents.enabler/18-agent-mail.enabler` -> `spx/43-coding-agents.enabler/18-agent-mail.enabler`
- [x] `spx/43-coding-agents.enabler/18-herdr-environment.enabler` -> `spx/43-coding-agents.enabler/18-herdr-environment.enabler`
- [x] `spx/43-coding-agents.enabler/21-agent-communication.enabler` -> `spx/43-coding-agents.enabler/21-agent-communication.enabler`
- [x] `spx/43-coding-agents.enabler/21-usage-controller.enabler` -> `spx/43-coding-agents.enabler/21-usage-controller.enabler`
- [x] `spx/43-coding-agents.enabler/32-native-agent-recovery.enabler` -> `spx/43-coding-agents.enabler/32-native-agent-recovery.enabler`
- [x] `spx/43-contribute.enabler/43-pull-requests.enabler` -> `spx/43-contribute.enabler/43-pull-requests.enabler`
- [x] `spx/43-instructions.enabler` -> `spx/43-instructions.enabler`
- [x] `spx/43-instructions.enabler/21-skills.enabler` -> `spx/43-instructions.enabler/21-skills.enabler`
- [x] `spx/43-instructions.enabler/21-subagents.enabler` -> `spx/43-instructions.enabler/21-subagents.enabler`
- [x] `spx/43-typescript.enabler/25-typescript-standards.enabler/21-typescript-architecture.enabler` -> `spx/43-typescript.enabler/25-typescript-standards.enabler/21-typescript-architecture.enabler`
- [x] `spx/43-typescript.enabler/25-typescript-standards.enabler/25-typescript-tests.enabler` -> `spx/43-typescript.enabler/25-typescript-standards.enabler/25-typescript-tests.enabler`
- [x] `spx/43-work.enabler` -> `spx/43-work.enabler`

## Code, tests, and infrastructure outside the tree

Files outside `spx/`, `src/plugins/spec-tree/`, and `dist/` that carry the term, with the number of lines each. A `CHANGELOG.md` keeps its history and takes only the Breaking entry named above. A file under `prototypes/` renames its prose and keeps its identifiers. A fixture whose text is a captured CLI payload or a retired-marker sample keeps the spelling the capture or the sample needs.

- [x] `.agents/plugins/marketplace.json` (2 lines)
- [x] `.claude-plugin/marketplace.json` (3 lines)
- [x] `.claude/settings.json` (1 lines)
- [x] `.codex/config.toml` (1 lines)
- [x] `.github/CLAUDE_WORKFLOWS.md` (8 lines)
- [x] `.github/workflows/refresh-instruction-blocks.yml` (1 lines)
- [x] `.github/workflows/spec-tree-evals.yml` (91 lines)
- [x] `.github/workflows/spec-tree-review.yml` (25 lines)
- [x] `.github/workflows/spec-tree.yml` (25 lines)
- [x] `.pi/claude-plugins.json` (1 lines)
- [x] `.sonarcloud.properties` (2 lines)
- [x] `AGENTS.md` (33 lines)
- [x] `CHANGELOG.md` (2 lines)
- [x] `CLAUDE.md` (33 lines)
- [x] `README.md` (30 lines)
- [x] `docs/cross-language-test-standards-drift-audit.md` (5 lines)
- [x] `docs/tutorial.md` (7 lines)
- [x] `justfile` (6 lines)
- [x] `lefthook.yml` (1 lines)
- [x] `methodology/AGENTS.md` (2 lines)
- [x] `methodology/research/claude-code-compaction-prompt.md` (1 lines)
- [x] `methodology/skills/skill-structure.md` (33 lines)
- [x] `outcomeeng/distribution/artifact_registry.py` (10 lines)
- [x] `outcomeeng/distribution/contracts.py` (1 lines)
- [x] `outcomeeng/distribution/diagnose_manifest.py` (1 lines)
- [x] `outcomeeng/distribution/installation.py` (10 lines)
- [x] `outcomeeng/distribution/instruction_block.py` (8 lines)
- [x] `outcomeeng/merging_policy.py` (1 lines)
- [x] `outcomeeng/spec_tree_structure.py` (5 lines)
- [x] `outcomeeng/validation/_steps.py` (1 lines)
- [x] `outcomeeng/validation/audit_artifacts.py` (4 lines)
- [x] `outcomeeng/validation/eval_links.py` (3 lines)
- [x] `outcomeeng/validation/foundation_manifest.py` (9 lines)
- [x] `outcomeeng/validation/implementation_audit_contract.py` (4 lines)
- [x] `outcomeeng/validation/infrastructure_index.py` (3 lines)
- [x] `outcomeeng/validation/link_integrity.py` (1 lines)
- [x] `outcomeeng/validation/reference_portability.py` (2 lines)
- [x] `outcomeeng/validation/runtime_tokens.py` (6 lines)
- [x] `outcomeeng/validation/selected_gate.py` (7 lines)
- [x] `outcomeeng/validation/skill_reference.py` (2 lines)
- [x] `outcomeeng/validation/spx_version.py` (2 lines)
- [x] `outcomeeng_testing/evals/__init__.py` (1 lines)
- [x] `outcomeeng_testing/evals/cli.py` (5 lines)
- [x] `outcomeeng_testing/evals/factories.py` (6 lines)
- [x] `outcomeeng_testing/evals/just_recipes.py` (1 lines)
- [x] `outcomeeng_testing/fixtures/agent_conversion/codex-rendered-agent.md` (1 lines)
- [x] `outcomeeng_testing/fixtures/agent_conversion/source-agent.md` (2 lines)
- [x] `outcomeeng_testing/fixtures/audit_change_run/change-record.md.txt` (3 lines)
- [x] `outcomeeng_testing/fixtures/ci_gate/violating_bounds/over_bound.yml` (1 lines)
- [x] `outcomeeng_testing/fixtures/installation/claude-code-2.1.296-plugin-update-unrecorded.stderr.txt` (1 lines)
- [x] `outcomeeng_testing/fixtures/installation/installed_plugins.json` (3 lines)
- [x] `outcomeeng_testing/fixtures/instruction_block/retired-managed.md` (6 lines)
- [x] `outcomeeng_testing/fixtures/instruction_block/shared-region-alternate.md` (2 lines)
- [x] `outcomeeng_testing/fixtures/instruction_block/shared-region-primary.md` (2 lines)
- [x] `outcomeeng_testing/fixtures/link_conversion/expected/docs/outside.md` (1 lines)
- [x] `outcomeeng_testing/fixtures/link_conversion/input/docs/outside.md` (1 lines)
- [x] `outcomeeng_testing/generators/grant_locality.py` (1 lines)
- [x] `outcomeeng_testing/generators/installation.py` (16 lines)
- [x] `outcomeeng_testing/generators/instruction_block.py` (1 lines)
- [x] `outcomeeng_testing/generators/link_conversion.py` (5 lines)
- [x] `outcomeeng_testing/generators/review_thread_resolver.py` (1 lines)
- [x] `outcomeeng_testing/generators/reviewing_changes.py` (5 lines)
- [x] `outcomeeng_testing/harnesses/agent_conversion.py` (5 lines)
- [x] `outcomeeng_testing/harnesses/agent_mail.py` (1 lines)
- [x] `outcomeeng_testing/harnesses/agent_tokens.py` (2 lines)
- [x] `outcomeeng_testing/harnesses/assertion_audit_run.py` (6 lines)
- [x] `outcomeeng_testing/harnesses/audit_change_run.py` (8 lines)
- [x] `outcomeeng_testing/harnesses/audit_verification_run_contract.py` (12 lines)
- [x] `outcomeeng_testing/harnesses/changeset_scope.py` (3 lines)
- [x] `outcomeeng_testing/harnesses/ci_triggers.py` (2 lines)
- [x] `outcomeeng_testing/harnesses/dist_drift.py` (1 lines)
- [x] `outcomeeng_testing/harnesses/hooks.py` (9 lines)
- [x] `outcomeeng_testing/harnesses/host_readiness.py` (1 lines)
- [x] `outcomeeng_testing/harnesses/implementation_scope.py` (2 lines)
- [x] `outcomeeng_testing/harnesses/infrastructure_index.py` (3 lines)
- [x] `outcomeeng_testing/harnesses/installation.py` (54 lines)
- [x] `outcomeeng_testing/harnesses/instruction_block.py` (2 lines)
- [x] `outcomeeng_testing/harnesses/instruction_block_compliance_evidence.py` (2 lines)
- [x] `outcomeeng_testing/harnesses/journal_projection.py` (2 lines)
- [x] `outcomeeng_testing/harnesses/link_conversion.py` (3 lines)
- [x] `outcomeeng_testing/harnesses/plugin_authorization.py` (1 lines)
- [x] `outcomeeng_testing/harnesses/plugin_manifest.py` (2 lines)
- [x] `outcomeeng_testing/harnesses/producer_section_prompt.py` (1 lines)
- [x] `outcomeeng_testing/harnesses/report_changes.py` (1 lines)
- [x] `outcomeeng_testing/harnesses/review_thread_resolver.py` (1 lines)
- [x] `outcomeeng_testing/harnesses/reviewing_changes.py` (8 lines)
- [x] `outcomeeng_testing/harnesses/reviewing_changes_audit.py` (1 lines)
- [x] `outcomeeng_testing/harnesses/spec_tree.py` (8 lines)
- [x] `outcomeeng_testing/harnesses/sync_base.py` (1 lines)
- [x] `outcomeeng_testing/harnesses/worktree_provisioning.py` (3 lines)
- [x] `prototypes/eval-cache-amortization/FINDINGS.md` (6 lines)
- [x] `prototypes/eval-cache-amortization/README.md` (4 lines)
- [x] `prototypes/eval-cache-amortization/investigation.md` (2 lines)
- [x] `prototypes/interview-live/README.md` (3 lines)
- [x] `prototypes/interview-live/boot.py` (1 lines)
- [x] `prototypes/interview-live/mcp_server.py` (7 lines)
- [x] `prototypes/interview-live/projection.py` (3 lines)
- [x] `prototypes/interview-live/seed.json` (2 lines)
- [x] `prototypes/interview-live/shell.html` (5 lines)
- [x] `prototypes/interview-live/spx_seed.py` (2 lines)
- [x] `prototypes/interview-live/state.py` (2 lines)
- [x] `renovate.json` (3 lines)
- [x] `scripts/distribution.yml` (5 lines)
- [x] `spx/local/generated-sources.toml` (9 lines)
- [x] `spx/local/merging.md` (4 lines)
- [x] `src/plugins/coding-agents/CHANGELOG.md` (2 lines)
- [x] `src/plugins/coding-agents/skills/direct-positions/SKILL.md` (1 lines)
- [x] `src/plugins/coding-agents/skills/direct-positions/scripts/direction_core.py` (1 lines)
- [x] `src/plugins/coding-agents/skills/orchestrate-change/SKILL.md` (4 lines)
- [x] `src/plugins/contribute/CHANGELOG.md` (1 lines)
- [x] `src/plugins/frontend/CHANGELOG.md` (1 lines)
- [x] `src/plugins/go/CHANGELOG.md` (2 lines)
- [x] `src/plugins/go/skills/audit-go-architecture/SKILL.md` (1 lines)
- [x] `src/plugins/go/skills/audit-go-code/SKILL.md` (1 lines)
- [x] `src/plugins/go/skills/audit-go-test/SKILL.md` (5 lines)
- [x] `src/plugins/go/skills/author-go-architecture/SKILL.md` (7 lines)
- [x] `src/plugins/go/skills/author-go-code/SKILL.md` (7 lines)
- [x] `src/plugins/go/skills/author-go-test/SKILL.md` (2 lines)
- [x] `src/plugins/hdl/CHANGELOG.md` (1 lines)
- [x] `src/plugins/instructions/CHANGELOG.md` (3 lines)
- [x] `src/plugins/instructions/skills/agent-prompt-standards/SKILL.md` (1 lines)
- [x] `src/plugins/instructions/skills/audit-skill/SKILL.md` (1 lines)
- [x] `src/plugins/instructions/skills/audit-skill/references/touched-text.md` (1 lines)
- [x] `src/plugins/instructions/skills/audit-subagent/SKILL.md` (1 lines)
- [x] `src/plugins/instructions/skills/audit-subagent/references/touched-text.md` (1 lines)
- [x] `src/plugins/instructions/skills/author-subagent/references/subagents.md` (4 lines)
- [x] `src/plugins/instructions/skills/skill-standards/SKILL.md` (3 lines)
- [x] `src/plugins/prose/CHANGELOG.md` (7 lines)
- [x] `src/plugins/prose/skills/audit-prose/SKILL.md` (3 lines)
- [x] `src/plugins/prose/skills/author-prose/SKILL.md` (1 lines)
- [x] `src/plugins/python/CHANGELOG.md` (2 lines)
- [x] `src/plugins/python/skills/audit-python-architecture/SKILL.md` (1 lines)
- [x] `src/plugins/python/skills/audit-python-test/SKILL.md` (6 lines)
- [x] `src/plugins/python/skills/author-python-architecture/SKILL.md` (3 lines)
- [x] `src/plugins/python/skills/author-python-code/SKILL.md` (2 lines)
- [x] `src/plugins/python/skills/author-python-test/SKILL.md` (3 lines)
- [x] `src/plugins/python/skills/python-test-standards/SKILL.md` (2 lines)
- [x] `src/plugins/rust/CHANGELOG.md` (3 lines)
- [x] `src/plugins/rust/skills/audit-rust-architecture/SKILL.md` (1 lines)
- [x] `src/plugins/rust/skills/audit-rust-code/SKILL.md` (1 lines)
- [x] `src/plugins/rust/skills/audit-rust-test/SKILL.md` (5 lines)
- [x] `src/plugins/rust/skills/author-rust-architecture/SKILL.md` (8 lines)
- [x] `src/plugins/rust/skills/author-rust-code/SKILL.md` (7 lines)
- [x] `src/plugins/rust/skills/author-rust-test/SKILL.md` (1 lines)
- [x] `src/plugins/rust/skills/rust-test-standards/SKILL.md` (2 lines)
- [x] `src/plugins/typescript/CHANGELOG.md` (3 lines)
- [x] `src/plugins/typescript/skills/audit-typescript-test/SKILL.md` (6 lines)
- [x] `src/plugins/typescript/skills/author-typescript-architecture/SKILL.md` (6 lines)
- [x] `src/plugins/typescript/skills/author-typescript-code/SKILL.md` (6 lines)
- [x] `src/plugins/typescript/skills/author-typescript-code/workflows/implementation.md` (1 lines)
- [x] `src/plugins/typescript/skills/author-typescript-test/SKILL.md` (2 lines)
- [x] `src/plugins/typescript/skills/typescript-test-standards/SKILL.md` (4 lines)
- [x] `src/plugins/typescript/skills/typescript-test-standards/levels/l1-local-deterministic.md` (1 lines)
- [x] `src/plugins/work/CHANGELOG.md` (1 lines)
- [x] `src/templates/plugin/SKILL.md` (1 lines)

## Follow-ups outside this Change

- [outcomeeng/changes#768](https://github.com/outcomeeng/changes/issues/768): the `spx` CLI help text (Product spx)
- [outcomeeng/changes#769](https://github.com/outcomeeng/changes/issues/769): `spx` -> `arbor` in this repository, blocked by #767
- [outcomeeng/changes#770](https://github.com/outcomeeng/changes/issues/770): the reusable review workflows, their variables, and the trigger phrase, blocked by #767
- [outcomeeng/changes#771](https://github.com/outcomeeng/changes/issues/771): the standalone skills repository, blocked by #767
