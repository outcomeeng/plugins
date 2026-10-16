#!/usr/bin/env python3
"""Run one bounded direction operation over the composed position configuration.

Every subcommand reads its configuration, performs one pass or one action,
writes JSON to stdout, and exits. No subcommand loops, waits, or outlives its
invocation; the skill re-arms the next pass.
"""

from __future__ import annotations

import argparse
import json
import sys
import tempfile
from pathlib import Path
from types import ModuleType
from typing import Any, Callable, Mapping, Sequence, TextIO

from direction_core import (
    ENVIRONMENT_HERDR,
    ENVIRONMENT_PROWL,
    OBSERVATIONS_FILE,
    QUIET_FILE,
    RUNGS_FILE,
    DirectionError,
    Environments,
    Pane,
    common_directory,
    compose_configuration,
    guard_reasons,
    invocation_checkout,
    load_sibling,
    now_seconds,
    quiet_minutes,
    read_state,
    resolve_pane,
    unresolved_pane_detail,
    write_state,
)

COMPACT_TEXT = "/compact"
RELOAD_TEXT = "/reload-plugins"
RESTART_TIMEOUT_MS = 60_000
MAIL_LIMIT = 100

ACT_OPERATIONS = ("prompt", "compact", "restart", "reload")


def absent_authority(subcommand: str) -> str:
    """The stop for an acting subcommand run without --authority."""
    return (
        f"{subcommand} was run without --authority, so no methodology chapter "
        "defines this action and no operator grant in the composed configuration "
        f"names it; run {subcommand} again with --authority <source> naming the "
        "methodology chapter or the operator grant with its bounds, or leave the "
        "action undone."
    )


def _runtime() -> tuple[ModuleType, Environments]:
    mail = load_sibling("operate-agent-mail", "agent_mail")
    herdr = load_sibling("operate-herdr", "herdr_environment")
    prowl = load_sibling("operate-prowl", "prowl_environment")
    runners = {
        ENVIRONMENT_HERDR: herdr.SubprocessRunner(),
        ENVIRONMENT_PROWL: prowl.SubprocessRunner(),
    }
    return mail, Environments(herdr, prowl, runners)


def _position_target(position: Mapping[str, Any], panes: list[Pane]) -> dict[str, Any]:
    pane = resolve_pane(panes, position["cwd"])
    detail = (
        None
        if pane
        else unresolved_pane_detail(
            panes, position["cwd"], position["name"], position["environment"]
        )
    )
    return {
        "label": position["name"],
        "position": position,
        "pane": pane,
        "settings": position,
        "detail": detail,
    }


def _group_targets(group: Mapping[str, Any], panes: list[Pane]) -> list[dict[str, Any]]:
    exclusions = group.get("exclusions", [])
    return [
        {
            "label": group["label"],
            "position": None,
            "pane": pane,
            "settings": group,
            "detail": None,
        }
        for pane in panes
        if pane.cwd.startswith(group["cwd_prefix"])
        and not any(pane.cwd.startswith(x) for x in exclusions)
    ]


def _targets(config: Mapping[str, Any], envs: Environments) -> list[dict[str, Any]]:
    """Every pane the configuration directs: positions first, then executor groups."""
    inventories: dict[str, list[Pane]] = {}

    def panes_of(environment: str) -> list[Pane]:
        if environment not in inventories:
            inventories[environment] = envs.panes(environment)
        return inventories[environment]

    found = [
        _position_target(position, panes_of(position["environment"]))
        for position in config["positions"]
    ]
    for group in config["executor_groups"]:
        found.extend(_group_targets(group, panes_of(group["environment"])))
    return found


