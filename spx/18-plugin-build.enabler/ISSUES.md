# ISSUES — plugin-build / post-restructure follow-ups

## Property predicates are hidden in boolean-returning harnesses

Implementation audit `2026-09-14_11-26-09-644-eb39d2a3b433` rejected
`tests/test_plugin_build.property.l1.py:21`: the formatter-version-drift test
asserts a boolean returned by `canonical_build_rejects_formatter_version_drift`.
The other two tests in that file use the same assertion-delegation pattern.
The test-infrastructure PDR requires predicates in linked tests and observations
from harnesses. Hidden predicates prevent the test file from exposing its oracle.

The audited test file is unchanged by the formatter-version update at
`349e3c3be3f88f496f228666036d6790b5be2a3c`. This records the rejected subject
under the merge policy for audit findings outside the changed files; it supplies
no evidence-audit approval. Settlement requires observation-returning harnesses
and test-owned predicates across this file, followed by a passing evidence audit.
Revisit before relying on this node's evidence-audit approval or changing these tests.

Known issues left by the `src/plugins/` → `dist/` build restructure. Coordination note; not spec truth.

## 1. `spx/` spec references still cite the pre-restructure `plugins/` path

The restructure migrated `AGENTS.md` references to `src/plugins/` but left `spx/` specs and decision records citing `plugins/spec-tree/skills/...`. Spec/decision files under `spx/` still use the old `plugins/` path — enumerate the live set with `grep -rln 'plugins/spec-tree' spx/` (the bare `plugins/`, not the migrated `src/plugins/`). Several matches are spec-assertion subjects and decision-record text, not only backtick citations — for example `spx/21-spec-tree.enabler/17-audit.adr.md`, `spx/21-spec-tree.enabler/68-reviewing.enabler/21-reviewing-changes.enabler/reviewing-changes.md`, and `spx/21-spec-tree.enabler/14-version-control.enabler/15-changeset-scope.enabler/13-changeset-derivation.adr.md`. Authored skills now live at `src/plugins/spec-tree/skills/...`; the generated output is `dist/{claude,codex}/...`. Migrate the prose references to the authored-source path. These are backtick citations, not Markdown links, so `just check` does not flag them — a deliberate repo-wide reference migration is needed, separate from any single node's work.

## 2. Codex rendering for Claude-authored argument syntax

Source skills are authored in Claude Code's supported `SKILL.md` syntax. `src/plugins/instructions/skills/skill-standards/references/command-capabilities.md` permits `$ARGUMENTS` for whole-string instruction capture and keeps `arguments` / `$name` for stable positional tokens. That source policy resolves the former skill-auditor contradiction that treated bare `$ARGUMENTS` as command-only syntax.

The remaining concern belongs to generated Codex output: when authored source uses a Claude-supported form that Codex does not consume directly, the build renderer must adapt Codex runtime output without weakening the authored source.

Audit checklist:

- Enumerate every authored skill argument form: `$ARGUMENTS`, `$ARGUMENTS[N]`, `$N`, declared `$name`, and `arguments`.
- Compare each generated Codex skill surface against the Codex runtime's consumed argument syntax.
- Classify each surface as works as rendered, requires build adaptation, or requires source-policy clarification.
- Preserve `$ARGUMENTS` in authored source when a skill accepts free-form multi-word instructions or forwards instructions between lifecycle skills.
- Preserve `arguments` / `$name` in authored source when a stable token boundary improves reliability for agent invocation or convenience for user invocation.
- Implement any required adaptation in the build renderer and regenerate committed runtime output.

Required handling: run the audit as a plugin-build/runtime-parameterization follow-up before editing the build. Gate any implementation with the focused runtime-parameterization tests, `just build-skills`, `just check-skills`, `just docs-check`, and the repository's merge lifecycle. Surfaced by the argument-syntax review during `feat/guide-filename-runtime-token` (2026-06-26).

## 3. Claude verifier subagents can inherit the globally configured Advisor model

Claude Code 2.1.207 enables its server-side Advisor tool when user settings carry `advisorModel`. A local A/B startup probe confirmed that inherited `"advisorModel": "fable"` enables `claude-fable-5`, while the command-level override `--settings '{"advisorModel":""}'` suppresses Advisor initialization. An eval trial showed the consequence: a Sonnet verifier consulted Fable, adding $1.137 of uncached model cost and exhausting the run budget after total spend reached $1.554. Fable also consumes subscription quota at a higher rate, so verifier agents must never inherit it implicitly.

