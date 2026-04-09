# HDL

PROVIDES HDL engineering skills for VHDL and SystemVerilog code review
SO THAT hardware engineers using Claude Code
CAN receive idiomatic, synthesizability-aware reviews of their HDL code

The HDL plugin contains `/reviewing-vhdl` (VHDL-2008 review with synthesizability analysis) and `/reviewing-systemverilog` (IEEE 1800-2017 review for Vivado and Quartus).

## Assertions

### Compliance

- ALWAYS: verify synthesizability in HDL reviews — simulation-only constructs that reach synthesis cause silent failures ([review])
- NEVER: apply software engineering patterns (dependency injection, mocking) to HDL reviews — hardware design has fundamentally different verification patterns ([review])