def _observe(
    config: Mapping[str, Any], envs: Environments, now: float
) -> list[dict[str, Any]]:
    state_dir = Path(config["stateDirectory"])
    quiet_state = read_state(state_dir, QUIET_FILE)
    observations: list[dict[str, Any]] = []
    for target in _targets(config, envs):
        pane: Pane | None = target["pane"]
        if pane is None:
            observations.append(
                {
                    "label": target["label"],
                    "state": "pane-unresolved",
                    "detail": target["detail"],
                }
            )
            continue
        screen = envs.read(pane)
        quiet = quiet_minutes(
            quiet_state, f"{pane.environment}:{pane.pane_id}", screen, now
        )
        position = target["position"] or {}
        reasons = guard_reasons(pane, screen, config["untouchable_panes"])
        observations.append(
            {
                "label": target["label"],
                "environment": pane.environment,
                "pane": pane.pane_id,
                "agentStatus": pane.status,
                "quietMinutes": quiet,
                "stalled": quiet >= position.get("stall_minutes", float("inf")),
                "guards": reasons,
                "screen": screen if reasons else None,
                "lastPrompt": "unavailable",
                "contextPercent": "unavailable",
            }
        )
    write_state(state_dir, QUIET_FILE, quiet_state)
    write_state(state_dir, OBSERVATIONS_FILE, {"at": now, "observations": observations})
    return observations


def _unread(mail: ModuleType, mail_name: str) -> list[dict[str, Any]]:
    request = {
        "schemaVersion": mail.SCHEMA_VERSION,
        "operation": "inbox",
        "arguments": {"agent": mail_name, "unreadOnly": True, "limit": MAIL_LIMIT},
    }
    result = mail.execute(request, mail.SubprocessRunner())
    if result["status"] != "succeeded":
        raise DirectionError(
            f"mail inbox for {mail_name} failed with status {result.get('status')!r}: "
            f"{result.get('detail')}; confirm the mail name is registered through "
            "coding-agents:operate-agent-mail."
        )
    return result["data"]["records"]


def _mail_agent_unset(config: Mapping[str, Any]) -> str:
    return (
        "mail.agent is unset, so no mail operation is available; set mail.agent "
        f"in the [mail] table of {config['overrideFile']['path']}."
    )


def _advisor_unset(config: Mapping[str, Any]) -> str:
    return (
        "advisor is unset, so forwarding is unavailable; set the advisor key to "
        f"the advisor's mail name in the front matter of {config['overrideFile']['path']}."
    )


def _send_mail(
    mail: ModuleType,
    config: Mapping[str, Any],
    recipient: str,
    kind: str,
    correlation: str,
    subject: str,
    body: str,
) -> dict[str, Any]:
    sender = config["mail"]["agent"]
    if sender is None:
        return {"status": "unavailable", "detail": _mail_agent_unset(config)}
    record = mail.message_record(
        kind=kind,
        correlation=correlation,
        sender=sender,
        recipient=recipient,
        subject=subject,
        body=body,
        ack_required=False,
    )
    request = {
        "schemaVersion": mail.SCHEMA_VERSION,
        "operation": "send",
        "arguments": {"record": record},
    }
    return mail.execute(request, mail.SubprocessRunner())


def monitor_pass(config, envs, now) -> dict[str, Any]:
    observations = _observe(config, envs, now)
    flagged = [o for o in observations if o.get("stalled") or o.get("guards")]
    return {
        "pass": "monitor",
        "observations": observations,
        "flagged": [o["label"] for o in flagged],
        "rearmAfterSeconds": config["interval_seconds"],
    }


def _ring(
    target: Mapping[str, Any],
    config: Mapping[str, Any],
    envs: Environments,
    mail: ModuleType,
    rungs: dict[str, Any],
    quiet_state: dict[str, Any],
    now: float,
) -> tuple[str, dict[str, Any]] | None:
    """One doorbell decision for one position: ("sent" | "skipped", entry), or None."""
    position = target["position"]
    pane: Pane | None = target["pane"]
    if pane is None:
        return "skipped", {"label": position["name"], "detail": target["detail"]}
    unread = _unread(mail, position["mail_name"])
    newest = max((int(r["id"]) for r in unread), default=0)
    if newest <= int(rungs.get(position["name"], 0)):
        return None
    screen = envs.read(pane)
    reasons = guard_reasons(pane, screen, config["untouchable_panes"])
    quiet = quiet_minutes(
        quiet_state, f"{pane.environment}:{pane.pane_id}", screen, now
    )
    idle = pane.status in ("idle", "done") or (pane.status is None and quiet >= 1)
    if reasons or not idle:
        return "skipped", {"label": position["name"], "guards": reasons, "idle": idle}
    line = f"[{config['mail']['agent']}] mail {newest}"
    result = envs.prompt(pane, line)
    if result.get("status") == "succeeded":
        rungs[position["name"]] = newest
    return "sent", {
        "label": position["name"],
        "line": line,
        "status": result.get("status"),
    }


