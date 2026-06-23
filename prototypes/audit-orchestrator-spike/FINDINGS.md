# Findings — audit-orchestrator benefit spike

Ran `spike.py` against the real `spx journal` (local backend) on 2026-06-23.
Three per-commit runs recorded, sealed, and read back; the fold ran over actual
journal events, not an in-memory mock.

## Result — the fold surfaces a signal the stateless audit cannot

Scenario: commit A finds three issues; B fixes the magic value; C fixes the
coupling finding but a refactor reintroduces the magic value.

At commit C:

|        | Stateless per-run audit (ships today)     | Orchestrator (fold of the run set)         |
| ------ | ----------------------------------------- | ------------------------------------------ |
| output | flat: `magic-value`, `missing-annotation` | open: `magic-value`, `missing-annotation`  |
|        |                                           | resolved: `no-mocking` (coupling fix held) |
|        |                                           | **reopened: `magic-value` — REGRESSION**   |

The headline is **reopened**. The stateless audit reports the magic value as
just another current finding; the orchestrator knows it was fixed at B and came
back at C — a regression, the single most actionable cross-commit signal. The
`resolved` line is secondary but real: positive confirmation that the coupling
fix held. Neither is reconstructable from a single run's events — they are a
function of the *run set*.

**Verdict: the benefit is real.** Folding prior runs earns its keep for a
developer iterating across local commits. A stateful audit orchestrator is
worth designing.

## What this spike does NOT establish

1. **Frequency, not just possibility.** It proves the fold *can* surface a
   regression; it does not measure how often real audit iterations regress, so
   it does not prove the value clears the cost bar on its own. The mechanism is
   sound; the cost/benefit at scale is a separate judgment.
2. **Synthetic findings.** The three finding sets are hand-built, not real
   `/audit` output. The fold logic is what was tested, not the audit itself.
3. **It sidesteps the actual hard primitive.** The orchestrator must read the
   *prior* runs back, but the journal has no run-set verb — `read` requires a
   `--run <token>`. The spike cheats by tracking the tokens it just created. A
   real orchestrator cannot know prior tokens across invocations: **discovering
   and reading the scope's sealed runs is the one primitive the local journal
   genuinely lacks.** The spike confirms the value *and* isolates the gap to
   exactly this — run-set discovery on the local backend, nothing more.
4. **No architecture conclusion.** It says nothing about *how* to build the
   orchestrator. The next question — follow the merge skill's backend-neutral
   pattern (neutral policy, edge-bound backend) rather than the
   pr-review-orchestrator's hard-coded mechanism — is only worth answering now
   that the value is shown.

## Next step

Design the orchestrator (architecture, on the merge-skill backend-neutral
pattern) and scope the journal primitive to its minimum: **list/read a local
scope's sealed runs in order.** No `github-pr` involvement — that backend is a
separate source of truth and out of the local orchestrator's scope.
