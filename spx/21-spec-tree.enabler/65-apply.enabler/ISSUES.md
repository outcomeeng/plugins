# Issues: Apply

`/apply` cannot execute a **language-neutral artifact slice** because its language gate requires one implementation language and a complete architecture, test, and code skill trio.

## Add a language-neutral artifact route

**Evidence.** [`src/plugins/spec-tree/skills/apply/SKILL.md`](../../../src/plugins/spec-tree/skills/apply/SKILL.md) lines 50-60 require exactly one supported implementation language before Steps 3-8 and stop when no language-specific skill trio applies. [`spx/21-spec-tree.enabler/65-apply.enabler/apply.md`](apply.md) defines a general apply lifecycle whose selected slice can include language-neutral methodology artifacts.

**Impact.** A skill-only or documentation-only slice selected through `/slice` cannot continue through `/apply` without inventing irrelevant architecture, test, and code work or stopping before the artifact-specific authoring workflow.

**Required handling.** Define a language-neutral artifact route that preserves methodology loading, node contextualization, artifact-specific authoring, touched-scope deterministic verification, applicable artifact audits, whole-changeset review, the terminal full gate when required, and `/merge`. The route skips language architecture, language test, and language implementation steps when the selected slice contains no implementation-language surface.

**Revisit condition.** Resolve this entry before the next language-neutral artifact slice enters `/apply`, or in the next change to `/apply` language detection or Steps 3-8, whichever occurs first.
