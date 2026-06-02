<!-- Prompt template for the merge-command-overlay-precedence eval.
     The harness substitutes the case id and input JSON tokens before
     sending the prompt to the model.

     Probe scope: the eval verifies the agent's merge-command selection
     when MERGE_READINESS and PRODUCTION_READINESS both hold. The case
     supplies the overlay's merge-command declaration (or its absence);
     the model decides which `gh pr merge` flag the agent runs. The
     gate's other predicates are stipulated as green for every case so
     this eval probes the command-selection rule in isolation. -->

You are simulating the PR-management agent evaluating the merge-command selection in `/managing-pr` Step 8 after `MERGE_READINESS` and `PRODUCTION_READINESS` are confirmed. Both hold for the PR under simulation: a clean current-head CI review exists, every other required check is terminal-green, branch hygiene holds, and the change is non-production-relevant or operator-approved. The agent is about to run the merge command.

The rule under audit:

- The agent follows the overlay's declared merge command when one exists, regardless of whether the overlay carries a rationale string. Rationale is documentation for human reviewers of the overlay change itself; it is not a runtime predicate the agent enforces.
- When the overlay is silent on the merge command, the universal default is rebase merge with inline branch deletion (`gh pr merge --rebase --delete-branch`).
- The agent never selects a merge commit (`--merge`) or squash (`--squash`) command from the gate alone — those require the overlay to opt in.

Case id: substituted by the harness.

The overlay configuration the agent has loaded for this PR (JSON-encoded):

```json
{input_json}
```

Verdict schema — two fields, both mandatory:

- `merge_flag`: `"--rebase"`, `"--merge"`, or `"--squash"` — the flag passed to `gh pr merge`.
- `source`: `"overlay"` (choice follows an overlay declaration) or `"universal-default"` (overlay is silent, falls back to rebase).

An `--merge` answer with `source: universal-default` is wrong because the universal default is rebase; an `--rebase` answer with `source: overlay` is wrong unless the overlay explicitly declares rebase.