The eval harness controls its own Claude subprocess and disables Advisor at `outcomeeng_evals.runner.ClaudeCliRunner`. Native Claude verifier subagents launched through the built-in `Agent` tool bypass that adapter. Their agent frontmatter has no documented per-agent `advisorModel` field, so prompt guidance and tool allowlists do not prove suppression of the server-side Advisor tool.

Revisit condition: before claiming cost-bounded verifier-agent execution, identify and test a supported Claude Code control that disables Advisor for every native verifier subagent while preserving the parent conversation's chosen advisor configuration. Prefer an enforceable per-agent runtime field. If Claude Code exposes no such field, introduce one shared verifier-launch policy or project-level override and prove through startup/debug evidence that every verifier agent runs without Advisor initialization. Keep this concern distinct from model selection: each verifier's declared `model: sonnet` does not disable its Advisor tool.

## 4. The build ADR restates rules its spec nodes already own

`15-build-architecture.adr.md` carries nine `[audit]`-tagged rules that a child or sibling node already declares with a `[test]` link. `spx/15-spec-coverage.adr.md` forbids exactly that: "use `[test]` evidence for assertions about executable code — audit is not a substitute for automated verification."

| ADR rule                                            | Already declared with `[test]` at                              |
| --------------------------------------------------- | -------------------------------------------------------------- |
| Jinja2 custom delimiters                            | `21-source-and-templating.enabler`                             |
| shared content under `src/_shared/<scope>/<topic>/` | `21-source-and-templating.enabler`                             |
| the pre-commit build gate                           | `65-build-orchestration.enabler`                               |
| no execution-time injection in built output         | `43-target-emission.enabler`                                   |
| no unescaped skill-directory token in Codex output  | `43-target-emission.enabler`                                   |
| render each divergent name from the registry        | `21-source-and-templating.enabler/21-runtime-parameterization` |
| registry keyed by token kind                        | `21-source-and-templating.enabler/21-runtime-parameterization` |
| frontmatter field stripping per target schema       | `43-target-emission.enabler`                                   |
| no raw runtime-divergent token in authored source   | `spx/15-validation.enabler/32-runtime-token.enabler`           |

**Resolution shape**: remove each restatement, leaving the decision that governs it. Distinguish a decision from a declaration by whether changing the sentence means a different architecture; if the same architecture spelled differently would falsify it, the spec owns it. Re-run `adr-auditor` afterwards.

**Also in the same pass**: the ADR's own `NEVER: add separate ADRs for individual build concerns` forbids splitting the decision if its concerns prove independently changeable.

**Not defects**, though an earlier draft of this entry listed them: the `### Testing` block's `[compliance]` tags carry no path because the canonical ADR template's Testing subsection has no path placeholder, unlike a spec assertion; and the no-separate-ADRs rule is correctly `[audit]`, being governance about decision shape.

**Evidence**: nine findings confirmed by `adr-auditor` against the decision as it stands on `main`.

## Optional tool-capability rendering has no deterministic evidence yet

Four untagged ALWAYS assertions declare the optional-capability class: the
optional-names lookup and complete-item removal in
`spx/18-plugin-build.enabler/21-source-and-templating.enabler/21-runtime-parameterization.enabler/runtime-parameterization.md`,
the remaining-item preservation and whole-field removal in
`spx/18-plugin-build.enabler/43-target-emission.enabler/target-emission.md`, and the
rendered-tool-only manual guidance and Codex composition in
`spx/18-plugin-build.enabler/54-conversion.enabler/21-agents.enabler/54-execution-policy.enabler/execution-policy.md`.
The behavior lives in `outcomeeng/distribution/build.py` (the registry's optional
names in `resolve_runtime_token`, `_remove_unavailable_frontmatter_items`,
`_remove_unavailable_tool_items`) and `outcomeeng/distribution/contracts.py`
(`RUNTIME_TOKEN_USE_SKILL_NAMES`). No
linked test exercises it: the `dist-diff` parity step detects drift between
authored source and generated output but not a wrong-but-stable rendering.

Commit `560a6e0ac4d13c680aedb73d5f797632baf32e20` added compliance tests and harness
changes for it; commit `4d2019250b17e8009649d127188bac24272f2550` withdrew them because
Change #76 treats these nodes as prototype scope — the three spec files carry no
`malleability` field, so the projector reads them as implementation-malleable —
adds no test file or test infrastructure, and assigns the fixtures, property generator, observation
harness, and linked tests to Change #85, whose assertion-design records #76
carries.

**Settlement condition**: Change #85 lands the deterministic evidence and tags
the four assertions with `[test](...)` links.

**Evidence**: `spec-tree:changes-reviewer` runs
`2026-09-18_03-20-58-166-8b80f274938c` and `2026-09-18_04-29-55-695-83f3737b9f22`
(debt, evidence) during Change #76.
