# Link conversion fixtures

One small product root in two states. `input/` carries every citation form. `expected/` carries the output of a correct conversion. The files are inert whole payloads: tests read them by path and never import them. `outcomeeng_testing/harnesses/link_conversion.py` owns the path providers, and `dprint.jsonc` excludes this directory so a formatter never rewrites a fixture.

## Layout

- `input/` and `expected/`: the product root before and after conversion, file for file. Each holds an `spx/` tree and a `docs/` directory outside it.
- `expected-rewrote.txt`: the files whose content changes, one path from the root per line, sorted bytewise.
- `expected-report.tsv`: the citations a run cannot convert. Columns: file, line, form, target. Sorted by file, then line.
- `untouched-forms.txt`: the files that hold convertible-looking forms the conversion must leave as written.
- `convertible-only/`: a small tree whose citations all convert, so a run reports nothing.

The tree has root decisions (`15-merging.pdr.md`, `20-storage.adr.md`), a 4.0 node with a child domain and a variant (`32-alpha.capability`), a 3.x node with a child outcome and a fractional-index insert (`40-legacy.enabler`), and a sibling node (`54-gamma.capability`).

## Forms

| Form | Where | Result |
| --- | --- | --- |
| Correct tree-absolute link, code-span or prose text, fragment | demo.spec.md; storage; gamma-rule; untouched-forms.md | untouched |
| Same-node decision link, prose text, path text, fragment, title, nested brackets, `./` prefix | alpha.spec.md; gamma.spec.md; legacy.md; merging; storage | href becomes tree-absolute; path text takes the full path |
| Same-node decision link at root level | demo.spec.md; merging | tree-absolute |
| `../` link to a root decision, a sibling node spec or decision, or inside the node | alpha.spec.md; alpha-child.spec.md; gamma.spec.md; legacy.md; probe.md; alpha-split.spec.md | tree-absolute |
| Leading-slash link | demo.spec.md; alpha.spec.md; alpha-parse | tree-absolute |
| Link into a descendant node: decision, spec, test, variant, 3.x outcome, fractional insert | alpha.spec.md; legacy.md | tree-absolute |
| Code-span decision path: full, relative, `../` | demo.spec.md; merging; alpha.spec.md; alpha ISSUES.md; child-rule; legacy-choice | link with the full path as text and href |
| Reference-style definition | alpha.spec.md | tree-absolute |
| Bare prose path | demo.spec.md; merging; alpha.spec.md; alpha ISSUES.md; legacy-insert.md | untouched, reported as `text-decision` |
| Unresolvable target: relative, tree-absolute, code span, `../` | storage; gamma.spec.md | untouched, reported as `broken` |
| Link inside a backtick or tilde fence | demo.spec.md; untouched-forms.md | untouched |
| Same-node link to a non-decision file, external link, `mailto:`, in-page anchor | alpha.spec.md; demo.spec.md; untouched-forms.md | untouched |
| Placeholder path: prose, bare `NN-` index, braces, braced directory | gamma ISSUES.md | untouched, not reported |
| Citation in a Markdown file outside `spx/` | docs/outside.md | untouched |
