---
name: audit-skill
description: >-
  SKILL.md audit methodology — judges skill content for standards compliance,
  operational effectiveness, portability, voice, and structure.
argument-hint: <skill-path>
arguments: skill_path
allowed-tools: Read, Grep, Glob, Bash(python3 -c 'from pathlib import Path; import sys; print(len(Path(sys.argv[1]).read_text(encoding="utf-8")))':*)
---

Use skill `instructions:skill-standards`.

Use skill `instructions:agent-prompt-standards`.

<objective>
An `APPROVED` or `REJECTED` verdict on a SKILL.md against `/skill-standards` and `/agent-prompt-standards`, with findings grouped as keep-these-aspects, worth-improving, and must-fix; every rejected finding names the artifact location, violated rule, and evidence.
</objective>

<constraints>
- NEVER modify files during audit - ONLY analyze and report findings
- NEVER report a score; report contextual judgment across the full skill-authoring surface
- MUST read the governing standards and the references their applicability rules require before evaluating
- ALWAYS provide file:line locations for every finding
- NEVER generate fixes unless explicitly requested by the user
- NEVER make assumptions about skill intent - flag ambiguities as findings
- MUST complete every applicable standards area
- ALWAYS apply contextual judgment - what matters for a simple skill differs from a complex one

</constraints>

<audit_workflow>
Use `$skill_path` as exactly one skill-directory or `SKILL.md` path. Preserve that supplied path in `target`; a file target selects its containing bundle. If the input is absent, ambiguous, unreadable, or does not identify a skill bundle, emit `REJECTED` with one `configuration_issue` finding in `must-fix` and empty passing observation rows. Use the supplied path as the finding location, or this skill's file when no path was supplied, with `line: null`; omit metadata that cannot be established. Never infer another target.

**MANDATORY**: Read standards FIRST, before auditing:

1. Read `/skill-standards` — the canonical standards for skill structure, frontmatter, XML tags, progressive disclosure, skill types, reference patterns, code-fence rules, bash restrictions, validation, and script testing. Then check for `spx/local/skills.md` at the repository root and read it if it exists.
2. Read `/agent-prompt-standards` — voice, description style, constraint language, and prose anti-patterns. Already injected above.
3. Read the complete target bundle, including uncited and orphaned files (SKILL.md and any `references/`, `workflows/`, `templates/`, `assets/`, `scripts/` subdirectories). When a read is truncated, retrieve the omitted ranges before judging absence; a missing closing-tag finding requires inspecting the actual end of the file.
4. When the target uses `/skill-standards`'s eager-foundation exception, run the following deterministic counter against every rendered target `SKILL.md`. Record each command's integer output in verdict metadata, then apply the exception's current threshold and qualitative checks from `/skill-standards`; never estimate the count from model inspection.

   ```bash
   python3 -c 'from pathlib import Path; import sys; print(len(Path(sys.argv[1]).read_text(encoding="utf-8")))' "<rendered-SKILL.md>"
   ```

5. When the target bundles scripts, read `/skill-standards`’s `references/script-standards.md` before evaluating them. Read this audit skill's own `${SKILL_DIR}/references/xml-structure-examples.md` and `${SKILL_DIR}/references/operational-effectiveness-examples.md` for annotated violation examples; both paths resolve from this `audit-skill` bundle. When the target carries command-capability fields — `argument-hint`/`arguments`, `allowed-tools`, `!`-dynamic context, or `@` file references — also read `/skill-standards`'s `references/command-capabilities.md` for the rules that govern that surface. When the target is an `audit-*` skill, also read `/skill-standards`'s `references/auditor-skeleton.md` — the `/skill-standards` table loaded in step 1 names it; read the file itself explicitly — the canonical auditor structure the `auditor_skeleton_violation` check verifies against.
6. Handle edge cases:
   - If `/skill-standards` or `/agent-prompt-standards` is unreadable, add a `REJECT` finding with rule `configuration_issue` to the `must-fix` row and proceed with available content; the incomplete audit remains `REJECTED`.
   - If YAML frontmatter is malformed, flag as critical issue.
   - If the skill references external files that don't exist, flag as critical issue and recommend fixing broken references.
   - If the skill references a bundled plugin file through repository-local authored or generated plugin paths, legacy plugin-root paths, or an authored Codex-only skill-directory token, flag as a portable file-reference defect.
   - Determine the skill type from its purpose and the loaded standards; record it in `metadata.skill_type`.
