# ISSUES — plugin manifest validation

Known defects and contradictions in the plugin manifest surface. Each entry names the artifact, the rule it violates, and the smallest unit of work that resolves it.

## No manifest expresses that the spec-tree plugin is mandatory

Every plugin operationalizes a methodology the spec-tree plugin carries, and a consumer is expected to have that plugin installed. No manifest says so. `.claude-plugin/plugin.json` and `.codex-plugin/plugin.json` carry name, version, description, author, repository, license, and keywords; neither declares a dependency, and neither marketplace catalog records one. The two catalogs list ten independently installable entries, and `README.md` presents each standalone repository as separately installable.

The mandate therefore lives only in operator knowledge. Anything reasoning from the artifacts alone — a reviewer, a validator, `spx`, or the next author — reads ten independent plugins and concludes a consumer may install any one of them alone. That conclusion is wrong, and nothing in the repository corrects it.

The gap has a concrete cost: content that only the spec-tree plugin ships is unreachable for a consumer the artifacts say may exist, so any review of such a change raises a blocking finding that only operator knowledge can refute.

**Resolution shape**: express the relationship where a reader already looks. A `methodology` block in each manifest declaring the methodology releases that plugin supports — with the providing plugin declaring what it provides — makes the dependency legible and checkable, and is the same declaration a consumer's own methodology version is validated against. Whether the relationship additionally warrants a hard dependency field in both catalogs is a separate question this entry does not settle.

**Evidence**: raised as a blocking `consistency` finding by the changeset reviewer against the marketplace-changelog relocation, on the grounds that no `plugin.json` declares a dependency on the spec-tree plugin and nothing in that changeset added one. The finding's premise was refuted by the operator, who confirmed the plugin is mandatory; the absence of any artifact expressing it is what the finding actually exposed.
