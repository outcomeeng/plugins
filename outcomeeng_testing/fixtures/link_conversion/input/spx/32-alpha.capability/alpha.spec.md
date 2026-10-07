# Alpha

- Test link, node-local (untouched): [test](tests/test_alpha.mapping.l1.py)
- Issues link, node-local (untouched): [issues](ISSUES.md)
- Same-node decision, prose text: [format](17-alpha-format.adr.md)
- Same-node decision, path text: [`17-alpha-format.adr.md`](17-alpha-format.adr.md)
- Same-node decision, fragment and title: [format rules](17-alpha-format.adr.md#rules "Alpha format")
- Same-node decision, nested brackets: [format [v2]](17-alpha-format.adr.md)
- Same-node decision, dot-slash: [format](./17-alpha-format.adr.md)
- Climb to a root decision: [merging](../15-merging.pdr.md)
- Climb to a sibling node spec: [gamma](../54-gamma.capability/gamma.spec.md)
- Climb to a sibling node decision: [gamma rule](../54-gamma.capability/15-gamma-rule.adr.md)
- Leading slash to a decision in another node: [gamma rule](/spx/54-gamma.capability/15-gamma-rule.adr.md)
- Descendant node decision: [child rule](21-alpha-child.domain/15-child-rule.pdr.md)
- Descendant node spec: [child](21-alpha-child.domain/alpha-child.spec.md)
- Descendant node test: [child test](21-alpha-child.domain/tests/test_child.scenario.l1.py)
- Descendant variant spec: [split](25-alpha-split.variant/alpha-split.spec.md)
- Reference style: [format][fmt] and [parse][prs]
- Three links on one line: [format](17-alpha-format.adr.md), [merging](spx/15-merging.pdr.md), [gamma rule](../54-gamma.capability/15-gamma-rule.adr.md)

[fmt]: 17-alpha-format.adr.md
[prs]: ../32-alpha.capability/18-alpha-parse.adr.md

Bare prose: the parse rule lives in 18-alpha-parse.adr.md.
Code span relative: `18-alpha-parse.adr.md`; code span climb: `../15-merging.pdr.md`.
Code span non-decision: `tests/test_alpha.mapping.l1.py`.
- Link out of the tree, climbing (reported, untouched): [outside](../../docs/outside.md)
- Link out of the tree, leading slash (reported, untouched): [outside](/docs/outside.md)
- Evidence link into a descendant node (reported, untouched): [test](21-alpha-child.domain/tests/test_child.scenario.l1.py)
- Evidence link that climbs (reported, untouched): [test](../32-alpha.capability/tests/test_alpha.mapping.l1.py)
Code span, placeholder beside a path: `NN-decision.pdr.md with 18-alpha-parse.adr.md`.
- Reference-style evidence link that climbs (reported, untouched): [test][ev]
[ev]: ../32-alpha.capability/tests/test_alpha.mapping.l1.py
