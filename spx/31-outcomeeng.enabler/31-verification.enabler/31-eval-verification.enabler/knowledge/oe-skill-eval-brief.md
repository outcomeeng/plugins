---
type: Archived Source
description: Received build brief that seeded the eval-verification design — evaluation layers, no-skill baseline arms, contract semantics, and a prior-art survey. Titled by its own top-level heading, because the markdown validator reads a frontmatter `title` as a second document title.
tags: [eval-verification, harness, contracts, research, source]
timestamp: 2026-07-21T22:17:00+02:00
origin: received outside the repository
source_sha256: f6e0fdd5db55f290ddafa6e56a199ebb334a9b6f1339800bd92ea31b44be4f5f
authority: none
---

# Outcome Engineering — Skill Evaluation Harness

**Build brief for Claude Code.** Self-contained: assume no access to the conversation that produced it.

> **Archival status:** Preserved as received apart from markdown formatting, so its bytes differ from the `source_sha256` above, which pins the original. Its imperative recommendations record the brief's proposal and carry no methodology authority; the decisions and specs in this subtree govern where they diverge from it.

---

## 0. What this is

The Outcome Engineering marketplace ships **skills** (workflow instructions backed by Python scripts) and **sub-agents** (thin wrappers around skills) for Codex CLI and Claude Code CLI, with Pi Agent and Copilot CLI as later targets.

We need to answer two questions repeatably:

1. Does a new skill or sub-agent **work**?
2. Does a revised version **improve observable behavior** over the previous one?

The strategy is to make skill behavior observable by having skill scripts emit **state-machine tokens**, then verify those tokens against a declared **contract** using a deterministic checker. This converts the softest metric — "did the skill follow its intended process?" — from an LLM judgement into an automaton conformance check.

This brief specifies three deliverables:

- **Part A** — `oe_trace`, the token emission library
- **Part B** — the contract schema
- **Part C** — the conformance checker and its matching semantics
- **Part D** — a two-arm harness bake-off to decide the runner

Parts A–C are the parts nobody else has built. Part D is mostly integration.

---

## 1. Design decisions already made

These were settled deliberately. Do not relitigate them without flagging the change explicitly and explaining what new information motivates it.

### 1.1 Scripts emit tokens. The model never does.

Tokens are emitted **only** by Python skill scripts, as a side effect of doing work. The LLM is never instructed to print state markers.

Rationale:

- A model-printed token is a self-report. Feeding self-reports into a deterministic checker launders a probabilistic signal into false ground truth — worse than having no conformance layer, because we would believe it.
- If markers live in `SKILL.md` prose, editing the skill changes the behavior **and** the instrumentation at once, confounding every v16-vs-v17 comparison. Instrumentation must be invariant across compared arms. Scripts are shared across arms; prose is not.
- Instructing a model to announce workflow stages measurably improves its adherence to that workflow. The instrumented skill would outperform the shipped skill.
- Sub-agents wrap skills. Script-emitted tokens propagate through the wrapper for free; prose markers may not survive the wrapping layer.

### 1.2 Every contract state is a side effect of an action

The corollary of 1.1. Where a state transition would otherwise be an announcement, restructure the skill so it is a script call:

```
# Wrong: model says "PDR_SELECTED"
# Right: model runs `select_pdr.py --id ADR-014`, which emits the token and captures the argument
```

This is where most of the restructuring effort goes. If a state matters enough to appear in a contract, it should be worth a script call. States that remain genuinely internal to model reasoning stay **out** of the normative contract and are graded separately by LLM-as-judge, where noise is expected and priced in.

A skill whose scripts the agent routinely bypasses is a badly designed skill. Missing tokens are a finding, not a blind spot — report them, do not paper over them.

### 1.3 Tokens go to a sidecar, never to stdout

Anything on stdout enters the agent's context, where the model may echo, paraphrase or react to it — reintroducing the contamination that 1.1 avoids. Tokens are written to a path given by `OE_TRACE_PATH`, which the agent never reads.

There must be an automated test asserting that a full skill run produces **zero** token-shaped output on stdout or stderr.

### 1.4 Every eval matrix includes a no-skill baseline arm

Not `baseline = previous version`. Baseline = **the agent with no skill loaded at all**.

Published research on open skill ecosystems (OpenSkillEval, arXiv 2605.23657) found that skill availability does not guarantee effective skill usage, that the benefit depends heavily on the model and agent framework, and that many popular skills do not consistently outperform base agents without skills. For a marketplace, the no-skill arm is also the retirement criterion: it tells us which skills to delete.

