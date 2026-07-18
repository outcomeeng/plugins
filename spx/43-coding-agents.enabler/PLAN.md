# Plan — Prowl agent environment slice

## Governing problem

Coding-agent workflows construct and inspect raw Prowl commands in multiple skills and scripts. A delegating workflow can send work to another pane but has no source-owned terminal-handback contract, so it may repeatedly inspect recipient task status to discover completion. Raw command construction also forces agents to consult `prowl --help` or load an external `prowl-cli` skill instead of consuming a stable product capability.

The product decision defines environment behavior; an ADR defines the Prowl-specific Python adapter. The decomposition result below owns tree placement and index assignment.

## Interview decisions

Coverage is complete for the problem, environment, seams, slice, command abstraction, result handback, delegation lifecycle, and evidence.

- **Environment:** the first slice supports agents running in Prowl. Claude Code web and Codex Cloud are remote-managed environments for later adapters, not part of this slice.
- **Participants:** any coding agent positively identified by public Prowl evidence can delegate to any other positively identified coding agent.
- **Abstraction:** one shipped Python capability wraps every public Prowl command. It exposes importable typed functions and a versioned JSON CLI. No agent-facing workflow invokes raw `prowl`, runs `prowl --help`, parses terminal presentation, or requires the external `prowl-cli` skill.
- **Seams:** environment identity, participant identity, command execution, delegation submission, terminal delivery, result projection, and recovery/re-entry remain separate typed boundaries. The Prowl adapter owns command grammar and response validation without owning another workflow's execution decisions.
- **Lifecycle:** `delegation-request` reaches exactly one terminal `delegation-completed`, `delegation-failed`, `delegation-rejected`, or `delegation-unavailable` handback carrying the complete initiating coordination reference. The first slice has no acceptance or progress phase.
- **Results:** a terminal handback contains a complete inline result or an exact durable result reference with a bounded inline projection. At least one result form is required.
- **Authority:** read-only and communication operations are model-invocable. Focus, key injection, pane/tab creation, and close operations retain the product's explicit external-mutation authority boundary.
- **Evidence:** deterministic adapter tests are the slice's evidence. They cover command mapping, JSON validation, exact identities, delegation correlation, terminal result forms, duplicate/conflicting terminals, failures, and the complete wrapped Prowl command surface. No coordination eval is added for this slice.

## Decomposition result

`spx/43-coding-agents.enabler` remains the aggregate domain. `spx/43-coding-agents.enabler/18-prowl-environment.enabler` is the shared substrate for the existing communication, coordination, and recovery children. It precedes `spx/43-coding-agents.enabler/21-agent-communication.enabler` because communication consumes its command and identity contract; both index-32 children consume the lower-index environment and communication outputs, while remaining independent peers of each other.

The environment-neutral PDR belongs at `spx/43-coding-agents.enabler/15-agent-environments.pdr.md`. The Python/Prowl architecture belongs at `spx/43-coding-agents.enabler/18-prowl-environment.enabler/15-prowl-adapter.adr.md`.

## Execution

1. Replace the transport-specific `spx/43-coding-agents.enabler/15-channel-selection.pdr.md` decision with `spx/43-coding-agents.enabler/15-agent-environments.pdr.md`. The PDR declares any-agent delegation, explicit terminal handback, result forms, unsupported-environment behavior, and the prohibition on raw environment command discovery without naming Python or Prowl command syntax.
2. Relocate `spx/43-coding-agents.enabler/15-runtime-adapters.adr.md` to `spx/43-coding-agents.enabler/18-prowl-environment.enabler/15-prowl-adapter.adr.md`. The ADR selects one Python 3.13+ standard-library Prowl adapter with typed importable functions, a versioned JSON CLI, dependency-injected command execution, exact public-identity validation, and explicit mutation containment.
3. Align the coding-agents root and every first affected lower spec. Keep native supervisor mechanisms and remote-managed Claude Code web or Codex Cloud adapters outside the first slice while preserving seams for later implementation.
4. Route each deterministic assertion through `/test` and `/test-python`. Write mapping, compliance, and property evidence before implementation. Use controlled runner spies or stubs only under the named `/test` Stage 5 interaction-protocol and failure-simulation exceptions.
5. Implement the authoritative Prowl command registry and operation functions. Cover `list`, `agents`, `read`, `send`, `key`, `focus`, `tab create`, `tab close`, `pane close`, and `open`, plus source-owned delegation request and terminal-handback operations. Preserve Prowl response values verbatim.
6. Refactor `/message-agents`, `/recover-prowl-agents`, `/coordinate-agents`, and their scripts so only the authoritative environment capability constructs Prowl commands. Remove duplicate command grammar and every instruction to run raw Prowl or load `prowl-cli`.
7. Repair the existing rejected audit classes while touching their surfaces: undefined coordination fields, missing Stage 5 runner-double exception, mapping assertions under the wrong heading, mutation HEAD/status evidence gaps, and unqualified command-result `Any`.
8. Regenerate `dist/`, catalogs, docs, and eval prompts or triggers only where source ownership requires it. Do not add delegation behavior to the coordination eval in this slice.
9. Run focused deterministic evidence, skill/docs checks, Markdown/spec status, and selected validation. Commit a clean checkpoint, then re-run the exact required decision, spec, skill, test-evidence, and implementation auditors through Codex typed agents. Run exact-head changes review, terminal `just check-full`, `/merge`, marketplace release sync, plugin reload, and `/handoff`.

## Existing audit evidence to reconcile

Exact prior audited head: `f4c97a5f5656f3f8c1e63045d49ade5f21331c41`.

- Skill audit agent `019f7560-0b21-7751-bc89-ac75a54cbfab`: undefined or inconsistent `reportedState`, `neededSource`, and `transferAcknowledged` fields.
- ADR audit agent `019f7560-2d36-7480-af39-60209737361a`: controlled runner doubles lack a named Python testing Stage 5 exception in `spx/12-shipped-scripting.adr.md`.
- Spec audit agent `019f7564-dc44-7b92-80be-76f0d690074e`: mapping-shaped coordination assertions are filed under `### Compliance`.
- Test-evidence audit agent `019f7565-2e62-7c91-a849-dd82949fec01`: mutation `head` and `status` values are not checked against live identity evidence.
- Eval-evidence audit agent `019f7565-7188-7011-a528-dda5db1ee916`: prior coordination eval evidence has incomplete participant, acknowledgement, routing, falsifiability, and current-head coverage; repair its pre-existing claims without adding delegation eval scope.
- Implementation audit agent `019f7565-a8fa-70e0-8a21-b3b6307b34c5`, run token `2026-07-18_13-24-41-367-17147b839ba8`: `RecordingRunner` uses unqualified `Any` for queued and returned command results.
