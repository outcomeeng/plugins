---
name: probe
description: >-
  ALWAYS invoke this skill before writing or repairing probe evidence for a spec assertion, recording an attested run of a probe protocol, or deciding whether a probe's attested run is current.
argument-hint: <full-spx-node-path> [selected-assertions-json-array] [repair-block]
allowed-tools: Read, Glob, Grep, Write, Edit, Bash, request_user_input
---

<objective>
Product Tree `[probe]` evidence: a probe protocol at `probes/{probe-slug}/probe.md` that any Author can repeat, an attested run whose observations and inspectable artifacts are linked from the protocol, and the Author's verdict, recorded for a claim only an executed observation of the running node settles.
</objective>

<prerequisites>

Use skill `product-tree:understand`. The probe template and the probe example it locates are the structure of every protocol this skill writes.

</prerequisites>

<essential_principles>

- A probe verdict is attested: the Author's verdict together with the inspectable artifacts of an executed protocol. It never stands in for a deterministic or agentic verdict. A claim with a deterministic verdict returns to `/verify` for a test or eval; a claim that needs semantic judgment returns to it for an audit.
- Record only what the executed protocol showed. Never write a verdict, an observation, or an artifact link for a step that did not run, and never invent an artifact.
- Write no actor identity, session, or model name into the protocol. The verification run supplies the actor provenance.
- Raise no cost, quota, worker, retry, timeout, or budget ceiling. A run that a default ceiling stops is reported with the exact command and ceiling, and the operator decides.
- Use skill `product-tree:wait-for-load` for every resource-intensive command the protocol runs: run each one under that skill's guard line in the foreground, and report a result only after every such line has exited.

</essential_principles>

<workflow>

<step name="load_context">

**Step 1: Load tree context**

Abort when `$ARGUMENTS` is empty: "A canonical spec node target is required." Otherwise parse one canonical node target followed by an optional JSON array of exact assertion texts already selected for probe. Preserve each array string verbatim. Reject malformed JSON or non-string members before reading the target. A decision target is invalid input: the decision grammar has no probe subsection, so the spec that implements the rule carries its probe assertion. Text after the target and the optional array is a repair block: the verbatim result of each rejected verdict and the exact command line and output of each failed deterministic command of an earlier round. Repair every finding and failure it names, and report each one's disposition.

Check for `<PRODUCT_TREE_FOUNDATION>` and `<PRODUCT_TREE_CONTEXT>` markers. When either is absent: Use skill `product-tree:understand`. Use skill `product-tree:contextualize`.

</step>

<step name="extract_assertions">

**Step 2: Extract probe assertions**

Take the assertions already tagged `[probe](path)` plus the exact untagged assertions supplied in the array. Ignore every other untagged assertion. For each, record the assertion text, the probe link and whether `probe.md` resolves, and the running node behavior the claim concerns.

Confirm that only an executed observation settles the claim. When a deterministic function of inputs, a scorable structured output, or a semantic constraint settles it, write no protocol and report `misrouted` naming the assertion and the verification type `/verify` should select.

</step>

<step name="inspect_protocol">

**Step 3: Inspect existing protocols**

For a resolving link, read `probe.md` and the artifacts it links. The attested run is current when the protocol text is unchanged since the run and none of the paths the run observed has changed since it. Treat unrecorded provenance as stale. A current attested run needs no new run; a stale or absent one proceeds to Step 4 and Step 5.

</step>

<step name="write_protocol">

**Step 4: Write the protocol**

Place the protocol at `probes/{probe-slug}/probe.md` inside the governing node, with a `{probe-slug}` that names the observed behavior. Read the probe template under the `Template root` the foundation marker records, and write the protocol from it: the intent names the uncertainty between operator and agent the probe exposes, the environment and preconditions state what must hold before the run, and each protocol step is one any Author, person or agent, can execute and repeat. State the limitations the protocol does not exercise. Write no attested run and no verdict before a run has happened.

When the target's governing node, context, or operator-owned detail leaves a precondition unknown, ask through request_user_input when that tool is available; otherwise stop with `blocked`, naming the question verbatim and the write it blocks.

</step>

<step name="attest_run">

**Step 5: Execute the protocol and attest the run**

Execute the protocol exactly as written, in the environment its preconditions describe. Keep working runs in the ignored `runs/` inside the probe directory. Retain at least one inspectable artifact beside `probe.md` — a recording, screenshot, transcript, log, or structured output — and record under `## Attested run` the date, the observations step by step, and a link to every retained artifact. Write the Author's verdict, `passed` or `failed`, with the observation that decides it.

When a precondition cannot be met in this session, such as a device, account, or build the Author lacks, leave the protocol without an attested run and report `run-required` naming the precondition. A failed verdict is evidence: record it and return the defect to the workflow that owns the running node. Never edit the node to make a protocol pass, and never alter a protocol step after a run to match what the run showed.

</step>

<step name="link_evidence">

**Step 6: Link the evidence**

Update the spec's `[probe](probes/{probe-slug}/probe.md)` link for each assertion the protocol evidences, with the node-local relative path. Leave every other assertion untouched.

</step>

<step name="report">

**Step 7: Report**

```markdown
| # | Assertion | Protocol | Attested run | Verdict | Result       |
| - | --------- | -------- | ------------ | ------- | ------------ |
| 1 | {text}    | {path}   | current      | passed  | Recorded     |
| 2 | {text}    | {path}   | absent       | —       | run-required |
```

</step>

</workflow>

<success_criteria>

- Every probe assertion's claim is one only an executed observation settles, or the assertion is reported `misrouted` with the verification type to select.
- Every protocol lives at `probes/{probe-slug}/probe.md`, follows the probe template, and holds steps any Author can repeat.
- Every recorded attested run links at least one inspectable artifact beside the protocol and every other artifact it retained, and rests on a step-by-step observation of an executed run.
- Every verdict is the Author's `passed` or `failed`, names the deciding observation, and carries no actor identity.
- A run that could not execute is reported `run-required` with its unmet precondition, and no verdict is written for it.
- No attested result is presented as a deterministic or agentic verdict.

</success_criteria>
