"""Place this plugin's agent definitions into a checkout's agent directory."""

import argparse
import json
import sys
from pathlib import Path

AGENTS_DIR = Path(__file__).resolve().parent.parent / "agents"
PLACEMENT_FILENAME = "placement.json"


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--checkout", type=Path, default=Path.cwd())
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args(argv)

    placement_file = AGENTS_DIR / PLACEMENT_FILENAME
    if not placement_file.is_file():
        print("no checkout placement applies for this plugin on this agent")
        return 0

    placement = json.loads(placement_file.read_text(encoding="utf-8"))
    prefix: str = placement["prefix"]
    destination = args.checkout / placement["directory"]
    shipped = {path.name: path for path in AGENTS_DIR.glob(f"{prefix}*")}
    placed = {path.name: path for path in destination.glob(f"{prefix}*")}

    stale = sorted(set(placed) - set(shipped))
    drifted = sorted(
        name
        for name, path in shipped.items()
        if name not in placed or placed[name].read_bytes() != path.read_bytes()
    )
    if args.check:
        for name in drifted + stale:
            print(f"drift: {name}")
        return 1 if drifted or stale else 0

    destination.mkdir(parents=True, exist_ok=True)
    for name in drifted:
        (destination / name).write_bytes(shipped[name].read_bytes())
    for name in stale:
        placed[name].unlink()
    print(f"placed {len(drifted)}, pruned {len(stale)} under {destination}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
