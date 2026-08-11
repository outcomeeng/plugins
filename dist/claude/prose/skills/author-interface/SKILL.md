---
name: author-interface
user-invocable: false
description: >-
  Interface authoring guidance — app chrome, UI text, product messages, notifications, and email templates — composed by author-prose for the interface kind. Reached only through author-prose, never matched directly.
allowed-tools: Read, Edit, Write, Glob, Grep, Skill
---

Invoke the `prose:interface-standards` skill before proceeding. If that skill is unavailable, report the missing skill and continue with the closest available workflow.

<objective>

Surface text — chrome, messages, and short page fragments — where every element leads with its action, fits its brevity cap, and stays terminologically consistent with its surface.

</objective>

<workflow>

1. Inventory the surface before writing an element. Collect the existing terms for the concepts the new text touches — the one-term-one-meaning rule binds new text to the surface's established vocabulary, and the element being written is rarely alone.

2. Apply `/interface-standards` `<voice_canon>` first — the shared canon every kind and the shipped output style render from. Its rules bind before every element-type rule below: substance-first openings, plain words, no filler words, assert only what is demonstrated, one term one meaning, failure text pairing what happened with what to do next, sentence case for titles and headings and labels, standard punctuation.

3. Write each element by its type, applying `/interface-standards` `<additional_rules>`: buttons and links lead with the verb; titles and labels are sentence-case fragments; errors pair what-happened with what-next; empty states orient; confirmations name the consequence and repeat the action verb.

4. Apply the base catalog through the two overrides only — fragments for surface elements, consistency-repetition across parallel elements. Everything else in `/prose-standards` binds at zero tolerance, including in body text inside elements.

5. Apply every `/prose-standards` rule pack the surface triggers. A stepped empty state or onboarding sequence triggers the instruction pack; a table rendered as an element triggers the table pack. A pack binds on the feature, in every kind.

6. Read the result as the surface, not as a list: parallel elements phrased in parallel, one name per concept, no filler words.

</workflow>

<success_criteria>

- New text uses the surface's established term for every shared concept.
- Each element type follows its `/interface-standards` rule and fits its brevity cap.
- Every voice-canon rule holds across the surface.
- Every rule pack the surface triggers was applied where its feature appears.
- Parallel elements are phrased in parallel; no base anti-pattern survives outside the declared overrides.

</success_criteria>
