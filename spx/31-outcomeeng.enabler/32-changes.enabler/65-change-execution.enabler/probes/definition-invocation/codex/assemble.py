import glob
import hashlib
import json
import os
import sys

H = os.environ["CODEX_HOME"]
OUT = os.path.realpath(sys.argv[1])
DEF = os.path.realpath(sys.argv[2])


def confined(base, name):
    target = os.path.realpath(os.path.join(base, name))
    if os.path.commonpath([base, target]) != base:
        sys.exit("path escapes " + base + ": " + name)
    return target


def rollouts():
    out = {}
    for f in glob.glob(H + "/sessions/*/*/*/rollout-*.jsonl"):
        lines = [json.loads(line) for line in open(f)]
        meta = next(d["payload"] for d in lines if d["type"] == "session_meta")
        out[meta["id"]] = (f, meta, lines)
    return out


R = rollouts()
for n in [
    "executor",
    "author",
    "implementer",
    "tester",
    "verifier",
    "skill-author",
    "subagent-author",
]:
    role = "spec-tree_change-" + n
    stream = [json.loads(line) for line in open(f"run-{n}.jsonl")]
    parent_id = stream[0]["thread_id"]
    final = [
        e
        for e in stream
        if e["type"] == "item.completed" and e["item"]["type"] == "agent_message"
    ][-1]["item"]["text"]
    usage = [e for e in stream if e["type"] == "turn.completed"][-1]["usage"]
    plines = R[parent_id][2]
    spawns = [
        json.loads(d["payload"]["arguments"])
        for d in plines
        if d["payload"].get("type") == "function_call"
        and d["payload"].get("name") == "spawn_agent"
    ]
    for s in spawns:
        s["message"] = "<redacted: " + str(len(s["message"])) + " chars>"
    child = [v for v in R.values() if v[1].get("parent_thread_id") == parent_id]
    cf, cm, cl = child[0]
    ctx = next(d["payload"] for d in cl if d["type"] == "turn_context")
    path = confined(DEF, f"spec-tree_change-{n}.toml")
    first_line = [
        line
        for line in open(path).read().split("\n")
        if line.startswith("developer_instructions")
    ][0].split('"""')[1]
    dev = json.dumps(
        [
            d["payload"]
            for d in cl
            if d["payload"].get("type") == "message"
            and d["payload"].get("role") == "developer"
        ]
    )
    calls = [
        (
            d["payload"].get("name"),
            str(d["payload"].get("input") or d["payload"].get("arguments"))[:300],
        )
        for d in cl
        if d["payload"].get("type") in ("function_call", "custom_tool_call")
    ]
    res = {
        "definition": role,
        "emitted_definition": {
            "path": f"dist/codex/spec-tree/skills/spec-tree-plugin/agents/{role}.toml",
            "sha256": hashlib.sha256(open(path, "rb").read()).hexdigest(),
        },
        "discovery": {
            "artifact": "discovery.jsonl",
            "listed": role in open("discovery.jsonl").read(),
        },
        "loaded_configuration": {
            "child_thread_id": cm["id"],
            "agent_role": cm.get("agent_role"),
            "model": ctx.get("model"),
            "effort": ctx.get("effort"),
            "definition_instructions_in_child_context": first_line in dev,
        },
        "child_invocation": {
            "parent_thread_id": parent_id,
            "spawn_calls": spawns,
            "child_parent_thread_id": cm.get("parent_thread_id"),
            "depth": cm["source"]["subagent"]["thread_spawn"]["depth"],
            "child_tool_calls": [{"name": a, "arguments_prefix": b} for a, b in calls],
            "child_spawn_count": sum(1 for a, _ in calls if a == "spawn_agent"),
        },
        "returned_result": {"parent_final_message": final, "usage": usage},
    }
    json.dump(res, open(confined(OUT, f"{role}.result.json"), "w"), indent=2)
    print(
        role,
        "child_calls:",
        len(calls),
        [a for a, _ in calls][:6],
        "spawns",
        len(spawns),
    )
