---
name: control-token-spend
description: >-
  ALWAYS invoke this skill when measuring coding-session token consumption,
  explaining context and cache costs, detecting spending bursts, or managing
  local usage-report schedules.
argument-hint: "[report|collect|detect|hourly|install|status|stop|restart] [options]"
allowed-tools: Read, Bash(python3 --version), Bash(python3 -B "${CLAUDE_SKILL_DIR}/scripts/usage_control.py":*), request_user_input
---

<objective>

Durable local consumption evidence and advisory budget signals from bounded,
deterministic transcript processing, with inspectable scheduled-worker state.

</objective>

<dependencies>

- Python 3.13 or 3.14; standard library only. Check the interpreter before running.
- Readable Claude Code transcripts; the default source is `~/.claude/projects`.
- macOS launchd for managed scheduling. Other platforms return unsupported.
- Optional investigation supports `aise 1.0.0-rc.4` with an explicitly selected
  existing database. Accounting works without it. Never install dependencies,
  start TraceRoost, rebuild an index, or invoke a model for these operations.

</dependencies>

<testing>

Release verification uses captured native assistant and tool-result records,
generated streaming usage and monetary boundaries, real SQLite partial-row and
timestamp-boundary imports, linked report formats, durable alert deduplication,
retention and overlap checks. Copied assets run with site packages disabled and
an empty executable search path. Recording command collaborators exercise managed
job restart and permission failure without changing shared launch agents.

</testing>

<input_output>

Read `$ARGUMENTS` as the requested operation and its options. Empty arguments
select `report`, covering the preceding hour. Translate natural-language intent
into individual CLI arguments; quote each value and never evaluate supplied text
as shell syntax. Use `--help` for the bundled command's exact option grammar.

| Input                         | Contract                                                                                                                                      |
| ----------------------------- | --------------------------------------------------------------------------------------------------------------------------------------------- |
| `SPX_USAGE_RESET_AT`          | Required explicit UTC timestamp anchoring seven-day periods; reuse saved installation configuration when available. Ask for an absent anchor. |
| `SPX_USAGE_ALERT_USD`         | Positive estimated API-equivalent threshold for the rolling fifteen-minute detector; default 20.                                              |
| `SPX_USAGE_WEEKLY_BUDGET_USD` | Optional positive weekly API-equivalent target; no default. Its absence disables weekly budget and pace signals.                              |
| `--root`                      | Stable operator-owned state root; default `~/Library/Application Support/Outcome Engineering/usage-control`.                                  |
| `--projects`                  | Read-only transcript root, disjoint from the state root.                                                                                      |
| `--start`, `--end`            | Inclusive start and exclusive end, timezone-aware ISO timestamps. Freeze these when comparing reports.                                        |
| `--aise`, `--aise-database`   | Both required when optional investigation is selected; an absent or incompatible tool records a gap.                                          |

The runtime persists incremental offsets, reconciled requests and bounded evidence
in SQLite. A report directory contains `report.html`, `measurements.json`,
`sessions.csv`, and linked `evidence.html` excerpts with original-source references.
`latest-report.json` identifies the latest report. Detector evidence lives under
`alerts/`; `worker-status.json` and `retention-status.json` expose operational state.

</input_output>

<available_scripts>

Run `python3 -B "${CLAUDE_SKILL_DIR}/scripts/usage_control.py"` with the selected
operation and validated options. Its sibling `usage_accounting.py`,
`usage_reports.py`, and `usage_schedule.py` supply accounting, rendering and
scheduling; invoke the entrypoint rather than the sibling modules.

| Operation         | Observable result                                                                                                        |
| ----------------- | ------------------------------------------------------------------------------------------------------------------------ |
| `collect`         | One bounded import page and explicit coverage gaps.                                                                      |
| `report`          | Frozen HTML, JSON and CSV evidence, with an equally sized previous interval.                                             |
| `detect`          | Rolling fifteen-minute and configured weekly advisory signals, with durable identities.                                  |
| `hourly`          | Report for the preceding completed UTC hour.                                                                             |
| `install`         | Reviewable plan; `--activate` explicitly writes stable assets and activates quarter-hour detection and hourly reporting. |
| `status`          | Actual managed-job observations and the last worker result.                                                              |
| `stop`, `restart` | Managed-job operations with checked outcomes; restart reuses durable state.                                              |

</available_scripts>

<workflow>

<step name="validate">

Resolve the operation, state root, source root, reset anchor and any supplied budget
from the request or saved configuration. Ask only for choices that remain missing.
Reject unsupported interpreter versions before execution. Keep invalid amounts,
timestamp order and incomplete investigation options outside the mutation path.

</step>

<step name="execute">

Run one finite invocation of the bundled entrypoint. Collection reads at most
32 MiB across 128 files per invocation, with bounded directory discovery and a
120-second worker deadline. Incomplete coverage resumes through saved offsets;
report that limitation and avoid an unattended whole-history loop. A busy worker
returns `overlap_skipped` immediately.

For scheduling, first obtain the `install` plan and inspect its exact asset root,
interpreter, job paths, source and effective configuration. Activate only when the
operator has authorized scheduling at those targets. Confirm with `status`.
Preserve unrelated launch agents and original transcripts.

</step>

<step name="interpret">

Read the generated measurement and selected linked excerpts. Reconcile all four
usage fields, request and native child shares, pricing gaps, context growth and
cache creation before drawing conclusions. Large tool results and repeated
arguments establish inspection candidates; they establish no waste or exact
tool-cost attribution on their own.

Treat API-equivalent cost as a priced estimate. Keep subscription-allowance
observations separate. Compare equally covered windows and qualify late imports,
unknown pricing and missing evidence. Attribute verified delivered output only
from Applied store state, default-branch merge evidence, or current passing pinned
verification. Preserve required gates and resource ceilings in every recommendation.

</step>

<step name="return_evidence">

Return the exact UTC interval, coverage, principal measured drivers and clickable
artifact paths. State the actual installation and worker status when scheduling
was requested. Agent-driven feedback, automatic mail delivery and model-routing
changes require their own authorized workflow.

</step>

</workflow>

<error_handling>

| Observation                                 | Action                                                                                               |
| ------------------------------------------- | ---------------------------------------------------------------------------------------------------- |
| Invalid configuration                       | Name the rejected field and correct it before execution.                                             |
| Partial import                              | Report measured totals as partial and preserve offsets for the next finite invocation.               |
| Unknown model or cache duration             | Preserve token counts; report unavailable pricing or the documented lower-bound assumption.          |
| Optional investigation failure              | Preserve deterministic accounting and name the missing investigation evidence.                       |
| Changed or unowned installed assets or jobs | Preserve them, report the exact path, and reconcile ownership before replacement.                    |
| Worker or launchd failure                   | Inspect the saved diagnostics and actual job observations; use `restart` after correcting the cause. |

The runtime owns atomic-write temporary files and retention of recognized artifacts.
Run no shell deletion command. A nonzero exit or unknown job state supplies no
successful-installation claim.

</error_handling>

<success_criteria>

- The selected operation returns an inspectable result with exact bounds and gaps.
- Reports reconcile their shared frozen measurement and link bounded transcript evidence.
- Signals retain effective configuration and never predict subscription percentages.
- Requested scheduling is verified through actual job observations; failures remain visible.
- Original transcripts, unrelated jobs, required gates and resource ceilings remain preserved.

</success_criteria>
