# Issues: Skill Authoring

Actionable findings from the post-merge skill audit of PR 458 at
`f5aa313016964a10854117e026ec4c3529106490`.

## Split router authority by workflow needs

`src/plugins/instructions/skills/create-skill/SKILL.md:5` grants `Bash`, `Write`,
`WebFetch`, and `WebSearch` to every route. Read-only audit and pattern-explanation
routes inherit mutation and network capabilities they do not use.

Required handling: narrow the router's top-level `allowed-tools` surface or split
routes whose authority requirements differ. Preserve the tools required by creation
and improvement workflows without granting them to read-only routes.

Source: skill-auditor finding `f-003`, rule `overbroad_allowed_tools`, severity
`WARNING`.

## Revalidate after exercise-driven edits

`src/plugins/instructions/skills/create-skill/workflows/create-new-skill.md:79`
allows the representative exercise to trigger iterative edits after deterministic
checks and the skill audit have already completed. The final bundle can therefore
differ from the bundle those gates evaluated.

Required handling: run the representative exercise before final validation, or loop
every exercise-driven edit back through deterministic checks and the complete-bundle
skill audit before publication.

Source: PR 458 review comment `3610850053`, classified as `DEBT` in the `evidence`
category after merge.

## The composing-skill assertion awaits verification selection

The assertion under `## Assertions` in `skills.md` that a composing skill names each
static dependency through the shared `require_skill` directive, states an argument- or
run-time-named dependency as the owned `Use skill` sentence, and declares skill-use
capability through the optional `tool('use_skill')` token is an authoring declaration
with no tag; every other assertion in the file carries `[audit]`. It is the fifth
declaration of the optional-capability class, beside the four
`spx/18-plugin-build.enabler/ISSUES.md` records under "Optional tool-capability
rendering has no deterministic evidence yet".

**Impact.** The declaration is approved for form only; no evidence result attaches to
it until a verification type is selected and tagged.

**Settlement condition.** Verification is selected for the assertion — `[audit]`
through the skill auditor's composed-dependency rule in `skill-standards`, or a
`[test]` link once the authored-source compliance evidence Change #85 lands reaches
skill bodies — and the tag is applied.

**Evidence.** CI changeset review on PR #584, head
`b0a6237f359687bd40a01755af6f4ff2d88387b2`, finding `DEBT [evidence]` at
`spx/43-instructions.enabler/21-skills.enabler/skills.md:15`, during Change #76.

## `skill-standards` names the eager-foundation exception by a section that does not hold it

`src/plugins/instructions/skills/skill-standards/SKILL.md:14` (`<success_criteria>`
(a)) points to "the eager-foundation exception in `<progressive_disclosure>`", and
`<progressive_disclosure>` at lines 320 and 346 says "unless the eager-foundation
exception below applies", while the exception lives in its own
`<eager_foundation_exception>` tag at line 301, which precedes
`<progressive_disclosure>`.

**Impact.** An author following the tag-by-name convention this skill prescribes
lands on a section that does not hold the rule.

**Settlement condition.** `<success_criteria>` names `<eager_foundation_exception>`
and both `<progressive_disclosure>` branches drop "below".

