<overview>
Idiomatic VHDL-2008 patterns and anti-patterns for reviewing hand-written VHDL. Organized by review category. Each section defines what idiomatic code looks like and what to flag.

</overview>

<library_usage>

**Required**: `ieee.numeric_std` for all arithmetic on `std_logic_vector` / `std_ulogic_vector`.

**Banned**:

| Library                   | Why Banned                                          |
| ------------------------- | --------------------------------------------------- |
| `ieee.std_logic_arith`    | Synopsys proprietary, not IEEE. Type conflicts.     |
| `ieee.std_logic_unsigned` | Synopsys proprietary. Implicit unsigned conversion. |
| `ieee.std_logic_signed`   | Synopsys proprietary. Implicit signed conversion.   |
| `std_logic_misc`          | Non-standard, vendor-specific.                      |

**Preferred library pattern**:

```vhdl
library ieee;
  use ieee.std_logic_1164.all;
  use ieee.numeric_std.all;
```

**VHDL-2008 addition**: `ieee.numeric_std_unsigned` allows arithmetic directly on `std_ulogic_vector` without casting to `unsigned`. Acceptable when the entire vector is always treated as unsigned.

**std_ulogic vs std_logic**:

- `std_ulogic` / `std_ulogic_vector`: unresolved, single-driver. Catches accidental multi-driver bugs at elaboration.
- `std_logic` / `std_logic_vector`: resolved, multi-driver. Required only for tri-state buses or bidirectional ports.
- **Default to `std_ulogic`** unless resolution is needed.
- In VHDL-2008, `std_logic` is defined as `resolved std_ulogic`, making them interchangeable in most contexts.

</library_usage>

<type_discipline>

**Use the strongest type that fits**:

| Need                    | Idiomatic Type                         | Anti-pattern                      |
| ----------------------- | -------------------------------------- | --------------------------------- |
| Enumerated states       | `type state_t is (IDLE, RUN, DONE);`   | `integer range 0 to 2`            |
| Counted values          | `unsigned(N-1 downto 0)`               | `std_logic_vector` + manual arith |
| Signed arithmetic       | `signed(N-1 downto 0)`                 | Two's complement in `slv`         |
| Structured data         | `record`                               | Parallel signal bundles           |
| Homogeneous collections | `array`                                | Numbered signal suffixes          |
| Loop indices / generics | `natural`, `positive`, `integer range` | Unconstrained `integer`           |

**Constrain everything**:

```vhdl
-- Idiomatic: constrained
signal count : unsigned(7 downto 0);
signal addr  : natural range 0 to 255;

-- Anti-pattern: unconstrained
signal count : integer;  -- 32-bit, wastes resources
```

**Records for structured data**:

```vhdl
type axi_req_t is record
  addr  : unsigned(31 downto 0);
  data  : std_ulogic_vector(31 downto 0);
  valid : std_ulogic;
end record axi_req_t;
```

**Subtypes for semantic meaning**:

```vhdl
subtype addr_t is unsigned(15 downto 0);
subtype data_t is std_ulogic_vector(31 downto 0);
```

</type_discipline>

<process_patterns>

**Clocked process (synchronous reset)**:

```vhdl
reg : process(clk) is
begin
  if rising_edge(clk) then
    if rst = '1' then
      count <= (others => '0');
    else
      count <= count + 1;
    end if;
  end if;
end process reg;
```

Key rules:

- Only `clk` in sensitivity list
- `rising_edge(clk)` as outermost condition
- Synchronous reset inside the clock edge
- All registered signals assigned in reset branch

**Clocked process (asynchronous reset)** — only when required by target:

```vhdl
reg : process(clk, rst) is
begin
  if rst = '1' then
    count <= (others => '0');
  elsif rising_edge(clk) then
    count <= count + 1;
  end if;
end process reg;
```

Key rules:

- Both `clk` and `rst` in sensitivity list
- Reset is outermost condition (checked before clock edge)
- Every registered signal must have a reset value

**Combinational process (VHDL-2008)**:

```vhdl
comb : process(all) is
begin
  next_state <= state;  -- default assignment prevents latches
  output     <= '0';

  case state is
    when IDLE =>
      if start = '1' then
        next_state <= RUNNING;
      end if;
    when RUNNING =>
      output <= '1';
      if done = '1' then
        next_state <= IDLE;
      end if;
  end case;
end process comb;
```

Key rules:

- `process(all)` eliminates sensitivity list bugs (VHDL-2008)
- Default assignments at top prevent latches
- Every path through the process assigns every driven signal

**Pre-2008 combinational process**: Same structure but explicit sensitivity list containing every signal read in the process.

**Anti-patterns**:

