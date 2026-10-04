# Issues: HDL

Known defects, contradictions and gaps in this node. Coordination note; not spec truth.

## Two review reference files over 100 lines carry no table of contents

`/skill-standards` `<progressive_disclosure>` requires a table of contents at the top of every reference file over 100 lines, so partial reads still see the full scope. `src/plugins/hdl/skills/review-systemverilog/references/systemverilog-idioms.md` (716 lines) and `src/plugins/hdl/skills/review-vhdl/references/vhdl-idioms.md` (472 lines) have none.

**Settlement condition.** Each file opens with a table of contents in the form its skill uses, listing every top-level section, and `instructions:skill-auditor` approves each affected skill afterward.
