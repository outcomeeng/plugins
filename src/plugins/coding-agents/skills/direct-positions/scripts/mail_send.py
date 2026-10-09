"""Send one mail record from CobaltSpire and ring the recipient's doorbell.

Usage: python3 mail_send.py RECIPIENT KIND CORRELATION SUBJECT BODYFILE
Set NOBELL=1 to send without a doorbell. Prints: status, store id, bell result.
Run from anywhere; the mail adapter runs inside the mail project key.
"""

import json
import os
import subprocess
import sys
from pathlib import Path

KEY = "/Users/shz/Code/outcomeeng/changes/changes.git"
BASE = "/Users/shz/Code/outcomeeng/"
SENDER = "CobaltSpire"
PATHS = {
    "AmberHarbor": "methodology/worktrees/maintainer",
    "TealOwl": "methodology/worktrees/contributor",
    "SnowyHeron": "methodology/worktrees/worktrees/advisor",
    "RusticOwl": "spx/worktrees/maintainer",
    "BlueCrane": "spx/worktrees/orchestrator",
    "ScarletGoose": "plugins/worktrees/maintainer",
    "PeachFrog": "plugins/worktrees/orchestrator",
    "TealHeron": "plugins/worktrees/contributor",
    "SilverHeron": "plugins/worktrees/contributor-2",
    "SageMaple": "spx/worktrees/contributor",
}


def skill_script(skill: str, script: str) -> str:
    """The newest installed coding-agents release's script, found by version."""
    root = Path.home() / ".claude/plugins/cache/outcomeeng/coding-agents"
    versions = sorted(
        (p for p in root.iterdir() if p.is_dir()),
        key=lambda p: tuple(int(x) for x in p.name.split(".")),
    )
    return str(versions[-1] / "skills" / skill / "scripts" / script)


def run(script: str, request: dict, cwd: str | None = None, timeout: int = 90) -> dict:
    done = subprocess.run(
        ["python3", script, "run"],
        input=json.dumps(request),
        capture_output=True,
        text=True,
        cwd=cwd,
        timeout=timeout,
    )
    return json.loads(done.stdout)


def ring(recipient: str, mail_id: int) -> str:
    prowl = skill_script("operate-prowl", "prowl_environment.py")
    try:
        resolved = json.loads(
            subprocess.run(
                ["python3", prowl, "resolve-target"],
                input=json.dumps({"schemaVersion": 1, "path": BASE + PATHS[recipient]}),
                capture_output=True,
                text=True,
                timeout=90,
            ).stdout
        )
        template = resolved["candidates"][0]["sendRequestTemplate"]
        template["arguments"]["text"] = f"[{SENDER}] mail {mail_id}"
        sent = run(prowl, template)
        enter = sent["response"]["data"]["input"]["trailing_enter_sent"]
        return f"bell={enter}"
    except Exception as error:
        return f"bell=error:{str(error)[:80]}"


def main(argv: list[str]) -> int:
    recipient, kind, correlation, subject, body_file = argv[:5]
    record = {
        "schema": 1,
        "kind": kind,
        "correlation": correlation,
        "sender": SENDER,
        "recipient": recipient,
        "subject": subject,
        "body": Path(body_file).read_text(),
        "ackRequired": False,
    }
    result = run(
        skill_script("operate-agent-mail", "agent_mail.py"),
        {"schemaVersion": 1, "operation": "send", "arguments": {"record": record}},
        cwd=KEY,
    )
    mail_id = result.get("data", {}).get("record", {}).get("id")
    bell = ""
    if (
        result.get("status") == "succeeded"
        and mail_id
        and recipient in PATHS
        and not os.environ.get("NOBELL")
    ):
        bell = ring(recipient, mail_id)
    print(result.get("status"), mail_id, bell, result.get("detail", ""))
    return 0 if result.get("status") == "succeeded" else 1


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
