# Levels probe

## Intent

The operator expects a document written from the PDR or spec template to abbreviate itself deterministically: an agent reads a short view to decide whether the document matters before it loads the whole file. The `levels-probe` rule states that an attested run retains each example's level 2 view as its artifact. Only reading a view beside its document settles whether the view keeps what a reader needs, and the run is a proof of concept a parser in the SPX CLI can reproduce.

## Environment and preconditions

- The commit under verification, with `just` and `uv` on the path.
- The filled examples `src/plugins/product-tree/skills/understand/examples/pdr-example.md` and `capability-example.md`, written in the template form.

## Protocol

1. Run `just levels 2 src/plugins/product-tree/skills/understand/examples/pdr-example.md` and `just levels 2 src/plugins/product-tree/skills/understand/examples/capability-example.md`.
2. Read each view beside its example. Confirm that level 1, the first lines up to the first heading, holds the path, the title, and the opening.
3. Confirm that level 2 keeps every subsection heading and the slug and sentence of every rule, and lists the case names of each mapping table in place of the table.
4. Confirm that the level 3 view is the whole file with `just levels 3 <example>` and a read of the example.

## Attested run

- Date: 2026-11-04
- Observations: both level 2 views hold the path, the title, and the opening, then every heading in order, every rule as its slug and sentence, and the case names of the capability example's mapping table. The PDR example has no mapping table and its view keeps its two groups. The level 1 view of the capability example stops after its three opening lines. The level 3 view of the PDR example equals the file.
- Artifacts: [PDR example, level 2](pdr-example.level-2.txt), [capability example, level 2](capability-example.level-2.txt)

## Verdict

`passed` — each view abbreviates its document and drops no heading or rule.

## Limitations

The protocol exercised two documents. It ran level 1 on the capability example only and level 3 on the PDR example only. It did not exercise a rule that wraps over several lines, a group with more than ten rules, a PDR with a mapping table, a document with no title line, or an ADR, which the form does not cover.
