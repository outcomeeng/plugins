<!-- Generated from the complete producer set:
dist/claude/coding-agents/skills/operate-prowl/SKILL.md
dist/claude/coding-agents/skills/operate-prowl/scripts/prowl_environment.py
dist/claude/coding-agents/skills/message-agents/SKILL.md
dist/claude/coding-agents/skills/coordinate-agents/SKILL.md
-->

Apply the complete Prowl resolution, semantic messaging, and coordination producers below to the supplied authoritative evidence. Resolve every operator-named path through the Prowl producer, construct every message through the messaging producer, and return only the coordinator's structured JSON verdict. Do not invoke external tools or send messages during this evaluation; execute the supplied producers against the public evidence in the request.

<pre><code>
<!-- Producer: dist/claude/coding-agents/skills/operate-prowl/SKILL.md -->

---
name: operate-prowl
description: >-
  ALWAYS invoke this skill when a workflow needs a public Prowl operation or a correlated delegation handback between Prowl coding agents. NEVER run Prowl command help or construct the public CLI command directly when this capability is available.
argument-hint: "<operation, delegation, or JSON request>"
allowed-tools: Bash(printf:*), Bash(python3 "${CLAUDE_SKILL_DIR}/scripts/prowl_environment.py":*), AskUserQuestion
---

<objective>
A versioned JSON Prowl operation result or one correlated terminal delegation handback, with complete public identities and checked command status preserved verbatim.
</objective>

<operation_surface>

The source-owned operation names are:

| Operation    | Arguments                                                                                           | Mutation authorization |
| ------------ | --------------------------------------------------------------------------------------------------- | ---------------------- |
| `list`       | none                                                                                                | no                     |
| `agents`     | none                                                                                                | no                     |
| `read`       | one selector; optional `last`, `waitStable`, stability bounds                                       | no                     |
| `send`       | one selector, `text`; optional `noEnter`, `noWait`, `capture`, `timeout` with the constraints below | no                     |
| `key`        | one selector, `key`; optional `repeat`                                                              | required               |
| `focus`      | one selector                                                                                        | required               |
| `tab-create` | optional selector and `path`                                                                        | required               |
| `tab-close`  | one selector; optional `force`                                                                      | required               |
| `pane-close` | one selector; optional `force`                                                                      | required               |
| `open`       | optional `path`                                                                                     | required               |

A selector is exactly one of `target`, `worktree`, `tab`, or `pane`. Preserve its complete public value. For `send`, `capture` cannot combine with `noEnter` or `noWait`, and `timeout` cannot combine with `noWait`. The adapter always requests public JSON and owns every Prowl command token and flag.

</operation_surface>

<operator_target_resolution>

An operator names a target by where the work lives — an absolute worktree path, repository directory, or working directory. Resolve that path through one `resolve-target` invocation before operating:

```bash
printf '%s\n' '{"schemaVersion":1,"path":"<absolute-operator-supplied-path>"}' | python3 "${CLAUDE_SKILL_DIR}/scripts/prowl_environment.py" resolve-target
```

The resolver runs the public `agents` operation once and returns its complete checked result under `inventory`, every complete participant under `participants`, the complete caller selected from `PROWL_PANE_ID` or the exact `PROWL_WORKTREE_PATH` fallback, and non-caller path matches under `candidates`. When both caller values exist, both must identify the same participant. Each candidate carries its complete participant metadata and a `sendRequestTemplate` with that pane already selected, `noWait: true`, and `text: null`. Fill `text` with the semantic payload; never repair the JSON through shell substitution or a temporary file.

Use the one candidate directly when `status` is `succeeded`. On `identity-ambiguous` with a complete caller, use `AskUserQuestion` for one single-select question. Number candidates in resolver order; show each candidate's complete pane, worktree, branch, and repository; and map the answer back to that exact captured candidate, including its `sendRequestTemplate`. When the runtime's option cap is below the candidate count, include the complete numbered inventory in the question and accept an exact candidate number through its free-form response; never omit a candidate. On `identity-ambiguous` with `caller: null`, report the exact detail as an unresolved caller-identity conflict and stop; no candidate choice can resolve it. On `identity-unavailable`, report the supplied path and the returned participant worktrees. The resolver performs no send in every result state.

A target that is not a coding-agent pane is outside what `agents` returns, so no path match is available for it. Say that the operator's target is not among the agent panes and name the ones that are, rather than falling back to an inventory that carries no worktree to match.

`resolve-target` resolves active pane targets from `agents`. When the supplied path matches no non-caller participant, return `identity-unavailable` with the complete pane inventory. A sidebar worktree that has never been entered has no pane UUID and cannot receive a message yet; an explicitly authorized `open` request can activate an operator-known path, after which `resolve-target` can run again. The resolver never probes with `open` or claims whether an unmatched path is known to Prowl.

Report the target back to the operator as the supplied path while using the selected template's pane internally. Never ask the operator for a pane UUID or guess by focus, position, or title.

</operator_target_resolution>

<workflow>

1. Interpret `$ARGUMENTS` as one target resolution, low-level operation, handback plan, delegation request, or terminal handback. When it is empty, require a concrete operation before running the adapter. Resolve an absolute worktree, repository, or working-directory target per `<operator_target_resolution>` before building its operation request.
2. For `list`, `agents`, `read`, or `send`, build this source-owned request shape and set only arguments the operation accepts:

```json
{
  "schemaVersion": 1,
  "operation": "agents",
  "arguments": {}
}
```

`list` inventories instantiated terminal panes only. A worktree visible in Prowl's sidebar but never entered in the current app process can be absent from `list` because it has no pane UUID yet.

3. For `key`, `focus`, `tab-create`, `tab-close`, `pane-close`, or `open`, require an explicit user instruction authorizing that exact external mutation in the same turn. `open` can visibly switch focus and create a first terminal tab, so it is never read-only. When authorization is absent, use `AskUserQuestion` with the exact operation and complete target identity; do not run the adapter. After authorization, add `"mutationAuthorized": true` inside `arguments`. For `open`, set arguments to `{"mutationAuthorized":true}` or `{"path":"<complete-source-supplied-path>","mutationAuthorized":true}`.
4. Submit a low-level request over stdin.

When the shell accepts multiline input:

```bash
python3 "${CLAUDE_SKILL_DIR}/scripts/prowl_environment.py" run <<'JSON'
{"schemaVersion":1,"operation":"agents","arguments":{}}
JSON
```

When the runner requires one physical command line:

```bash
printf '%s\n' '{"schemaVersion":1,"operation":"agents","arguments":{}}' | python3 "${CLAUDE_SKILL_DIR}/scripts/prowl_environment.py" run
```

5. Accept only `status: "succeeded"` for a submitted operation. Preserve the complete versioned result, `commandExitCode`, and public `response` values. For `open`, preserve `response.data.resolution`, `created_tab`, and the complete target; `exact-root` with `created_tab: true` is the lazy equivalent of clicking a known sidebar worktree that has no terminal pane. `new-root` means Prowl added a previously unknown root and never proves a prepared recovery target existed. For submitted `send`, require `commandExitCode: 0` and preserve `response.data.input.trailing_enter_sent`; success with that field false or absent does not prove the turn left the editor. Once the checked send reports `trailing_enter_sent: true`, the turn is queued and delivery is complete; never send it again because the entry box becomes free. Stop with the exact `status` and `detail` on `command-failed`, `invalid-schema`, `prowl-unavailable`, `mutation-unauthorized`, or `operation-unavailable`.
6. For bounded delegation between two identities returned by `agents`, supply semantic completion text and submit this shape to `delegate`:

```json
{
  "sender": {
    "agent": "<complete-agent-id>",
    "pane": "<complete-pane-id>",
    "worktree": "<absolute-worktree-path>",
    "branch": "<complete-branch>",
    "repository": "<absolute-repository-root>",
    "run": "<complete-run-id-when-present>"
  },
  "recipient": {
    "agent": "<complete-agent-id>",
    "pane": "<complete-pane-id>",
    "worktree": "<absolute-worktree-path>",
    "branch": "<complete-branch>",
    "repository": "<absolute-repository-root>",
    "run": "<complete-run-id-when-present>"
  },
  "subject": "<bounded subject>",
  "instruction": "<complete bounded request, with no shell command or return-path fields>",
  "completionText": "<one-line completion signal for the sender>",
  "coordinationReference": null
}
```

The adapter maps `completionText` and the two identities to a versioned `handback` block. The block contains `completionText`, the absolute `adapterPath`, an exact one-line `command` ending at `run`, checked `successCriteria`, `retryPolicy: "never-after-trailing-enter"`, `socket: "default"`, and `expectedPanes` in sender-recipient order. A caller never supplies `handback`, `command`, `handbackCommand`, `returnPane`, or `adapterPath`.

The result carries the complete source-owned schema-version-2 `delegation` envelope and generated handback block. Preserve it for the terminal handback; transport success is not acceptance or completion.

A direct delegation submission uses the same stdin boundary:

```bash
python3 "${CLAUDE_SKILL_DIR}/scripts/prowl_environment.py" delegate <<'JSON'
{"sender":{"agent":"agent-a","pane":"11111111-1111-4111-8111-111111111111","worktree":"/repo-a","branch":"work/a","repository":"/repo.git","run":"run-a"},"recipient":{"agent":"agent-b","pane":"22222222-2222-4222-8222-222222222222","worktree":"/repo-b","branch":"work/b","repository":"/repo.git","run":"run-b"},"subject":"Review resolver evidence","instruction":"Write the complete review result before sending the handback signal.","completionText":"Resolver evidence review completed; terminal result follows.","coordinationReference":null}
JSON
```

For a production request carried by `/message-agents`, generate the same block without sending a delegation. Submit exactly `sender`, `recipient`, and `completionText` to `plan-handback` and preserve the returned `handback` object unchanged:

```bash
printf '%s\n' '{"sender":{"agent":"agent-a","pane":"11111111-1111-4111-8111-111111111111","worktree":"/repo-a","branch":"work/a","repository":"/repo.git","run":"run-a"},"recipient":{"agent":"agent-b","pane":"22222222-2222-4222-8222-222222222222","worktree":"/repo-b","branch":"work/b","repository":"/repo.git","run":"run-b"},"completionText":"Requested artifact completed."}' | python3 "${CLAUDE_SKILL_DIR}/scripts/prowl_environment.py" plan-handback
```

7. The recipient writes any durable result first, executes the generated `handback.command` exactly, and submits exactly one terminal result to `handback`, carrying the complete original `delegation`, one `kind`, and one supported result form:

- `delegation-completed`
- `delegation-failed`
- `delegation-rejected`
- `delegation-unavailable`

A complete inline result uses `inlineResult`. A durable result uses a scheme-bearing `resultReference` plus a bounded `projection`; use `file:///absolute/path` for a local file. Both forms may appear together. The adapter rejects a missing result, a reference without a URI scheme or projection, and a conflicting terminal handback.

The direct stdin payload uses `{"delegation":<complete-returned-delegation>,"kind":"delegation-completed","inlineResult":"<complete-result>"}`. Replace the angle-bracket value with the returned delegation object itself, never a quoted summary or reconstructed envelope.

8. Return the complete terminal result to the delegating workflow. Do not poll the recipient, add acceptance or progress phases, or infer completion from pane output.

</workflow>

<handback_delivery>

Completion travels by push, never by pull. The sender's environment blocks polling loops by design, so a sender that "checks later" has no later to check in — it reads once, sees nothing, and moves on while the finished result sits on disk. The recipient closes the loop or nobody does.

**A durable result separates payload from signal.** The file carries the payload; one line sent into the sender's pane carries the signal. Write the file first, then send. `resultReference` names the complete scheme-bearing reference — `file:///absolute/path` for a local file — and `projection` carries the bounded summary, so the sender knows what arrived without opening it.

**The recipient delivers the handback by sending one line into the return address's pane**, using the `send` operation with normal trailing-Enter behavior. That send lands as a turn in the sender's session, which is what makes it a signal rather than a message the sender must go looking for. A `noEnter` send prefills the sender's editor and signals nothing.

**The adapter generates the handback at delegation time.** The caller supplies only semantic completion text. The generated block binds that text to `sender.pane`, the bundled adapter path, checked submission criteria, the default socket, both expected panes, and the no-retry policy. This separation prevents a caller from changing CLI grammar while describing the requested work.

</handback_delivery>

<environment_traps>

Two environment conditions silently break a handback. The generated block names both instead of leaving the recipient to discover them.

**The CLI may not be on `PATH`.** A recipient whose shell cannot resolve the command reads the failure as "the environment is unavailable" and abandons the handback. The executable bundled inside the application resolves when `PATH` does not, so the return address carries the command form that works in the recipient's environment rather than a bare command name.

**A non-default socket may belong to a different instance.** When the socket is overridden, the CLI talks to whichever instance owns that socket — which can be another agent's verification harness holding no real panes rather than the operator's live application. An empty or unrecognizable pane inventory is that condition, not an absent recipient. Confirm the inventory contains the expected panes before concluding a target is gone, and use the same socket value for every command in the exchange.

</environment_traps>

<constraints>

- ALWAYS preserve complete source-supplied agent, pane, worktree, branch, repository, run, coordination, status, conclusion, exit-code, and result-reference values.
- ALWAYS execute the bundled script through `${CLAUDE_SKILL_DIR}`; never import it from another filesystem location or manufacture a path outside this skill directory.
- ALWAYS generate executable handback data from semantic completion text through `delegate` or `plan-handback`.
- NEVER accept caller-authored `handback`, `command`, `handbackCommand`, `returnPane`, or `adapterPath` fields.
- NEVER invoke raw Prowl commands, Prowl command help, or an external environment-control skill.
- NEVER mutate focus, keys, tabs, panes, or open-path selection without explicit authorization for the exact operation and target in the same turn.
- NEVER equate `list` with the sidebar worktree inventory or enumerate filesystem worktrees to compensate for an uninstantiated pane.
- NEVER scan transcripts, parse terminal presentation as identity, or poll for delegation completion.
- NEVER make retry, checkpoint, persistence, result-interpretation, or continuation decisions for another workflow.

