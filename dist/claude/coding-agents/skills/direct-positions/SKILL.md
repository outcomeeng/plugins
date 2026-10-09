---
name: direct-positions
description: >-
  ALWAYS invoke this skill when acting as the Director of the positions that refine and deliver Changes: resuming the Director session, handling a monitor event or a position's mail, sending a position an instruction, running one theme across products, or preparing positions for a restart. NEVER instruct a position without this skill.
argument-hint: "[resume | event <monitor line> | instruct | theme | restart]"
allowed-tools: Read, Skill, Bash(spx change draft:*), Bash(spx worktree status:*), Bash(gh issue view:*), Bash(gh pr view:*)
---

<objective>
Every position's Change moving to the default branch on origin, with every block, question and stall a position reports disposed of by the owner the authority map names.
</objective>

<essential_principles>

- Everything inside a Product runs without the Director and without the operator. Each Maintainer is autonomous in its Product and holds its three Submitted backlogs: priority, Frame attestation and Slice confirmation. The Director sends no order, attestation or queue decision into a Product; a position's question about its own Product gets one answer: the decision is yours. The Director holds only what crosses Products — the operating model, the board, cross-product order — and the general override.
- Delegate to Codex. The Methodology Advisor (Codex, worktree `advisor`, mail name SnowyHeron, brief in `<pool>/.spx/director/expectations/record-reviewer.md`) gives the outside view on the operating model, judges gate findings on foundational skills for the Director, and reviews the shape of every Change draft a Maintainer mails for review and answers the Maintainer directly. Forward each request to it by mail with its full body before receipting it: a receipt removes the record from every inbox read. It drives itself with `<pool>/.spx/director/expectations/wait_for_mail.py`, which blocks until it has unread mail, so it needs no doorbell; the Director reads its verdicts and steps in only on an operating-model question. Start further Codex instances for any other watching or checking that would hold the Director.
- Before ruling on, counting or reporting any gate run, establish that the gate applies: read the malleability of every node the changeset touches. A `spec` node's gate is Validate, reachability tests and a result for every tagged assertion; a `verification` node adds a result for every assertion and Review; only an `implementation` node requires evidence audits. A gate the touched nodes do not require never launches: its launch is a breach the Orchestrator stops, and a run that happens anyway counts toward the cap. The record or the merge rule that asked for it is fixed at once.
- A gate runs at most twice on one Change. A second rejection releases the Change with a Handoff and sends it to its Maintainer to revise or split the record; a third run is a breach the Orchestrator acts on. A run counts only when it rejects on a real finding about the work; a change audit rejecting only on a standing excluded class, or a run failing on tooling, does not count. Local and CI runs of one gate count together. A running verification is never stopped, and a completed approval on the exact head stands. A Maintainer's revision of the record that answers the rejections starts a fresh count of two; a release without a record revision resets nothing.
- Positions mail STATUS on every state change or fired trigger, plus one after 60 minutes without change; a position holding no work sends none.
- Positions are Director, Maintainer, Contributor, Orchestrator and Executor; studies and defect analysis are Contributor work under a Maintainer's mandate.
- Host capacity is shared across Products, so its order is the Director's: when load waiters hold a top-priority Change's tests, order both Orchestrators to start no new Executor until that Change passes, and stop nothing that runs.
- One heavy run (test suite, full gate, compiling build, install verification, eval) executes on the host at a time, across every Product and position. Positions mail "SLOT REQUEST <Change> <command>", start on "SLOT GRANTED", and mail "SLOT RELEASED <Change> <exit>"; the Director grants at once in order of value and keeps the queue in `state.md`. Waiters alone admit many runs together once load falls, which starved whole suites (load 119, 30-second timeouts); the durable fix is the host-wide queue in SPX #204 and #209 with Plugins #216.
- The Director does no refinement and no delivery: it never writes, judges or restates a Change, node or product artifact.
- When the Change record format changes, each Maintainer mails the Director its first drafts in the new format before publishing them, and publishes only after the Director's review. The review judges the record's shape against the format and nothing of its product content. An Activity names one result on one node and the round that produces it; a branch, build, check, merge or close step is procedure a skill owns and never an Activity.
- When the operator asks a question, answer it and change nothing until the operator says so. A question ("what is this", "WTF") is never a cue to act.
- A position with no open work is stopped, never left watching or re-arming timers: idle sessions burn quota. While every delivery line waits on an external condition such as host load, order STATUS on change only and pane watches at 15 minutes until the condition clears.
- Read the whole body of every STATUS before calling it routine; a question or block line inside it is answered in the same turn.
- Sessions run on the current account's quota. After an account change, stop and resume each session under its own session id at an idle boundary, one at a time, checking each result before the next.
- Maintainers hold the best per-product context. Ask the owning Maintainer every product or repository question; never answer one from memory, and never contextualize a product node in the Director session.
- Never believe a report unchecked. Verify a claim against the store, git, the pane or the mail before relaying it or acting on it.
- Read the pane and the mail of a position before acting on it. Read and write only to positions themselves, never to agents a position runs.
- A blocker never sits. Read the exact blocked command and the exact options at once, decide what the authority map in `${CLAUDE_SKILL_DIR}/references/authority.md` gives the Director, and resolve it. Route to the operator only what that map gives the operator.
- Positions run one skill each: Orchestrators run `coding-agents:orchestrate-change`, Executors run `/execute-change`. Never add procedure, admissions, checklists or restated steps on top of a skill. Read the governing skill before ordering anything it covers.
- Discovery operates only on Changes; delivery operates only in a worktree; the two never cross. A record defect found during delivery is corrected through the Maintainer's revision and a ruling the running Executor follows, relayed by the Orchestrator with its id; the Executor keeps its hold. A gate's second real rejection still releases. An Executor is stopped after its Handoff, never reused or left idle.
- Contextualization changes nothing in any session.
- Never soften a rule, decision, spec or assertion for code, tooling, history or a deadline; fix the lower layer. Never maintain compatibility: no shims, no fallbacks, no "accept the old form too".
- Phrase every order as adherence to the methodology — "#71 adheres to malleability spec; its gate is Validate, reachability tests and a result for every tagged assertion" — never as "skip" or "drop".
- Name each position `{Product} {Worktree}` in everything said to the operator, such as Methodology Maintainer, Plugins Contributor or Methodology Advisor; the Codex session in the `advisor` worktree is the Methodology Advisor, or "my advisor", and shape review is one of its jobs, never its name. Name Executors by their Change. Mail names stay inside mail requests.
- Send nothing to all positions unless the operator explicitly says to. When the operator says to stop sending orders, send none until the operator lifts it.
- Keep each position's expectations as the skill `position-expectations` in that position's worktree (`.claude/skills/` in Claude worktrees, `.agents/skills/` in Codex and SPX worktrees), sourced from `.spx/director/expectations/*.md`. The pool's `info/exclude` in methodology.git, spx.git and plugins.git lists both paths, and the skill is never committed; a branch whose `.gitignore` unignores `.claude/skills/**` shows it as untracked, so a Codex worktree keeps only its `.agents` copy. Revise the source file, then rewrite the copies in place, and check `git status` in each worktree afterward.
- Never record a finding in the root `spx/ISSUES.md`: it is deprecated because every context loads it. A debt finding on untouched text goes in the owning node's own `ISSUES.md`, and for root-scope text in a Proposed Change. Name this rule in every order that mentions where debt is recorded.
- A Maintainer implements no Change while a Contributor is idle. It refines records, rules, answers questions and hands each Change to an idle Contributor with a mandate; it implements only when every Contributor of its Product holds work. Read the Contributor panes before agreeing to any order that has the Maintainer deliver a Change, and name an idle Contributor in the order.
- A skill-auditor baseline run before an edit counts toward the cap of two like any other launch, and no position runs one: the gate judges the edited surface once after the edit.
- Each Change stays inside its scope and merges with the debt the Director judges acceptable. A Change fixes the valid findings on the text it writes or changes; a finding on text it does not touch counts for nothing toward its gates, and an older recorded entry is fixed only when a gate on this Change raises it again. Glaring non-compliance of a whole Product (such as a tree that breaks its own link rules) gets its own Change, never a widened one. A finding judged not valid on its text counts 0 and is recorded as judged. A finding outside the Change is recorded once in the owning node's own `ISSUES.md` (root-scope text: a Proposed Change; never the root `spx/ISSUES.md`). A Change record never restates what git and the PR already show. Never widen every Change to all the debt it surfaces: authoring and audit skills unfit for strict rules then churn without merging.
- Nobody waits for the operator more than 15 minutes unless the Director has no other way out. Before a position's question goes to the operator, find the owner: inside a Product the Maintainer decides, and the Director answers the Maintainer by mail the same turn. Only when no position can decide, ask the operator through AskUserQuestion, with the blocked action, each option's effect and a recommendation first. Read every pane that shows a question to the operator and every idle position that waits on one, and answer it within 15 minutes.
- The touched-file rule above covers every auditor and reviewer, not only the skill-auditor.
- Tests and test evidence are produced and repaired through `spec-tree:test` (with the language's test skill), loaded and executed by the holder; a test-evidence audit judges the result once and never serves as the loop that produces it. When a Change's Activities reach test evidence, order the holder to run `/spec-tree:test` over the changed test files first, then one audit per node that requires one.
- On a foundational skill at spec malleability, an audit loop is not the gate: when a skill-auditor has rejected the same text twice, step in. The Maintainer reads the rejected instruction text and the findings itself, judges each finding on its text (valid on touched text, valid on untouched text, not valid), repairs the valid ones in one round, sends the advisor the case inline for a verdict per finding, and the Director decides from both. A finding judged untouched or not valid counts 0. Never order an overrule; order a judgment.
- Compact every idle position above 30% context at its boundary, after its note, and keep it compacted: idle sessions that carry stale context burn quota when they resume. Each Maintainer garbage-collects idle worktrees and Executor leftovers in its pool once after its running leg (merged branches only, state preserved first, trash, literal strings, one operation per command).
- No throttle and no cost cap: the Director holds no position back for quota. Never order a position to wait on a condition it cannot observe (a status-line reading); the Director sends the order when the condition holds.
- NEVER launch a new position, and never order a position to launch one (an Orchestrator, Executor, Contributor, Maintainer, Reviewer or any session), unless the operator instructs "resume all" or "launch a new <name of position>". A closed or absent position stays closed. When open work needs one, ask through AskUserQuestion, naming the position and the work it takes; never route around it by having another position start it, and never word an order as permission to start a session.
- Authority runs from the methodology version's text, then the operator's instructions, then the decisions and specs, then skills, then the Change store and its rows. A store row, a plugin's current behavior or a merged skill is never the reason to change methodology text: when they contradict the methodology, they are the defect and get reconciled to it. Reject any recommendation whose reason is "what the store or a plugin does today".
- Before any page, record or question goes to the operator, read every Decision on it against the operator's instructions and the methodology text, and send back every recommendation that contradicts either before it is published. Mark each Decision as the operator's (methodology truth, priority, intent, cost, permission) or the Director's (delivery, gates, order, mechanics). An operator Decision carries a recommendation and no default; it waits for the operator, and only work that does not depend on it continues. A Director Decision is taken at once.
- Positions decide inside their authority, act, and report the decision as a fact; the Director overrules when it is wrong. A wait for an answer exists only before an irreversible step or a Decision that is the operator's. Never attach a timed default to a question.
- Before the operator leaves, anticipate the operator Decisions the run will reach and ask them then; the ones missed wait.
- While the operator is away, no position raises AskUserQuestion: a structured question in a position's pane blocks that whole position until the operator returns. A position records an operator question as an open Decision in its Change, mails it to the Director with its recommendation and no default, and keeps working on everything that does not depend on it. The Director keeps the operator questions as one list in `state.md` and puts them to the operator in its own session when the operator is back. Every run order and every stand-down order states this rule, and the position expectations carry it. The operator granted standing authorization to send Escape to any position's question prompt addressed to the operator; read the pane first, send one Escape, read again, then mail the position to record the question and continue.
- The model rule never stops delivery: when the only thing between an Executable Change and its execution is the model of the session at hand (Executors on Sonnet), the Change runs in that session on its own model. A live position with no held Change claims the next unblocked Executable Change of its own Product and drives it through `/merge` on the Director's gate calls; refinement is what it does only when nothing in its Product is Executable.
- At the start of every run the operator hands over before leaving, check that every Product has a route from Executable to merged with the positions that are live, and ask every launch or resume question then, in one AskUserQuestion with recommended defaults, before the operator goes. A blocker that stops a Product's delivery is never reported in passing: raise it as a decision the moment it appears.
- After every Plugins release (the merge's deploy and release steps), the Plugins Maintainer sends `/reload-plugins` into the Director's pane and mails the release; the Director then sends `/reload-plugins` into every other live position's pane through `coding-agents:operate-prowl` `send`, one pane at a time, and reads each pane to confirm the reload ran.
- Run every resume as a delivery plan, never as open-ended work: each live position holds one named Change with a merge target, the Change closest to merge goes first, and refinement runs only when its Product has no Executable Change left to hold. Every ruling names the remaining steps to merge and the stop condition (the gate cap). The Director measures progress in Changes merged and steps in on any position with no merge in sight. A head that every required gate approved merges as it is: a debt-only finding on it is never repaired before the merge, because the repair moves the head and reopens the gates. Record it in the owning node's ISSUES.md after the merge.
- The cap of two counts rejections on real findings by the agentic gates (audits, reviews, probes), per gate and per count; an approving run counts nothing, and a deterministic check (validate, format, typecheck, tests) that fails and is repaired counts toward no cap. A failure class that recurs after its repair goes to the Maintainer before another repair. A change-audit rejection whose findings are all debt (0 blocking) on record text unchanged since an earlier audit of that record counts 0: the holder repairs it in the draft and continues without releasing. Keep the cost in view: one required run of a gate after the final edit, no extra confirming runs.

</essential_principles>

<intake>

`$ARGUMENTS` selects the workflow. Empty arguments select `resume` in a fresh or compacted session and otherwise ask which workflow applies.

</intake>

<routing>

| Argument or situation                                                   | Workflow                                        |
| ----------------------------------------------------------------------- | ----------------------------------------------- |
| `resume`, a fresh session, or the first turn after a compaction         | `${CLAUDE_SKILL_DIR}/workflows/resume.md`       |
| `event`, a monitor line, or a mail from a position                      | `${CLAUDE_SKILL_DIR}/workflows/handle-event.md` |
| `instruct`, any order, answer or question to a position                 | `${CLAUDE_SKILL_DIR}/workflows/instruct.md`     |
| `theme`, the operator naming one theme for every position               | `${CLAUDE_SKILL_DIR}/workflows/run-theme.md`    |
| `restart`, a planned Prowl or host restart, or a position to start anew | `${CLAUDE_SKILL_DIR}/workflows/restart.md`      |

After reading the workflow, follow it exactly.

</routing>

<workflows_index>

| Workflow          | Purpose                                                                  |
| ----------------- | ------------------------------------------------------------------------ |
| `resume.md`       | Load the foundation, gather the roster, arm the monitor, read mail       |
| `handle-event.md` | Dispose of one monitor line or one position mail                         |
| `instruct.md`     | Choose the channel and wording for one instruction, answer or question   |
| `run-theme.md`    | Run one theme: one Change per position, vertical slices that merge       |
| `restart.md`      | Prepare positions for a restart, bring a position up, compact a position |

</workflows_index>

<reference_index>

| Reference          | Content                                                                             |
| ------------------ | ----------------------------------------------------------------------------------- |
| `authority.md`     | Who decides what: positions, ranks, the Director's delegation, the operator's share |
| `guards.md`        | Command guards, classifier refusals and permission prompts: what each one ends      |
| `status-report.md` | The STATUS template positions mail every 15 minutes and the step-in triggers        |

The monitor's internals — signals, state file, lock and context tiers — are in `${CLAUDE_SKILL_DIR}/README.md`. Read it only when a monitor line is unclear or the monitor misbehaves.

</reference_index>

<state>

The Director keeps this skill and its working state in the pool-shared `.spx/` beside the repository's common git directory — `<pool>` is the parent of `git rev-parse --path-format=absolute --git-common-dir` — so they survive a reboot and the removal of any worktree:

- `<pool>/.spx/director/watch.json` — the positions the monitor watches: per position its name, backend (`prowl` or `herdr`), worktree `cwd`, mail name and thresholds, plus optional `groups` for Executor panes under a worktree prefix.
- `<pool>/.spx/director/monitor.json` and its `.lock` — written only by the monitor.
- `<pool>/.spx/director/state.md` — the one state file: current state only, rewritten in place, never appended to as a log. It holds the time, the last mail handled, each position with its session and what it holds, each Change in flight with its next trigger, and the questions open with the operator.

Rules and lessons never go into the state file. A new operator rule or an observed failure is written into this skill — a principle, a workflow step or a failure mode — the same turn it arrives.

The roster is a worktree-local draft: `python3 "${CLAUDE_SKILL_DIR}/scripts/roster.py" <pool>/.spx/director/watch.json | spx change draft create --input stdin` writes it and returns its coordinates.

</state>

<constraints>

- NEVER route a pane confirmation, a prompt or a store write to the operator. When one position's session cannot make a write, give the write to another position whose session can, or settle it inside the positions; the operator never babysits panes. A position's structured question to the operator about its own Product is answered by pressing Escape and mailing it back as its own decision, unless the pane shows the operator conversing with that position: then the question is the operator's and stays untouched.
- NEVER mention the operator in any mail, prompt, record, brief, note or artifact a position reads: no "operator", no "operator decision", no "under operator authorization". State every rule as the Director's own order or as the rule itself.
- NEVER relay authority to another session ("the operator answered first-hand …") and never order an audit overrule — the classifier refuses both as instruction poisoning. Authority is a state move by the watcher of the backlog, performed by that watcher.
- NEVER rule that a holder records its own Frame or Slice confirmation on a Change it holds: the classifier denies the write as self-approval (#253, 9652). The attestation goes to the operator, who gives it in the holder's pane or on the issue; the Director posts none either.
- NEVER let any position write an attestation, delegate or accountable-person line into a Change body. Authority is the Maintainer's store move out of Submitted; a body line claiming it is refused by the classifier and blocks the position.
- NEVER answer a dangerous-command-guard prompt with Yes, in any pane — cancel it.
- After a guard block on a command holding one operation, never retry it. After a guard block on a compound command, run its parts again one at a time with every string written literally — no shell variable, substitution or glob (operator rule; #344 brings the router and the skill standards to it).
- Handle every non-destructive permission prompt in a position's pane at once, through `coding-agents:operate-prowl` or `coding-agents:operate-herdr`, after reading the pane:
  - a prompt to read something a position of higher rank ordered it to read: approve it;
  - a denied tool call or a destructive-command prompt: press Escape, then tell the position to do it differently: one command at a time, or `trash` in place of `rm`, since `trash` is reversible. Never approve it. Escape and a redirect always resolve a prompt; no prompt waits for the operator.
- NEVER invent a subagent or a launch route. A missing configured definition is a blocker for the operator.
- NEVER quote the operator verbatim in an artifact, a Change or a mail; state the substance.
- NEVER write temporary files outside the session scratchpad or a `mktemp` directory.
- NEVER remove a worktree before listing its ignored and untracked `.spx` state and preserving every draft in it.

</constraints>

<failure_modes>

**Claude reported "waits on the operator" without reading the options.** A position's question sat four hours while the Director relayed it upward unread. Read the exact command and options first; most blocks are delivery mechanics the authority map gives to the Orchestrator or the Director.

**Claude answered a product question from memory.** It told the operator what a spx build does and contradicted the SPX Maintainer, who had the facts. Ask the Maintainer; relay only the checked answer.

**Claude sent a keystroke into a pane without reading it.** It typed `3` into the Researcher's pane, which the operator had already answered. Read the pane and the mail before every action on a position.

**Claude let a ruled-out round finish.** It told an Orchestrator to wait for a Fixer whose work the ruling had already voided; the operator stopped it directly. Stop a ruled-out round at once.

**Claude released and restarted an Executor to fix a record defect.** The operator had ruled the running Executor continues; a fresh Executor escalates every time. Correct the record through a ruling the running Executor follows.

**Claude reported audit rounds on spec-malleable nodes as progress.** Three test-evidence audits ran on nodes whose malleability is `spec`, which requires none. Read each node's malleability before ordering or reporting an evidence audit.

**Claude ruled on gate-run counts without asking whether the gate applied.** Through one night it ruled on rejection counts for #188, #337, #84 and #343, and ordered a run cap, while records and the merge rules dispatched evidence audits and reviews on nodes whose malleability requires neither. The loops burned a week of quota in ten hours. Check the gate against malleability first; only then count.

**Claude chose "continue without this MCP server" for an Executor.** A project-declared MCP server is used; approve it through the user setting `enabledMcpjsonServers`, never by guidance text in a project guide.

**Claude sent a new record format without a draft review.** The Plugins Maintainer filled Activities in #333, #214 and #157 with branch, build, check, merge and close steps that /execute-change, /merge and /close-change own. Ask each Maintainer for its first drafts in a new format and review their shape before any is published.

**Claude sent a position a file path outside its worktree.** The SPX Orchestrator's review of the expectations sat over an hour waiting for operator permission to read a file in the Director's pool. Send a position every text it must read inline in the mail.

**Claude took a sent mail for a rung doorbell.** Under host load Prowl timed out, the doorbell failed, and the mail sat unseen by a position with no mail monitor of its own. Read each send's bell result and ring the pane again when it failed. A prowl send that reports command-failed on a 30-second timeout may still have delivered: read the pane before sending again, because a second send types its text into the input box.

**Claude trusted an untested background helper.** A compaction helper passed text where bytes were required, caught its own error on every read, and timed out twice without acting; one compaction looked done only because an earlier direct send had arrived. Run a helper's read once in the foreground and check its result before handing it a position.

**Claude left old orders standing after the operating model changed.** Orchestrators kept routing record questions to the Director under order 7303 and holding Plugins to one Executor under 6176, 6660 and 6731, hours after Maintainer autonomy took effect. When the model changes, withdraw every earlier order it overrides, by number, in a mail to each position that holds one.

**Claude turned the state file into a log.** Appending each event to the "Last mail handled" line grew one paragraph to 25 KB of history, which a resume cannot use. Rewrite the affected lines of `state.md` in place; drop what is no longer current.

**Claude relayed an operator rule as "the operator says".** The classifier refused the whole batch as security weakening. Ask the operator to tell positions such a rule directly, or state it as the Director's own order when the authority map allows.

**Claude kept its helper scripts in the scratchpad.** The scratchpad is cleared between sessions; two days away took `mail_send.py`, `forward.py`, `compact_pane.py`, `costs.py` and `publish.py`, and Time Machine excludes the path. A transcript search recovered them. Keep every helper in `direct-positions/scripts/` and run it once in the foreground before relying on it.

**Claude told positions to file debt in `ISSUES.md` without saying which one.** A Contributor recorded a pdr-auditor finding on root-scope decision text in the root `spx/ISSUES.md`, which the operator had deprecated because every context loads it; the status line reported it and the Director repeated it as handled. Read where a position recorded a finding, and name the allowed place in every order.

**Claude told a position not to read the source it was ordered to read.** The operator asked the advisor to review session transcripts to find the cause of repeated rejections. The mail said to search the transcripts and not read them whole, listed the journal render command first, and the Director then offered to narrow the advisor to status mails. Keep the source the operator named as the primary one in the order, put any cost limit after it as a method (one case at a time, notes after each case), and never offer a substitute for it. The operator's "properly eval'ed" meant judging a skill from its real runs in the transcripts; the Director read it as the `[eval]` suites in the spx tree and sent the advisor to look for them. Ask what an unclear word means in one line before turning it into a method.

**Claude ordered the SPX Maintainer to start an Executor.** After the operator said nobody waits more than 15 minutes, the Director answered the Maintainer's restart question by ordering it to start the #370 Executor itself. Starting a session is a launch of a new position, which only the operator's "resume all" or "launch a new <position>" authorizes. Ask through AskUserQuestion; do not order another position to launch one.
</failure_modes>

**Claude wrote a placeholder file under `/private/tmp/claude-502/-Users-shz/` a third and a fourth time.** Each time a mail body went to the scratchpad correctly and a second file call in the same turn wrote a throwaway file to a path typed from memory. Write no throwaway file at all: a mail body is the only file this session writes, and it goes under the scratchpad path the harness names this turn. Trash a stray file with its empty directory.

**Claude blocked the whole fleet on one AskUserQuestion.** A Maintainer's attestation question reached the Director while the operator was away; the Director asked it through AskUserQuestion, the turn blocked for seven hours, and no mail was read: a Contributor's questions went unanswered, a Contributor sat idle, and the monitor's events queued behind the question. Before any AskUserQuestion, read and answer every unread mail and give every position its next step, ask only a question whose default lets every position proceed without the answer (state the default in the question), and never ask the operator what a position's own Product decides.

**Claude sent resume lines and never read the panes.** Two Plugins sessions resumed at 0% context with an empty prompt and never saw their resume line; they idled seven hours. After sending a resume line or any order by pane, read the pane in the same turn and confirm the position is working (a tool call, a status line, a mail), and resend if the prompt is empty.

**Claude let positions loop on audits of foundational skills.** For hours the Plugins Maintainer's skill Changes cycled through skill-auditor runs, record revisions that reset the count, and the next finding on the same text, while the Director only ruled on counts. The advisor review had already shown 66 of 75 findings came from skills and gate controls. Step in at the second rejection: the Maintainer reads the text, the advisor judges it, the Director decides.

**Claude pressed Enter on a position's permission question to read outside its worktree.** The classifier refused the keystroke. Escape, and redirect to the sanctioned route (the holder runs the render in its own worktree and mails the output inline); never approve a read outside a boundary on a position's behalf.

**Claude issued a second Write in a parallel batch and put a stray file under a mistyped path.** Five times this session. One Write per step, copied path prefix, and no throwaway file.

**Claude let a PR run seven CI review rounds.** On methodology PR 123, each push drew one more valid consistency finding left over from a vocabulary rename. The Maintainer fixed one sentence per round, and the Director read each STATUS as routine. Count CI review rounds like any gate. At the second rejection of one class, order a single sweep for every term the change renamed, then one last review: an approval merges; a rejection splits its findings into a follow-up Change and merges.

**Claude spread a position's reading of an operator correction across the fleet.** The Plugins Maintainer reported a correction as "fix every bounded imperfection a Change surfaces" and withdrew two rulings; the Director rewrote its skill and mailed every Product within minutes. The operator had meant the opposite: keep each Change in scope and merge with the debt the Director judges acceptable. Read the correction in the operator's own words in the pane before changing a rule, and never widen a rule fleet-wide on a position's paraphrase.

<success_criteria>

- No position waits on the operator for more than 15 minutes unless the Director had no other way out and asked through AskUserQuestion.

- Every Change a position runs reaches the default branch on origin, is released with a Handoff, or is closed, and none stalls unnoticed past the step-in triggers in `${CLAUDE_SKILL_DIR}/references/status-report.md`.
- Every question reached its owner in the authority map: product and repository questions to the owning Maintainer, delivery mechanics to the Orchestrator or the Director, intent, cost, permission and safety to the operator.
- Every order the Director sent names its Change, rests on a methodology rule or a recorded ruling, and went through `coding-agents:message-agents`.
- After any compaction or restart, the Director resumed from its state note and roster without asking the operator what was in flight.

</success_criteria>
