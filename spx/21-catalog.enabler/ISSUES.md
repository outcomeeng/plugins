# Issues

## Catalog sentinel matching lacks line-start anchoring

`outcomeeng/catalog/plugin_catalog.py` locates the README catalog sentinels with bare `readme.find(BEGIN_SENTINEL)` / `readme.find(END_SENTINEL)`, so a sentinel quoted mid-line elsewhere in `README.md` could be taken for a real boundary. `spx/local/generated-sources.toml` declares line-start matching for this marker family and notes the deviation; the declared rule governs attribution, per `spx/31-outcomeeng.enabler/31-verification.enabler/15-generated-attribution.pdr.md`.

**Resolution shape**: anchor the sentinel search to line starts in `splice_catalog`, cover the anchoring in this node's catalog tests, then drop the deviation note from `spx/local/generated-sources.toml`.
