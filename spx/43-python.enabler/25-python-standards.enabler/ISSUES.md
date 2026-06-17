# Issues: Python Standards

## 1. Python skills predate current develop naming rules

The Python plugin's skill names predate the current develop naming rules.

Required handling: Any material change to a Python skill implies renaming all
skills in the entire Python plugin to match the latest develop rules. The rename
is a breaking change across every `/skill` invocation path, `require_skill`
directive, agent `skills:` field, catalog entry, and cross-reference in that
plugin, so it moves as part of the first material Python skill change.

Surfaced by the skill auditor during the Python-standards content hardening.