def doorbell_pass(config, envs, mail, now, authority: str | None) -> dict[str, Any]:
    if not authority:
        return {
            "pass": "doorbell",
            "status": "stopped",
            "detail": absent_authority("doorbell"),
        }
    if config["mail"]["agent"] is None:
        return {
            "pass": "doorbell",
            "status": "unavailable",
            "detail": _mail_agent_unset(config),
        }
    state_dir = Path(config["stateDirectory"])
    rungs = read_state(state_dir, RUNGS_FILE)
    quiet_state = read_state(state_dir, QUIET_FILE)
    entries: dict[str, list[dict[str, Any]]] = {"sent": [], "skipped": []}
    for target in _targets(config, envs):
        if target["position"] is None:
            continue
        decision = _ring(target, config, envs, mail, rungs, quiet_state, now)
        if decision:
            entries[decision[0]].append(decision[1])
    write_state(state_dir, RUNGS_FILE, rungs)
    write_state(state_dir, QUIET_FILE, quiet_state)
    return {
        "pass": "doorbell",
        "authority": authority,
        "sent": entries["sent"],
        "skipped": entries["skipped"],
        "startDelaySeconds": config["doorbell_start_delay_seconds"],
        "rearmAfterSeconds": config["interval_seconds"],
    }


def _forward_stalled(
    observation: Mapping[str, Any], config: Mapping[str, Any], mail: ModuleType
) -> dict[str, Any]:
    """The forwarding action for one stalled position."""
    guards = observation["guards"]
    action: dict[str, Any] = {
        "label": observation["label"],
        "action": "forward",
        "guards": guards,
    }
    if not config["advisor"]:
        return {**action, "result": "unavailable", "detail": _advisor_unset(config)}
    body = (
        observation["screen"]
        if guards and observation["screen"]
        else f"{observation['label']} has been quiet."
    )
    sent = _send_mail(
        mail,
        config,
        config["advisor"],
        "question",
        f"stall-{observation['label']}",
        f"{observation['label']} is stalled",
        body,
    )
    action["result"] = sent.get("status")
    if sent.get("detail"):
        action["detail"] = sent["detail"]
    return action


def _controller_actions(
    observation: Mapping[str, Any],
    config: Mapping[str, Any],
    mail: ModuleType,
    authority: str,
) -> list[dict[str, Any]]:
    """Every action the controller reports for one observed position."""
    if observation.get("state") == "pane-unresolved":
        return [
            {
                "label": observation["label"],
                "action": "skipped",
                "detail": observation["detail"],
            }
        ]
    actions: list[dict[str, Any]] = []
    if observation["stalled"]:
        actions.append(_forward_stalled(observation, config, mail))
    percent = observation["contextPercent"]
    over = isinstance(percent, (int, float)) and percent > config["compact_at_percent"]
    if over and not observation["guards"]:
        actions.append(
            {
                "label": observation["label"],
                "action": "compact-recommended",
                "authority": authority,
            }
        )
    return actions


def controller_pass(config, envs, mail, now, authority: str | None) -> dict[str, Any]:
    if not authority:
        return {
            "pass": "controller",
            "status": "stopped",
            "detail": absent_authority("controller"),
        }
    actions: list[dict[str, Any]] = []
    for observation in _observe(config, envs, now):
        actions.extend(_controller_actions(observation, config, mail, authority))
    return {
        "pass": "controller",
        "authority": authority,
        "reportOnly": (
            "The controller forwards a stalled position's question to the advisor "
            "and reports compact-recommended positions and the configured pace; it "
            "compacts and paces nothing. Run act --operation compact for each "
            "recommended position."
        ),
        "actions": actions,
        "pace": config["pace"],
        "rearmAfterSeconds": config["interval_seconds"],
    }