Every eval therefore runs at least three arms: `none`, `v_prev`, `v_new`.

### 1.5 Contracts are normative for first-party skills, descriptive for third-party

- **Normative** — a violation fails CI. Used for skills we own.
- **Descriptive** — violations are recorded and reported as drift, never fail the build. Used for third-party skills, and as the on-ramp for authoring a normative contract later.

Third-party contracts are **inferred** from observed traces, then ratified by a human, rather than authored from scratch. See §5.6.

### 1.6 Normative does not mean strict sequence equality

Exact-sequence matching is brittle and will be disabled within a month of shipping. The contract language expresses what we actually care about — required states, forbidden states and transitions, partial ordering, cardinality bounds — and tolerates legitimate variation everywhere else.

### 1.7 The checker is a pure function

`(trace, contract) -> verdict`. No LLM, no network, no clock, no filesystem beyond reading its two inputs. Same inputs must always produce byte-identical output. This is what makes conformance results trustworthy enough to gate a build.

---

## 2. Evaluation layers

The harness measures five layers. Contracts cover Layer 2. The rest are noted so the data model accommodates them.

| Layer                   | Question                                                      | Mechanism                                     | Deterministic? |
| ----------------------- | ------------------------------------------------------------- | --------------------------------------------- | -------------- |
| 1. Routing              | Did the right skill fire, and did the wrong one stay quiet?   | Harness-native skill-invocation signals       | Yes            |
| 2. Workflow conformance | Did the skill execute its intended process?                   | **Contract + token trace**                    | Yes            |
| 3. Behavioral quality   | Did it actually solve the task?                               | LLM-as-judge rubrics, expected-finding recall | No             |
| 4. Engineering quality  | Files modified, tests passing, git hygiene, policy compliance | Post-run repo/state assertions                | Yes            |
| 5. Cost                 | Wall clock, tokens, tool calls, retries, USD                  | Harness metrics + trace timings               | Yes            |

Layer 1 needs no instrumentation from us — the agent harnesses expose skill invocation natively (Claude Agent SDK exposes `Skill` tool calls; Codex infers invocation from reads of the matching `SKILL.md`; OpenCode has a native skill tool). Layer 4 follows the Terminal-Bench/Harbor discipline: **verify properties of the final repository state, never parse the agent's narrative account of what it did.**

---

## 3. Repository layout

```
oe-skill-eval/
├── README.md
├── pyproject.toml
├── src/
│   ├── oe_trace/                  # Part A — emission library
│   │   ├── __init__.py
│   │   ├── emitter.py
│   │   └── otel.py                # optional OTLP sink
│   └── oe_conformance/            # Parts B + C
│       ├── __init__.py
│       ├── schema.py              # contract model + validation
│       ├── checker.py             # the pure function
│       ├── infer.py               # trace -> proposed contract
│       ├── aggregate.py           # N runs -> stability report
│       ├── report.py              # uplift report rendering
│       └── cli.py
├── contracts/
│   └── <skill-id>/
│       ├── contract.yaml
│       └── golden/                # frozen traces + expected verdicts
│           ├── pass-nominal.jsonl
│           ├── fail-missing-required.jsonl
│           └── expected.json
├── fixtures/
│   └── <skill-id>/
│       ├── none/                  # baseline: no skill installed
│       ├── v16/
│       │   ├── .claude/skills/<skill>/SKILL.md
│       │   ├── .agents/skills/<skill>/SKILL.md
│       │   └── <task workspace files>
│       └── v17/
└── harness/
    ├── arm-a-promptfoo/
    └── arm-b-python/
```

Note the dual skill directories in each fixture: Claude Code discovers skills under `.claude/skills/`, while Codex CLI and OpenCode discover them under `.agents/skills/`. Keep both in sync from a single source; a fixture generator script is preferable to hand-copying.

Fixture arms must differ **only** in the skill definition. Same task files, same permissions, same model, same sandbox mode. Any other difference confounds the comparison.

---

## 4. Part A — `oe_trace` emission library

### 4.1 Event schema

One JSON object per line, appended to `$OE_TRACE_PATH`.