</constraints>

<testing>

Before release, import the bundled module with controlled `CommandRunner` implementations under the interaction-protocol and failure-simulation exceptions. Run the documented `run` form with an `agents` payload and require `status: "succeeded"`, `commandExitCode: 0`, and a public response; run `resolve-target` with pane-only, worktree-only, and combined caller evidence and require one inventory call, caller exclusion, and zero sends; fill one returned send template and require `response.data.input.trailing_enter_sent: true`; run `plan-handback`, `delegate`, and `handback` with the documented shapes and require the command to end exactly at `run`, the initiating coordination reference to survive, and every caller-authored executable handback field to fail. Cover every operation mapping, public JSON failure, mutation rejection before command construction, URI-bearing delegation result forms, repeated terminals, conflicting terminals, malformed input, missing Prowl, and CLI stdin dispatch.

Recorded exercised payload/results:

- `{"schemaVersion":1,"operation":"agents","arguments":{}}` with a successful public agents response → `status: "succeeded"`, `commandExitCode: 0`, and the response preserved.
- `resolve-target` with an active non-caller worktree path → one candidate and no send; an unmatched absolute path → `identity-unavailable`, an empty candidate array, and no `open` probe.
- A filled returned send template with `trailing_enter_sent: true` in the public response → one `succeeded` send result; the same submission evidence then supports one delivered message envelope.

</testing>

<failure_modes>

**A selectorless tab creation was rejected.** Claude applied the shared selector requirement to `tab-create`, even though the public operation accepts both selectorless and selected forms. The shared request builder hid the operation-specific shape. Build `tab-create` from its declared optional-selector contract and preserve optional `path` independently.

**An advertised operation had no construction branch.** Claude listed `open` in the public surface but grouped only list, agents, read, and send into the non-mutating workflow. Claude then had to infer the request shape. Keep every advertised operation in an explicit construction branch; `open` accepts empty arguments or one source-supplied `path`, always with explicit mutation authorization.

**A visible worktree was absent from `list`.** Claude inferred missing Prowl topology because a sidebar row had no listed pane. The row was known but not entered; `open` returned `resolution: exact-root`, `created_tab: true`, and the first pane UUID. Treat `list` as the terminal inventory and use authorized `open` for visible lazy activation.

**A delegation had no return path, so the operator became the message bus.** Claude asked a recipient to write a file, then had no signal that it had. Polling loops are blocked in the environment, so Claude read the pane once, saw nothing, and moved on while a complete result sat on disk. Generate the structured handback from the sender, recipient, and completion text, then require the recipient to send one line on completion per `<handback_delivery>`.

**A caller added a trailing argument to the return command.** Claude copied a hand-written `run .` command into a delegation. `argparse` rejected the extra positional argument before any send occurred. Generate the command from `completionText`; the adapter renders the final token as `run` and rejects caller-authored executable fields.

**A single read was mistaken for a terminal answer.** Claude treated one empty pane read as evidence the recipient had produced nothing, when it proved only that nothing was on screen at that instant. A read establishes the pane's state at the moment it ran and never establishes that a delegation is incomplete. Completion arrives as the recipient's handback; its absence is an open delegation, not a negative result.

**An overridden socket was read as an empty environment.** Claude pointed the CLI at a non-default socket, saw an inventory with none of the expected panes, and concluded the recipient was gone. The socket belonged to a different instance — a verification harness, not the operator's live application. Confirm the inventory contains the expected panes before concluding a target is absent, per `<environment_traps>`.

**Target resolution was rebuilt around scratch files.** Claude wrote the `agents` result and discovery result through dynamic redirects under `$SP`. The dangerous-command guard terminated the command because the shell would open an unproved path with truncation. Claude then rewrote the same operation as a Python script, bypassing the stop instead of using a sanctioned capability. Invoke `resolve-target` over direct stdin, keep its returned JSON as the tool result, and stop when a guard terminates that command family; never reformulate the blocked operation.

</failure_modes>

<success_criteria>

- A successful public operation is mechanically established only when the bundled script exits zero and emits `schemaVersion: 1`, `status: "succeeded"`, `commandExitCode: 0`, and a public `response` object without exposing Prowl command grammar.
- Every positively identified Prowl participant retains complete public identities verbatim.
- Every delegation preserves its initiating coordination reference through exactly one completed, failed, rejected, or unavailable terminal handback.
- Every delegation carries one source-generated handback block whose command ends exactly at `run` and whose conditions identify checked submission, no retry after submission, the default socket, and both expected panes.
- A durable handback writes its file before sending, and the notification reaches the sender's pane as a submitted turn rather than editor prefill.
- One `resolve-target` invocation returns the checked inventory, complete caller and participants, non-caller path matches, and candidate-specific immediate-return send templates without sending.
- An operator-named target is reported as the supplied worktree or directory, never as a pane UUID the operator must verify.
- Terminal results carry complete inline content or an exact durable reference with a bounded projection.
- Unauthorized focus, key, creation, closure, and open requests fail before Prowl runs.
- Lazy activation is established by an authorized `open` result carrying `resolution: exact-root`, `created_tab: true`, and the complete returned pane identity.
- No workflow polls, invokes help, or depends on a separate environment-control skill.

</success_criteria>


<!-- Producer: dist/claude/coding-agents/skills/operate-prowl/scripts/prowl_environment.py -->

#!/usr/bin/env python3
"""Operate Prowl through a checked, versioned environment contract."""

from __future__ import annotations

import argparse
import json
import os
import re
import shlex
import subprocess
import sys
import uuid
from dataclasses import dataclass
from enum import StrEnum
from pathlib import Path
from typing import Final, Mapping, Protocol, TextIO, cast
from urllib.parse import urlparse

SCHEMA_VERSION = 1
DELEGATION_SCHEMA_VERSION = 2
HANDBACK_SCHEMA_VERSION = 1
COMMAND_TIMEOUT_SECONDS = 30
MAX_RESULT_PROJECTION_CHARACTERS = 4_000
PROWL_COMMAND = "prowl"
LIST_COMMAND = "list"
AGENTS_COMMAND = "agents"
READ_COMMAND = "read"
SEND_COMMAND = "send"
KEY_COMMAND = "key"
FOCUS_COMMAND = "focus"
TAB_COMMAND = "tab"
PANE_COMMAND = "pane"
OPEN_COMMAND = "open"
CREATE_COMMAND = "create"
CLOSE_COMMAND = "close"
JSON_OPTION = "--json"
HELP_OPTION = "--help"
TARGET_OPTION = "--target"
WORKTREE_OPTION = "--worktree"
TAB_OPTION = "--tab"
PANE_OPTION = "--pane"
LAST_OPTION = "--last"
WAIT_STABLE_OPTION = "--wait-stable"
STABLE_INTERVAL_OPTION = "--stable-interval"
STABLE_PERIOD_OPTION = "--stable-period"
WAIT_TIMEOUT_OPTION = "--wait-timeout"
NO_ENTER_OPTION = "--no-enter"
NO_WAIT_OPTION = "--no-wait"
CAPTURE_OPTION = "--capture"
TIMEOUT_OPTION = "--timeout"
REPEAT_OPTION = "--repeat"
PATH_OPTION = "--path"
FORCE_OPTION = "--force"

SCHEMA_VERSION_FIELD = "schemaVersion"
SCHEMA_VERSION_SNAKE_FIELD = "schema_version"
OPERATION_FIELD = "operation"
ARGUMENTS_FIELD = "arguments"
STATUS_FIELD = "status"
DETAIL_FIELD = "detail"
COMMAND_FIELD = "command"
COMMAND_EXIT_CODE_FIELD = "commandExitCode"
RESPONSE_FIELD = "response"
OK_FIELD = "ok"
DATA_FIELD = "data"
ERROR_FIELD = "error"
MESSAGE_FIELD = "message"
ITEMS_FIELD = "items"
AGENTS_FIELD = "agents"
ID_FIELD = "id"
AGENT_FIELD = "agent"
PANE_FIELD = "pane"
WORKTREE_FIELD = "worktree"
TAB_FIELD = "tab"
TARGET_FIELD = "target"
PROJECT_FIELD = "project"
RUN_FIELD = "run"
PATH_FIELD = "path"
ROOT_PATH_FIELD = "root_path"
BRANCH_FIELD = "branch"
REPOSITORY_FIELD = "repository"
LAST_FIELD = "last"
WAIT_STABLE_FIELD = "waitStable"
STABLE_INTERVAL_FIELD = "stableInterval"
STABLE_PERIOD_FIELD = "stablePeriod"
WAIT_TIMEOUT_FIELD = "waitTimeout"
TEXT_FIELD = "text"
NO_ENTER_FIELD = "noEnter"
NO_WAIT_FIELD = "noWait"
CAPTURE_FIELD = "capture"
TIMEOUT_FIELD = "timeout"
KEY_FIELD = "key"
REPEAT_FIELD = "repeat"
FORCE_FIELD = "force"
MUTATION_AUTHORIZED_FIELD = "mutationAuthorized"
KIND_FIELD = "kind"
SENDER_FIELD = "sender"
RECIPIENT_FIELD = "recipient"
SUBJECT_FIELD = "subject"
INSTRUCTION_FIELD = "instruction"
COMPLETION_TEXT_FIELD = "completionText"
COORDINATION_REFERENCE_FIELD = "coordinationReference"
INLINE_RESULT_FIELD = "inlineResult"
RESULT_REFERENCE_FIELD = "resultReference"
PROJECTION_FIELD = "projection"
DELEGATION_FIELD = "delegation"
TERMINAL_FIELD = "terminal"
HANDBACK_FIELD = "handback"
ADAPTER_PATH_FIELD = "adapterPath"
SUCCESS_CRITERIA_FIELD = "successCriteria"
RETRY_POLICY_FIELD = "retryPolicy"
SOCKET_FIELD = "socket"
EXPECTED_PANES_FIELD = "expectedPanes"
CONCLUSION_FIELD = "conclusion"
PARTICIPANTS_FIELD = "participants"
PARTICIPANT_FIELD = "participant"
CALLER_FIELD = "caller"
CANDIDATES_FIELD = "candidates"
INVENTORY_FIELD = "inventory"
SEND_REQUEST_TEMPLATE_FIELD = "sendRequestTemplate"
INPUT_FIELD = "input"
TRAILING_ENTER_SENT_FIELD = "trailing_enter_sent"
RESOLUTION_FIELD = "resolution"
CREATED_TAB_FIELD = "created_tab"
PROWL_PANE_ID_ENV = "PROWL_PANE_ID"
PROWL_WORKTREE_PATH_ENV = "PROWL_WORKTREE_PATH"
CALLER_IDENTITY_ENV_FIELDS = (PROWL_PANE_ID_ENV, PROWL_WORKTREE_PATH_ENV)
HANDBACK_RETRY_POLICY = "never-after-trailing-enter"
DEFAULT_SOCKET = "default"

REQUEST_FIELDS = frozenset({SCHEMA_VERSION_FIELD, OPERATION_FIELD, ARGUMENTS_FIELD})
SUCCESS_RESULT_FIELDS = frozenset(
    {
        SCHEMA_VERSION_FIELD,
        OPERATION_FIELD,
        STATUS_FIELD,
        COMMAND_EXIT_CODE_FIELD,
        RESPONSE_FIELD,
    }
)
FAILURE_RESULT_REQUIRED_FIELDS = frozenset(
    {SCHEMA_VERSION_FIELD, OPERATION_FIELD, STATUS_FIELD, DETAIL_FIELD}
)
FAILURE_RESULT_OPTIONAL_FIELDS = frozenset({COMMAND_EXIT_CODE_FIELD})
SELECTOR_FIELDS = (TARGET_FIELD, WORKTREE_FIELD, TAB_FIELD, PANE_FIELD)
IDENTITY_FIELDS = (
    AGENT_FIELD,
    PANE_FIELD,
    WORKTREE_FIELD,
    BRANCH_FIELD,
    REPOSITORY_FIELD,
)
IDENTITY_INPUT_FIELDS = frozenset((*IDENTITY_FIELDS, RUN_FIELD))
# The keys a delegation request may carry over stdin. `schemaVersion` and `kind`
# are owned by the envelope builder, so a caller never supplies them.
DELEGATION_CLI_FIELDS = frozenset(
    {
        SENDER_FIELD,
        RECIPIENT_FIELD,
        SUBJECT_FIELD,
        INSTRUCTION_FIELD,
        COMPLETION_TEXT_FIELD,
        COORDINATION_REFERENCE_FIELD,
    }
)
DELEGATION_REQUEST_FIELDS = frozenset(
    {
        SCHEMA_VERSION_FIELD,
        KIND_FIELD,
        COORDINATION_REFERENCE_FIELD,
        SENDER_FIELD,
        RECIPIENT_FIELD,
        SUBJECT_FIELD,
        INSTRUCTION_FIELD,
        HANDBACK_FIELD,
    }
)
HANDBACK_FIELDS = frozenset(
    {
        SCHEMA_VERSION_FIELD,
        COMPLETION_TEXT_FIELD,
        ADAPTER_PATH_FIELD,
        COMMAND_FIELD,
        SUCCESS_CRITERIA_FIELD,
        RETRY_POLICY_FIELD,
        SOCKET_FIELD,
        EXPECTED_PANES_FIELD,
    }
)
HANDBACK_SUCCESS_FIELDS = frozenset(
    {STATUS_FIELD, COMMAND_EXIT_CODE_FIELD, TRAILING_ENTER_SENT_FIELD}
)
HANDBACK_PLAN_CLI_FIELDS = frozenset(
    {SENDER_FIELD, RECIPIENT_FIELD, COMPLETION_TEXT_FIELD}
)
TERMINAL_HANDBACK_FIELDS = frozenset(
    {
        SCHEMA_VERSION_FIELD,
        KIND_FIELD,
        COORDINATION_REFERENCE_FIELD,
        SENDER_FIELD,
        RECIPIENT_FIELD,
        INLINE_RESULT_FIELD,
        RESULT_REFERENCE_FIELD,
        PROJECTION_FIELD,
    }
)


