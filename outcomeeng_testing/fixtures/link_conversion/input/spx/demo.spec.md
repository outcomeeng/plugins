# Demo

Fixture product for the link conversion.

- Correct, code-span text: [`spx/15-merging.pdr.md`](spx/15-merging.pdr.md)
- Correct, prose text with fragment: [storage layout](spx/20-storage.adr.md#layout)
- Same-node (root) decision link: [merging](15-merging.pdr.md)
- Same-node (root) decision link, path text: [`20-storage.adr.md`](20-storage.adr.md)
- Leading slash: [merging](/spx/15-merging.pdr.md)
- Code-span decision: `spx/20-storage.adr.md`
- Code-span non-decision: `src/demo/main.py`
- Bare prose: storage follows spx/20-storage.adr.md in every node.
- External and anchor: [site](https://example.com/spx/15-merging.pdr.md), [mail](mailto:team@example.com), [top](#demo)

```text
[merging](/spx/15-merging.pdr.md)
`spx/20-storage.adr.md` and 20-storage.adr.md
[climb](../x/15-merging.pdr.md)
```

~~~markdown
[merging](15-merging.pdr.md) and `20-storage.adr.md`
~~~
