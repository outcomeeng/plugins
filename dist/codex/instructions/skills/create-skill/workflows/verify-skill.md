<required_reading>

Read `/skill-standards` and `/agent-prompt-standards`. Read `spx/local/skills.md` when the target repository provides it.

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

The overall verdict is `CURRENT` only when every inventory row is `current`. Any `update-required`, `broken`, or `unverifiable` row prevents that verdict.

</step>

<step name="apply_authorized_updates">

When the operator explicitly requests updates, require an authoritative replacement for every changed claim, resolve the exact authored paths, and never convert an `unverifiable` row into guessed guidance. Apply each evidence-backed replacement through the creator workflow. Do not add a persistent verification timestamp; source evidence and current repository validation establish currency without a stale-prone marker.

</step>

<step name="validate_updates">

When updates were applied, confirm each updated claim matches its recorded primary evidence, every bundled citation resolves, structure remains valid, and focused checks for changed commands or examples pass. Run repository checks and obtain a fresh typed `skill-auditor` verdict over the complete bundle.

</step>

</process>

<success_criteria>

- Every changeable external claim has a location, primary source, and explicit status.
- The overall verdict follows mechanically from the row statuses.
- Audit-only verification changes no file.
- Authorized updates match primary evidence, pass repository checks, and receive typed `skill-auditor` approval.

</success_criteria>
