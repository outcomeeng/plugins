# Consumption Evidence and Advisory Signals

Consumption control provides deterministic local evidence for Claude Code agent sessions and advisory spending signals. API-equivalent amounts are accounting estimates; subscription-allowance observations remain independent. Scheduling requires explicit activation and produces finite workers whose state and reports survive a source-worktree move.

## Rationale

Request-level usage, context growth, cache creation, and agent/tool activity explain measured consumption more precisely than a dollar total. Deterministic collection avoids model overhead and a continuously running trace server while retaining inspectable evidence and clear coverage limits.

## Product properties

1. Four usage fields, pricing provenance, stable request identities, native parent relationships, exact half-open UTC windows, and coverage gaps accompany every measurement. Reports distinguish measured activity, supported interpretation, and unknown attribution; a transcript mention establishes no verified delivered output.
2. `SPX_USAGE_ALERT_USD` defaults to 20 estimated API-equivalent dollars for a rolling fifteen-minute window. `SPX_USAGE_WEEKLY_BUDGET_USD` is an explicit positive operator-supplied dollar target with no default; `SPX_USAGE_RESET_AT` is an explicit UTC timestamp anchoring successive seven-day periods. Expected accumulated spend is the target multiplied by the elapsed fraction of that period. Invalid configuration names the rejected field.
3. Local HTML, JSON, CSV, and durable alert records share one frozen measurement result. macOS launchd schedules detection every fifteen minutes and reporting hourly from versioned assets under an operator-selected stable root, defaulting to `~/Library/Application Support/Outcome Engineering/usage-control`, with labels in `engineering.outcome.usage-control`. Other scheduling platforms return unsupported. Optional indexed investigation is explicitly selected and version-checked; it is unnecessary for accounting.

## Verification

### Testing

- ALWAYS: original transcripts remain unchanged, every invocation has finite collection and execution bounds, and interrupted imports resume from durable offsets with incomplete history identified ([compliance]).
- ALWAYS: accounting reconciles uncached input, cache reads, cache creation, output, request identities, and native parent/subagent relationships across the report's exact frozen window; unsupported schemas, missing fields, or unknown prices produce named coverage gaps ([property]).
- ALWAYS: detector records include the effective threshold, weekly target, reset anchor, measured window, and evidence references; repeated evaluation preserves one alert identity for one signal occurrence ([property]).
- ALWAYS: managed installation uses stable versioned assets, preserves accounting and alert state across restart, excludes overlapping workers, bounds retained state and excerpts, and reports actual job status and failures ([compliance]).
- NEVER: deterministic collection/reporting invokes a model or installs a runtime dependency ([compliance]).
- ALWAYS: the installed skill and accounting worker operate without TraceRoost, a source checkout, or a SPX usage-evidence interface; optional investigation failure preserves accounting and reports the missing evidence ([compliance]).

### Audit

- ALWAYS: verified output attribution requires Applied store state, a default-branch merge, or current passing pinned evidence; absent skill, plugin, MCP, file, output, or usefulness attribution is unknown ([audit]).
- NEVER: API-equivalent amounts predict Claude MAX usage percentages, or detector signals weaken a required gate or raise a resource ceiling ([audit]).
