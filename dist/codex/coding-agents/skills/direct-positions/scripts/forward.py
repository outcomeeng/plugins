import json, subprocess, sys, tempfile
from pathlib import Path

# usage: forward.py ID [ID ...]
# Forwards each record from CobaltSpire's inbox to the Record Reviewer SnowyHeron with its full body.
A = "/Users/shz/.claude/plugins/cache/outcomeeng/coding-agents/0.11.0/skills/operate-agent-mail/scripts/agent_mail.py"
MAIL_SEND = str(Path(__file__).with_name("mail_send.py"))
C = "/Users/shz/Code/outcomeeng/changes/changes.git"
req = {"schemaVersion": 1, "operation": "inbox", "arguments": {"agent": "CobaltSpire", "unreadOnly": False, "includeBodies": True, "limit": 300}}
d = json.loads(subprocess.run(["python3", A, "run"], input=json.dumps(req), capture_output=True, text=True, cwd=C).stdout)
recs = {r["id"]: r for r in d["data"]["records"]}
for i in map(int, sys.argv[1:]):
    r = recs.get(i)
    if not r:
        print(i, "not found")
        continue
    with tempfile.NamedTemporaryFile("w", suffix=".txt", delete=False) as f:
        f.write(f"Review request {i} from {r['sender']}. Send your verdict to {r['sender']}.\n\n{r['body']}")
    out = subprocess.run(["python3", MAIL_SEND, "SnowyHeron", "order", "change-format", f"Review {i} from {r['sender']}: {r['subject']}"[:180], f.name], capture_output=True, text=True, cwd=C)
    print(i, out.stdout.strip(), out.stderr.strip()[-200:])