- `clk'event and clk = '1'` instead of `rising_edge(clk)` — fails on `'X'` to `'1'`
- Missing signals in sensitivity list — simulation/synthesis mismatch
- Variable used where signal is appropriate — loses registered behavior
- `wait` statements in synthesizable code (except `wait until rising_edge(clk)` as sole sensitivity)

</process_patterns>

<fsm_coding>

**Two-process FSM** (most idiomatic for synthesis):

```vhdl
type state_t is (IDLE, LOADING, PROCESSING, DONE);
signal state, next_state : state_t;

-- Process 1: State register
state_reg : process(clk) is
begin
  if rising_edge(clk) then
    if rst = '1' then
      state <= IDLE;
    else
      state <= next_state;
    end if;
  end if;
end process state_reg;

-- Process 2: Next-state logic + outputs
next_logic : process(all) is
begin
  next_state <= state;  -- default: hold
  busy       <= '1';    -- default output values

  case state is
    when IDLE =>
      busy <= '0';
      if start = '1' then
        next_state <= LOADING;
      end if;
    when LOADING =>
      if data_ready = '1' then
        next_state <= PROCESSING;
      end if;
    when PROCESSING =>
      if compute_done = '1' then
        next_state <= DONE;
      end if;
    when DONE =>
      next_state <= IDLE;
  end case;
end process next_logic;
```

**One-process FSM** (simpler, all outputs registered):

```vhdl
fsm : process(clk) is
begin
  if rising_edge(clk) then
    if rst = '1' then
      state <= IDLE;
      busy  <= '0';
    else
      case state is
        when IDLE =>
          busy <= '0';
          if start = '1' then
            state <= LOADING;
            busy  <= '1';
          end if;
        -- ...
      end case;
    end if;
  end if;
end process fsm;
```

**Three-process FSM** (separate output process) — generally avoid. Adds a third process without benefit. The combinational output process can be merged with next-state logic.

**State type rules**:

- Always use an enumeration, never integer encoding
- Let the synthesizer choose encoding (or use synthesis attributes)
- Name states descriptively: `WAIT_FOR_ACK`, not `S3`

</fsm_coding>

<naming_conventions>

| Element        | Convention           | Examples                            |
| -------------- | -------------------- | ----------------------------------- |
| Signals        | `snake_case`         | `data_valid`, `byte_count`          |
| Constants      | `UPPER_SNAKE_CASE`   | `DATA_WIDTH`, `CLK_FREQ_HZ`         |
| Types          | `_t` suffix          | `state_t`, `bus_data_t`             |
| Subtypes       | `_t` suffix          | `addr_t`, `pixel_t`                 |
| Generics       | `UPPER_SNAKE_CASE`   | `DATA_WIDTH`, `DEPTH`               |
| Clocks         | `clk` or `clk_<dom>` | `clk`, `clk_sys`, `clk_pixel`       |
| Resets         | `rst` or `rst_n`     | `rst` (active-high), `rst_n` (low)  |
| Active-low     | `_n` suffix          | `cs_n`, `oe_n`, `we_n`              |
| Enables        | `_en` suffix         | `count_en`, `tx_en`                 |
| Register stage | `_d` / `_q`          | `data_d` (input), `data_q` (output) |
| Next-state     | `next_` prefix       | `next_state`, `next_count`          |
| Process labels | `snake_case`         | `state_reg`, `output_mux`           |

**Always label processes.** Unlabeled processes are harder to debug in simulation and synthesis reports.

**Avoid**:

- Hungarian notation (`slv_data`, `sig_count`)
- Single-letter names except `i`, `j`, `k` for generate/loop indices
- Abbreviations that aren't universally understood

</naming_conventions>

<structural_patterns>

**Named association in port maps** (non-negotiable):

```vhdl
-- Idiomatic
uart_inst : entity work.uart_tx
  generic map (
    BAUD_RATE  => 115200,
    DATA_BITS  => 8
  )
  port map (
    clk      => clk,
    rst      => rst,
    tx_data  => tx_data,
    tx_valid => tx_start,
    tx_ready => tx_ready,
    tx       => uart_tx_pin
  );

-- Anti-pattern: positional
uart_inst : entity work.uart_tx
  generic map (115200, 8)
  port map (clk, rst, tx_data, tx_start, tx_ready, uart_tx_pin);
```

**Direct entity instantiation** (VHDL-93 and later):

```vhdl
-- Preferred: direct instantiation (no component declaration needed)
inst : entity work.fifo
  generic map (...)
  port map (...);

-- Acceptable: component instantiation (when configuration is needed)
inst : component fifo
  generic map (...)
  port map (...);
```

**Generate statements**:

```vhdl
-- for-generate with label
gen_pipeline : for i in 0 to STAGES-1 generate
  stage_inst : entity work.pipe_stage
    port map (
      clk   => clk,
      d_in  => pipe(i),
      d_out => pipe(i + 1)
    );
end generate gen_pipeline;
```

