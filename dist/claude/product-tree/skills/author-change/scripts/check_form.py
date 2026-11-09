#!/usr/bin/env python3
"""Run the form check that change-standards owns, from author-change's own entrypoint."""

from __future__ import annotations

import importlib.util
import pathlib
import sys

PROVIDER = pathlib.Path(__file__).resolve().parents[2] / "change-standards" / "scripts" / "form_check.py"


def main() -> int:
    spec = importlib.util.spec_from_file_location("form_check", PROVIDER)
    if spec is None or spec.loader is None:
        print(f"error: the form check is absent at {PROVIDER}; reinstall the product-tree plugin", file=sys.stderr)
        return 2
    module = importlib.util.module_from_spec(spec)
    sys.modules["form_check"] = module
    spec.loader.exec_module(module)
    return int(module.main(sys.argv[1:]))


if __name__ == "__main__":
    sys.exit(main())