class Operation(StrEnum):
    LIST = "list"
    AGENTS = "agents"
    READ = "read"
    SEND = "send"
    KEY = "key"
    FOCUS = "focus"
    TAB_CREATE = "tab-create"
    TAB_CLOSE = "tab-close"
    PANE_CLOSE = "pane-close"
    OPEN = "open"


MUTATING_OPERATIONS = frozenset(
    {
        Operation.KEY,
        Operation.FOCUS,
        Operation.TAB_CREATE,
        Operation.TAB_CLOSE,
        Operation.PANE_CLOSE,
        Operation.OPEN,
    }
)


@dataclass(frozen=True)
class RequestShape:
    required_fields: frozenset[str] = frozenset()
    optional_fields: frozenset[str] = frozenset()

    def accepts(self, fields: frozenset[str]) -> bool:
        return (
            self.required_fields
            <= fields
            <= (self.required_fields | self.optional_fields)
        )


@dataclass(frozen=True)
class OperationContract:
    request_shapes: tuple[RequestShape, ...]

    @property
    def allowed_fields(self) -> frozenset[str]:
        return frozenset(
            field
            for shape in self.request_shapes
            for field in shape.required_fields | shape.optional_fields
        )


def _selector_shapes(
    required_fields: frozenset[str], optional_fields: frozenset[str] = frozenset()
) -> tuple[RequestShape, ...]:
    return tuple(
        RequestShape(required_fields | {selector}, optional_fields)
        for selector in SELECTOR_FIELDS
    )


def _send_shapes() -> tuple[RequestShape, ...]:
    shapes: list[RequestShape] = []
    for selector in SELECTOR_FIELDS:
        base = frozenset({selector, TEXT_FIELD})
        shapes.extend(
            (
                RequestShape(base, frozenset({NO_ENTER_FIELD, TIMEOUT_FIELD})),
                RequestShape(base | {NO_WAIT_FIELD}, frozenset({NO_ENTER_FIELD})),
                RequestShape(base | {CAPTURE_FIELD}, frozenset({TIMEOUT_FIELD})),
            )
        )
    return tuple(shapes)


PUBLIC_PROWL_COMMAND_PREFIXES: Final[Mapping[Operation, tuple[str, ...]]] = {
    Operation.LIST: ("prowl", "list"),
    Operation.AGENTS: ("prowl", "agents"),
    Operation.READ: ("prowl", "read"),
    Operation.SEND: ("prowl", "send"),
    Operation.KEY: ("prowl", "key"),
    Operation.FOCUS: ("prowl", "focus"),
    Operation.TAB_CREATE: ("prowl", "tab", "create"),
    Operation.TAB_CLOSE: ("prowl", "tab", "close"),
    Operation.PANE_CLOSE: ("prowl", "pane", "close"),
    Operation.OPEN: ("prowl", "open"),
}
PUBLIC_PROWL_SELECTOR_OPTIONS: Final[Mapping[str, str]] = {
    TARGET_FIELD: "--target",
    WORKTREE_FIELD: "--worktree",
    TAB_FIELD: "--tab",
    PANE_FIELD: "--pane",
}
PUBLIC_PROWL_ARGUMENT_OPTIONS: Final[Mapping[str, str]] = {
    LAST_FIELD: "--last",
    WAIT_STABLE_FIELD: "--wait-stable",
    STABLE_INTERVAL_FIELD: "--stable-interval",
    STABLE_PERIOD_FIELD: "--stable-period",
    WAIT_TIMEOUT_FIELD: "--wait-timeout",
    NO_ENTER_FIELD: "--no-enter",
    NO_WAIT_FIELD: "--no-wait",
    CAPTURE_FIELD: "--capture",
    TIMEOUT_FIELD: "--timeout",
    REPEAT_FIELD: "--repeat",
    PATH_FIELD: "--path",
    FORCE_FIELD: "--force",
}
PUBLIC_PROWL_JSON_OPTION = "--json"

OPERATION_CONTRACTS: Final[Mapping[Operation, OperationContract]] = {
    Operation.LIST: OperationContract((RequestShape(),)),
    Operation.AGENTS: OperationContract((RequestShape(),)),
    Operation.READ: OperationContract(
        _selector_shapes(
            frozenset(),
            frozenset(
                {
                    LAST_FIELD,
                    WAIT_STABLE_FIELD,
                    STABLE_INTERVAL_FIELD,
                    STABLE_PERIOD_FIELD,
                    WAIT_TIMEOUT_FIELD,
                }
            ),
        )
    ),
    Operation.SEND: OperationContract(_send_shapes()),
    Operation.KEY: OperationContract(
        _selector_shapes(
            frozenset({KEY_FIELD, MUTATION_AUTHORIZED_FIELD}),
            frozenset({REPEAT_FIELD}),
        )
    ),
    Operation.FOCUS: OperationContract(
        _selector_shapes(frozenset({MUTATION_AUTHORIZED_FIELD}))
    ),
    Operation.TAB_CREATE: OperationContract(
        (
            RequestShape(
                frozenset({MUTATION_AUTHORIZED_FIELD}), frozenset({PATH_FIELD})
            ),
            *_selector_shapes(
                frozenset({MUTATION_AUTHORIZED_FIELD}), frozenset({PATH_FIELD})
            ),
        )
    ),
    Operation.TAB_CLOSE: OperationContract(
        _selector_shapes(
            frozenset({MUTATION_AUTHORIZED_FIELD}), frozenset({FORCE_FIELD})
        )
    ),
    Operation.PANE_CLOSE: OperationContract(
        _selector_shapes(
            frozenset({MUTATION_AUTHORIZED_FIELD}), frozenset({FORCE_FIELD})
        )
    ),
    Operation.OPEN: OperationContract(
        (RequestShape(frozenset({MUTATION_AUTHORIZED_FIELD}), frozenset({PATH_FIELD})),)
    ),
}
INTEGER_BOUNDS: Final[Mapping[str, tuple[int, int]]] = {
    LAST_FIELD: (1, 1_000_000),
    STABLE_INTERVAL_FIELD: (50, 5_000),
    STABLE_PERIOD_FIELD: (100, 60_000),
    WAIT_TIMEOUT_FIELD: (1, 300),
    TIMEOUT_FIELD: (1, 300),
    REPEAT_FIELD: (1, 100),
}
BOOLEAN_ARGUMENT_FIELDS = frozenset(
    {
        WAIT_STABLE_FIELD,
        NO_ENTER_FIELD,
        NO_WAIT_FIELD,
        CAPTURE_FIELD,
        FORCE_FIELD,
        MUTATION_AUTHORIZED_FIELD,
    }
)
TEXT_ARGUMENT_FIELDS = frozenset({TEXT_FIELD, KEY_FIELD})
ARGUMENT_NAMES: Final[Mapping[str, str]] = {
    "target": TARGET_FIELD,
    "worktree": WORKTREE_FIELD,
    "tab": TAB_FIELD,
    "pane": PANE_FIELD,
    "last": LAST_FIELD,
    "wait_stable": WAIT_STABLE_FIELD,
    "stable_interval": STABLE_INTERVAL_FIELD,
    "stable_period": STABLE_PERIOD_FIELD,
    "wait_timeout": WAIT_TIMEOUT_FIELD,
    "text": TEXT_FIELD,
    "no_enter": NO_ENTER_FIELD,
    "no_wait": NO_WAIT_FIELD,
    "capture": CAPTURE_FIELD,
    "timeout": TIMEOUT_FIELD,
    "key": KEY_FIELD,
    "repeat": REPEAT_FIELD,
    "path": PATH_FIELD,
    "force": FORCE_FIELD,
    "mutation_authorized": MUTATION_AUTHORIZED_FIELD,
}
RAW_PROWL_COMMAND_PATTERNS: Final[tuple[re.Pattern[str], ...]] = (
    re.compile(r"PROWL_COMMAND|[\[(]['\"]prowl['\"]"),
    re.compile(r"\bHELP_OPTION\b"),
)
LOCAL_WORKTREE_ENUMERATION_PATTERNS: Final[tuple[re.Pattern[str], ...]] = (
    re.compile(r"['\"]git['\"]\s*,\s*['\"]worktree['\"]\s*,\s*['\"]list['\"]"),
    re.compile(r"['\"]\.git[/\\\\]worktrees(?:[/\\\\]|['\"])"),
    re.compile(r"\bos\.(?:listdir|scandir|walk)\s*\("),
    re.compile(r"\.(?:iterdir|glob|rglob)\s*\("),
)


class ExecutionStatus(StrEnum):
    SUCCEEDED = "succeeded"
    COMMAND_FAILED = "command-failed"
    INVALID_SCHEMA = "invalid-schema"
    PROWL_UNAVAILABLE = "prowl-unavailable"
    IDENTITY_UNAVAILABLE = "identity-unavailable"
    IDENTITY_AMBIGUOUS = "identity-ambiguous"
    MUTATION_UNAUTHORIZED = "mutation-unauthorized"
    OPERATION_UNAVAILABLE = "operation-unavailable"


class TargetMatchCardinality(StrEnum):
    ZERO = "zero"
    ONE = "one"
    MULTIPLE = "multiple"


class OpenResolution(StrEnum):
    EXACT_ROOT = "exact-root"
    INSIDE_ROOT = "inside-root"
    NEW_ROOT = "new-root"


def target_match_cardinality(candidate_count: int) -> TargetMatchCardinality:
    if candidate_count == 0:
        return TargetMatchCardinality.ZERO
    if candidate_count == 1:
        return TargetMatchCardinality.ONE
    return TargetMatchCardinality.MULTIPLE


class EnvelopeKind(StrEnum):
    DELEGATION_REQUEST = "delegation-request"


class TerminalKind(StrEnum):
    COMPLETED = "delegation-completed"
    FAILED = "delegation-failed"
    REJECTED = "delegation-rejected"
    UNAVAILABLE = "delegation-unavailable"


class CliOperation(StrEnum):
    RUN = "run"
    RESOLVE_TARGET = "resolve-target"
    DELEGATE = "delegate"
    HAND_BACK = "handback"
    PLAN_HAND_BACK = "plan-handback"


@dataclass(frozen=True)
class CommandResult:
    returncode: int
    stdout: str
    stderr: str


class CommandRunner(Protocol):
    def run(self, argv: tuple[str, ...], stdin: str | None = None) -> CommandResult: ...


@dataclass(frozen=True)
class SubprocessRunner:
    timeout_seconds: int = COMMAND_TIMEOUT_SECONDS

    def run(self, argv: tuple[str, ...], stdin: str | None = None) -> CommandResult:
        try:
            completed = subprocess.run(
                argv,
                input=stdin,
                stdin=subprocess.DEVNULL if stdin is None else None,
                capture_output=True,
                text=True,
                timeout=self.timeout_seconds,
                check=False,
            )
        except FileNotFoundError as error:
            raise ProwlEnvironmentError(
                ExecutionStatus.PROWL_UNAVAILABLE,
                "Prowl CLI is unavailable. Run this capability inside a Prowl environment with the public CLI installed.",
            ) from error
        except subprocess.TimeoutExpired as error:
            raise ProwlEnvironmentError(
                ExecutionStatus.COMMAND_FAILED,
                f"Prowl command exceeded the {self.timeout_seconds}-second bound: {' '.join(argv)}",
            ) from error
        return CommandResult(completed.returncode, completed.stdout, completed.stderr)


class ProwlEnvironmentError(RuntimeError):
    def __init__(self, status: ExecutionStatus, message: str) -> None:
        super().__init__(message)
        self.status = status


def _object(value: object, location: str) -> dict[str, object]:
    if not isinstance(value, dict):
        raise ProwlEnvironmentError(
            ExecutionStatus.INVALID_SCHEMA, f"Expected an object at {location}."
        )
    return value


def _array(value: object, location: str) -> list[dict[str, object]]:
    if not isinstance(value, list):
        raise ProwlEnvironmentError(
            ExecutionStatus.INVALID_SCHEMA, f"Expected an array at {location}."
        )
    return [_object(item, f"{location}[{index}]") for index, item in enumerate(value)]


def _text(value: object, location: str) -> str:
    if not isinstance(value, str) or not value:
        raise ProwlEnvironmentError(
            ExecutionStatus.INVALID_SCHEMA,
            f"Expected a non-empty string at {location}.",
        )
    return value


def _optional_text(value: object, location: str) -> str | None:
    if value is None:
        return None
    return _text(value, location)


def _boolean(value: object, location: str) -> bool:
    if not isinstance(value, bool):
        raise ProwlEnvironmentError(
            ExecutionStatus.INVALID_SCHEMA, f"Expected a boolean at {location}."
        )
    return value


def _integer(value: object, location: str, *, minimum: int, maximum: int) -> int:
    if not isinstance(value, int) or isinstance(value, bool):
        raise ProwlEnvironmentError(
            ExecutionStatus.INVALID_SCHEMA, f"Expected an integer at {location}."
        )
    if not minimum <= value <= maximum:
        raise ProwlEnvironmentError(
            ExecutionStatus.INVALID_SCHEMA,
            f"Expected {location} between {minimum} and {maximum}; received {value}.",
        )
    return value


