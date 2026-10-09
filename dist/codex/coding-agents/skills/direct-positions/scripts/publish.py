from pathlib import Path

B = Path("/Users/shz/Code/outcomeeng")
SRC = B / "methodology/.spx/director/expectations"
NAME = "position-expectations"
FRONT = (
    "---\n"
    f"name: {NAME}\n"
    "description: >-\n"
    "  Outcomes this position owns, outcomes it monitors, and artifacts it produces.\n"
    "  Read at each step boundary and after every compaction.\n"
    "---\n\n"
)

# worktree -> (source file, trees that receive the skill)
CLAUDE = (".claude",)
BOTH = (".claude", ".agents")
TARGETS = {
    "spx/worktrees/maintainer": ("maintainer.md", (".agents",)),
    "spx/worktrees/orchestrator": ("orchestrator.md", (".agents",)),
    "plugins/worktrees/maintainer": ("maintainer.md", CLAUDE),
    "plugins/worktrees/orchestrator": ("orchestrator.md", CLAUDE),
    "plugins/worktrees/contributor": ("contributor.md", CLAUDE),
    "plugins/worktrees/contributor-2": ("contributor.md", CLAUDE),
    "methodology/worktrees/maintainer": ("maintainer.md", (".agents",)),
    "methodology/worktrees/contributor": ("contributor.md", (".agents",)),
    "methodology/worktrees/worktrees/advisor": ("record-reviewer.md", (".agents",)),
}
POOLS = {
    "methodology": B / "methodology/methodology.git/info/exclude",
    "spx": B / "spx/spx.git/info/exclude",
    "plugins": B / "plugins/plugins.git/info/exclude",
}
LINES = (f".claude/skills/{NAME}/", f".agents/skills/{NAME}/")

for pool, path in POOLS.items():
    text = path.read_text() if path.exists() else ""
    have = text.splitlines()
    add = [l for l in LINES if l not in have]
    if add:
        sep = "" if text.endswith("\n") or not text else "\n"
        path.write_text(text + sep + "\n".join(add) + "\n")
    print("exclude", pool, "added" if add else "present")

for wt, (src, trees) in TARGETS.items():
    root = B / wt
    if not root.is_dir():
        print("MISSING", wt)
        continue
    body = (SRC / src).read_text()
    for tree in trees:
        d = root / tree / "skills" / NAME
        d.mkdir(parents=True, exist_ok=True)
        (d / "SKILL.md").write_text(FRONT + body)
        print("wrote", wt, tree, src)