```json
{
  "v": 1,
  "seq": 12,
  "ts": "2026-07-21T09:14:02.481Z",
  "run_id": "01J8X...",
  "instance_id": "01J8Y...",
  "parent_instance_id": null,
  "skill": "spec-tree:applying",
  "skill_version": "v17",
  "state": "CONSTRAINTS_VALIDATED",
  "ok": true,
  "dur_ms": 412,
  "args": { "spec": "spx/004" },
  "args_sha256": "9f2c...",
  "error": null
}
```

Field notes:

- `seq` — monotonic per `run_id`, assigned by the emitter. The checker orders by `seq`, **not** by `ts`. Wall-clock timestamps are unreliable across processes and must never determine ordering.
- `instance_id` — one per skill activation. Scopes transition adjacency (§5.3). Without it, a sub-agent invoking a skill mid-run would produce false adjacent-transition violations from interleaving.
- `parent_instance_id` — set when a sub-agent or skill invokes another skill. Yields the call tree for free.
- `ok` — `false` means the state was **attempted and failed**. A state counts as *reached* only when `ok: true`. Failed attempts still appear in the trace and are available to the checker.
- `args` — optional and redactable. `args_sha256` is always present, computed over the canonical JSON form of `args`, so two runs can be compared for argument equality even when args are redacted.

### 4.2 API

```python
from oe_trace import trace

# Point emission
trace.emit("SPEC_LOADED", args={"path": spec_path})

# Span form — records dur_ms, sets ok=False and error on exception, then re-raises
with trace.span("REPO_SCANNED", args={"root": root}):
    scan(root)

# Sub-skill invocation
with trace.child(skill="spec-tree:testing", version="v3") as child:
    ...
```

### 4.3 Emitter requirements

- Open `$OE_TRACE_PATH` with `O_APPEND`; write one line per event with a single `write()` call so concurrent processes cannot interleave partial lines.
- If `OE_TRACE_PATH` is unset, **no-op silently**. Skills must run identically in production with no trace sink. Never crash a user's run because tracing is unconfigured.
- Never write to stdout or stderr under any circumstance, including on internal error. Failures inside the emitter are swallowed and optionally recorded to `$OE_TRACE_PATH.err`.
- Optional second sink: if `OTEL_EXPORTER_OTLP_ENDPOINT` is set, mirror each event as an OpenTelemetry span (state as span name, args as attributes, `instance_id` as the span hierarchy). This gives the dashboard for free without a second instrumentation pass. Keep it strictly optional and out of the checker's path.
- Cost is measured by the harness, not the emitter. Do not attempt token accounting here.

---

## 5. Part B — contract schema

### 5.1 Full example

```yaml
contract_version: 1

skill: spec-tree:applying
skill_version: v17
mode: normative # normative | descriptive
provenance: authored # authored | inferred
inferred_from_runs: null # int, when provenance == inferred

# Declared vocabulary. Any state in the trace that is not declared here is
# reported as UNDECLARED_STATE (warning in normative mode, ignored in descriptive).
states:
  - SPEC_LOADED
  - CONSTRAINTS_VALIDATED
  - REPO_SCANNED
  - PDR_SELECTED
  - IMPLEMENTATION_STARTED
  - VERIFICATION_RUNNING
  - AUDIT_COMPLETED
  - SUCCESS
  - ABORTED

# Must be reached (ok: true) at least once.
required:
  - SPEC_LOADED
  - CONSTRAINTS_VALIDATED
  - IMPLEMENTATION_STARTED
  - AUDIT_COMPLETED

# Must never be reached.
forbidden_states:
  - LEGACY_PATCH_APPLIED

# Must never occur as adjacent states within one instance_id.
forbidden_transitions:
  - from: SPEC_LOADED
    to: IMPLEMENTATION_STARTED
    reason: implementation must not begin before constraints are validated

# Partial ordering.
#   scope: first  — first occurrence of `before` precedes first occurrence of `after`
#   scope: all    — every occurrence of `after` is preceded by some occurrence of `before`
ordering:
  - before: CONSTRAINTS_VALIDATED
    after: IMPLEMENTATION_STARTED
    scope: all
  - before: REPO_SCANNED
    after: PDR_SELECTED
    scope: first

# Occurrence counts (ok: true only).
cardinality:
  PDR_SELECTED: { min: 1, max: 1 }
  VERIFICATION_RUNNING: { min: 1, max: 3 }
  REPO_SCANNED: { max: 2 }

# The run must end in exactly one of these.
terminal:
  any_of: [SUCCESS, ABORTED]

# Layer 5 gates. Sourced from the harness, not the trace.
budgets:
  wall_clock_s: 180
  tokens: 60000
  tool_calls: 80
  usd: 0.75

# Per-rule severity overrides. Defaults in §5.5.
severity_overrides:
  UNDECLARED_STATE: warning
```

