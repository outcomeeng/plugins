# Issues: Skill Authoring

Actionable findings from the post-merge skill audit of PR 458 at
`f5aa313016964a10854117e026ec4c3529106490`.

## Split router authority by workflow needs

`src/plugins/instructions/skills/author-skill/SKILL.md:5` grants `Bash`, `Write`,
`WebFetch`, and `WebSearch` to every route. Read-only audit and pattern-explanation
routes inherit mutation and network capabilities they do not use.

Required handling: narrow the router's top-level `allowed-tools` surface or split
routes whose authority requirements differ. Preserve the tools required by creation
and improvement workflows without granting them to read-only routes.

Source: skill-auditor finding `f-003`, rule `overbroad_allowed_tools`, severity
`WARNING`.

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

## Authoring surfaces teach payload forms and a payload-pipe exemption the router does not hold

Surfaces of the `instructions` plugin teach payload forms that [`spx/15-agent-tools.pdr.md`](spx/15-agent-tools.pdr.md) forbids, and state a guard-block rule with a payload-pipe exemption that the router does not hold. The payload rule requires every payload to reach a command through a file in the scratch directory the harness names, under a file name unique to the agent. The router states the guard-block rule with no payload-pipe exemption: a pipe between two operations ends the command family, and a blocked compound command runs its parts again one at a time.

**Evidence.**

- `src/plugins/instructions/skills/skill-standards/SKILL.md` line 49 teaches choosing a quoted heredoc or a one-line `printf '%s\n' ... | <tool>` pipe by harness environment.
- `src/plugins/instructions/skills/author-skill/templates/auditor-skill.md` lines 98, 130 and 135 teach a quoted heredoc and a `printf` pipe for `spx verification run scope add` and `finding add` payloads, with `Bash(printf '%s\n':*)` in the template's `allowed-tools`.
- `src/plugins/instructions/skills/skill-standards/SKILL.md` line 452 states the guard-block rule with "a pipe between two operations other than a payload pipe".
- `src/plugins/instructions/skills/skill-standards/references/command-capabilities.md` line 98 says "other than the payload pipe above".
- `src/plugins/instructions/skills/skill-standards/references/rule-catalog.md` line 175, rule `unbounded_guard_rerun`, says "a payload pipe is never split".
- `src/plugins/instructions/skills/skill-standards/SKILL.md` line 49, under "The harness environment is not a caller", states the caller-independence rule as a payload command form chosen by harness environment: "a quoted heredoc where the harness accepts multiline shell and one physical `printf '%s\n' ... | <tool>` line where the runner requires a single command line". The assertion at `spx/43-instructions.enabler/21-skills.enabler/skills.md` line 38 states that the `/skill-standards` caller-independence rule reads the payload scratch-directory fallback location a skill selects by harness environment, as [`spx/15-agent-tools.pdr.md`](spx/15-agent-tools.pdr.md) requires. The two differ in the selected property: the skill text selects a payload command form by environment, and names no scratch-directory location or fallback such as `$RUNNER_TEMP`; the assertion selects a scratch-directory fallback location by environment. The skill text's forms are the heredoc and the pipe that [`spx/15-agent-tools.pdr.md`](spx/15-agent-tools.pdr.md) forbids as payload forms.

The three guard-block sites contradict the router, so the skill auditor enforces a rule the router no longer holds. The caller-independence paragraph contradicts the assertion at `spx/43-instructions.enabler/21-skills.enabler/skills.md` line 38, so the skill standards teach a different environment-selected property than the node declares.

The `audit-skill` and `audit-subagent` skills and the `skill-auditor` and `subagent-auditor` agents carry the same forms under the exemption recorded in `spx/21-spec-tree.enabler/68-audit.enabler/ISSUES.md`. This entry does not cover them.

**Impact.** The skill standards and the auditor template shape every new skill. A skill authored from them teaches the forbidden forms, so the payload rule holds for existing skills and not for the skills these surfaces produce. The caller-independence paragraph gives an author a heredoc or pipe form where the node and [`spx/15-agent-tools.pdr.md`](spx/15-agent-tools.pdr.md) require a scratch-directory file, and the skill auditor holds no text to judge a skill's scratch-directory fallback against.

**Settlement condition.** The skill standards and the auditor template state the file form, or the exemption's grant rule is lifted and the auditors move to the file form. The guard-block wording in the three guard-block sites matches the router: a pipe between two operations ends the command family, with no payload-pipe exemption, and a blocked compound command runs its parts again one at a time. The caller-independence paragraph at `src/plugins/instructions/skills/skill-standards/SKILL.md` line 49 and the assertion at `spx/43-instructions.enabler/21-skills.enabler/skills.md` line 38 agree: both state the payload scratch-directory fallback location a skill selects by harness environment as a property of the run, with no heredoc or pipe payload form. The skill auditor then raises no payload-form finding on either surface.

## The same-plugin sibling-script import exception names no checkable form

