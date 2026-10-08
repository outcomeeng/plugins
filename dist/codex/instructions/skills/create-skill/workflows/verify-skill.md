<required_reading>

Read the complete target bundle named in `resolve_target`; this route loads no conditional reference.

</required_reading>

<process>

<step name="resolve_target">

Use the exact skill path supplied by the operator or established from the repository's authored layout. Read the complete bundle and keep the verification read-only unless the operator explicitly requested updates.

</step>

<step name="inventory_claims">

Inventory every claim whose truth can change: APIs and services, package versions, command syntax, authentication methods, external links, platform behavior, and time-sensitive recommendations. Record the file and line for each claim. Exclude stable local instructions whose authority is repository truth.

</step>

<step name="verify_sources">

Check each inventory row against the current primary source for the exact product and environment the skill names. Prefer official documentation, package registries, release notes, and direct hosted-surface observation. Distinguish Cloud, Server, hosted runner, and local CLI variants when their contracts differ. Record the source URL or repository path and one status: `current`, `update-required`, `broken`, or `unverifiable`.

</step>

<step name="produce_report">

Return a report with these fields for every claim:

| Field           | Required content                                          |
| --------------- | --------------------------------------------------------- |
| Location        | Exact file and line                                       |
| Claim           | The skill's current statement                             |
| Evidence        | Primary source URL or repository path                     |
| Status          | `current`, `update-required`, `broken`, or `unverifiable` |
| Required change | Exact replacement or `none`                               |

Representative rows:

| Location                 | Claim                                                | Evidence                                                | Status            | Required change                                   |
| ------------------------ | ---------------------------------------------------- | ------------------------------------------------------- | ----------------- | ------------------------------------------------- |
| `SKILL.md:42`            | `$ARGUMENTS` preserves free-form input               | `/skill-standards` `references/command-capabilities.md` | `current`         | `none`                                            |
| `workflows/create.md:18` | Authored source uses `${SKILL_DIR}` for bundle paths | `/skill-standards` `references/command-capabilities.md` | `update-required` | Replace `${SKILL_DIR}` with `${CLAUDE_SKILL_DIR}` |

The overall verdict is `CURRENT` only when every inventory row is `current`. Any `update-required`, `broken`, or `unverifiable` row prevents that verdict.

</step>

<step name="apply_authorized_updates">

When the operator explicitly requests updates, require an authoritative replacement for every changed claim, resolve the exact authored paths, and never convert an `unverifiable` row into guessed guidance. Apply each evidence-backed replacement through `${SKILL_DIR}/workflows/repair-skill.md`, one requested-change row per replacement. Do not add a persistent verification timestamp; source evidence and current repository validation establish currency without a stale-prone marker.

</step>

<step name="validate_updates">

When updates were applied, confirm each updated claim matches its recorded primary evidence, every bundled citation resolves, structure remains valid, and focused checks for changed commands or examples pass. Run repository checks and confirm the bundle violates no rule in the `/skill-standards` or `/agent-prompt-standards` rule catalog.

</step>

</process>

<success_criteria>

- Every changeable external claim has a location, primary source, and explicit status.
- The overall verdict follows mechanically from the row statuses.
- Verification without requested updates changes no file.
- Authorized updates match primary evidence, pass repository checks, and leave the bundle violating no catalog rule.

</success_criteria>