7. Evaluate the target skill against the standards loaded in steps 1-2.

**Use ACTUAL patterns from `/skill-standards`, not memory.** Never treat a creator skill's workflow references as standards — those references carry authoring workflow content only.
</audit_workflow>

<verdict_format>
Emit a structured verdict. The skill's entire output is the verdict payload.

The skill's `overall` is `APPROVED` iff the `must-fix` row has no `REJECT` findings; otherwise it is `REJECTED`. An audit that cannot complete records a `REJECT` finding in `must-fix` and returns `REJECTED`. Worth-improving and keep-these-aspects observations land as `WARNING` and `INFO` findings respectively and do not reject the skill.

```json
{
  "schema_version": 1,
  "skill": "audit-skill",
  "target": "<skill-path>",
  "overall": "APPROVED | REJECTED",
  "rows": [
    {
      "name": "keep-these-aspects",
      "status": "PASS",
      "findings": [
        {
          "id": "f-001",
          "file": "<skill-file>",
          "line": 12,
          "rule": "<strength-name>",
          "severity": "INFO",
          "message": "<what it does> — removing this would <specific consequence>"
        }
      ]
    },
    {
      "name": "worth-improving",
      "status": "PASS",
      "findings": [
        {
          "id": "f-002",
          "file": "<skill-file>",
          "line": 24,
          "rule": "<issue-name>",
          "severity": "WARNING",
          "message": "Current: <what exists>. Change to: <what it should be>. Benefit: <specific gain>."
        }
      ]
    },
    {
      "name": "must-fix",
      "status": "PASS | FAIL",
      "findings": [
        {
          "id": "f-003",
          "file": "<skill-file>",
          "line": 36,
          "rule": "<issue-name>",
          "severity": "REJECT",
          "message": "Current: <what exists>. Fix: <specific action>. Impact if unfixed: <what breaks>."
        }
      ]
    }
  ],
  "metadata": {
    "skill_type": "simple | complex | delegation | etc.",
    "line_count": "<n>",
    "eager_payload_code_points": { "<rendered-SKILL.md>": "<n>" }
  }
}
```

Omit `eager_payload_code_points` when the eager-foundation exception does not apply.

Note: While this skill uses pure XML structure, it produces JSON output that the verdict toolchain renders as markdown for human readability.
</verdict_format>

<failure_modes>

**Failure 1: Approved a skill whose objective was still activity-shaped.** Claude read an `<objective>` that opened with a verb ("Audit…", "Generate…") or an actor ("The skill…") and passed it, because the activity reading felt natural. The objective states an output; an activity- or actor-shaped one is a must-fix the `actor_or_activity_objective` flag exists to catch. Read every objective against `/agent-prompt-standards` `<objective_shape>`, not by feel.

**Failure 2: Skipped an evaluation area and missed a whole class.** Claude judged YAML and structure, formed a verdict, and stopped — leaving prompt craft or anti-patterns unexamined, so a class of violations passed unseen. The verdict is sound only when every evaluation area was judged; a skipped area yields an unsound verdict, not a shorter one. Cover every applicable rule in the loaded standards before issuing the verdict.

**Failure 3: Scored the skill instead of judging it.** Claude assigned a number ("8/10 structure") instead of grouping findings as keep / worth-improving / must-fix, turning a verdict into a rating the author cannot act on. Each finding names a location, a standard, and a consequence; a score names none of them. Emit findings, never scores.

</failure_modes>

<success_criteria>
The verdict is sound when:

- Every applicable rule in the loaded standards was judged, with none skipped.
- The verdict states an overall APPROVED/REJECTED with findings grouped keep-these-aspects / worth-improving / must-fix.
- Each finding is falsifiable: it names the location (file:line), the standard at issue, and the consequence — every keep names what degrades if removed, every must-fix names the failure it prevents.
- The same SKILL.md yields the same verdict.

</success_criteria>

<validation>
Before returning the verdict, require exactly one row for each category in `<verdict_format>`, with each row’s status consistent with its findings. Verify its completeness against the applicable standards,
its locations against the actual files, and each finding against its cited rule and evidence.
The `rows` array contains exactly `keep-these-aspects`, `worth-improving`, and `must-fix` in that order. `metadata` is a top-level object and never a row. Remove any extra row before returning the verdict.
Check every rendered target's recorded code-point count when the eager-foundation
exception applies. Remove findings that impose an optional mechanism without a governing
requirement; an absent failure-mode section is assessed under the loaded prompt standard.
</validation>
