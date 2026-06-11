# Marketplace Skill Authoring Overrides

Loaded by `/standardizing-skills` `<repo_local_overlay>` when authoring or auditing skills in this repository. These specialize the base skill-authoring standards for the Outcome Engineering marketplace.

## Transition from gerund to imperative names for skills

The use of gerund skill names is deprecated because the `slash command` type offered by Claude Code is officially deprecated and replaced by `skill` only. This marketplace is in a transition period.

ALWAYS: New skills are named in imperative form
ALWAYS: New agents are named in actor form and ALWAYS differ from the skill name they implement. For example, `adr-auditor` implements `audit-adr`.