def _operation(value: object) -> Operation:
    raw = _text(value, f"request.{OPERATION_FIELD}")
    try:
        return Operation(raw)
    except ValueError as error:
        valid = ", ".join(operation.value for operation in Operation)
        raise ProwlEnvironmentError(
            ExecutionStatus.OPERATION_UNAVAILABLE,
            f"Unsupported Prowl operation {raw!r}. Supported operations: {valid}.",
        ) from error


def _terminal_kind(value: object) -> TerminalKind:
    raw = _text(value, KIND_FIELD)
    try:
        return TerminalKind(raw)
    except ValueError as error:
        valid = ", ".join(kind.value for kind in TerminalKind)
        raise ProwlEnvironmentError(
            ExecutionStatus.INVALID_SCHEMA,
            f"Unsupported terminal kind {raw!r}. Valid terminal kinds: {valid}.",
        ) from error


def _one_selector(arguments: dict[str, object]) -> None:
    selected = [field for field in SELECTOR_FIELDS if field in arguments]
    if len(selected) > 1:
        raise ProwlEnvironmentError(
            ExecutionStatus.INVALID_SCHEMA,
            f"Operation accepts at most one selector; received: {', '.join(selected)}.",
        )
    for field in selected:
        _text(arguments[field], f"request.{ARGUMENTS_FIELD}.{field}")


def _allowed_fields(operation: Operation) -> frozenset[str]:
    return OPERATION_CONTRACTS[operation].allowed_fields


def _validated_request(request: object) -> tuple[Operation, dict[str, object]]:
    value = _object(request, "request")
    unexpected = sorted(set(value) - REQUEST_FIELDS)
    missing = sorted(REQUEST_FIELDS - set(value))
    if unexpected or missing:
        details: list[str] = []
        if unexpected:
            details.append(f"unsupported: {', '.join(unexpected)}")
        if missing:
            details.append(f"missing: {', '.join(missing)}")
        raise ProwlEnvironmentError(
            ExecutionStatus.INVALID_SCHEMA,
            f"Operation request fields are invalid ({'; '.join(details)}).",
        )
    if value.get(SCHEMA_VERSION_FIELD) != SCHEMA_VERSION:
        raise ProwlEnvironmentError(
            ExecutionStatus.INVALID_SCHEMA,
            f"Operation request schema version must be {SCHEMA_VERSION}.",
        )
    operation = _operation(value.get(OPERATION_FIELD))
    arguments = _object(value.get(ARGUMENTS_FIELD), f"request.{ARGUMENTS_FIELD}")
    unexpected_arguments = sorted(set(arguments) - _allowed_fields(operation))
    if unexpected_arguments:
        raise ProwlEnvironmentError(
            ExecutionStatus.INVALID_SCHEMA,
            f"{operation.value} contains unsupported arguments: {', '.join(unexpected_arguments)}.",
        )
    if (
        operation in MUTATING_OPERATIONS
        and arguments.get(MUTATION_AUTHORIZED_FIELD) is not True
    ):
        raise ProwlEnvironmentError(
            ExecutionStatus.MUTATION_UNAUTHORIZED,
            f"{operation.value} requires mutationAuthorized: true before command construction.",
        )
    argument_fields = frozenset(arguments)
    if not any(
        shape.accepts(argument_fields)
        for shape in OPERATION_CONTRACTS[operation].request_shapes
    ):
        raise ProwlEnvironmentError(
            ExecutionStatus.INVALID_SCHEMA,
            f"{operation.value} arguments do not match a source-owned request shape.",
        )
    _one_selector(arguments)

    if operation is Operation.SEND:
        _text(arguments.get(TEXT_FIELD), f"request.{ARGUMENTS_FIELD}.{TEXT_FIELD}")
        no_wait = arguments.get(NO_WAIT_FIELD)
        capture = arguments.get(CAPTURE_FIELD)
        if no_wait is not None:
            _boolean(no_wait, f"request.{ARGUMENTS_FIELD}.{NO_WAIT_FIELD}")
        if capture is not None:
            _boolean(capture, f"request.{ARGUMENTS_FIELD}.{CAPTURE_FIELD}")
        if no_wait is True and capture is True:
            raise ProwlEnvironmentError(
                ExecutionStatus.INVALID_SCHEMA,
                "send cannot combine noWait with capture.",
            )
    elif operation is Operation.KEY:
        _text(arguments.get(KEY_FIELD), f"request.{ARGUMENTS_FIELD}.{KEY_FIELD}")
    elif operation in {Operation.TAB_CLOSE, Operation.PANE_CLOSE} and not any(
        field in arguments for field in SELECTOR_FIELDS
    ):
        raise ProwlEnvironmentError(
            ExecutionStatus.INVALID_SCHEMA,
            f"{operation.value} requires one exact target selector.",
        )

    for field, (minimum, maximum) in INTEGER_BOUNDS.items():
        if field in arguments:
            _integer(
                arguments[field],
                f"request.{ARGUMENTS_FIELD}.{field}",
                minimum=minimum,
                maximum=maximum,
            )
    for field in BOOLEAN_ARGUMENT_FIELDS - {MUTATION_AUTHORIZED_FIELD}:
        if field in arguments:
            _boolean(arguments[field], f"request.{ARGUMENTS_FIELD}.{field}")
    if PATH_FIELD in arguments:
        _text(arguments[PATH_FIELD], f"request.{ARGUMENTS_FIELD}.{PATH_FIELD}")
    return operation, arguments


def operation_request(
    operation: Operation | str, **kwargs: object
) -> dict[str, object]:
    operation_value = Operation(operation)
    arguments: dict[str, object] = {}
    for name, value in kwargs.items():
        if name not in ARGUMENT_NAMES:
            valid = ", ".join(sorted(ARGUMENT_NAMES))
            raise ProwlEnvironmentError(
                ExecutionStatus.INVALID_SCHEMA,
                f"Unsupported operation-request argument {name!r}. Valid arguments: {valid}.",
            )
        if value is not None:
            arguments[ARGUMENT_NAMES[name]] = value
    request: dict[str, object] = {
        SCHEMA_VERSION_FIELD: SCHEMA_VERSION,
        OPERATION_FIELD: operation_value,
        ARGUMENTS_FIELD: arguments,
    }
    _validated_request(request)
    return request


def _selector_arguments(arguments: dict[str, object]) -> list[str]:
    command: list[str] = []
    for field, option in (
        (TARGET_FIELD, TARGET_OPTION),
        (WORKTREE_FIELD, WORKTREE_OPTION),
        (TAB_FIELD, TAB_OPTION),
        (PANE_FIELD, PANE_OPTION),
    ):
        if field in arguments:
            command.extend((option, cast(str, arguments[field])))
    return command


def command_for(request: object) -> tuple[str, ...]:
    operation, arguments = _validated_request(request)
    if operation is Operation.LIST:
        return (PROWL_COMMAND, LIST_COMMAND, JSON_OPTION)
    if operation is Operation.AGENTS:
        return (PROWL_COMMAND, AGENTS_COMMAND, JSON_OPTION)
    if operation is Operation.OPEN:
        command = [PROWL_COMMAND, OPEN_COMMAND, JSON_OPTION]
        if PATH_FIELD in arguments:
            command.append(cast(str, arguments[PATH_FIELD]))
        return tuple(command)

    if operation is Operation.TAB_CREATE:
        command = [PROWL_COMMAND, TAB_COMMAND, CREATE_COMMAND]
    elif operation is Operation.TAB_CLOSE:
        command = [PROWL_COMMAND, TAB_COMMAND, CLOSE_COMMAND]
    elif operation is Operation.PANE_CLOSE:
        command = [PROWL_COMMAND, PANE_COMMAND, CLOSE_COMMAND]
    else:
        command = [PROWL_COMMAND, operation.value]
    command.extend(_selector_arguments(arguments))
    command.append(JSON_OPTION)

    if operation is Operation.READ:
        for field, option in (
            (LAST_FIELD, LAST_OPTION),
            (STABLE_INTERVAL_FIELD, STABLE_INTERVAL_OPTION),
            (STABLE_PERIOD_FIELD, STABLE_PERIOD_OPTION),
            (WAIT_TIMEOUT_FIELD, WAIT_TIMEOUT_OPTION),
        ):
            if field in arguments:
                command.extend((option, str(arguments[field])))
        if arguments.get(WAIT_STABLE_FIELD) is True:
            command.append(WAIT_STABLE_OPTION)
    elif operation is Operation.SEND:
        for field, option in (
            (NO_ENTER_FIELD, NO_ENTER_OPTION),
            (NO_WAIT_FIELD, NO_WAIT_OPTION),
            (CAPTURE_FIELD, CAPTURE_OPTION),
        ):
            if arguments.get(field) is True:
                command.append(option)
        if TIMEOUT_FIELD in arguments:
            command.extend((TIMEOUT_OPTION, str(arguments[TIMEOUT_FIELD])))
        command.append(cast(str, arguments[TEXT_FIELD]))
    elif operation is Operation.KEY:
        if REPEAT_FIELD in arguments:
            command.extend((REPEAT_OPTION, str(arguments[REPEAT_FIELD])))
        command.append(cast(str, arguments[KEY_FIELD]))
    elif operation is Operation.TAB_CREATE and PATH_FIELD in arguments:
        command.extend((PATH_OPTION, cast(str, arguments[PATH_FIELD])))
    elif (
        operation in {Operation.TAB_CLOSE, Operation.PANE_CLOSE}
        and arguments.get(FORCE_FIELD) is True
    ):
        command.append(FORCE_OPTION)
    return tuple(command)


def raw_prowl_command_violations(sources: Mapping[str, str]) -> list[str]:
    return sorted(
        name
        for name, text in sources.items()
        if any(pattern.search(text) for pattern in RAW_PROWL_COMMAND_PATTERNS)
    )


def local_worktree_enumeration_violations(
    sources: Mapping[str, str],
) -> list[str]:
    return sorted(
        name
        for name, text in sources.items()
        if any(pattern.search(text) for pattern in LOCAL_WORKTREE_ENUMERATION_PATTERNS)
    )


def validate_operation_result(
    result: object, expected_operation: Operation | None = None
) -> dict[str, object]:
    value = _object(result, "result")
    if value.get(SCHEMA_VERSION_FIELD) != SCHEMA_VERSION:
        raise ProwlEnvironmentError(
            ExecutionStatus.INVALID_SCHEMA,
            f"Operation result schema version must be {SCHEMA_VERSION}.",
        )
    operation = _operation(value.get(OPERATION_FIELD))
    if expected_operation is not None and operation is not expected_operation:
        raise ProwlEnvironmentError(
            ExecutionStatus.INVALID_SCHEMA,
            f"Operation result identifies {operation.value}; expected {expected_operation.value}.",
        )
    try:
        status = ExecutionStatus(_text(value.get(STATUS_FIELD), STATUS_FIELD))
    except ValueError as error:
        raise ProwlEnvironmentError(
            ExecutionStatus.INVALID_SCHEMA,
            f"Unsupported operation result status: {value.get(STATUS_FIELD)!r}.",
        ) from error

    if status is ExecutionStatus.SUCCEEDED:
        if set(value) != SUCCESS_RESULT_FIELDS:
            raise ProwlEnvironmentError(
                ExecutionStatus.INVALID_SCHEMA,
                "Successful operation result fields do not match the source-owned schema.",
            )
        exit_code = value.get(COMMAND_EXIT_CODE_FIELD)
        if not isinstance(exit_code, int) or isinstance(exit_code, bool):
            raise ProwlEnvironmentError(
                ExecutionStatus.INVALID_SCHEMA,
                f"Expected an integer at result.{COMMAND_EXIT_CODE_FIELD}.",
            )
        response = _object(value.get(RESPONSE_FIELD), f"result.{RESPONSE_FIELD}")
        return {
            SCHEMA_VERSION_FIELD: SCHEMA_VERSION,
            OPERATION_FIELD: operation,
            STATUS_FIELD: status,
            COMMAND_EXIT_CODE_FIELD: exit_code,
            RESPONSE_FIELD: response,
        }

    allowed_fields = FAILURE_RESULT_REQUIRED_FIELDS | FAILURE_RESULT_OPTIONAL_FIELDS
    if not FAILURE_RESULT_REQUIRED_FIELDS <= set(value) or set(value) - allowed_fields:
        raise ProwlEnvironmentError(
            ExecutionStatus.INVALID_SCHEMA,
            "Failed operation result fields do not match the source-owned schema.",
        )
    validated: dict[str, object] = {
        SCHEMA_VERSION_FIELD: SCHEMA_VERSION,
        OPERATION_FIELD: operation,
        STATUS_FIELD: status,
        DETAIL_FIELD: _text(value.get(DETAIL_FIELD), f"result.{DETAIL_FIELD}"),
    }
    if COMMAND_EXIT_CODE_FIELD in value:
        exit_code = value[COMMAND_EXIT_CODE_FIELD]
        if not isinstance(exit_code, int) or isinstance(exit_code, bool):
            raise ProwlEnvironmentError(
                ExecutionStatus.INVALID_SCHEMA,
                f"Expected an integer at result.{COMMAND_EXIT_CODE_FIELD}.",
            )
        validated[COMMAND_EXIT_CODE_FIELD] = exit_code
    return validated


def _failure_result(
    operation: Operation,
    status: ExecutionStatus,
    detail: str,
    command_exit_code: int | None,
) -> dict[str, object]:
    result: dict[str, object] = {
        SCHEMA_VERSION_FIELD: SCHEMA_VERSION,
        OPERATION_FIELD: operation,
        STATUS_FIELD: status,
        DETAIL_FIELD: detail,
    }
    if command_exit_code is not None:
        result[COMMAND_EXIT_CODE_FIELD] = command_exit_code
    return validate_operation_result(result, operation)


