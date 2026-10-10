<objective>

The sweep table of one repair: every same-class site and every changed dependency, each with a resolved or unresolved disposition.

</objective>

<same_class_site>

A same-class site is any location in the bundle, in any file under `SKILL.md`, `references/`, `workflows/`, `templates/`, `assets/`, and `scripts/`, that carries the defect class a repair removes: a violation of the same catalog rule, or the same wording or structure the repair rewrote. Locate each by searching the whole bundle for the rewritten pattern and for the rule's characteristic text, never by reading only the files the finding names.

</same_class_site>

<changed_dependency>

A changed dependency is text that cites, quotes, restates, or relies on text the repair changed, and that now disagrees with it. Check each of these against every edit:

| Edit                                     | Dependents to check                                                                        |
| ---------------------------------------- | ------------------------------------------------------------------------------------------ |
| Renamed, moved, or removed file          | Every path citation, index row, and routing row in the bundle                              |
| Renamed or removed tag, step, or section | Every reference to it by name, including success criteria and failure modes                |
| Changed count, limit, or enumerated set  | Every sentence, table, and checklist that states the number or lists the members           |
| Changed output, disposition, or contract | Every consumer of that output in the bundle, and the description that summarizes the skill |
| Changed trigger or scope                 | The frontmatter description and every routing row that selects the changed behavior        |
| New rule the edit enforces               | Every other file in the bundle that the new rule now forbids from stating the old behavior |

</changed_dependency>

<sweep_table>

One row per site or dependency found:

| Site | Class or dependency | Disposition |
| ---- | ------------------- | ----------- |

The disposition is `repaired` with the changed path, or `unresolved` with the reason. A repair that leaves a row `unresolved` without a reason is incomplete. An edit made to resolve a row is itself an edit: its own same-class sites and dependents enter the table before the sweep ends.

</sweep_table>
