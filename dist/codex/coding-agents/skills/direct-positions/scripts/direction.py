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


def _targets(config: Mapping[str, Any], envs: Environments) -> list[dict[str, Any]]:
    """Every pane the configuration directs: positions first, then executor groups."""
    inventories: dict[str, list[Pane]] = {}

    def panes_of(environment: str) -> list[Pane]:
        if environment not in inventories:
            inventories[environment] = envs.panes(environment)
        return inventories[environment]

    found: list[dict[str, Any]] = []
    for position in config["positions"]:
        panes = panes_of(position["environment"])
        pane = resolve_pane(panes, position["cwd"])
        detail = (
            None
            if pane
            else unresolved_pane_detail(
                panes, position["cwd"], position["name"], position["environment"]
            )
        )
        found.append(
            {
                "label": position["name"],
                "position": position,
                "pane": pane,
                "settings": position,
                "detail": detail,
            }
        )
    for group in config["executor_groups"]:
        for pane in panes_of(group["environment"]):
            excluded = any(pane.cwd.startswith(x) for x in group.get("exclusions", []))
            if pane.cwd.startswith(group["cwd_prefix"]) and not excluded:
                found.append(
                    {
                        "label": group["label"],
                        "position": None,
                        "pane": pane,
                        "settings": group,
                        "detail": None,
                    }
                )
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
            quiet_state, f"{pane.environment}:{pane.pane}", screen, now
        )
        position = target["position"] or {}
        reasons = guard_reasons(pane, screen, config["untouchable_panes"])
        observations.append(
            {
                "label": target["label"],
                "environment": pane.environment,
                "pane": pane.pane,
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
    sent: list[dict[str, Any]] = []
    skipped: list[dict[str, Any]] = []
    for target in _targets(config, envs):
        position = target["position"]
        pane: Pane | None = target["pane"]
        if position is None:
            continue
        if pane is None:
            skipped.append({"label": position["name"], "detail": target["detail"]})
            continue
        unread = _unread(mail, position["mail_name"])
        newest = max((int(r["id"]) for r in unread), default=0)
        if newest <= int(rungs.get(position["name"], 0)):
            continue
        screen = envs.read(pane)
        reasons = guard_reasons(pane, screen, config["untouchable_panes"])
        quiet = quiet_minutes(
            quiet_state, f"{pane.environment}:{pane.pane}", screen, now
        )
        idle = pane.status in ("idle", "done") or (pane.status is None and quiet >= 1)
        if reasons or not idle:
            skipped.append({"label": position["name"], "guards": reasons, "idle": idle})
            continue
        line = f"[{config['mail']['agent']}] mail {newest}"
        result = envs.prompt(pane, line)
        if result.get("status") == "succeeded":
            rungs[position["name"]] = newest
        sent.append(
            {"label": position["name"], "line": line, "status": result.get("status")}
        )
    write_state(state_dir, RUNGS_FILE, rungs)
    write_state(state_dir, QUIET_FILE, quiet_state)
    return {
        "pass": "doorbell",
        "authority": authority,
        "sent": sent,
        "skipped": skipped,
        "startDelaySeconds": config["doorbell_start_delay_seconds"],
        "rearmAfterSeconds": config["interval_seconds"],
    }


def controller_pass(config, envs, mail, now, authority: str | None) -> dict[str, Any]:
    if not authority:
        return {
            "pass": "controller",
            "status": "stopped",
            "detail": absent_authority("controller"),
        }
    observations = _observe(config, envs, now)
    actions: list[dict[str, Any]] = []
    for observation in observations:
        if observation.get("state") == "pane-unresolved":
            actions.append(
                {
                    "label": observation["label"],
                    "action": "skipped",
                    "detail": observation["detail"],
                }
            )
            continue
        guards = observation["guards"]
        if observation["stalled"] and not config["advisor"]:
            actions.append(
                {
                    "label": observation["label"],
                    "action": "forward",
                    "guards": guards,
                    "result": "unavailable",
                    "detail": _advisor_unset(config),
                }
            )
        elif observation["stalled"]:
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
            actions.append(
                {
                    "label": observation["label"],
                    "action": "forward",
                    "guards": guards,
                    "result": sent.get("status"),
                    **({"detail": sent["detail"]} if sent.get("detail") else {}),
                }
            )
        if guards:
            continue
        percent = observation["contextPercent"]
        if isinstance(percent, (int, float)) and percent > config["compact_at_percent"]:
            actions.append(
                {
                    "label": observation["label"],
                    "action": "compact-recommended",
                    "authority": authority,
                }
            )
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


def act(
    config, envs, target: str, operation: str, text: str | None, authority: str | None
) -> dict[str, Any]:
    if not authority:
        return {"status": "stopped", "detail": absent_authority("act")}
    if not target:
        labels = [p["name"] for p in config["positions"]] + [
            g["label"] for g in config["executor_groups"]
        ]
        return {
            "status": "stopped",
            "detail": f"act received no --target; pass --target with one of the labels {labels} "
            "or a pane id from the roster subcommand.",
        }
    if operation not in ACT_OPERATIONS:
        return {
            "status": "stopped",
            "detail": f"act received --operation {operation!r}; pass --operation "
            f"with one of {list(ACT_OPERATIONS)}.",
        }
    if operation == "prompt" and not text:
        return {
            "status": "stopped",
            "detail": f"act --operation prompt for {target!r} needs --text; pass "
            '--text "<the prompt to type>" or choose --operation compact, '
            "restart, or reload.",
        }
    targets = _targets(config, envs)
    matches = [
        t
        for t in targets
        if t["pane"] is not None and target in (t["label"], t["pane"].pane)
    ]
    if len(matches) != 1:
        available = [t["label"] for t in targets if t["pane"] is not None] + [
            t["pane"].pane for t in targets if t["pane"] is not None
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
            f"pane {pane.pane} is guarded by {reasons}. Its screen is quoted in "
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
    parser.add_argument("--body-file", help="send: a file holding the record body")
    return parser


def main(
    argv: Sequence[str] | None = None,
    *,
    stdout: TextIO | None = None,
    runtime: tuple[ModuleType, Environments] | None = None,
    clock: Callable[[], float] = now_seconds,
) -> int:
    out = sys.stdout if stdout is None else stdout
    args = _parser().parse_args(argv)
    try:
        mail, envs = _runtime() if runtime is None else runtime
        config = compose_configuration(common_directory(mail), args.position)
        if args.subcommand == "compose":
            result: dict[str, Any] = config
        elif args.subcommand == "roster":
            result = {
                "roster": [
                    {
                        "label": t["label"],
                        "pane": t["pane"].pane if t["pane"] else None,
                        "environment": t["pane"].environment if t["pane"] else None,
                    }
                    for t in _targets(config, envs)
                ]
            }
        elif args.subcommand == "monitor":
            result = monitor_pass(config, envs, clock())
        elif args.subcommand == "doorbell":
            result = doorbell_pass(config, envs, mail, clock(), args.authority)
        elif args.subcommand == "controller":
            result = controller_pass(config, envs, mail, clock(), args.authority)
        elif args.subcommand == "inbox":
            recipient = args.recipient or config["mail"]["agent"]
            if recipient is None:
                result = {
                    "status": "unavailable",
                    "detail": "inbox received no --recipient, and "
                    + _mail_agent_unset(config),
                }
            else:
                result = {"records": _unread(mail, recipient)}
        elif args.subcommand == "send" and not args.authority:
            result = {"status": "stopped", "detail": absent_authority("send")}
        elif args.subcommand == "send":
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
            try:
                body = (
                    Path(args.body_file).read_text(encoding="utf-8")
                    if args.body_file
                    else ""
                )
            except OSError as error:
                raise DirectionError(
                    f"send cannot read --body-file {args.body_file}: {error}; "
                    "write the body to a readable file first."
                ) from error
            result = {
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
        else:
            result = act(
                config, envs, args.target, args.operation, args.text, args.authority
            )
    except DirectionError as error:
        json.dump({"status": "stopped", "detail": str(error)}, out)
        out.write("\n")
        return 1
    json.dump(result, out, sort_keys=True, default=str)
    out.write("\n")
    return 1 if result.get("status") in ("stopped", "unavailable") else 0


if __name__ == "__main__":
    sys.exit(main())