def execute(request: object, runner: CommandRunner) -> dict[str, object]:
    operation, _ = _validated_request(request)
    command = command_for(request)
    try:
        result = runner.run(command)
    except ProwlEnvironmentError as error:
        return _failure_result(operation, error.status, str(error), None)
    if result.returncode != 0:
        detail = result.stderr.strip() or result.stdout.strip() or "no command detail"
        return _failure_result(
            operation, ExecutionStatus.COMMAND_FAILED, detail, result.returncode
        )
    try:
        payload = _object(json.loads(result.stdout), "response")
    except json.JSONDecodeError as error:
        return _failure_result(
            operation,
            ExecutionStatus.INVALID_SCHEMA,
            f"Prowl returned invalid JSON: {error.msg}",
            result.returncode,
        )
    if payload.get(OK_FIELD) is not True:
        error_payload = payload.get(ERROR_FIELD)
        detail = "Prowl public response reported failure."
        if isinstance(error_payload, dict):
            message = error_payload.get(MESSAGE_FIELD)
            if isinstance(message, str) and message:
                detail = message
        return _failure_result(
            operation, ExecutionStatus.COMMAND_FAILED, detail, result.returncode
        )
    return validate_operation_result(
        {
            SCHEMA_VERSION_FIELD: SCHEMA_VERSION,
            OPERATION_FIELD: operation,
            STATUS_FIELD: ExecutionStatus.SUCCEEDED,
            COMMAND_EXIT_CODE_FIELD: result.returncode,
            RESPONSE_FIELD: payload,
        },
        operation,
    )


def validate_identity(identity: object, location: str) -> dict[str, str]:
    value = _object(identity, location)
    unexpected = sorted(set(value) - IDENTITY_INPUT_FIELDS)
    missing = sorted(set(IDENTITY_FIELDS) - set(value))
    if unexpected or missing:
        details: list[str] = []
        if unexpected:
            details.append(f"unsupported: {', '.join(unexpected)}")
        if missing:
            details.append(f"missing: {', '.join(missing)}")
        raise ProwlEnvironmentError(
            ExecutionStatus.INVALID_SCHEMA,
            f"{location} identity fields are invalid ({'; '.join(details)}).",
        )
    validated = {
        field: _text(value.get(field), f"{location}.{field}")
        for field in IDENTITY_FIELDS
    }
    for path_field in (WORKTREE_FIELD, REPOSITORY_FIELD):
        if not os.path.isabs(validated[path_field]):
            raise ProwlEnvironmentError(
                ExecutionStatus.INVALID_SCHEMA,
                f"Expected an absolute path at {location}.{path_field}.",
            )
    if RUN_FIELD in value:
        validated[RUN_FIELD] = _text(value.get(RUN_FIELD), f"{location}.{RUN_FIELD}")
    return validated


def participant_from_agent(item: object) -> dict[str, str]:
    value = _object(item, "agent")
    pane = _object(value.get(PANE_FIELD), f"agent.{PANE_FIELD}")
    worktree = _object(value.get(WORKTREE_FIELD), f"agent.{WORKTREE_FIELD}")
    project = _object(value.get(PROJECT_FIELD), f"agent.{PROJECT_FIELD}")
    identity = {
        AGENT_FIELD: _text(value.get(ID_FIELD), f"agent.{ID_FIELD}"),
        PANE_FIELD: _text(pane.get(ID_FIELD), f"agent.{PANE_FIELD}.{ID_FIELD}"),
        WORKTREE_FIELD: _text(
            worktree.get(PATH_FIELD), f"agent.{WORKTREE_FIELD}.{PATH_FIELD}"
        ),
        BRANCH_FIELD: _text(
            project.get(BRANCH_FIELD), f"agent.{PROJECT_FIELD}.{BRANCH_FIELD}"
        ),
        REPOSITORY_FIELD: _text(
            worktree.get(ROOT_PATH_FIELD),
            f"agent.{WORKTREE_FIELD}.{ROOT_PATH_FIELD}",
        ),
    }
    run = value.get(RUN_FIELD)
    if run is not None:
        identity[RUN_FIELD] = _text(
            _object(run, f"agent.{RUN_FIELD}").get(ID_FIELD),
            f"agent.{RUN_FIELD}.{ID_FIELD}",
        )
    return validate_identity(identity, "participant")


def participants_from_agents(payload: object) -> list[dict[str, str]]:
    response = _object(payload, "response")
    data = _object(response.get(DATA_FIELD), f"response.{DATA_FIELD}")
    agents = _array(data.get(AGENTS_FIELD), f"response.{DATA_FIELD}.{AGENTS_FIELD}")
    participants = [participant_from_agent(item) for item in agents]
    if not participants:
        raise ProwlEnvironmentError(
            ExecutionStatus.IDENTITY_UNAVAILABLE,
            "Prowl returned no positively identified agents.",
        )
    pane_ids = [participant[PANE_FIELD] for participant in participants]
    if len(pane_ids) != len(set(pane_ids)):
        raise ProwlEnvironmentError(
            ExecutionStatus.IDENTITY_AMBIGUOUS,
            "Prowl returned ambiguous duplicate agent pane identities.",
        )
    return participants


def participant_projection(payload: object) -> dict[str, object]:
    try:
        participants = participants_from_agents(payload)
    except ProwlEnvironmentError as error:
        status = (
            ExecutionStatus.IDENTITY_AMBIGUOUS
            if error.status is ExecutionStatus.IDENTITY_AMBIGUOUS
            else ExecutionStatus.IDENTITY_UNAVAILABLE
        )
        return {
            SCHEMA_VERSION_FIELD: SCHEMA_VERSION,
            OPERATION_FIELD: Operation.AGENTS,
            STATUS_FIELD: status,
            DETAIL_FIELD: str(error),
        }
    return {
        SCHEMA_VERSION_FIELD: SCHEMA_VERSION,
        OPERATION_FIELD: Operation.AGENTS,
        STATUS_FIELD: ExecutionStatus.SUCCEEDED,
        PARTICIPANTS_FIELD: participants,
    }


def _path_contains(root: str, target: str) -> bool:
    if not os.path.isabs(root):
        return False
    normalized_root = os.path.normpath(root)
    normalized_target = os.path.normpath(target)
    try:
        return (
            os.path.commonpath((normalized_root, normalized_target)) == normalized_root
        )
    except ValueError:
        return False


def _send_request_template(participant: Mapping[str, str]) -> dict[str, object]:
    return {
        SCHEMA_VERSION_FIELD: SCHEMA_VERSION,
        OPERATION_FIELD: Operation.SEND,
        ARGUMENTS_FIELD: {
            PANE_FIELD: participant[PANE_FIELD],
            TEXT_FIELD: None,
            NO_WAIT_FIELD: True,
        },
    }


def _resolve_caller(
    participants: list[dict[str, str]], environment: Mapping[str, str]
) -> dict[str, str]:
    pane_id = environment.get(PROWL_PANE_ID_ENV)
    worktree_path = environment.get(PROWL_WORKTREE_PATH_ENV)
    if not pane_id and not worktree_path:
        raise ProwlEnvironmentError(
            ExecutionStatus.IDENTITY_UNAVAILABLE,
            "resolve-target requires caller identity from PROWL_PANE_ID or PROWL_WORKTREE_PATH.",
        )
    matches = [
        participant
        for participant in participants
        if (not pane_id or participant[PANE_FIELD] == pane_id)
        and (
            not worktree_path
            or os.path.normpath(participant[WORKTREE_FIELD])
            == os.path.normpath(worktree_path)
        )
    ]
    if len(matches) == 1:
        return matches[0]
    status = (
        ExecutionStatus.IDENTITY_AMBIGUOUS
        if len(matches) > 1
        else ExecutionStatus.IDENTITY_UNAVAILABLE
    )
    supplied = ", ".join(
        field for field in CALLER_IDENTITY_ENV_FIELDS if environment.get(field)
    )
    raise ProwlEnvironmentError(
        status,
        f"Caller identity from {supplied} matches {len(matches)} public Prowl agents.",
    )


def resolve_target(
    path: str, environment: Mapping[str, str], runner: CommandRunner
) -> dict[str, object]:
    if not path or not os.path.isabs(path):
        raise ProwlEnvironmentError(
            ExecutionStatus.INVALID_SCHEMA,
            "resolve-target path must be an absolute worktree, repository, or working-directory path.",
        )
    inventory = execute(operation_request(Operation.AGENTS), runner)
    participants: list[dict[str, str]] = []
    caller: dict[str, str] | None = None
    candidates: list[dict[str, object]] = []
    status = inventory[STATUS_FIELD]
    detail: str | None = None
    if status is ExecutionStatus.SUCCEEDED:
        try:
            participants = participants_from_agents(inventory[RESPONSE_FIELD])
            caller = _resolve_caller(participants, environment)
            matched = [
                participant
                for participant in participants
                if participant[PANE_FIELD] != caller[PANE_FIELD]
                and (
                    _path_contains(participant[WORKTREE_FIELD], path)
                    or os.path.normpath(participant[REPOSITORY_FIELD])
                    == os.path.normpath(path)
                )
            ]
            candidates = [
                {
                    PARTICIPANT_FIELD: participant,
                    SEND_REQUEST_TEMPLATE_FIELD: _send_request_template(participant),
                }
                for participant in matched
            ]
            cardinality = target_match_cardinality(len(candidates))
            if cardinality is TargetMatchCardinality.ZERO:
                status = ExecutionStatus.IDENTITY_UNAVAILABLE
                detail = f"No non-caller Prowl agent contains target path {path}."
            elif cardinality is TargetMatchCardinality.ONE:
                status = ExecutionStatus.SUCCEEDED
            elif cardinality is TargetMatchCardinality.MULTIPLE:
                status = ExecutionStatus.IDENTITY_AMBIGUOUS
                detail = f"Target path {path} matches multiple non-caller Prowl agents."
        except ProwlEnvironmentError as error:
            status = error.status
            detail = str(error)
    else:
        detail = cast(str, inventory.get(DETAIL_FIELD))

    return {
        SCHEMA_VERSION_FIELD: SCHEMA_VERSION,
        OPERATION_FIELD: CliOperation.RESOLVE_TARGET,
        STATUS_FIELD: status,
        DETAIL_FIELD: detail,
        INVENTORY_FIELD: inventory,
        PARTICIPANTS_FIELD: participants,
        CALLER_FIELD: caller,
        CANDIDATES_FIELD: candidates,
    }


def _canonical_reference(value: object) -> str:
    reference = _text(value, COORDINATION_REFERENCE_FIELD)
    try:
        return str(uuid.UUID(reference))
    except ValueError as error:
        raise ProwlEnvironmentError(
            ExecutionStatus.INVALID_SCHEMA,
            f"Coordination reference is not a UUID: {reference}",
        ) from error


def _handback_command(*, pane: str, completion_text: str, adapter_path: str) -> str:
    request = operation_request(
        Operation.SEND,
        pane=pane,
        text=completion_text,
        no_wait=True,
    )
    payload = json.dumps(request, sort_keys=True, separators=(",", ":"))
    return (
        "printf '%s\\n' "
        f"{shlex.quote(payload)} | python3 {shlex.quote(adapter_path)} run"
    )


def handback_plan(
    *,
    sender: object,
    recipient: object,
    completion_text: str,
) -> dict[str, object]:
    validated_sender = validate_identity(sender, SENDER_FIELD)
    validated_recipient = validate_identity(recipient, RECIPIENT_FIELD)
    if validated_sender[PANE_FIELD] == validated_recipient[PANE_FIELD]:
        raise ProwlEnvironmentError(
            ExecutionStatus.INVALID_SCHEMA,
            "A handback recipient must be a different positively identified Prowl agent.",
        )
    completion = _text(completion_text, COMPLETION_TEXT_FIELD)
    adapter_path = str(Path(__file__).resolve())
    return {
        SCHEMA_VERSION_FIELD: HANDBACK_SCHEMA_VERSION,
        COMPLETION_TEXT_FIELD: completion,
        ADAPTER_PATH_FIELD: adapter_path,
        COMMAND_FIELD: _handback_command(
            pane=validated_sender[PANE_FIELD],
            completion_text=completion,
            adapter_path=adapter_path,
        ),
        SUCCESS_CRITERIA_FIELD: {
            STATUS_FIELD: ExecutionStatus.SUCCEEDED,
            COMMAND_EXIT_CODE_FIELD: 0,
            TRAILING_ENTER_SENT_FIELD: True,
        },
        RETRY_POLICY_FIELD: HANDBACK_RETRY_POLICY,
        SOCKET_FIELD: DEFAULT_SOCKET,
        EXPECTED_PANES_FIELD: [
            validated_sender[PANE_FIELD],
            validated_recipient[PANE_FIELD],
        ],
    }