Source: `instructions:skill-auditor` finding rule `stale_cross_reference`, severity
`WARNING`, on head `524b9c46c7960a106d84ef856b4020a0ce904b16` during Change #76;
[Change #92](https://github.com/outcomeeng/changes/issues/92) carries the
standards-skill pass that owns it.

## `script-standards.md` states the testing-record requirement with a weak modal

`src/plugins/instructions/skills/skill-standards/references/script-standards.md:32`,
inside `<script_testing_rule>`, reads "The skill's documentation should record what
was tested and with what inputs"; `/agent-prompt-standards` `<constraint_language>`
bars "should" from a rule block.

**Impact.** The testing-record requirement reads as optional beside the preceding
"must be tested" sentence.

**Settlement condition.** The sentence reads "records what was tested and with what
inputs".

Source: `instructions:skill-auditor` finding rule `weak_modal_in_rule`, severity
`WARNING`, on head `524b9c46c7960a106d84ef856b4020a0ce904b16` during Change #76;
[Change #92](https://github.com/outcomeeng/changes/issues/92) carries the
standards-skill pass that owns it.

## The skill auditor returns opposite verdicts on unchanged skill text

`instructions:skill-auditor` ran against `src/plugins/coding-agents/skills/orchestrate-officers/`
across a run of consecutive heads and reversed itself in both directions, more than once, and inside
a single verdict document.

On head `08d4ef11a7085974f27e3cf58afe92942cde066c` it raised finding `f-007`, rule
`unverified_allow_list_match`, severity `WARNING`, against `SKILL.md` line 6: the `allowed-tools`
entry spells `${CLAUDE_SKILL_DIR}` inside a permission pattern, and whether that pattern matches
the command the loader issues is unestablished. On head
`387ba22d437193295ddd3287e449732ca52d7a96` it reported the same line as keep-these finding `f-003`,
rule `narrow_allowed_tools`, severity `INFO`, stating the grant satisfies `/skill-standards`
`references/command-capabilities.md` `<tool_restriction_security>`. The line is byte-identical
across the two heads: `git diff` between them over that file has no hunk before line 13, and
line 6 hashes to `67d58e26697f8a475031b50628f88ad7937c9c78f16c647d6dd000058971cbc4` at both.

The reversal runs the other way in the same pair. On the first head, keep-these finding `f-002`
praised the `<essential_principles>` result-acceptance contract for naming exact proof fields —
`response.result` against `response.output`, and the non-empty `projectKey`/`response`/`data` set —
as satisfying `/skill-standards` `<conciseness>` concrete-over-abstract, and stated that removing it
would leave every workflow's validation instruction pointing at nothing. On the second head,
finding `f-008`, rule `restated_dependency_contract`, severity `WARNING`, raised that restatement as
a defect and asked for its replacement by a citation to the owning capability skill. That passage is
not byte-identical between the heads: the second head rewrites the framing sentence to scope the
rule to a result reporting a store or environment command, and adds a paragraph carving out the
agent-mail project-key answer as the one result the rule does not govern. What does not change is
the restatement itself — every proof field `f-002` named survives verbatim, moving only from lines
43-47 to lines 39-44. `f-008` targets the presence of those fields, which is what `f-002` said the
skill would be worse without.

The router shape draws opposite readings. On head `581e53137d45defb65757dac683a3132e1edf5c6` the
run praised the coexistence of `<routing>` and `<workflows_index>` as the complete router shape. On
head `a18cf8929a8280899e6637c6d1b47482c5e61eeb` finding `f-005`, severity `WARNING`, asked for the
two to be merged into one table. Both sections are byte-identical across the pair: `<routing>`
occupies lines 71-84 and `<workflows_index>` lines 98-113 at both heads, and each block hashes to the
same value at both.

The project-key consequence clause reverses the same way. On head
`581e53137d45defb65757dac683a3132e1edf5c6` the run praised that clause by quoting it approvingly; on
head `a18cf8929a8280899e6637c6d1b47482c5e61eeb` finding `f-006`, severity `WARNING`, asked for it to
be moved out of `<essential_principles>`. That section occupies lines 16-60 at both heads and hashes
to the same value at both. The only change to `SKILL.md` between the two heads falls at lines
199-204, outside every section these two reversals judge.

The `<failure_modes>` entries reverse and then reverse back. Consecutive runs praised the four
entries, one calling their corroboration with `references/standing-rules.md` a virtue because it kept
the operational knowledge non-speculative. Then on heads
`96d8c01ed5d92711519e392b826410ca86761451` and `405584488036a9cbbd617519bb09659a132446c5` finding
`f-006`, severity `WARNING`, faulted that same corroboration as duplication drift. Then on head
`f0b078ea0b0c8870084c24a422edb1caa4b9b596` finding `f-003` praised them again. The `<failure_modes>`
block at lines 216-236 hashes to
`b1e8eabca6691b699e8e9ca78c75488c40169f13c87de5b8aaeb615ce412b003` at every head this entry names,
from `08d4ef11a7085974f27e3cf58afe92942cde066c` through `f0b078ea0b0c8870084c24a422edb1caa4b9b596`.
`references/standing-rules.md`, the other half of the corroboration, is blob
`4c23c5e8e68f4afcc5e53618ded003f348208de7` at `96d8c01ed5d92711519e392b826410ca86761451`,
`405584488036a9cbbd617519bb09659a132446c5`, and `f0b078ea0b0c8870084c24a422edb1caa4b9b596` alike, so
the fault and the return to praise judge identical text on both sides of the corroboration.

The description's closing clause is passed over and then faulted. On head
`ccaef088c98007c963125af0fc621040d1f6b51b` the run returned `APPROVED` with `must-fix` empty and
three `worth-improving` warnings — on the locatability of `references/ledger-script-coverage.md`, on
`<success_criteria>` enumerating three of the eight routed operations, and on the sentence "Spend and
wall time are courtesy fields rather than gates" standing in both `SKILL.md` and
`references/standing-rules.md` — and none of the three concerned line 4. On head
`1ea3cf1567a963c6466366098155fcaa3a04d01a` the run returned `APPROVED` with `must-fix` empty and two
warnings, of which `f-006`, rule `redundant_never_clause`, faults line 4's closing NEVER clause as a
negative the sibling capability skills already carry and asks for it to be dropped. Line 4 is the
`description` frontmatter value, and it is byte-identical at
`ab87d964b416a6e8067d3930fbc64748c378449e`, `ccaef088c98007c963125af0fc621040d1f6b51b`, and
`1ea3cf1567a963c6466366098155fcaa3a04d01a`, hashing to
`92d888a23de5a58281959046ee4b8a3a56c35ab88cb4ad2c4962a01b5ba327a6` at each. One run passed over that
line and the next faulted it, with no edit between them.

One verdict document contradicts itself with no second head involved. On head
`f0b078ea0b0c8870084c24a422edb1caa4b9b596` finding `f-004` praised the router's
progressive-disclosure split while finding `f-007`, in that same document, faulted that same split
for having all eight workflows read `references/standing-rules.md`. The split and those workflows are
one arrangement: `workflows/` holds `answer.md`, `close.md`, `correct.md`, `escalate.md`,
`housekeep.md`, `launch.md`, `order.md`, and `read.md` at that head, and each names
`references/standing-rules.md` once. The shape repeats on head
`581e53137d45defb65757dac683a3132e1edf5c6`, where finding `f-004` praised
`references/ledger-script-coverage.md` for satisfying the script-testing rule while finding `f-009`
faulted that same file under that same rule for naming no command form.

Intra-run contradiction is the stronger form of the claim. It admits no explanation that a
cross-head comparison admits: no text moved, no reference changed, and no slug was minted between
the two findings, because there is no between. One file set is the subject and one document is the
judgment.

The auditor's own rule vocabulary is unbounded, which is what lets opposed readings coexist. Its
`<verdict_format>` types the `rule` field as a free-form `<strength-name>` or `<issue-name>`
placeholder, and `src/plugins/instructions/skills/audit-skill/SKILL.md` fixes only
`configuration_issue`, `actor_or_activity_objective`, and `auditor_skeleton_violation`. None of
`unverified_allow_list_match`, `narrow_allowed_tools`, or `restated_dependency_contract` appears
anywhere under `src/plugins/` or `dist/`, so each run mints the slug it judges under and nothing
binds one run's classification of a line to the next run's.

**Impact.** `src/plugins/instructions/skills/audit-skill/SKILL.md` `<success_criteria>` states "The
same SKILL.md yields the same verdict"; these runs falsify that criterion on its own subject.
Convergence requires a verdict to be a function of its subject. Where the same Verifier definition
returns opposite judgments on unchanged input, repair chases noise, and a changeset cannot converge,
because the next round raises what this one blessed and dropping a finding as unbacked is
indistinguishable from dropping a finding the next round will restore. It also makes the
finding-disposition rule in [`spx/15-merging.pdr.md`](spx/15-merging.pdr.md) undecidable for this auditor: a finding whose
severity is unstable across runs on unchanged text carries no `blocking`-versus-`debt` reading to
act on, and the repeated-class invalidation rule in the same decision reads a re-raised reversal as
a failed repair invariant when no repair was owed.

The filing has twice prevented wasted work. On each occasion a finding this auditor raised, and a
later run of the same auditor then praised, was dropped rather than repaired; repairing either would
have undone correct work.

**Settlement condition.** Two runs of `instructions:skill-auditor` against one unchanged skill
surface return the same rule and severity for every line both judge, and no single run's verdict
document both praises and faults the same subject under the same rule. The intra-run contradictions
add the second clause: runs that contradict themselves the same way satisfy the cross-run clause
while each verdict stays unusable. Reaching either needs the rule vocabulary bounded —
`/skill-standards` owning the enumerated rule slugs `/audit-skill` may emit,
which is what the node assertion requiring `/skill-standards` to own every rule `/audit-skill`
enforces already declares — so a line cannot be classified under a slug minted for one run.

**Related.** Three adjacent Verifier-judgment problems are recorded elsewhere in this tree; this is
the fourth and the first where one auditor definition contradicts itself on unchanged input, rather
than two Verifiers disagreeing or one raising an unactionable finding. "Auditors read a conforming
absent `<failure_modes>` section as a gap", below in this file, is the same auditor raising a finding no edit satisfies; this
entry is the stronger claim, because there the finding was at least stable across runs. "Two
verifier rules collide on pinning a spec-declared tuning value" in
`spx/31-outcomeeng.enabler/31-verification.enabler/31-test-verification.enabler/ISSUES.md`, and "Two
verifier rules collide on naming the evidence location in a shipped skill" in
`spx/43-coding-agents.enabler/18-agent-mail.enabler/ISSUES.md`, each record two different Verifiers
reading two decisions to opposite verdicts — resolvable by amending one decision, which a
self-contradiction is not. "A skill-directory token inside an `allowed-tools` pattern may never
match", below in this file, is opened by `f-007`, the first half of the reversal above; its settlement
condition rests on an executed invocation rather than an auditor verdict, and the `f-003` reversal
neither answers nor closes it.

## The Codex render of `command-capabilities.md` contradicts itself and ships build instructions

`src/plugins/instructions/skills/skill-standards/references/command-capabilities.md`
carries no per-target content, so its Codex render at
`dist/codex/instructions/skills/skill-standards/references/command-capabilities.md`
lines 69-76 tells a Codex author to write the Claude Code skill-directory token in
authored source, shows `${SKILL_DIR}` in the example directly below, and then says
never to write Codex's token in source. A reader who follows the example breaks the
rule beside it. The same render tells consumer repositories to "update build
rendering" and to "fix the renderer for Codex" (lines 5, 11, and 30), which only this
repository can do. Both contradict the bundle's own rule in
`references/runtime-variables.md` that generated runtime guidance describes only its
own runtime token, and `SKILL.md` routes every Codex author to this reference.

**Impact.** A Codex consumer authoring bundled-file references from this standard
receives a token rule that contradicts its own example and instructions to change a
build it does not have.

**Settlement condition.** The reference carries per-target content, as
`runtime-variables.md` and `platform-constraints.md` already do, so each render
describes only its own harness's token and syntax, and build and renderer guidance
stays in source-only comments; one skill audit of `skill-standards` then raises no
finding on this reference.

**Why separate.** The fix restructures a whole reference file per target. Change #200
changed no line of that file; the audit read it only because `SKILL.md` routes to it.

Source: `instructions:skill-auditor` finding `f-015`, rule
`rendered_output_contradiction_and_portability`, severity `REJECT`, on head
`913a65e5b370ffa846bfe7a47be4a551e6a9c547` during Change #200.

## `/create-skill` assumes a spec tree and restates its standards loads

**Evidence**: `instructions:skill-auditor` warnings on `src/plugins/instructions/skills/create-skill` at head `add3e3e862f7512a55e8b9655d07f78412abe87c`: f-010 (rule `plugin_portability_undefined_reference`) — `workflows/audit-skill.md:21` tells a consumer to persist requirements in decisions and specs and to follow the root guide's isolation mechanics, surfaces a repository without a spec tree lacks; f-011 (rule `conciseness_duplicated_loading`) — `SKILL.md` composes `/skill-standards` and `/agent-prompt-standards`, and `<reference_loading>` and every workflow's `<required_reading>` restate both loads and the overlay read.

**Impact**: a consumer without a spec tree or a root guide meets an instruction it cannot resolve, and every route pays for the restated loads.

**Settlement condition**: the isolation requirement is stated directly or conditioned on the surfaces existing, the loads stand once, and one typed skill audit of `create-skill` raises neither finding.

## `audit-skill`'s structure examples use `xml` fences for pseudo-XML

**Evidence**: `instructions:skill-auditor` warning f-009 (rule `repository-markdown-pseudo-xml-fence`) on `src/plugins/instructions/skills/audit-skill/references/xml-structure-examples.md` at head `add3e3e862f7512a55e8b9655d07f78412abe87c`: pseudo-XML examples sit in `xml` fences, some closed by mismatched four-backtick fences.

**Impact**: dprint `markup_fmt` may rewrite the examples, and fence boundaries are ambiguous to a reader.

**Settlement condition**: every pseudo-XML example uses a `text` fence with matched delimiters; one typed skill audit raises no such finding.

## `skill-standards` describes the context that loads it

**Evidence**: `instructions:skill-auditor` warning f-010 (rule `caller_independence`) on `src/plugins/instructions/skills/skill-standards/SKILL.md:22` at head `8e631614b562ec5edf05c0e4c80a38625ada90d7`: `<repo_local_overlay>` opens "When another skill loads this reference inside a repository", and line 18 describes its callers, while the same skill's caller-independence rule bars a skill from naming or describing its caller or invocation context.

**Impact**: the canonical standard does not hold its own rule, so an auditor can cite it as a counterexample.

**Settlement condition**: the overlay rule and the reference note state their behavior without naming who loads the skill; one typed skill audit raises no `caller_independence` finding against them.

## `audit-skill`'s annotated examples grade in a vocabulary the run does not record

**Evidence**: the built `instructions:skill-auditor` run `2026-10-03_22-58-55-808-4bb7d31783f5` on `src/plugins/instructions/skills/audit-skill` at head `8e631614b562ec5edf05c0e4c80a38625ada90d7` raised debt findings (rule `severity-vocabulary-mismatch`) against `references/operational-effectiveness-examples.md` lines 5, 31, 56, 95 and `references/xml-structure-examples.md` lines 5, 31, 53, 88, 116, 130: the examples flag violations as critical or recommendation, while `SKILL.md` records only the `blocking` and `debt` severities and states no mapping.

**Impact**: an auditor reading an example grades by a label the run cannot record and maps it to a severity by its own judgment.

**Settlement condition**: the examples use `blocking` and `debt`, or `SKILL.md` states the mapping; one typed skill audit of `audit-skill` raises no `severity-vocabulary-mismatch` finding.

## Two audit-skill reference files over 100 lines carry no table of contents

`/skill-standards` `<progressive_disclosure>` requires a table of contents at the top of every reference file over 100 lines, so partial reads still see the full scope. `src/plugins/instructions/skills/audit-skill/references/operational-effectiveness-examples.md` (116 lines) and `src/plugins/instructions/skills/audit-skill/references/xml-structure-examples.md` (140 lines) have none. The `create-subagent` references carry theirs.

**Settlement condition.** Each file opens with a `## Contents` section or an XML `<contents>` block listing every top-level section, in the form its skill uses, and `instructions:skill-auditor` approves `audit-skill` afterward.

## Auditors read a conforming absent `<failure_modes>` section as a gap

`/agent-prompt-standards` `<failure_mode_writing>` prescribes omitting `<failure_modes>` from a skill that has not failed yet: "Never invent failure modes... Add failure modes as they occur in real usage." A new skill therefore conforms by carrying no such section. `instructions:audit-skill` nonetheless raises the absence as a `worth-improving` warning, and its own remedy then restates the standard back: "once a real near-miss occurs", "do not fabricate one if none has occurred". `spec-tree:changes-reviewer` reads the same absence as a coordination-note gap. The warning is unactionable by construction: no edit satisfies it, and declining it leaves the next Verifier to raise it again. It fired six times over three skills and four verification rounds across the contribute-plugin consolidation, each costing a full re-audit or re-review cycle to answer with the same reasoning.

**Evidence.** `instructions:skill-auditor` warnings on `src/plugins/contribute/skills/open-upstream-issue/SKILL.md` and `src/plugins/contribute/skills/sync-fork/SKILL.md`, three rounds running, with `spec-tree:changes-reviewer` debt findings on the same absence in review runs `2026-08-17_00-39-40-323-2100d0f7fbde` and `2026-08-17_00-58-42-318-56d83c759ed7`.

**Settlement condition.** `instructions:audit-skill` stops raising a bare missing `<failure_modes>` as a finding for a skill whose history shows no observed failure, or raises it only where a governing node, changelog or commit history records one the skill omits. The reviewer's coordination-note rule carries the matching case: a note tracking work a standard declares complete-as-absent represents no future work, so its removal closes the item. The reviewer's side is in `spx/21-spec-tree.enabler/68-reviewing.enabler/21-reviewing-changes.enabler/ISSUES.md`.

## A skill-directory token inside an `allowed-tools` pattern may never match

`/skill-standards` `references/command-capabilities.md` `<file_references>` documents `${CLAUDE_SKILL_DIR}` for the skill body, where the loader substitutes the absolute path before Claude sees the command, and states no substitution behavior for an `allowed-tools` frontmatter pattern. Skill surfaces across three plugins nonetheless spell the token inside a permission entry, as in `Bash(python3 "${CLAUDE_SKILL_DIR}/scripts/<name>.py":*)`, so each grant is written against a string the loader may never produce. Either the loader expands the token in the pattern as it does in the body and the grant means what it says, or the pattern is matched literally against a command whose path is already expanded and the grant matches nothing. Reading the loader's documentation, a skill body or the frontmatter settles nothing.

**Impact.** A grant that never matches does not fail; it degrades. The declared containment stops being the real approval boundary, and every invocation of the script falls back to a per-call permission prompt, which strands an unattended run. Nothing in the skill surface, the build or the deterministic gate distinguishes a grant that matches from one that never will.

**Evidence.** `instructions:skill-auditor` finding `f-007`, severity `WARNING`, against `src/plugins/coding-agents/skills/orchestrate-officers/SKILL.md:6`, then a sweep of the `allowed-tools` frontmatter across `src/plugins/*/skills/*/SKILL.md` that found the token in a permission entry on 17 surfaces across `coding-agents`, `spec-tree` and `contribute`. `grep -l 'allowed-tools:.*CLAUDE_SKILL_DIR' src/plugins/*/skills/*/SKILL.md` derives the current population.

**Settlement condition.** A session runs one of the surfaces the sweep names to the point where it issues its `python3` command and records whether the harness admits the command under the declared grant or prompts for it; the established behavior then fixes one spelling across the whole population. An executed invocation is the only evidence that closes this.

**Related.** "A non-interactive git guard sits on the command that cannot prompt", in `spx/21-spec-tree.enabler/76-merge.enabler/32-github-pr.enabler/ISSUES.md`, asks whether the Bash grant matcher tolerates an `ENV=value` prefix. One executed invocation that reports the matcher's behavior on an unexpanded token and on an environment-variable prefix answers both.

## `skill-standards` carries four findings no other entry records

**Evidence.** `instructions:skill-auditor` run `2026-10-06_18-37-53-397-59929467e6ad` on `src/plugins/instructions/skills/skill-standards` raised eight `debt` findings. The entries above record three of them: `progressive-disclosure-exception-reference` (the stale cross-reference entry), `caller-independence` on `<repo_local_overlay>` (the entry on the context that loads the skill), and `constraint-language-weak-modal` (the `script-standards.md` entry). The self-justification finding, `eager-foundation-exception`, is settled by removing the paragraph that invoked the exception for the skill. This entry records four others:

- `reference-skills-duplication` on `<descriptions>` and `<conciseness>`, which `agent-prompt-standards` restates in `<description_style>` and `<conciseness>`.
- `caller-independence` on the `<xml_structure>` intelligence-rules table, whose row label reads "Auditor (agent-preloaded)".
- `conciseness-concrete-over-abstract` on `<progressive_disclosure>`, whose token-efficiency figures understate a 40,000-code-point eager payload.
- `path-boundary-deleting-command`, where `<path_boundary>` states that no skill directs a deleting command while `<progressive_disclosure>` directs `git rm` for an orphaned reference file.

**Standing.** The four findings lie on text the changeset leaves untouched. The diff of the skill against `origin/main` holds these hunks: `SKILL.md:274` (the `<context>` paragraph, replaced by a one-line pointer), `SKILL.md:299-304` (the paragraph in `<eager_foundation_exception>` that invoked the exception for the skill, with its measurement command, removed), `SKILL.md:518-520` (the closing sentence of the classifier-refusal paragraph and the added guard-block paragraph in `<path_boundary>`), and `references/command-capabilities.md:41` and `references/command-capabilities.md:44-45` (the `<dynamic_context>` rules). None falls in `<descriptions>`, `<conciseness>`, the intelligence-rules table, the token-efficiency sentence of `<progressive_disclosure>`, or the scratch-storage paragraph of `<path_boundary>`.

**Impact.** The standard restates a standard it defers to, labels a skill class by its caller, quotes a token figure its own limits falsify, and leaves the scope of its deleting-command ban unstated.

**Settlement condition.** Each standard has one owning skill with the other pointing to it, the auditor row names its class by output, the figure is accurate or cut, the ban states its scope so the orphan-file instruction sits inside it or is rewritten, and a typed skill audit of `skill-standards` raises no such finding.
