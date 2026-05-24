<!-- Prompt template for the merge-command-overlay-precedence eval.
     The harness substitutes the case id and input JSON tokens before
     sending the prompt to the model.

     Probe scope: the eval verifies the agent's merge-command selection
     when the PR authority gate is gate-green-autonomous. The case
     supplies the overlay's merge-command declaration (or its absence);
     the model decides which `gh pr merge` flag the agent runs. The
     gate's other predicates are stipulated as green for every case so
     this eval probes the command-selection rule in isolation. -->

You are simulating the PR-management agent at /managing-pr Step 8 (gate-green-autonomous merge). The gate's predicates have all evaluated green for the PR under simulation: closure gate passed, required checks terminal-green, current-head three-severity review with no `blocking` or `debt`, settle window elapsed, branch hygiene holds, no production-class markers. The agent is about to run the merge command.

The rule under audit:

- The agent follows the overlay's declared merge command when one exists.
- When the overlay is silent on the merge command, the universal default is rebase merge (`gh pr merge --rebase`).
- The agent never selects a merge commit (`--merge`) or squash (`--squash`) command from the gate alone; those require the overlay to opt in with explicit rationale.

Case id: substituted by the harness.

The overlay configuration the agent has loaded for this PR (JSON-encoded):

```json
{input_json}
```

Your **entire response** must be exactly one JSON document — no prose, no markdown fences, no commentary before or after — in this exact shape:

```
{
  "merge_flag": "--rebase" | "--merge" | "--squash",
  "source": "overlay" | "universal-default"
}
```

`merge_flag` is the flag the agent passes to `gh pr merge <pr-number>`. `source` is `overlay` when the agent's choice follows an overlay declaration, or `universal-default` when the overlay is silent and the agent falls back to rebase. The coupling ensures the model identifies WHERE its choice came from rather than just emitting a flag — an `--merge` answer with `source: universal-default` is wrong because the universal default is rebase, not merge commit; an `--rebase` answer with `source: overlay` is wrong unless the overlay explicitly declares rebase.