def _validated_handback(
    value: object,
    *,
    sender: dict[str, str],
    recipient: dict[str, str],
) -> dict[str, object]:
    handback = _object(value, HANDBACK_FIELD)
    unexpected = sorted(set(handback) - HANDBACK_FIELDS)
    missing = sorted(HANDBACK_FIELDS - set(handback))
    if unexpected or missing:
        raise ProwlEnvironmentError(
            ExecutionStatus.INVALID_SCHEMA,
            "Handback must contain exactly the source-owned fields.",
        )
    if handback.get(SCHEMA_VERSION_FIELD) != HANDBACK_SCHEMA_VERSION:
        raise ProwlEnvironmentError(
            ExecutionStatus.INVALID_SCHEMA,
            f"Handback schema version must be {HANDBACK_SCHEMA_VERSION}.",
        )
    completion = _text(
        handback.get(COMPLETION_TEXT_FIELD),
        f"{HANDBACK_FIELD}.{COMPLETION_TEXT_FIELD}",
    )
    adapter_path = _text(
        handback.get(ADAPTER_PATH_FIELD),
        f"{HANDBACK_FIELD}.{ADAPTER_PATH_FIELD}",
    )
    if not Path(adapter_path).is_absolute():
        raise ProwlEnvironmentError(
            ExecutionStatus.INVALID_SCHEMA,
            "Handback adapterPath must be absolute.",
        )
    expected_command = _handback_command(
        pane=sender[PANE_FIELD],
        completion_text=completion,
        adapter_path=adapter_path,
    )
    command = _text(handback.get(COMMAND_FIELD), f"{HANDBACK_FIELD}.{COMMAND_FIELD}")
    if command != expected_command:
        raise ProwlEnvironmentError(
            ExecutionStatus.INVALID_SCHEMA,
            "Handback command does not match its semantic completion data.",
        )
    success = _object(
        handback.get(SUCCESS_CRITERIA_FIELD),
        f"{HANDBACK_FIELD}.{SUCCESS_CRITERIA_FIELD}",
    )
    command_exit_code = success.get(COMMAND_EXIT_CODE_FIELD)
    if (
        set(success) != HANDBACK_SUCCESS_FIELDS
        or success.get(STATUS_FIELD) != ExecutionStatus.SUCCEEDED
        or not isinstance(command_exit_code, int)
        or isinstance(command_exit_code, bool)
        or command_exit_code != 0
        or success.get(TRAILING_ENTER_SENT_FIELD) is not True
    ):
        raise ProwlEnvironmentError(
            ExecutionStatus.INVALID_SCHEMA,
            "Handback success criteria must require checked turn submission.",
        )
    if handback.get(RETRY_POLICY_FIELD) != HANDBACK_RETRY_POLICY:
        raise ProwlEnvironmentError(
            ExecutionStatus.INVALID_SCHEMA,
            f"Handback retryPolicy must be {HANDBACK_RETRY_POLICY}.",
        )
    if handback.get(SOCKET_FIELD) != DEFAULT_SOCKET:
        raise ProwlEnvironmentError(
            ExecutionStatus.INVALID_SCHEMA,
            f"Handback socket must be {DEFAULT_SOCKET}.",
        )
    if handback.get(EXPECTED_PANES_FIELD) != [
        sender[PANE_FIELD],
        recipient[PANE_FIELD],
    ]:
        raise ProwlEnvironmentError(
            ExecutionStatus.INVALID_SCHEMA,
            "Handback expectedPanes must preserve sender and recipient pane order.",
        )
    return {
        SCHEMA_VERSION_FIELD: HANDBACK_SCHEMA_VERSION,
        COMPLETION_TEXT_FIELD: completion,
        ADAPTER_PATH_FIELD: adapter_path,
        COMMAND_FIELD: command,
        SUCCESS_CRITERIA_FIELD: success,
        RETRY_POLICY_FIELD: HANDBACK_RETRY_POLICY,
        SOCKET_FIELD: DEFAULT_SOCKET,
        EXPECTED_PANES_FIELD: [sender[PANE_FIELD], recipient[PANE_FIELD]],
    }


def delegation_request(
    *,
    sender: object,
    recipient: object,
    subject: str,
    instruction: str,
    completion_text: str,
    coordination_reference: str | None = None,
) -> dict[str, object]:
    validated_sender = validate_identity(sender, SENDER_FIELD)
    validated_recipient = validate_identity(recipient, RECIPIENT_FIELD)
    if validated_sender[PANE_FIELD] == validated_recipient[PANE_FIELD]:
        raise ProwlEnvironmentError(
            ExecutionStatus.INVALID_SCHEMA,
            "A delegation recipient must be a different positively identified Prowl agent.",
        )
    reference = (
        str(uuid.uuid4())
        if coordination_reference is None
        else _canonical_reference(coordination_reference)
    )
    return {
        SCHEMA_VERSION_FIELD: DELEGATION_SCHEMA_VERSION,
        KIND_FIELD: EnvelopeKind.DELEGATION_REQUEST,
        COORDINATION_REFERENCE_FIELD: reference,
        SENDER_FIELD: validated_sender,
        RECIPIENT_FIELD: validated_recipient,
        SUBJECT_FIELD: _text(subject, SUBJECT_FIELD),
        INSTRUCTION_FIELD: _text(instruction, INSTRUCTION_FIELD),
        HANDBACK_FIELD: handback_plan(
            sender=validated_sender,
            recipient=validated_recipient,
            completion_text=completion_text,
        ),
    }


def _validated_delegation(value: object) -> dict[str, object]:
    request = _object(value, "delegationRequest")
    unexpected = sorted(set(request) - DELEGATION_REQUEST_FIELDS)
    missing = sorted(DELEGATION_REQUEST_FIELDS - set(request))
    if unexpected or missing:
        raise ProwlEnvironmentError(
            ExecutionStatus.INVALID_SCHEMA,
            "Delegation request must contain exactly the source-owned request fields.",
        )
    if request.get(SCHEMA_VERSION_FIELD) != DELEGATION_SCHEMA_VERSION:
        raise ProwlEnvironmentError(
            ExecutionStatus.INVALID_SCHEMA,
            f"Delegation request schema version must be {DELEGATION_SCHEMA_VERSION}.",
        )
    if request.get(KIND_FIELD) != EnvelopeKind.DELEGATION_REQUEST:
        raise ProwlEnvironmentError(
            ExecutionStatus.INVALID_SCHEMA,
            f"Delegation request kind must be {EnvelopeKind.DELEGATION_REQUEST}.",
        )
    sender = validate_identity(request.get(SENDER_FIELD), SENDER_FIELD)
    recipient = validate_identity(request.get(RECIPIENT_FIELD), RECIPIENT_FIELD)
    if sender[PANE_FIELD] == recipient[PANE_FIELD]:
        raise ProwlEnvironmentError(
            ExecutionStatus.INVALID_SCHEMA,
            "A delegation recipient must be a different positively identified Prowl agent.",
        )
    return {
        SCHEMA_VERSION_FIELD: DELEGATION_SCHEMA_VERSION,
        KIND_FIELD: EnvelopeKind.DELEGATION_REQUEST,
        COORDINATION_REFERENCE_FIELD: _canonical_reference(
            request.get(COORDINATION_REFERENCE_FIELD)
        ),
        SENDER_FIELD: sender,
        RECIPIENT_FIELD: recipient,
        SUBJECT_FIELD: _text(request.get(SUBJECT_FIELD), SUBJECT_FIELD),
        INSTRUCTION_FIELD: _text(request.get(INSTRUCTION_FIELD), INSTRUCTION_FIELD),
        HANDBACK_FIELD: _validated_handback(
            request.get(HANDBACK_FIELD),
            sender=sender,
            recipient=recipient,
        ),
    }


def _durable_reference(value: object) -> str:
    reference = _text(value, RESULT_REFERENCE_FIELD)
    parsed = urlparse(reference)
    if not parsed.scheme:
        raise ProwlEnvironmentError(
            ExecutionStatus.INVALID_SCHEMA,
            "A durable result reference must include a URI scheme.",
        )
    return reference


def terminal_handback(
    delegation: object,
    terminal_kind: TerminalKind | str,
    *,
    inline_result: str | None = None,
    result_reference: str | None = None,
    projection: str | None = None,
) -> dict[str, object]:
    request = _validated_delegation(delegation)
    kind = TerminalKind(terminal_kind)
    inline = _optional_text(inline_result, INLINE_RESULT_FIELD)
    reference = (
        None if result_reference is None else _durable_reference(result_reference)
    )
    bounded_projection = _optional_text(projection, PROJECTION_FIELD)
    if inline is None and reference is None:
        raise ProwlEnvironmentError(
            ExecutionStatus.INVALID_SCHEMA,
            "A terminal handback requires inlineResult or resultReference with projection.",
        )
    if reference is not None and bounded_projection is None:
        raise ProwlEnvironmentError(
            ExecutionStatus.INVALID_SCHEMA,
            "A durable result reference requires a bounded inline projection.",
        )
    if reference is None and bounded_projection is not None:
        raise ProwlEnvironmentError(
            ExecutionStatus.INVALID_SCHEMA,
            "projection is valid only with resultReference.",
        )
    if (
        bounded_projection is not None
        and len(bounded_projection) > MAX_RESULT_PROJECTION_CHARACTERS
    ):
        raise ProwlEnvironmentError(
            ExecutionStatus.INVALID_SCHEMA,
            f"projection exceeds {MAX_RESULT_PROJECTION_CHARACTERS} characters.",
        )
    return {
        SCHEMA_VERSION_FIELD: DELEGATION_SCHEMA_VERSION,
        KIND_FIELD: kind,
        COORDINATION_REFERENCE_FIELD: request[COORDINATION_REFERENCE_FIELD],
        SENDER_FIELD: request[RECIPIENT_FIELD],
        RECIPIENT_FIELD: request[SENDER_FIELD],
        INLINE_RESULT_FIELD: inline,
        RESULT_REFERENCE_FIELD: reference,
        PROJECTION_FIELD: bounded_projection,
    }


def _validated_terminal(value: object) -> dict[str, object]:
    terminal = _object(value, "terminalHandback")
    unexpected = sorted(set(terminal) - TERMINAL_HANDBACK_FIELDS)
    missing = sorted(TERMINAL_HANDBACK_FIELDS - set(terminal))
    if unexpected or missing:
        raise ProwlEnvironmentError(
            ExecutionStatus.INVALID_SCHEMA,
            "Terminal handback must contain exactly the source-owned terminal fields.",
        )
    if terminal.get(SCHEMA_VERSION_FIELD) != DELEGATION_SCHEMA_VERSION:
        raise ProwlEnvironmentError(
            ExecutionStatus.INVALID_SCHEMA,
            f"Terminal handback schema version must be {DELEGATION_SCHEMA_VERSION}.",
        )
    kind = _terminal_kind(terminal.get(KIND_FIELD))
    inline = _optional_text(terminal.get(INLINE_RESULT_FIELD), INLINE_RESULT_FIELD)
    reference = terminal.get(RESULT_REFERENCE_FIELD)
    projection = terminal.get(PROJECTION_FIELD)
    if reference is not None:
        reference = _durable_reference(reference)
    if projection is not None:
        projection = _text(projection, PROJECTION_FIELD)
    if inline is None and reference is None:
        raise ProwlEnvironmentError(
            ExecutionStatus.INVALID_SCHEMA,
            "A terminal handback requires one supported result form.",
        )
    if (reference is None) != (projection is None):
        raise ProwlEnvironmentError(
            ExecutionStatus.INVALID_SCHEMA,
            "resultReference and projection must appear together.",
        )
    if (
        isinstance(projection, str)
        and len(projection) > MAX_RESULT_PROJECTION_CHARACTERS
    ):
        raise ProwlEnvironmentError(
            ExecutionStatus.INVALID_SCHEMA,
            f"projection exceeds {MAX_RESULT_PROJECTION_CHARACTERS} characters.",
        )
    return {
        SCHEMA_VERSION_FIELD: DELEGATION_SCHEMA_VERSION,
        KIND_FIELD: kind,
        COORDINATION_REFERENCE_FIELD: _canonical_reference(
            terminal.get(COORDINATION_REFERENCE_FIELD)
        ),
        SENDER_FIELD: validate_identity(terminal.get(SENDER_FIELD), SENDER_FIELD),
        RECIPIENT_FIELD: validate_identity(
            terminal.get(RECIPIENT_FIELD), RECIPIENT_FIELD
        ),
        INLINE_RESULT_FIELD: inline,
        RESULT_REFERENCE_FIELD: reference,
        PROJECTION_FIELD: projection,
    }


def reduce_terminal(current: object | None, incoming: object) -> dict[str, object]:
    validated_incoming = _validated_terminal(incoming)
    if current is None:
        return validated_incoming
    validated_current = _validated_terminal(current)
    if validated_current != validated_incoming:
        raise ProwlEnvironmentError(
            ExecutionStatus.INVALID_SCHEMA,
            "A conflicting terminal handback already exists for the coordination reference.",
        )
    return validated_current


def delegation_delivery_request(envelope: object) -> dict[str, object]:
    value = _object(envelope, "envelope")
    kind = value.get(KIND_FIELD)
    if kind == EnvelopeKind.DELEGATION_REQUEST:
        validated = _validated_delegation(value)
    else:
        validated = _validated_terminal(value)
    recipient = validate_identity(validated.get(RECIPIENT_FIELD), RECIPIENT_FIELD)
    return operation_request(
        Operation.SEND,
        pane=recipient[PANE_FIELD],
        text=json.dumps(validated, sort_keys=True),
        no_wait=True,
    )


def result_form_arguments(fields: Mapping[str, object]) -> dict[str, str | None]:
    unexpected = sorted(
        set(fields) - {INLINE_RESULT_FIELD, RESULT_REFERENCE_FIELD, PROJECTION_FIELD}
    )
    if unexpected:
        raise ProwlEnvironmentError(
            ExecutionStatus.INVALID_SCHEMA,
            f"Unsupported terminal result fields: {', '.join(unexpected)}.",
        )
    return {
        "inline_result": cast(str | None, fields.get(INLINE_RESULT_FIELD)),
        "result_reference": cast(str | None, fields.get(RESULT_REFERENCE_FIELD)),
        "projection": cast(str | None, fields.get(PROJECTION_FIELD)),
    }