### 5.2 Sub-agent contracts

A sub-agent contract is a normal contract whose `states` are drawn from the sub-agent's own vocabulary, plus a `delegates` block asserting which child skills it must invoke:

```yaml
skill: subagent:apply-and-verify
delegates:
  required:
    - spec-tree:applying
    - spec-tree:testing
  forbidden:
    - spec-tree:bootstrapping
```

`delegates` is checked against `parent_instance_id` linkage, not against state names. This gives Layer 1 routing verification *inside* a sub-agent, which harness-level skill-invocation signals cannot see.

### 5.3 Validation of the contract itself

`oe-conformance validate contracts/<skill>/contract.yaml` must reject, with exit code 3:

- states referenced in `required`, `forbidden_*`, `ordering`, `cardinality` or `terminal` but absent from `states`
- a state in both `required` and `forbidden_states`
- cyclic `ordering` constraints
- `cardinality` with `min > max`, or `min: 0` combined with membership in `required`
- `mode: normative` combined with `provenance: inferred` and no human ratification marker

---

## 6. Part C — conformance checker

### 6.1 Input normalization

1. Read the JSONL trace; discard lines that fail schema validation, counting them as `MALFORMED_EVENT` warnings.
2. Filter to events whose `skill` matches the contract, **plus** child events when the contract has a `delegates` block.
3. Sort by `seq` ascending. Ties (which indicate an emitter bug) are broken by file order and raise a `SEQ_COLLISION` warning.
4. Partition by `instance_id`. Each partition is checked independently; a run passes only if every instance passes.

Definition used throughout: a state is **reached** iff at least one event exists for it with `ok: true`. Events with `ok: false` are *attempts*; they are visible to the checker but do not satisfy `required` or count toward `cardinality`.

### 6.2 Rule evaluation

| Rule                        | Passes when                                                                                                                                                                  |
| --------------------------- | ---------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `required`                  | every listed state is reached                                                                                                                                                |
| `forbidden_states`          | no listed state is reached                                                                                                                                                   |
| `forbidden_transitions`     | no listed `(from, to)` pair appears at adjacent positions in the instance's ordered event list                                                                               |
| `ordering` / `scope: first` | `index(first ok occurrence of before) < index(first ok occurrence of after)`; vacuously true if `after` never occurs; **violated** if `after` occurs and `before` never does |
| `ordering` / `scope: all`   | for every ok occurrence of `after` at index *i*, there exists an ok occurrence of `before` at index *j < i*                                                                  |
| `cardinality`               | `min <= count(ok occurrences) <= max`; omitted bounds are unbounded                                                                                                          |
| `terminal`                  | the last ok event in the instance is a member of `any_of`                                                                                                                    |
| `budgets`                   | harness-reported metric is at or below the declared ceiling                                                                                                                  |
| `delegates`                 | required child skills appear with `parent_instance_id` linking to this instance; forbidden ones do not                                                                       |

Adjacency for `forbidden_transitions` is computed **within an `instance_id` only**. Child-instance events do not break adjacency in the parent.

### 6.3 Violation record

```json
{
  "code": "ORDERING_VIOLATED",
  "severity": "error",
  "rule": { "before": "CONSTRAINTS_VALIDATED", "after": "IMPLEMENTATION_STARTED", "scope": "all" },
  "instance_id": "01J8Y...",
  "evidence": { "offending_seq": 31, "state": "IMPLEMENTATION_STARTED" },
  "message": "IMPLEMENTATION_STARTED at seq 31 with no preceding CONSTRAINTS_VALIDATED"
}
```

Every violation must carry `evidence` pointing at concrete `seq` values. A violation the author cannot locate in the trace is a bug in the checker.

### 6.4 Verdict

```json
{
  "contract": "spec-tree:applying",
  "skill_version": "v17",
  "mode": "normative",
  "run_id": "01J8X...",
  "pass": false,
  "conformance_score": 0.86,
  "checks_total": 22,
  "checks_failed": 3,
  "violations": [ ... ],
  "warnings": [ ... ],
  "states_reached": ["SPEC_LOADED", "..."],
  "states_declared_unreached": ["PDR_SELECTED"]
}
```

