# Issues: Issue Filing

## The two handoff stdin forms are coupled by prose alone

`src/plugins/spec-tree/skills/issue/SKILL.md` Step 6 spells the
`<dependency_followup_body>` line sequence twice — once as heredoc lines, once as
`printf` arguments — because `spx/15-agent-tools.pdr.md` requires a named form per
harness. Two notes state the coupling, one at the body contract and one at the forms,
but nothing enforces it: an edit to the section order or count in one block can ship
while the other keeps the old sequence, and the resulting handoff body differs by
harness.

**Resolution shape**: render both blocks from one ordered section list at build time, or
add a deterministic check asserting the two blocks enumerate the same tag sequence and
wire it into the skill checks. Either is verification machinery this changeset does not
carry — a build-step or gate change with its own evidence and its own auditor pass —
rather than an edit to the skill body.

A fully worked `<dependency_followup_body>` — the section sequence filled with real
values rather than placeholders — belongs to the same fix. The sequence is already
spelled three times: once canonically under `<dependency_followup_body>` and once in
each Step 6 stdin form. A hand-maintained fourth copy widens exactly the drift this
entry records, so the worked example is emitted by whatever renders the other blocks
from the ordered section list, never authored beside them.

**Evidence**: raised by `instructions:skill-auditor` across three rounds on
`work/issue-harness-command-form-and-mapping-domain`; the prose notes it accepted close
the reader-facing half, and it kept the enforcement gap open as worth-improving. The
worked-example request is that auditor's `f-006` on the third round, which the
higher-risk external-target confirmation example (`f-007`) was applied for because it
duplicates nothing.

Selecting between the two forms is stated without a checkable signal. The same Step 6
names which harness takes which form — an interactive Claude Code or Codex session the
heredoc, a programmatic run the `printf` line — and names no environment variable, tty
check, or invocation-mode flag that decides which a session is.
`src/plugins/spec-tree/skills/open-pr/SKILL.md` and
`src/plugins/spec-tree/skills/commit-changes/SKILL.md` carry the same construction, so a
wording fix here alone leaves the marketplace holding two spellings of one convention.
`spx/15-agent-tools.pdr.md` scopes the guidance by environment rather than by a runtime
signal, so closing this asks whether a detectable harness-mode signal belongs in that
decision — a decision change reaching three skills under three governing nodes, not an
edit to this skill's prose.

**Evidence**: `instructions:skill-auditor` `f-008` (`unverifiable_harness_selection`,
WARNING) on head `4b2ea0125a4ac9fa281bb105646179a850554f93`; that verdict names the
sibling occurrences.

## Two Compliance assertions bundle roughly seven rules each

`spx/21-spec-tree.enabler/76-sessions.enabler/43-issue.enabler/issue.md` carries two Compliance
bullets that each decompose into about seven independently falsifiable rules: the resolution
assertion (invoking-repository self-identification, the marketplace Directory source, the `spx` CLI
checkout, the invoking repository for its own product, the queue-safe-checkout run target, and two
NEVER clauses) and the one-fresh-record assertion (one fresh `todo`, header-only reading, overlap
reporting, and four NEVER clauses).

Every sub-clause is a well-formed universal `[audit]` claim, so `/audit-specs` passes the node on
section structure, atemporal voice, and tag fitness; its closed violation vocabulary carries no
compound-assertion pattern. Splitting a bullet into separately verifiable assertions is a
composition decision.

**Resolution shape**: run `/decompose` over this node, splitting each bundle into assertions with
their own validation boundary, and settle the assertion count below against the same pass.

**Evidence**: surfaced by an adversarial `spec-auditor` pass over the merged PR #528 changeset
(range `9b55d438eb0223b0d78ed6e300d18292da1ec8b0..c7cd1e650adc59d915f3417cfa6ee7b7367b0591`), which
confirmed the rule counts and recorded them as outside its own REJECT vocabulary.

## The node's assertion count carries no recorded disposition

The node carries 18 assertions. `spx/21-spec-tree.enabler/54-decomposing.enabler/decomposing.md`
treats more than roughly seven as a signal requiring decomposition analysis. The parent's
`spx/21-spec-tree.enabler/76-sessions.enabler/PLAN.md` records an assertion-count disposition for
`spx/21-spec-tree.enabler/76-sessions.enabler/15-session-store.enabler`,
`spx/21-spec-tree.enabler/76-sessions.enabler/25-handoff.enabler/40-continuation-disposition.enabler`,
`spx/21-spec-tree.enabler/76-sessions.enabler/25-handoff.enabler/20-closure.enabler`, and
`spx/21-spec-tree.enabler/76-sessions.enabler/28-pickup.enabler/30-claim-verification.enabler`, and
does not list this node. The signal is therefore open and unrecorded rather than analyzed and
accepted.

**Resolution shape**: in the same `/decompose` pass as the entry above, either split the node or
record the accepted count and its reasoning in the parent's assertion-count disposition table,
alongside the four nodes already dispositioned there.

**Evidence**: same adversarial `spec-auditor` pass; both counts confirmed against the node spec and
the parent `PLAN.md`.

## Marketplace-resolver extraction awaits a published SPX CLI capability

`src/plugins/spec-tree/skills/issue/scripts/resolve_marketplace.py` runs to 152
lines — resolution of a marketplace entry's registered local source from JSON on
stdin, covering the Claude Directory-source and Codex local-marketplace-source
shapes, with distinct errors for malformed JSON and an unresolvable target. Past
fifty lines `spx/12-shipped-scripting.adr.md` makes a shipped script debt whose
logic moves into the SPX CLI once the script proves its value; the resolver has
proven its value in use, so extraction is what it owes.

The extraction is a cross-repo port into `@outcomeeng/spx`, a separate product,
and the plugins product may depend on the resulting capability only once it is
published to npm and `REQUIRED_SPX_VERSION` advances to it. That sequencing puts
the fix outside any changeset confined to this repository.

**Resolution shape**: port marketplace-source resolution into the SPX CLI,
publish it, advance the floor, and reduce the shipped skill to its instruction
with no script. Keep the per-agent source shapes — Claude Directory source and
Codex local marketplace source — both resolvable after the move, since
`spx/12-marketplace-state.adr.md` makes each agent's registration committed
repository configuration. Revisit when the capability publishes.