def _json_input(stream: TextIO, location: str) -> dict[str, object]:
    try:
        return _object(json.load(stream), location)
    except json.JSONDecodeError as error:
        raise ProwlEnvironmentError(
            ExecutionStatus.INVALID_SCHEMA,
            f"{location} is invalid JSON: {error.msg}",
        ) from error


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    subparsers = parser.add_subparsers(dest="cli_operation", required=True)
    for operation in CliOperation:
        subparsers.add_parser(operation.value)
    return parser


def _delegation_from_cli(value: dict[str, object]) -> dict[str, object]:
    # Reading each field by name would ignore every other key, so a caller that
    # invents one sends a delegation missing the data it believed it supplied.
    # The envelope builder owns schemaVersion and kind, so they are not accepted
    # here; every remaining key must be one this function actually forwards.
    unexpected = sorted(set(value) - DELEGATION_CLI_FIELDS)
    if unexpected:
        raise ProwlEnvironmentError(
            ExecutionStatus.INVALID_SCHEMA,
            "Delegation request carries unsupported fields: " + ", ".join(unexpected),
        )
    return delegation_request(
        sender=value.get(SENDER_FIELD),
        recipient=value.get(RECIPIENT_FIELD),
        subject=_text(value.get(SUBJECT_FIELD), SUBJECT_FIELD),
        instruction=_text(value.get(INSTRUCTION_FIELD), INSTRUCTION_FIELD),
        completion_text=_text(value.get(COMPLETION_TEXT_FIELD), COMPLETION_TEXT_FIELD),
        coordination_reference=cast(
            str | None, value.get(COORDINATION_REFERENCE_FIELD)
        ),
    )


def _handback_from_cli(value: dict[str, object]) -> dict[str, object]:
    unexpected = sorted(set(value) - HANDBACK_PLAN_CLI_FIELDS)
    missing = sorted(HANDBACK_PLAN_CLI_FIELDS - set(value))
    if unexpected or missing:
        raise ProwlEnvironmentError(
            ExecutionStatus.INVALID_SCHEMA,
            "plan-handback requires exactly sender, recipient, and completionText.",
        )
    handback = handback_plan(
        sender=value.get(SENDER_FIELD),
        recipient=value.get(RECIPIENT_FIELD),
        completion_text=_text(value.get(COMPLETION_TEXT_FIELD), COMPLETION_TEXT_FIELD),
    )
    return {
        SCHEMA_VERSION_FIELD: DELEGATION_SCHEMA_VERSION,
        OPERATION_FIELD: CliOperation.PLAN_HAND_BACK,
        STATUS_FIELD: ExecutionStatus.SUCCEEDED,
        HANDBACK_FIELD: handback,
    }


def command_exit_code(result: object) -> int:
    value = _object(result, "result")
    status = value.get(STATUS_FIELD)
    if status == ExecutionStatus.SUCCEEDED:
        return 0
    if value.get(OPERATION_FIELD) == CliOperation.RESOLVE_TARGET and status in {
        ExecutionStatus.IDENTITY_UNAVAILABLE,
        ExecutionStatus.IDENTITY_AMBIGUOUS,
    }:
        return 0
    return 2


def _resolve_target_from_cli(
    value: dict[str, object],
    environment: Mapping[str, str],
    runner: CommandRunner,
) -> dict[str, object]:
    unexpected = sorted(set(value) - {SCHEMA_VERSION_FIELD, PATH_FIELD})
    if unexpected or value.get(SCHEMA_VERSION_FIELD) != SCHEMA_VERSION:
        raise ProwlEnvironmentError(
            ExecutionStatus.INVALID_SCHEMA,
            "resolve-target requires exactly schemaVersion and path.",
        )
    return resolve_target(_text(value.get(PATH_FIELD), PATH_FIELD), environment, runner)


def _execute_cli_operation(
    cli_operation: CliOperation,
    value: dict[str, object],
    environment: Mapping[str, str],
    runner: CommandRunner,
) -> dict[str, object]:
    if cli_operation is CliOperation.RESOLVE_TARGET:
        return _resolve_target_from_cli(value, environment, runner)
    if cli_operation is CliOperation.RUN:
        return execute(value, runner)
    if cli_operation is CliOperation.PLAN_HAND_BACK:
        return _handback_from_cli(value)
    if cli_operation is CliOperation.DELEGATE:
        delegation = _delegation_from_cli(value)
        result = execute(delegation_delivery_request(delegation), runner)
        result[DELEGATION_FIELD] = delegation
        return result

    delegation = _object(value.get(DELEGATION_FIELD), DELEGATION_FIELD)
    terminal = terminal_handback(
        delegation,
        _terminal_kind(value.get(KIND_FIELD)),
        inline_result=cast(str | None, value.get(INLINE_RESULT_FIELD)),
        result_reference=cast(str | None, value.get(RESULT_REFERENCE_FIELD)),
        projection=cast(str | None, value.get(PROJECTION_FIELD)),
    )
    result = execute(delegation_delivery_request(terminal), runner)
    result[DELEGATION_FIELD] = delegation
    result[TERMINAL_FIELD] = terminal
    return result


def main(
    argv: list[str] | None = None,
    *,
    runner: CommandRunner | None = None,
    stdin: TextIO | None = None,
    stdout: TextIO | None = None,
    environment: Mapping[str, str] | None = None,
) -> int:
    args = _parser().parse_args(argv)
    cli_operation = CliOperation(args.cli_operation)
    command_runner = runner if runner is not None else SubprocessRunner()
    input_stream = stdin if stdin is not None else sys.stdin
    output_stream = stdout if stdout is not None else sys.stdout
    active_environment = environment if environment is not None else os.environ
    try:
        value = _json_input(input_stream, "stdin")
        result = _execute_cli_operation(
            cli_operation, value, active_environment, command_runner
        )
    except ProwlEnvironmentError as error:
        result = {
            SCHEMA_VERSION_FIELD: SCHEMA_VERSION,
            STATUS_FIELD: error.status,
            DETAIL_FIELD: str(error),
        }
    print(json.dumps(result, sort_keys=True), file=output_stream)
    return command_exit_code(result)


if __name__ == "__main__":
    sys.exit(main())


<!-- Producer: dist/claude/coding-agents/skills/message-agents/SKILL.md -->

---
name: message-agents
description: >-
  ALWAYS invoke this skill when discovering a Prowl coding-agent recipient or sending facts, ownership proposals, state reports, authorizations, or acknowledgements to another agent pane.
argument-hint: "<JSON message request>"
allowed-tools: Skill, Bash(printf:*), Bash(python3 "${CLAUDE_SKILL_DIR}/scripts/agent_message.py":*), AskUserQuestion
---

<objective>
A source-owned coordination envelope delivered to one complete Prowl pane identity, with transport status kept distinct from acknowledgement, agreement, authorization, and ownership.
</objective>

<workflow>

1. Read `$ARGUMENTS`. When it is empty or whitespace, stop with `invalid-schema` and require one JSON message request containing `recipientPath`, `kind`, `subject`, and `facts`; perform no discovery or delivery. Otherwise interpret it as that request, with `recipientPath` holding the recipient's absolute worktree, repository, or working-directory path and with any applicable coordination fields. The request may carry `toPane` only as a complete identity assertion from an upstream coordination plan and may carry `handback` only as the complete structured block returned by `/operate-prowl plan-handback`. When required data is absent, stop and name it before discovery or delivery; never invent message data or ask for a pane UUID.
2. Invoke `/operate-prowl` once for `resolve-target` with the supplied path. Preserve the complete result. It returns the checked inventory, complete caller and participants, and non-caller candidates whose `sendRequestTemplate` already selects each pane with immediate-return mode and normal trailing-Enter behavior.
3. Require a complete resolved caller and one selected candidate. On `identity-ambiguous` with `caller: null`, report the exact detail as an unresolved caller-identity conflict and stop; never ask the operator to select from the empty candidate set. Otherwise, when the request carries `toPane`, match it against the captured non-caller candidates before considering cardinality: exactly one matching candidate selects it, while zero or multiple matches stop with `invalid-identity`. Without `toPane`, use the sole candidate on `succeeded`. On `identity-ambiguous`, use `AskUserQuestion` for one single-select question: number candidates in resolver order, show each candidate's complete pane, worktree, branch, and repository, and map the answer back to that exact captured candidate and its `sendRequestTemplate` without rerunning resolution. When the runtime's option cap is below the candidate count, include the complete numbered inventory in the question and accept an exact candidate number through its free-form response; never omit a candidate. On `identity-unavailable`, report the exact detail and participant worktrees. NEVER select by title, focus, position, prose, or the caller's pane.
4. Build the bundled script's `discovery` input directly from the resolver result: `caller` is the returned caller, `targets` is the returned complete participant list, and `status` is `prowl-pane`. Set `toPane` from the selected candidate's complete participant. This source-owned bridge uses the captured resolver result directly; never write an intermediate file or run an ad hoc transformation script.
5. Build the bundled script's message request with the selected candidate's `toPane`, `kind`, `subject`, `facts`, optional `request`, optional `handback`, optional `coordinationReference`, optional `mutationTarget`, optional `observedState`, and optional `accepted`. `recipientPath` has completed target resolution and never enters the envelope. `kind` is exactly `ownership-proposal`, `fact`, `acknowledgement`, `mutation-state`, or `mutation-authorization`. An acknowledgement, mutation-state report, or mutation authorization MUST reuse the active proposal UUID; an initiating proposal or fact MUST omit it so the adapter creates a new UUID. An acknowledgement MUST carry boolean `accepted`; every other kind omits it. Only a `fact` production request carries `handback`. Preserve that block byte-for-byte from `/operate-prowl`; reject top-level `command`, `handbackCommand`, `returnPane`, or `adapterPath` fields and never reconstruct the block.
6. For a delegated mutation, use the source-owned handshake:
   - An `ownership-proposal` carries `mutationTarget` with exact `pane`, `worktree`, `branch`, `repository`, full `head`, and `status` values; pane, worktree, branch, and repository match the live recipient identity.
   - A `mutation-state` response carries the same target plus `observedState` with exact `worktree`, `branch`, `repository`, full `head`, and `status` values matching the live sender identity.
   - A `mutation-authorization` carries the checked target and observed state and targets that same live recipient. Any mismatch returns `invalid-identity` before delivery planning.
7. Pass the discovery and message request to the bundled script's `build` operation. It returns the complete `envelope` and a semantic `delivery` containing `toPane` and `text`.
8. Confirm the selected candidate template's pane equals the delivery's complete `toPane`, fill its null `text` with the delivery's exact text, and invoke `/operate-prowl` once with that request. NEVER alter its `pane` or `noWait`, construct a second request, use `noEnter`, or retry after the editor becomes free.
9. Pass the envelope and the exact environment result to the bundled script's `result` operation. Set `delivered` true only when `/operate-prowl` returned a complete checked `send` result with `status: "succeeded"`, `commandExitCode: 0`, and public `response.data.input.trailing_enter_sent: true`; preserve that complete result under `transport`. The bundled script rejects delivered status when any checked transport or submission field is absent or inconsistent. Prefilled text that remains in the recipient editor is not delivered.
10. Report the complete `coordinationReference`, checked `commandExitCode`, and delivery `status`. Once trailing Enter is confirmed, the turn is queued and no second send is needed. `delivered` means only that the environment capability accepted transport; it NEVER means acknowledged, agreed, authorized, or owned. Stop with the exact status and detail on `delivery-failed`, `invalid-identity`, `environment-unavailable`, or `invalid-schema`.

</workflow>

<command_forms>

Pass every payload over stdin. When the shell accepts multiline input:

```bash
python3 "${CLAUDE_SKILL_DIR}/scripts/agent_message.py" build <<'JSON'
{"discovery":{},"messageRequest":{}}
JSON

python3 "${CLAUDE_SKILL_DIR}/scripts/agent_message.py" result <<'JSON'
{"envelope":{},"delivered":false,"commandExitCode":1,"transport":{},"detail":"<exact-environment-detail>"}
JSON
```

When the runner requires one physical command line:

```bash
printf '%s\n' '{"discovery":{},"messageRequest":{}}' | python3 "${CLAUDE_SKILL_DIR}/scripts/agent_message.py" build
printf '%s\n' '{"envelope":{},"delivered":false,"commandExitCode":1,"transport":{},"detail":"<exact-environment-detail>"}' | python3 "${CLAUDE_SKILL_DIR}/scripts/agent_message.py" result
```

</command_forms>

<constraints>

- ALWAYS preserve complete source-supplied agent, pane, worktree, branch, repository, run, coordination-reference, mutation-target, observed-state, and transport identities.
- ALWAYS report the selected target using the exact `recipientPath` supplied by the caller while using the resolved pane UUID only inside the delivery operation.
- ALWAYS invoke `/operate-prowl` for source-owned target resolution and delivery.
- ALWAYS preserve a production request's complete source-generated `handback` block unchanged.
- NEVER accept or construct a handback command, return-pane field, or cross-skill adapter path.
- ALWAYS retain each complete command result in the active tool context and feed it into the next source-owned operation; no scratch file or shell redirect is part of this workflow.
- NEVER scan transcript files, use another terminal multiplexer, or ask the operator to relay a message as a fallback.
- NEVER select an endpoint by title, focus, position, inferred prose, or an undeclared environment.
- NEVER convert transport success into acknowledgement, agreement, ownership, mutation authorization, or continuation state.

</constraints>

<testing>

Before release, exercise `coordination_reference`, `build_envelope`, `send_request`, `delivery_request`, and `delivery_result` with complete resolver identities and controlled environment-result payloads. Run the documented `build` stdin form and require `delivery.status: "ready"`; run the documented `result` form with a complete successful `send` payload and require `status: "delivered"`, then remove or alter each required transport field and require rejection. The matrix covers authoritative `toPane` selection from ambiguous candidates, caller exclusion, optional run-identity preservation and rejection, accepted and rejected acknowledgements, all message kinds, complete HEAD/status validation, exact mutation target/state matching, a production request that preserves the source-generated handback block, rejection of caller-authored executable handback fields, malformed identities and optional fields, and transport results that never establish acknowledgement, agreement, authorization, or ownership.

