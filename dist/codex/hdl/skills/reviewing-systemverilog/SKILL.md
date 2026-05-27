---
name: reviewing-systemverilog
description: >-
  ALWAYS invoke this skill when reviewing SystemVerilog or Verilog code for idiomatic style,
  synthesizability, or best practices. NEVER review SystemVerilog or Verilog without this skill.
---

<objective>
Review hand-written SystemVerilog (IEEE 1800-2017) through the lens of an experienced FPGA engineer targeting AMD Vivado and Altera Quartus Prime. Produce prioritized findings covering type discipline, always-block usage, naming conventions, and synthesizability. Flag legacy Verilog-2001 patterns as style findings.

</objective>

<quick_start>
Invoke: `/reviewing-systemverilog`

Provide the SystemVerilog files you want reviewed (design files, packages, interfaces, testbenches, or any combination). The skill walks through a structured review:

1. **Type & Package Review** - `logic` usage, enums, structs, packages, parameterization
2. **Always-Block & FSM Review** - `always_ff`/`always_comb`, blocking vs non-blocking, FSM patterns
3. **Structural & Style Review** - Port declarations, instantiation, naming conventions
4. **Synthesizability Review** - Latch detection, width mismatches, tool compatibility
5. **Findings Report** - Prioritized improvements with idiomatic alternatives

</quick_start>

<essential_principles>

**logic everywhere.** `wire` and `reg` are legacy. `logic` is the unified type — it works in all contexts. Only use `wire` for multi-driver nets (tri-state buses).

**always_ff and always_comb, never always @.** `always_ff` enforces sequential semantics. `always_comb` enforces combinational semantics and auto-infers the sensitivity list. `always @(posedge clk)` and `always @(*)` are legacy Verilog-2001.

**unique case, not bare case.** `unique case` tells the synthesizer all cases are covered and mutually exclusive. `priority case` when first-match priority encoding is intended. Bare `case` communicates nothing about designer intent.

**Non-blocking (<=) in always_ff, blocking (=) in always_comb.** Mixing them up causes simulation/synthesis mismatch. `always_ff` enforces this; `always @(posedge clk)` does not.

**ANSI-style ports, named connections.** Module ports declared in the header, not in a separate body. Instantiations use `.port_name(signal)`, never positional.

**Packages for shared types.** Enums, structs, typedefs, constants, and functions belong in packages. No `` `define `` macros for things that can be `parameter` or `localparam`.

</essential_principles>

<intake>
What would you like reviewed?

Provide any combination of:

- **Design files** (.sv, .v) - Modules, always blocks, instantiations
- **Package files** (.sv) - Type definitions, constants, functions
- **Interface files** (.sv) - Interface and modport definitions
- **Testbench files** (.sv) - Stimulus, assertions, coverage
- **Constraint files** (.xdc, .sdc) - Timing and placement constraints (for context)

You can provide file paths, paste code, or point to a directory.

**Wait for the user to provide files before proceeding.**

</intake>

<routing>
After the user provides files, execute the review workflow:

Read `${SKILL_DIR}/references/systemverilog-idioms.md` first, then follow `${SKILL_DIR}/workflows/systemverilog-review.md` exactly.

| User Provides   | Reference to Read                                 | Additional Context                       |
| --------------- | ------------------------------------------------- | ---------------------------------------- |
| Design files    | `${SKILL_DIR}/references/systemverilog-idioms.md` | Full review against all idiom categories |
| Package files   | `${SKILL_DIR}/references/systemverilog-idioms.md` | Focus on type discipline, naming         |
| Interface files | `${SKILL_DIR}/references/systemverilog-idioms.md` | Focus on modport, parameterization       |
| Testbench files | `${SKILL_DIR}/references/systemverilog-idioms.md` | Testbench-specific idioms apply          |
| Mixed           | `${SKILL_DIR}/references/systemverilog-idioms.md` | Review each file in its appropriate mode |

</routing>

<reference_index>

| File                                              | Purpose                                                        |
| ------------------------------------------------- | -------------------------------------------------------------- |
| `${SKILL_DIR}/references/systemverilog-idioms.md` | Comprehensive idiomatic SystemVerilog IEEE 1800-2017 reference |
| `${SKILL_DIR}/workflows/systemverilog-review.md`  | Step-by-step review procedure with finding format              |

</reference_index>

<success_criteria>
Review is complete when:

- [ ] Every file reviewed against idiomatic SystemVerilog standards
- [ ] Findings are specific: file, line, what, why, idiomatic alternative
- [ ] Findings are prioritized: P0 (incorrect hardware), P1 (quality/maintainability), P2 (style)
- [ ] Legacy Verilog-2001 patterns flagged
- [ ] Latch and blocking/non-blocking issues identified
- [ ] Naming convention deviations noted
- [ ] Summary table of all findings delivered

</success_criteria>
