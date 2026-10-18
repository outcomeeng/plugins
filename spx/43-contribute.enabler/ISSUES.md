# Issues: Contribute

Known defects, contradictions and gaps in this node. Coordination note; not spec truth.

## `open-upstream-issue` carries two blocking and four debt skill-audit findings

`instructions:skill-auditor` run `2026-10-06_18-44-04-815-8dade2dba8d8` rejected the post-edit audit of `src/plugins/contribute/skills/open-upstream-issue/SKILL.md` at head `4be7a922d11c27af632039953b5baf36db8b999f` on two `blocking` and four `debt` findings. The changeset's diff of the file is lines 27-28 and 31-32 at that head. The finding at line 31 and the missing criterion for the bound-filled stop lay on changed text, and a later commit on the same branch repairs both; the findings below lie outside the changed text.

The skill is one of the five workflow skills `contribute.md` names. The note sits in this node because `spx/43-contribute.enabler/43-issues.enabler/issues.md` and an `ISSUES.md` in that directory name one file on a case-insensitive filesystem.

- Rule `authorization-precedes-final-text`, severity `blocking`, line 43 (Steps 5-7): Step 5 presents the issue title for authorization before Step 6 drafts and reviews the title and body, and Step 7 files without re-authorization, so the filed text can differ from the authorized text.
- Rule `shell-safe-outward-text`, severity `blocking`, line 66 (Step 7): the `printf` form single-quotes every body line and both filing forms pass `--title "<title>"` in double quotes, with no escaping rule; the worked example's body contains `unexpected '='`, which the single-quoted form re-tokenizes to a different text.
- Rule `composed-skill-dependency`, severity `debt`, line 20 (Step 2): the step invokes `/upstream` by slash name instead of the `Use skill` instruction.
- Rule `worked-example-consistency`, severity `debt`, line 124 (`<worked_example>`): the annotation says the negative control changes one value, and the shown control changes two.
- Rule `success-criteria-cover-outcomes`, severity `debt`, lines 11 and 142 (`<objective>`, `<success_criteria>`): the objective and criteria name the filed and duplicate-found outcomes, and the `controlled` and `blocked` stops of Step 2 fail the first criterion. The criterion for the Step 3 bound-filled stop is added by the later commit, and the remainder of the finding stays.

**Impact.** An issue filed in a repository the operator does not control can carry text the operator did not authorize or a body the shell has altered, and the filed issue cannot be withdrawn.

**Settlement condition.** The authorization gate follows drafting and review and names the exact final title and body Step 7 files, each filing form states how title and body are made shell-safe, `Use skill` names `contribute:upstream`, the worked example's control varies one value, and the objective and criteria cover every terminal outcome; one typed skill audit of `open-upstream-issue` then raises none of the findings.