`src/plugins/instructions/skills/skill-standards/references/command-capabilities.md` line 90, in `<file_references>`, and `src/plugins/instructions/skills/skill-standards/references/runtime-variables.md` line 22, in `<skill_file_references>`, admit a sibling-script import "as a typed operation" without stating what makes the import typed. The phrase is an abstraction in the skill-standard passages: an author cannot apply it, and an auditor cannot check an import against it. The same phrase is a qualifier in the assertion in `spx/43-instructions.enabler/21-skills.enabler/skills.md` that the governing decision, [spx/13-plugin-and-runtime-conventions.adr.md](spx/13-plugin-and-runtime-conventions.adr.md) line 173, does not state: the decision admits a `__file__`-relative import of a provider skill only within the same plugin and says nothing of a typed operation, so the spec layer asserts what the decision layer does not establish. The admitted case needs a concrete form, such as the import statement shape or the typing requirement the import imposes, stated in the decision.

**Evidence.** `instructions:skill-auditor` finding, run `2026-10-12_18-18-03-578-7f4e9a7a3f91`, on head `022934dfb920be182e6569e489a0d2cdf7f0b628`, rule `abstract_guidance`, severity `debt`, location `src/plugins/instructions/skills/skill-standards/references/command-capabilities.md:90`. A second skill audit, run `2026-10-12_18-22-43-353-13c6497db086`, on head `b75b124583b312aa89f00fdf082e11ded3d20eaa`, raised the same rule `abstract_guidance` at two locations: `src/plugins/instructions/skills/skill-standards/references/command-capabilities.md:90` and `src/plugins/instructions/skills/skill-standards/references/runtime-variables.md:22`. The phrase "as a typed operation" comes from the assertion text in `spx/43-instructions.enabler/21-skills.enabler/skills.md`, so both references mirror the declaration and the defect originates in the assertion wording. The CI review of pull request 660, on head `2f9897d826eb336909a92d74d406d7d78ff65903`, raised a `debt` finding of category `consistency` at `spx/43-instructions.enabler/21-skills.enabler/skills.md:48`: the assertion's "as a typed operation" is a qualifier the decision at [spx/13-plugin-and-runtime-conventions.adr.md](spx/13-plugin-and-runtime-conventions.adr.md) line 173 never states, and `command-capabilities.md` line 90 and `runtime-variables.md` line 22 inherit the ungrounded phrase from the assertion. Only `skills.md`, `command-capabilities.md`, and `runtime-variables.md` carry the phrase "as a typed operation".

**Impact.** The exception is unverifiable as written: two authors can read it differently, and two audit runs can classify the same import differently.

**Settlement condition.** The assertion in `spx/43-instructions.enabler/21-skills.enabler/skills.md` states the concrete form of the admitted import, and both passages carry that form: `src/plugins/instructions/skills/skill-standards/references/command-capabilities.md` in `<file_references>` and `src/plugins/instructions/skills/skill-standards/references/runtime-variables.md` in `<skill_file_references>`; one skill audit of `skill-standards` then raises no `abstract_guidance` finding on the exception at either passage. Equivalently, the qualifier leaves the assertion and both passages, the only files that carry the phrase "as a typed operation", so no layer asserts what the decision does not state. Either repair also closes the decision-to-spec traceability gap: the decision states what makes the import typed, or the qualifier is absent from the spec layer.

**Why this Change does not repair it.** The assertion text and the decision text are operator-approved verbatim in the Change record, so either repair changes approved wording and waits for an operator decision.

## The skill auditor rejects on unchanged lines of a changed file

`/audit-skill` keys every finding to one unit per changed file, `instructions:skill:file:<path>`, as the node assertion on its run shape declares, and then rates a finding on an unchanged line of that file `blocking`. The node assertion that `/audit-skill` rejects only on touched text inside each changed file, and returns each other finding as `filed`, therefore does not hold.

**Evidence.** `instructions:skill-auditor` run `2026-10-13_23-22-04-233-88fc0c8e61f3` (instructions 0.20.0) on the changeset `800f38e2689e4e6564b9075aeb4681014dccff73..3142f91a24cd730db5c8dae65112eb91a89b8d5c`, unit `instructions:skill:file:src/plugins/prose/skills/audit-prose/SKILL.md`. The run rated `auditor-verdict-format` `blocking` at lines 25, 71, 83 and 115 of that file, and `composed-dependency-form` `blocking` at line 55; the changeset changes none of those lines and invalidates none of them. The run returned zero `filed` findings.

**Impact.** Every defect an edited skill file already carries rejects any changeset that touches one line of it, so a holder spends the two-run gate cap on findings the disposition rule in [`spx/15-merging.pdr.md`](spx/15-merging.pdr.md) files, and judges touched text by hand where the run should carry that judgment.

**Settlement condition.** A run against a changeset that changes some lines of a skill file returns each finding on an unchanged, uninvalidated line as `filed`, with `baseRefEvidence` and `issuesEntry` per properties 11 and 13 of [`spx/31-outcomeeng.enabler/31-verification.enabler/14-verification.pdr.md`](spx/31-outcomeeng.enabler/31-verification.enabler/14-verification.pdr.md), and rejects only on touched text.