**Concurrent signal assignments** for simple logic:

```vhdl
-- Preferred for simple combinational logic
data_out <= data_a when sel = '1' else data_b;
mux_out  <= data_a when sel = "00" else
            data_b when sel = "01" else
            data_c when sel = "10" else
            data_d;

-- Don't wrap trivial logic in a process
```

**Use `others` for default/reset values**:

```vhdl
signal data : std_ulogic_vector(31 downto 0) := (others => '0');
data <= (others => '1');  -- all ones
data <= (0 => '1', others => '0');  -- bit 0 high, rest low
```

</structural_patterns>

<synthesizability>

**Latch prevention** — the most common synthesizability defect:

```vhdl
-- LATCH: missing else branch
process(all) is
begin
  if enable = '1' then
    output <= data;
  end if;  -- What happens when enable = '0'? Latch!
end process;

-- FIXED: complete assignment
process(all) is
begin
  output <= '0';  -- default prevents latch
  if enable = '1' then
    output <= data;
  end if;
end process;
```

**Case completeness**:

```vhdl
-- LATCH: missing states
case state is
  when IDLE =>
    output <= '0';
  when RUNNING =>
    output <= '1';
  -- DONE state missing! Infers latch for output.
end case;

-- FIXED: cover all states (or use default assignment at top)
```

**Constructs to avoid in synthesizable code**:

| Construct               | Problem                         | Alternative                          |
| ----------------------- | ------------------------------- | ------------------------------------ |
| `after X ns`            | Simulation-only delay           | Remove (synthesis ignores it anyway) |
| `wait for X ns`         | Not synthesizable               | Use clock-counted delays             |
| `file` / `textio`       | Not synthesizable               | Testbench only                       |
| `assert` (VHDL assert)  | Ignored by most synthesis tools | PSL or vendor assert for synthesis   |
| Floating-point          | Not directly synthesizable      | Fixed-point with `signed`/`unsigned` |
| Unconstrained `integer` | 32-bit default wastes resources | Use `natural range 0 to MAX`         |

**Initialization**:

- Signal declarations with `:= value` are ignored by most FPGA synthesis tools (Xilinx supports them for initial values in block RAM)
- Always initialize in the reset branch of a clocked process
- Don't rely on declaration initialization for correctness

**Combinational loops**: No signal should feed back to itself through purely combinational logic. Always break loops with a register.

</synthesizability>

<testbench_idioms>

**Testbench structure**:

```vhdl
entity tb_module_name is
end entity tb_module_name;

architecture sim of tb_module_name is
  constant CLK_PERIOD : time := 10 ns;
  signal clk : std_ulogic := '0';
  signal rst : std_ulogic := '1';
  -- DUT signals
begin
  -- Clock generation
  clk <= not clk after CLK_PERIOD / 2;

  -- DUT instantiation
  dut : entity work.module_name
    port map (...);

  -- Stimulus
  stim : process is
  begin
    -- Hold reset
    wait for CLK_PERIOD * 5;
    rst <= '0';
    wait for CLK_PERIOD;

    -- Test vectors
    -- ...

    -- End simulation
    report "Simulation complete" severity note;
    std.env.stop;  -- VHDL-2008 clean stop
  end process stim;
end architecture sim;
```

**Testbench-specific rules**:

- `after` delays are fine (testbench is not synthesized)
- Use `std.env.stop` (VHDL-2008) or `std.env.finish` instead of `assert false severity failure`
- Use `report` for status messages
- Name testbench entity `tb_<module_name>`
- Architecture name `sim` or `test`
- Clock generation via concurrent statement, not process

</testbench_idioms>

<vhdl_2008_features>

Features to prefer when VHDL-2008 is available (most modern toolchains support it):

| Feature                | VHDL-2008                            | Pre-2008                           |
| ---------------------- | ------------------------------------ | ---------------------------------- |
| Sensitivity list       | `process(all)`                       | Explicit list of every read signal |
| Resolved types         | `std_ulogic` for everything          | `std_logic` for ports              |
| Conditional assignment | `x <= a when b else c;` (in process) | Only in concurrent context         |
| Case expression        | `case? expr is` (don't-care)         | Manual masking                     |
| Block comments         | `/* ... */`                          | Only `--` line comments            |
| External names         | `<< signal .tb.dut.sig >>`           | Not available                      |
| Simulation control     | `std.env.stop`                       | `assert false severity failure`    |

**When reviewing**: Check the product's VHDL standard. If VHDL-2008 is available, flag pre-2008 patterns as style findings (P2). If only VHDL-93 is available, don't flag missing VHDL-2008 features.

</vhdl_2008_features>