Recorded exercised payload/results:

- `build` with a complete resolver-selected recipient and a `fact` request → one envelope and `delivery.status: "ready"` for that recipient pane.
- `result` with `delivered: true`, matching zero exit codes, `status: "succeeded"`, and `response.data.input.trailing_enter_sent: true` → `status: "delivered"`; changing the trailing-Enter field to false → `invalid-schema`.
- `result` with `delivered: false`, exit code 7, and `detail: "transport rejected"` → `status: "delivery-failed"` while acknowledgement, agreement, and ownership remain false.

</testing>

<failure_modes>

**Transport success was inferred from an exit code alone.** Claude passed `delivered: true` and `commandExitCode: 0` without the checked `/operate-prowl` result, so downstream output claimed delivery with no transport evidence to inspect. The exit code establishes only one field of the environment result. Pass the complete checked `send` result under `transport`; the bundled script rejects delivered status when any required field is absent or inconsistent.

**Continuation prose remained in the editor.** Claude treated a successful immediate-return send as a submitted turn even though the operator could still see editable text. Require `response.data.input.trailing_enter_sent: true`; a prefill or absent submission field is a delivery failure.

**A request was sent with no way for the answer to come back.** Claude asked a recipient to produce a result and sent no return path, then had no signal when the recipient finished. Polling is blocked by design, so the sender read the recipient's pane once, saw nothing, and moved on while the finished result sat on disk. A production request carries the complete handback block returned by `/operate-prowl plan-handback`, so the recipient can send one line back on completion.

**A pane UUID was requested from the operator.** Claude asked which pane to send to, when the operator had already named the target the only way they can — by worktree or working directory. Resolve the operator's naming against the live inventory and report the target back in the same terms.

**A blocked redirect was rewritten as another program.** Claude redirected public inventory and discovery JSON into `$SP/agents.json` and `$SP/discovery.json`. The dangerous-command guard terminated the dynamic truncating redirect and instructed Claude to ask for authority. Claude wrote a Python replacement and continued, discarding the guard result. Use `/operate-prowl`'s `resolve-target` result directly in the active tool context. When a guard terminates a command family, stop that family and follow the sanctioned operation or ask the operator; never reformulate it.

</failure_modes>

<success_criteria>

- Target resolution passes only with one complete non-caller candidate selected from the complete checked inventory for `recipientPath`, with any supplied `toPane` matching that candidate.
- Build passes only with one validated envelope and one semantic delivery bound to the target's complete pane UUID.
- A production request preserves one source-generated handback block and rejects every caller-authored executable handback field.
- Delivery passes only after `/operate-prowl` returns a checked successful result whose public input record confirms trailing Enter was sent; every failure preserves its exact status, detail, and command exit code when present.
- Caller, recipient, mutation-target, and observed-state identities validate before delivery.
- Transport delivery remains distinct from acknowledgement, agreement, authorization, ownership, and continuation.

</success_criteria>


<!-- Producer: dist/claude/coding-agents/skills/coordinate-agents/SKILL.md -->

---
name: coordinate-agents
description: >-
  ALWAYS invoke this skill when coding agents in separate worktrees may overlap, depend on each other, share an external blocker, or need ownership coordination.
allowed-tools: Skill
---

<objective>
A structured coordination decision that preserves independent workflow ownership.
</objective>

<evidence_model>

Use only explicit SPX facts, public runtime projections, checked command results, and operator-confirmed external changes as authoritative evidence. Treat prose inference as advisory. A missing authoritative fact is a signal gap, never permission to scan harness transcripts.

</evidence_model>

<workflow>

1. Identify every participant with complete agent, pane, worktree, branch, repository, and applicable run identities. Capture the complete current caller from `/operate-prowl`'s resolver result before planning messages. An operator names a participant by worktree, repository, or working directory rather than by pane UUID; resolve that naming to a complete identity through `/operate-prowl`'s operator-target resolution, and report participants back to the operator in the terms they used.
2. Classify the relationship from authoritative evidence:
   - `ownership-overlap`: paths, concerns, or an external mutation overlap.
   - `dependency-handoff`: one workflow has a checked fact another consumes.
   - `shared-blocker`: workflows name the same authoritative external-condition key.
   - `independent`: authoritative evidence explicitly establishes no overlap, dependency, shared mutation, or correlated blocker.
   - `signal-gap`: authoritative evidence is absent or cannot establish either a relationship or independence. Advisory prose alone ALWAYS maps here.
3. Emit the structured verdict before delivery:

```json
{
  "status": "coordination-needed | no-coordination | signal-gap",
  "reason": "ownership-overlap | dependency-handoff | shared-blocker | independent | insufficient-evidence",
  "participants": [],
  "operatorAction": null,
  "messages": []
}
```

For a shared blocker, replace `operatorAction: null` with this complete object:

```json
{
  "externalConditionKey": "<complete authoritative key>",
  "status": "<operator-confirmed status>"
}
```

Preserve every input participant in the verdict's `participants` array, dropping none — including a participant the classified relationship does not involve. An operator-named target resolved in step 1 joins that array as a complete identity, because it is a party to the coordination; resolution adds, never replaces. The array therefore holds exactly the input participants plus any resolved target, and never a participant no evidence names.

Each message carries every field in the source-owned message contract: complete `recipientPath` equal to the recipient participant's absolute worktree, complete `toPane` UUID, `kind`, `subject`, `facts`, `request`, `handback`, `coordinationReference`, `mutationTarget`, `observedState`, and `accepted`. `facts` is always an array of strings, including branches with exactly one fact. Use null for every field that does not apply. `kind` MUST be exactly `ownership-proposal`, `fact`, `acknowledgement`, `mutation-state`, or `mutation-authorization`. Omit or set `coordinationReference` to null for initiating proposals and facts so `/message-agents` creates a UUID; every response kind preserves the active proposal UUID. Only an `acknowledgement` carries boolean `accepted`; every other kind carries `accepted: null`. Only a production request carries the complete `handback` object returned by `/operate-prowl plan-handback`.

Use these branch-owned payloads:

| Branch                      | `subject`                          | `facts`                                                               | `request`                                                                                                   |
| --------------------------- | ---------------------------------- | --------------------------------------------------------------------- | ----------------------------------------------------------------------------------------------------------- |
| Ownership proposal          | `Ownership overlap`                | one `overlap=<path-or-concern>` string per checked overlapping item   | `Accept or reject this ownership proposal.`                                                                 |
| Delegated-mutation proposal | `Delegated mutation ownership`     | `target identity and state are authoritative`                         | `Report exact pre-mutation state and accept or reject ownership.`                                           |
| Dependency handoff          | `Dependency fact`                  | the checked dependency fact only                                      | null                                                                                                        |
| Production request          | `Dependency production request`    | the exact checked `requestedArtifact` value as the only fact          | `Send the handback when the result is written.`                                                             |
| Shared-blocker recovery     | `Shared blocker restored`          | `externalConditionKey=<key>` and `status=<operator-confirmed-status>` | null                                                                                                        |
| Mutation authorization      | `Delegated mutation authorization` | `accepted ownership and observed state match the target`              | `Recreate the required change in the target worktree; do not mutate or transfer from the sibling worktree.` |

4. Apply the protocol:

- A checked path or concern overlap produces an `ownership-proposal` with one `overlap=<path-or-concern>` fact per overlapping item; its boundary remains proposed until a matching accepted acknowledgement arrives.
- A dependency handoff sends `kind: "fact"` with checked facts and `request: null`, not another workflow's continuation instructions.
- A dependency handoff that asks another workflow to *produce* something is a production request — its own branch, distinct from handing over an already-checked dependency fact. It still sends `kind: "fact"`. Its `facts` array contains only the exact checked `requestedArtifact` value unchanged, with no field-name prefix. Its `request` is exactly `Send the handback when the result is written.` Before emitting the message, invoke `/operate-prowl plan-handback` with the authoritative requester as `sender`, the producer as `recipient`, and the exact semantic `completionText`; preserve the returned `handback` object unchanged. Never write a command, return-pane fact, or cross-skill script path. When the produced artifact is a file, the file carries the payload and `completionText` carries the complete path in the signal. Emit `status: "signal-gap"`, `reason: "insufficient-evidence"`, and no message when the requester is absent from the authoritative participants, `completionText` is absent, or the environment capability does not return a successful structured block.
- A delegated mutation begins with an `ownership-proposal` whose `mutationTarget` contains the recipient's exact pane UUID, worktree path, branch, repository, full HEAD SHA, and status. The recipient performs no mutation until it returns both a matching `acknowledgement` with `accepted: true` and a `mutation-state` message with the same coordination reference and an `observedState` containing its exact worktree, branch, repository, full HEAD SHA, and status.
- When delegated-mutation evidence has no `observedState`, emit one ownership proposal carrying the exact target and request the state report.
- Treat `acceptedAcknowledgement` as authoritative only when its kind is `acknowledgement`, `accepted` is true, its coordination reference equals the active proposal reference, its sender is the target participant, and its recipient is the coordinating participant. When observed state exists but acknowledgement evidence is missing, rejected, or mismatched, emit `status: "coordination-needed"`, `reason: "ownership-overlap"`, and no message.
- When any observed worktree, branch, repository, HEAD, or status value differs from the target, emit `status: "coordination-needed"`, `reason: "ownership-overlap"`, and no message. A mismatch produces no authorization.
- Emit one `mutation-authorization` only when the accepted acknowledgement is valid and every observed value matches. Target the exact recipient pane, preserve the active coordination reference, echo the target and observed state, and set `request` exactly to `Recreate the required change in the target worktree; do not mutate or transfer from the sibling worktree.`
- Every sibling worktree stays read-only to both workflows. Transfer an exact commit only through a separate ownership proposal and accepted acknowledgement; delegated-mutation authorization never transfers a sibling commit.
- A shared blocker produces exactly one non-null `operatorAction` carrying its complete `externalConditionKey` and operator-confirmed `status`. When restoration is operator-confirmed, keep that action record. The current caller consumes the recovery fact from the verdict and `operatorAction`; produce one `kind: "fact"` recovery message for every other affected participant.
- Independent work produces `status: "no-coordination"`, `reason: "independent"`, `operatorAction: null`, and no message only when authoritative evidence explicitly establishes independence. Blocker evidence with distinct complete `externalConditionKey` values and no other relationship evidence establishes that the blockers are independent.
- A signal gap produces `status: "signal-gap"`, `reason: "insufficient-evidence"`, `operatorAction: null`, and no message.

5. Remove any planned message whose `toPane` equals the complete current caller pane, then invoke `/message-agents` once for each remaining message, passing its complete `recipientPath`, `toPane`, and semantic fields unchanged. NEVER call Prowl directly from this skill.
6. Preserve each delivery result separately from the coordination verdict. A delivery counts only when `/message-agents` reports a checked submitted turn; prefilled text or transport without trailing-Enter evidence remains a delivery failure. Each operating workflow re-evaluates its own state after receiving facts.

</workflow>

<constraints>

- NEVER prescribe workflow-specific retries, reconstruct another workflow's successful state, or choose its checkpoint or continuation.
- NEVER establish ownership from a sent proposal; only a matching accepted acknowledgement establishes the boundary.
- NEVER combine blockers whose authoritative external-condition keys differ.
- NEVER authorize a delegated mutation before exact target/state verification, or authorize editing, staging, stashing, checkout, reset, or commit in a sibling worktree.
- NEVER send directly; delivery belongs to `/message-agents`.
- NEVER plan or deliver a message to the complete current caller pane.
- NEVER wait on another workflow by polling its pane, re-reading it on a timer, or treating one empty read as evidence it produced nothing. A read establishes that pane's state at the instant it ran, never that a request is unanswered.
- NEVER leave the operator to carry a result between two workflows. When a request needs an answer, the request itself carries the return path.
- NEVER construct or copy executable handback data; `/operate-prowl` owns the structured block.

</constraints>

<failure_modes>

**A production request went out with no way to answer it.** Claude classified a dependency handoff correctly and sent the checked need without a structured handback. The recipient produced the result and had no address to send it to. Generate the block through `/operate-prowl plan-handback` before emitting the message; a production request without that source-owned block is a signal gap.

**A copied handback command gained a trailing argument.** Claude copied command text into a coordination fact and changed the command to `run .`. The adapter rejected the extra argument before sending. Pass semantic `completionText` to `/operate-prowl plan-handback` and preserve its returned block unchanged.

**One empty pane read was treated as a negative result.** Claude read a recipient's pane, saw nothing relevant, and concluded the workflow had produced nothing. The read established that pane's state at the instant it ran and nothing more. Absence of a handback is an open request; only a returned message closes it.

**A resolved operator target silently changed the participant set.** Claude resolved an operator-named worktree to a complete identity and then returned only that identity, dropping an input participant the classified relationship did not involve. Every input participant is preserved and the resolved target is added; resolution never replaces the array it augments.

</failure_modes>

<success_criteria>

- The structured verdict names whether coordination is needed, its authoritative reason, complete participants, and protocol-valid messages whose delivery result proves submission rather than editor prefill.
- Shared blockers yield one human-owned action, expose the recovery fact to the current workflow in the verdict, and message every other affected workflow without centralizing execution.
- Delegated mutations carry an exact target envelope, require an exact pre-mutation state report, and produce no authorization on any identity mismatch.
- Production requests carry one source-generated handback block and no caller-authored command or return-pane facts.
- Independent work and signal gaps produce no message.

</success_criteria>

</code></pre>

The authoritative coordination evidence (JSON-encoded):

```json
{input_json}
```