def _act_stop(config, target: str, operation: str, text: str | None) -> str | None:
    """The detail of the stop an act request's arguments raise, or None."""
    if not target:
        labels = [p["name"] for p in config["positions"]] + [
            g["label"] for g in config["executor_groups"]
        ]
        return (
            f"act received no --target; pass --target with one of the labels {labels} "
            "or a pane id from the roster subcommand."
        )
    if operation not in ACT_OPERATIONS:
        return (
            f"act received --operation {operation!r}; pass --operation "
            f"with one of {list(ACT_OPERATIONS)}."
        )
    if operation == "prompt" and not text:
        return (
            f"act --operation prompt for {target!r} needs --text; pass "
            '--text "<the prompt to type>" or choose --operation compact, '
            "restart, or reload."
        )
    return None


def act(
    config, envs, target: str, operation: str, text: str | None, authority: str | None
) -> dict[str, Any]:
    if not authority:
        return {"status": "stopped", "detail": absent_authority("act")}
    stop = _act_stop(config, target, operation, text)
    if stop:
        return {"status": "stopped", "detail": stop}
    targets = _targets(config, envs)
    matches = [
        t
        for t in targets
        if t["pane"] is not None and target in (t["label"], t["pane"].pane_id)
    ]
    if len(matches) != 1:
        available = [t["label"] for t in targets if t["pane"] is not None] + [
            t["pane"].pane_id for t in targets if t["pane"] is not None
        ]
        unresolved = [t["detail"] for t in targets if t["detail"]]
        return {
            "status": "stopped",
            "detail": f"act --target {target!r} names {len(matches)} panes; pass "
            f"exactly one of {available} (a position label or a pane id)."
            + (f" Unresolved positions: {unresolved}." if unresolved else ""),
        }
    pane: Pane = matches[0]["pane"]
    screen = envs.read(pane)
    reasons = guard_reasons(pane, screen, config["untouchable_panes"])
    if reasons:
        return {
            "status": "stopped",
            "guards": reasons,
            "screen": screen,
            "detail": f"act --target {target!r} --operation {operation} sent nothing: "
            f"pane {pane.pane_id} is guarded by {reasons}. Its screen is quoted in "
            "this result. A question-or-approval-screen pane waits for its own "
            "answer; an operator-prompt pane waits for the operator; an "
            "untouchable pane stays untouched until the operator removes it from "
            f"untouchable_panes in {config['overrideFile']['path']}.",
        }
    if operation == "restart":
        result = envs.restart(pane, RESTART_TIMEOUT_MS)
    else:
        wording = {"prompt": text, "compact": COMPACT_TEXT, "reload": RELOAD_TEXT}[
            operation
        ]
        result = envs.prompt(pane, wording)
    outcome: dict[str, Any] = {
        "status": result.get("status"),
        "operation": operation,
        "authority": authority,
        "result": result,
    }
    if result.get("status") != "succeeded" and result.get("detail"):
        outcome["detail"] = result["detail"]
    return outcome


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="direction")
    parser.add_argument(
        "subcommand",
        choices=[
            "compose",
            "roster",
            "monitor",
            "doorbell",
            "controller",
            "inbox",
            "send",
            "act",
        ],
    )
    parser.add_argument(
        "--position", required=True, help="the directing position's display name"
    )
    parser.add_argument("--target", help="act: a position name or pane id")
    parser.add_argument("--operation", choices=ACT_OPERATIONS)
    parser.add_argument("--text")
    parser.add_argument(
        "--authority",
        help="doorbell, controller, send, act: the methodology chapter or operator grant",
    )
    parser.add_argument("--recipient")
    parser.add_argument("--kind", default="fact")
    parser.add_argument("--correlation")
    parser.add_argument("--subject")
    parser.add_argument(
        "--body-file",
        help="send: a file holding the record body, inside --scratch-directory",
    )
    parser.add_argument(
        "--scratch-directory",
        help="send: the directory --body-file must resolve inside; "
        "defaults to the process temporary directory",
    )
    return parser


