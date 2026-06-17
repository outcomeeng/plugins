<required_reading>
Read `${SKILL_DIR}/references/vhdl-idioms.md` before starting the review. This is the authoritative reference for all idiomatic VHDL patterns.

</required_reading>

<process>

<step_1>

**Library & Type Review**

Examine each file's library/use clauses and type usage:

**Libraries**:

- Flag any use of `std_logic_arith`, `std_logic_unsigned`, `std_logic_signed`
- Verify `numeric_std` is used for all arithmetic
- Check if `std_ulogic` is used where `std_logic` is unnecessary (single-driver signals)
- Note VHDL standard in use (2008 features available?)

**Types**:

- Are enumerations used for FSM states (not integers)?
- Are records used for structured data (not parallel signal bundles)?
- Are signal widths constrained (no bare `integer` without range)?
- Are subtypes used for semantic clarity?
- Are constants named (no magic numbers)?

For each finding, record:

- **File:line** - exact location
- **What** - the specific issue
- **Why** - what goes wrong (simulation/synthesis mismatch, wasted resources, maintenance burden)
- **Idiomatic alternative** - concrete code showing the fix

</step_1>

<step_2>

**Process & FSM Review**

Examine every process in each design file:

**Clocked processes**:

- Is `rising_edge(clk)` used (not `clk'event and clk = '1'`)?
- Is the sensitivity list correct (only `clk` for sync reset, `clk` + `rst` for async)?
- Does the reset branch initialize every registered signal?
- Is the reset strategy consistent across the design (sync vs async)?

**Combinational processes**:

- Is `process(all)` used (VHDL-2008), or is the explicit sensitivity list complete?
- Do default assignments at process top prevent latches?
- Are `if`/`case` statements complete (every branch assigns every signal)?
- Could this process be replaced with a concurrent signal assignment?

**FSMs**:

- Is a two-process or one-process pattern used (flag three-process)?
- Are states enumerated types (not encoded integers)?
- Is there a default/unreachable state handler?
- Are FSM outputs registered where timing requires it?

**Signal vs variable**:

- Are variables confined to combinational logic within a single process?
- Is `shared variable` used anywhere (flag it)?
- Are signals used for inter-process communication (not variables)?

</step_2>

<step_3>

**Structural & Style Review**

Examine entity declarations, architecture structure, and naming:

**Entity/Architecture**:

- Are port maps using named association (flag positional)?
- Are generic maps using named association?
- Is direct entity instantiation used (preferred over component declarations)?
- Are generate statements labeled?
- Is `others` used for reset/default values?

**Naming**:

- Do signals use `snake_case`?
- Do constants use `UPPER_SNAKE_CASE`?
- Do types have `_t` suffix?
- Are clocks named `clk` / `clk_<domain>`?
- Are resets named `rst` / `rst_n`?
- Are active-low signals marked with `_n`?
- Are all processes labeled?

**Readability**:

- Are deeply nested conditionals factored into functions?
- Is concurrent assignment used for simple combinational logic?
- Are related ports grouped (clock/reset, data, control, status)?
- Are comments explaining *why*, not *what*?

</step_3>

<step_4>

**Synthesizability Review**

Check for constructs that cause synthesis issues:

**Latches** (most critical):

- Scan every combinational process for incomplete assignments
- Check every `if` without `else` in combinational context
- Check every `case` without `when others` in combinational context
- Verify default assignments at process top

**Timing**:

- Are entity outputs registered (for timing closure at module boundaries)?
- Are there long combinational chains that could fail timing?
- Are pipeline stages used where needed?

**Resource usage**:

- Are unconstrained integers consuming 32 bits unnecessarily?
- Are memories structured for block RAM inference (synchronous read)?
- Are unnecessary resets on block RAM causing distributed RAM inference?

**Prohibited in synthesis**:

- `after` delays in non-testbench code
- `wait for` time delays
- `file` I/O, `textio`
- Combinational feedback loops

</step_4>

<step_5>

**Findings Report**

Synthesize all findings into a single prioritized report:

**Priority definitions**:

- **P0 (Critical)**: Will cause incorrect hardware, simulation/synthesis mismatch, or elaboration failure
- **P1 (Important)**: Reduces quality, wastes resources, or creates maintenance burden
- **P2 (Style)**: Improves readability, follows convention, modernizes to VHDL-2008

**Summary table**:

| Priority | File:Line | Finding | Category | Idiomatic Fix |
| -------- | --------- | ------- | -------- | ------------- |
| P0       | ...       | ...     | ...      | ...           |
| P1       | ...       | ...     | ...      | ...           |
| P2       | ...       | ...     | ...      | ...           |

**Categories**: Library, Type, Process, FSM, Naming, Structure, Synthesizability

**For each P0 finding**, include the complete idiomatic code replacement, not just a description.

**Overall assessment**:

| Aspect             | Status         | Notes |
| ------------------ | -------------- | ----- |
| Library compliance | Yes/No/Partial | ...   |
| Type discipline    | Yes/No/Partial | ...   |
| Latch-free         | Yes/No/Partial | ...   |
| Naming consistency | Yes/No/Partial | ...   |
| Synthesizable      | Yes/No/Partial | ...   |
| VHDL-2008 adoption | Yes/No/Partial | ...   |

</step_5>

</process>

<success_criteria>
The review is complete when:

- [ ] Every file's library clauses checked against idiomatic standards
- [ ] Every process reviewed for sensitivity list, reset, and completeness
- [ ] Every FSM reviewed for coding style and state type
- [ ] Every port/generic map checked for named association
- [ ] Naming conventions audited across all files
- [ ] Latch analysis performed on all combinational processes
- [ ] Findings table delivered with priority, location, and idiomatic fix
- [ ] Overall assessment table delivered
- [ ] All P0 findings include complete replacement code

</success_criteria>
