---
name: reviewing-vhdl
description: >-
  ALWAYS invoke this skill when reviewing VHDL code for idiomatic style, synthesizability,
  or best practices. NEVER review VHDL without this skill.
---

<objective>
Review hand-written VHDL through the lens of an experienced FPGA/ASIC engineer who writes idiomatic, synthesizable VHDL-2008. Produce prioritized findings covering library usage, type discipline, process patterns, naming conventions, and synthesizability.

</objective>

<quick_start>
Invoke: `/reviewing-vhdl`

Provide the VHDL files you want reviewed (design files, packages, testbenches, or any combination). The skill walks through a structured review:

1. **Library & Type Review** - IEEE library usage, type discipline, package organization
2. **Process & Structural Review** - Process patterns, FSMs, entity/architecture idioms
3. **Synthesizability & Style Review** - Latch detection, naming, readability
4. **Findings Report** - Prioritized improvements with idiomatic alternatives

</quick_start>

<essential_principles>

**ieee.numeric_std is the only arithmetic library.** `std_logic_arith`, `std_logic_unsigned`, and `std_logic_signed` are Synopsys packages, not IEEE standard. Their presence is always a finding.

**std_ulogic over std_logic for single-driver signals.** `std_logic` is resolved (supports multiple drivers). Most signals have one driver. Use `std_ulogic` / `std_ulogic_vector` unless multi-driver resolution is required.

**Named association, always.** Positional port maps and generic maps are fragile and unreadable. Named association is non-negotiable.

**Complete assignments prevent latches.** Every branch of an `if` or `case` must assign every signal that any branch assigns. Missing assignments infer latches in synthesis.

**rising_edge() over 'event.** `clk'event and clk = '1'` fails on transitions from `'X'` to `'1'`. `rising_edge(clk)` is correct.

**Synchronous reset in the clocked process.** Asynchronous resets require careful CDC handling and complicate timing analysis. Prefer synchronous unless the target fabric demands otherwise.

</essential_principles>

<intake>
What would you like reviewed?

Provide any combination of:

- **Design files** (.vhd) - Entities, architectures, component declarations
- **Package files** (.vhd) - Type definitions, constants, functions
- **Testbench files** (.vhd) - Stimulus generation, checking logic
- **Constraint files** (.xdc, .sdc) - Timing and placement constraints (for context)

You can provide file paths, paste code, or point to a directory.

**Wait for the user to provide files before proceeding.**

</intake>

<routing>
After the user provides files, execute the review workflow:

Read `${SKILL_DIR}/references/vhdl-idioms.md` first, then follow `${SKILL_DIR}/workflows/vhdl-review.md` exactly.

| User Provides   | Reference to Read                        | Additional Context                       |
| --------------- | ---------------------------------------- | ---------------------------------------- |
| Design files    | `${SKILL_DIR}/references/vhdl-idioms.md` | Full review against all idiom categories |
| Package files   | `${SKILL_DIR}/references/vhdl-idioms.md` | Focus on type discipline, naming         |
| Testbench files | `${SKILL_DIR}/references/vhdl-idioms.md` | Testbench-specific idioms apply          |
| Mixed           | `${SKILL_DIR}/references/vhdl-idioms.md` | Review each file in its appropriate mode |

</routing>

<reference_index>

| File                                     | Purpose                                           |
| ---------------------------------------- | ------------------------------------------------- |
| `${SKILL_DIR}/references/vhdl-idioms.md` | Comprehensive idiomatic VHDL-2008 reference       |
| `${SKILL_DIR}/workflows/vhdl-review.md`  | Step-by-step review procedure with finding format |

</reference_index>

<success_criteria>
Review is complete when:

- [ ] Every file reviewed against idiomatic VHDL standards
- [ ] Findings are specific: file, line, what, why, idiomatic alternative
- [ ] Findings are prioritized: P0 (incorrect hardware), P1 (quality/maintainability), P2 (style)
- [ ] Non-standard library usage flagged
- [ ] Latch and sensitivity-list issues identified
- [ ] Naming convention deviations noted
- [ ] Summary table of all findings delivered

</success_criteria>
