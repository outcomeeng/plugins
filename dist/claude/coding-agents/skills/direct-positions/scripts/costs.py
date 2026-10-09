import json, re, subprocess

P = "/Users/shz/.claude/plugins/cache/outcomeeng/coding-agents/0.11.0/skills/operate-prowl/scripts/prowl_environment.py"
H = "/Users/shz/.claude/plugins/cache/outcomeeng/coding-agents/0.11.0/skills/operate-herdr/scripts/herdr_environment.py"


def run(script, req):
    try:
        out = subprocess.run(["python3", script, "run"], input=json.dumps(req).encode(), capture_output=True, timeout=60).stdout
        return json.loads(out.decode("utf-8", "replace"))
    except Exception as e:
        return {"status": "error", "detail": str(e)}


def line(text):
    m = re.findall(r"\[([^\]]+)\][^\n]*?(\d+)%[^\n]*?\$([\d.,]+)[^\n]*?(\d+)m", text or "")
    cost = re.findall(r"\$([\d,]+\.\d+)", text or "")
    ctx = re.findall(r"tokens\)\s*(\d+)%", text or "")
    model = re.findall(r"\[(Opus[^\]]*|Sonnet[^\]]*|Haiku[^\]]*)\]", text or "")
    week = re.findall(r"7d:\s*(\d+)%", text or "")
    codex = re.findall(r"(\d+(?:\.\d+)?[KM]) used", text or "")
    return (model[-1] if model else ("codex" if codex else "?"), cost[-1] if cost else (codex[-1] if codex else "?"), ctx[-1] if ctx else "?", week[-1] if week else "?")


rows = []
a = run(P, {"schemaVersion": 1, "operation": "agents", "arguments": {}})
for ag in a.get("response", {}).get("data", {}).get("agents", []):
    t = run(P, {"schemaVersion": 1, "operation": "read", "arguments": {"pane": ag["id"], "last": 6}})
    text = t.get("response", {}).get("data", {}).get("text") if t.get("status") == "succeeded" else None
    rows.append(("prowl", ag["pane"]["title"].strip("◐◑✳ "), *line(text)))
inv = run(H, {"schemaVersion": 1, "operation": "inventory", "arguments": {}})
for ag in inv.get("agents", []):
    t = run(H, {"schemaVersion": 1, "operation": "read", "arguments": {"agent": ag["name"], "source": "recent", "lines": 8}})
    text = t.get("response", {}).get("output") if t.get("status") == "succeeded" else None
    rows.append(("herdr", ag["name"], *line(text)))


def dollars(r):
    try:
        return float(r[3].replace(",", ""))
    except ValueError:
        return -1


for r in sorted(rows, key=dollars, reverse=True):
    print(f"{r[0]:5} | {r[1][:34]:34} | {r[2][:22]:22} | ${r[3]:>9} | ctx {r[4]:>3}% | 7d {r[5]}%")