- `pass` is **binary and strict**: false if any `error`-severity violation exists. This is what gates CI in normative mode. In descriptive mode `pass` is always `true` and violations are reported as drift.
- `conformance_score` is `1 - (failed_checks / total_checks)`, all checks weighted equally. It exists for regression *tracking*, never for gating. Do not weight it — weights invite tuning the score instead of fixing the skill.

### 6.5 Default severities

| Code                                      | Default                                             |
| ----------------------------------------- | --------------------------------------------------- |
| `REQUIRED_STATE_MISSING`                  | error                                               |
| `FORBIDDEN_STATE_REACHED`                 | error                                               |
| `FORBIDDEN_TRANSITION`                    | error                                               |
| `ORDERING_VIOLATED`                       | error                                               |
| `CARDINALITY_VIOLATED`                    | error                                               |
| `TERMINAL_STATE_INVALID`                  | error                                               |
| `BUDGET_EXCEEDED`                         | error                                               |
| `DELEGATE_MISSING` / `DELEGATE_FORBIDDEN` | error                                               |
| `UNDECLARED_STATE`                        | warning                                             |
| `MALFORMED_EVENT`                         | warning                                             |
| `SEQ_COLLISION`                           | warning                                             |
| `NO_TRACE_EMITTED`                        | error (exit 2 — harness failure, not skill failure) |

Distinguish exit 2 from exit 1 carefully. "The skill violated its contract" and "no trace was produced" are different failures and must not be conflated in CI output.

### 6.6 Multi-run aggregation

Agent runs are nondeterministic; a single run proves little. `oe-conformance aggregate` takes N verdicts for one arm and emits:

- `pass_rate` with a bootstrap 95% confidence interval
- `violations_by_code` frequency table
- `unstable_states` — states reached in some runs but not others. Reported as an **`unstable_path` warning, never a failure.** Path instability is a property worth tracking over versions in its own right; a v17 that reaches the same states every time is better than a v16 that wanders, even at equal pass rates.
- `flake_rate` — proportion of runs whose verdict differs from the modal verdict

Default N is 5. Comparisons between arms must use identical N.

### 6.7 Contract inference (third-party on-ramp)

`oe-conformance infer --traces <dir> --skill <id>` proposes a contract from observed traces:

- `states` — every state observed
- `required` — states reached in ≥ 95% of runs
- `ordering` — pairs whose relative order held in **100%** of runs, emitted with `scope: all`
- `cardinality` — observed `[min, max]`, with `max` padded by 1 to allow headroom
- `forbidden_states` / `forbidden_transitions` — **always empty.** Absence cannot be inferred from observation; these require a human.
- `terminal` — observed terminal states
- emitted with `mode: descriptive`, `provenance: inferred`, `inferred_from_runs: N`

Requires ≥ 20 traces; refuse below that with a clear message. The output is a **proposal for human ratification**, and promoting it to `mode: normative` must be an explicit human edit. This is the marketplace onboarding path, and it makes descriptive mode a contract-authoring tool rather than a second-class citizen.

---

## 7. Part D — harness bake-off

Build both arms against the **same** fixture set, then decide. Do not attempt to pick a winner on paper.

### 7.1 Choosing the bake-off fixture

Use a skill where the answer is already known:

- one revision pair believed to be a **real improvement**
- one revision pair believed to be **behaviorally neutral**

A harness that cannot detect the improvement we know is there is underpowered, and we learn that in a day rather than a quarter. A harness that reports a large difference on the neutral pair is too noisy. Validate the instrument against known ground truth before pointing it at unknowns.

### 7.2 Arm A — promptfoo runner

TypeScript/YAML, MIT-licensed. Provides out of the box: providers for Codex SDK and Claude Agent SDK, normalized skill-invocation assertions (`skill-used` / `not-skill-used`), `cost` and `latency` assertions, `--repeat N`, side-by-side web view, and a GitHub Action.

Wire Layer 2 in by setting `OE_TRACE_PATH` per test case and adding a JavaScript assertion that shells out to `oe-conformance check` and returns its verdict. Layer 1, 3 and 5 use native assertions.

Neither Pi Agent nor Copilot CLI has a first-party provider anywhere in the ecosystem. Both need a custom exec provider (~100 lines each) that shells out, captures output, and normalizes. **Out of scope for v1** — do Codex and Claude Code first, then generalize.

