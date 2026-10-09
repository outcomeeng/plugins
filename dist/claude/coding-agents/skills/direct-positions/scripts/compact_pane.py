import json, re, subprocess, sys, time

# usage: compact_pane.py PANE RESUME_TEXT
# Sends /compact to an idle Claude pane unless a compaction is already under way,
# waits for the status line's context to drop by 30 points (or below 10%) after it sent /compact,
# then sends the resume line. A pane under 60% is refused; a fresh pane never gets the resume line.
P = "/Users/shz/.claude/plugins/cache/outcomeeng/coding-agents/0.11.0/skills/operate-prowl/scripts/prowl_environment.py"
pane, resume = sys.argv[1], sys.argv[2]


def run(req):
    try:
        out = subprocess.run(["python3", P, "run"], input=json.dumps(req).encode(), capture_output=True, timeout=60).stdout
        return json.loads(out.decode("utf-8", "replace"))
    except Exception as e:
        return {"status": "error", "detail": str(e)}


def read():
    d = run({"schemaVersion": 1, "operation": "read", "arguments": {"pane": pane, "last": 14}})
    return d["response"]["data"]["text"] if d.get("status") == "succeeded" else None


def context(text):
    m = re.findall(r"\(\s*[\d.]+\s*[kKmM]?\s*/\s*[\d.]+\s*[kKmM]?\s*tokens\s*\)\s*(\d{1,3})\s*%", text)
    return int(m[-1]) if m else None


def send(text):
    return run({"schemaVersion": 1, "operation": "send", "arguments": {"pane": pane, "text": text, "noWait": True}}).get("status")


deadline = time.time() + 900
sent = False
start = None
while time.time() < deadline:
    t = read()
    if t is None:
        time.sleep(15)
        continue
    c = context(t)
    if start is None and c is not None:
        start = c
    dropped = c is not None and start is not None and (start - c >= 30 or c < 10)
    if sent and dropped and "Compacting conversation" not in t:
        time.sleep(5)
        print("compacted to", c, "% ; resume:", send(resume))
        sys.exit(0)
    if "Compacting conversation" in t or "/compact" in t:
        sent = True
    elif not sent:
        if c is None or c < 60:
            print("context", c, "% is not high; no /compact sent")
            sys.exit(2)
        print("send /compact:", send("/compact"))
        sent = True
    time.sleep(15)
print("timed out; last context", c if "c" in dir() else None)
sys.exit(1)
