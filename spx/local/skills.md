# Marketplace Skill Authoring Overrides

Loaded by `/skill-standards` `<repo_local_overlay>` when authoring or auditing skills in this repository. These specialize the base skill-authoring standards for the Outcome Engineering marketplace.

## Current Skill Names

ALWAYS: Invoked workflow skills name the artifact one invocation produces, per `spx/14-skill-naming.pdr.md`, written as an imperative phrase that matches user speech; grammatical number follows the capability's meaning and is never changed mechanically across a plugin.
ALWAYS: An invoked workflow skill drops the imperative form and takes the artifact's own term when the operator already types that term for the artifact — a verb-led alternative then names an action nobody asks for and buries what the invocation produces. `/upstream` resolves and publishes the upstream contribution target under that term.
ALWAYS: Reference skills are named `{domain}-standards`, where `{domain}` names the standardized subject.
ALWAYS: Any material change to a skill implies auditing every skill name in the entire plugin against the latest instruction-authoring rules and renaming each nonconforming skill; compliant names remain unchanged.
ALWAYS: Before proposing a skill rename, classify every reviewed skill by current name, skill type, governing naming form, proposed name or keep disposition, and reason. Read declared methodology vocabulary and relevant file history before treating a name as defective. A shared token, suffix, or grammatical number never proves a batch rename.
ALWAYS: New agents are named in actor form and ALWAYS differ from the skill name they implement. For example, `adr-auditor` implements `audit-adr`.

## Version Bumps

ALWAYS: A skill change that requires a plugin version bump writes it only through `just bump`, run before `just build-skills` so the regenerated `dist/` carries the bumped version. NEVER hand-edit a manifest `version` field; `spx/local/commit-changes.md` carries the full bump policy.