### 7.3 Arm B — Python harness

Plain `pytest` plus a thin subprocess driver per CLI, or Inspect AI if its dataset/scorer primitives earn their keep. Reuses `oe_conformance` directly rather than shelling out.

### 7.4 Decision criteria

Judge on, in order: lines of code we have to maintain; flake rate across 5 repeats; time from `git clone` to first result; and whether adding the third and fourth CLI targets looks linear or quadratic. **Not** on feature count.

### 7.5 Uplift report

Whichever arm wins, the output artifact is the same — one table per skill, Markdown and HTML:

| Metric                      | none  | v16   | v17   | Δ v16→v17 |
| --------------------------- | ----- | ----- | ----- | --------- |
| Routing precision           | —     | 0.91  | 0.97  | +0.06     |
| Conformance pass rate       | —     | 0.60  | 1.00  | +0.40     |
| Contract violations (total) | —     | 5     | 0     | −100%     |
| Goal completion             | 0.41  | 0.84  | 0.89  | +0.05     |
| Unstable states             | —     | 3     | 0     | −3        |
| Tokens (median)             | 3,900 | 8,100 | 6,500 | −20%      |
| Wall clock (median)         | 12s   | 47s   | 38s   | −19%      |

The `none` column is mandatory. A skill whose `v17` column does not clearly beat `none` is a deletion candidate regardless of how much it improved over `v16`.

---

## 8. Build order

1. `oe_trace` emitter + event schema + the stdout-cleanliness test (§1.3)
2. Instrument **one** skill end to end; restructure its announcements into script calls per §1.2
3. Contract schema + `validate` command
4. Checker, driven entirely by golden traces — write `pass-nominal` and one golden trace per violation code **before** the checker exists
5. Aggregation and the uplift report
6. Arm A and Arm B, in parallel, against the §7.1 fixture
7. Decide; delete the losing arm
8. `infer` for third-party skills
9. Optional OTLP sink and dashboard
10. Pi Agent and Copilot adapters

Steps 1–5 are the durable work and are harness-independent. Do not start step 6 before step 4 is green.

---

## 9. Acceptance criteria

- Checker is a pure function: the golden-trace suite produces byte-identical verdicts across 100 consecutive runs, on a fresh process each time.
- Every violation code has at least one golden trace that triggers it and one that does not.
- A full instrumented skill run emits zero token-shaped output on stdout and stderr.
- Skill scripts run correctly with `OE_TRACE_PATH` unset, producing no trace and no errors.
- Contract validation rejects all malformed cases in §5.3 with exit code 3.
- `infer` on 20+ traces from a known skill reproduces that skill's hand-authored `required` and `ordering` sets.
- The harness detects the known-good improvement in the §7.1 fixture at N=5 and does **not** report a significant difference on the neutral pair.
- Exit codes are distinct and documented: `0` pass, `1` contract violation, `2` harness/trace failure, `3` invalid contract.

---

## 10. Non-goals for v1

- MCP server evaluation
- Automatic synthesis of eval tasks. Published frameworks synthesize tasks because they grade thousands of skills they did not write; we wrote ours and know what correct looks like. Hand-written fixtures win until we are maintenance-bound.
- Red-teaming and adversarial robustness
- Pi Agent and Copilot CLI adapters
- Any LLM in the conformance path

---

## 11. Prior art worth reading, and what to take from each

| Source                                                                | Take                                                                                                                                          |
| --------------------------------------------------------------------- | --------------------------------------------------------------------------------------------------------------------------------------------- |
| OpenSkillEval (arXiv 2605.23657)                                      | The no-skill baseline finding (§1.4). Also its two-perspective split: agent-level vs skill-level comparison.                                  |
| A Framework for Evaluating Agentic Skills at Scale (arXiv 2606.17819) | Evaluating a single skill in isolation, and instruction-following vs goal-completion as separable metrics.                                    |
| promptfoo — "Test Agent Skills" guide                                 | Fixture-per-version layout; hold everything constant and swap only `SKILL.md`. Near-miss prompts that must route to a *sibling* skill.        |
| Terminal-Bench / Harbor                                               | Verify final environment state, never the agent's console narrative. Repeated trials with confidence intervals as the default reporting unit. |

Nothing in the surveyed ecosystem treats skills as contract-defined state machines. Parts B and C are novel and are the components worth open-sourcing.