def read_body_file(
    body_file: str | None, scratch_directory: str | None
) -> tuple[str, dict[str, Any] | None]:
    """The body text, or an explicit rejection result when the path leaves the scratch directory."""
    if not body_file:
        return "", None
    root = Path(scratch_directory or tempfile.gettempdir()).resolve()
    resolved = (root / body_file).resolve()
    if not resolved.is_relative_to(root):
        return "", {
            "status": "stopped",
            "rejectedPath": body_file,
            "resolvedPath": str(resolved),
            "scratchDirectory": str(root),
            "detail": f"send --body-file {body_file} resolves to {resolved}, "
            f"outside the scratch directory {root}; write the body to a file "
            "inside that directory and pass its path.",
        }
    try:
        return resolved.read_text(encoding="utf-8"), None
    except OSError as error:
        raise DirectionError(
            f"send cannot read --body-file {body_file}: {error}; "
            "write the body to a readable file first."
        ) from error


def _send(args, config, mail) -> dict[str, Any]:
    if not args.authority:
        return {"status": "stopped", "detail": absent_authority("send")}
    missing = [
        f"--{name}"
        for name in ("recipient", "subject", "correlation")
        if not getattr(args, name)
    ]
    if missing:
        raise DirectionError(
            f"send needs {missing}; pass each with a value, and "
            "--body-file for the record body."
        )
    body, rejection = read_body_file(args.body_file, args.scratch_directory)
    if rejection:
        return rejection
    return {
        **_send_mail(
            mail,
            config,
            args.recipient,
            args.kind,
            args.correlation,
            args.subject,
            body,
        ),
        "authority": args.authority,
    }


def _inbox(args, config, mail) -> dict[str, Any]:
    recipient = args.recipient or config["mail"]["agent"]
    if recipient is None:
        return {
            "status": "unavailable",
            "detail": "inbox received no --recipient, and " + _mail_agent_unset(config),
        }
    return {"records": _unread(mail, recipient)}


def _roster(config, envs) -> dict[str, Any]:
    return {
        "roster": [
            {
                "label": t["label"],
                "pane": t["pane"].pane_id if t["pane"] else None,
                "environment": t["pane"].environment if t["pane"] else None,
            }
            for t in _targets(config, envs)
        ]
    }


def _dispatch(args, config, envs, mail, clock) -> dict[str, Any]:
    handlers: dict[str, Callable[[], dict[str, Any]]] = {
        "compose": lambda: dict(config),
        "roster": lambda: _roster(config, envs),
        "monitor": lambda: monitor_pass(config, envs, clock()),
        "doorbell": lambda: doorbell_pass(config, envs, mail, clock(), args.authority),
        "controller": lambda: controller_pass(
            config, envs, mail, clock(), args.authority
        ),
        "inbox": lambda: _inbox(args, config, mail),
        "send": lambda: _send(args, config, mail),
        "act": lambda: act(
            config, envs, args.target, args.operation, args.text, args.authority
        ),
    }
    return handlers[args.subcommand]()


def main(
    argv: Sequence[str] | None = None,
    *,
    stdout: TextIO | None = None,
    runtime: tuple[ModuleType, Environments] | None = None,
    clock: Callable[[], float] = now_seconds,
    checkout: Path | None = None,
) -> int:
    out = sys.stdout if stdout is None else stdout
    args = _parser().parse_args(argv)
    try:
        mail, envs = _runtime() if runtime is None else runtime
        config = compose_configuration(
            common_directory(mail),
            invocation_checkout() if checkout is None else checkout,
            args.position,
        )
        result = _dispatch(args, config, envs, mail, clock)
    except DirectionError as error:
        json.dump({"status": "stopped", "detail": str(error)}, out)
        out.write("\n")
        return 1
    json.dump(result, out, sort_keys=True, default=str)
    out.write("\n")
    return 1 if result.get("status") in ("stopped", "unavailable") else 0


if __name__ == "__main__":
    sys.exit(main())
