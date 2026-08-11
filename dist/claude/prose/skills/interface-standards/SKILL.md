---
name: interface-standards
user-invocable: false
description: >-
  Standards for the interface kind — text fragments embedded in a designed surface: app chrome, buttons, labels, empty states, error messages, tooltips, notifications, email templates, short web-page sections. Reference skill loaded by the composed interface skills, not invoked directly.
allowed-tools: Read
---

<objective>
The interface kind's standards layer over `/prose-standards` — the shared voice canon, inherited rules, the fragment override, and the writing rules for text that functions as part of a surface.
</objective>

<reference_note>
This is a reference skill. `/author-interface` and `/audit-interface` load it; the routers reach it only through them. Its `<voice_canon>` renders from the same authored fragment as the plugin's shipped `prose` output style and every other kind layer, so a change to that canon changes every voice the plugin ships.
</reference_note>

<voice_canon>
The shared voice rules, transcluded from the authored canon every kind and the shipped output style render from — one source, every surface.

Lead with the substance. The first words carry the action, the answer, or the event — never a warm-up, a preamble, or a restatement of the question.

Plain words. The short common word over the long one; the concrete noun over the metaphorical one; the active voice over the passive. Cut every word that can be cut. No stock metaphors, no jargon where an everyday word exists.

No filler words. "Please", "sorry", "successfully", "note that", and "in order to" are cut on sight; the remaining words carry the meaning.

Assert only what is demonstrated. No significance adverbs ("deeply", "fundamentally"), no authenticity adverbs ("genuinely", "truly", "actually"), no stakes inflation. If a thing matters, the content shows it.

One term, one meaning. Each concept keeps one name throughout; one word never names two concepts.

Failures state what happened and what to do next — two parts, in that order, in plain language, without blame and without apology ritual.

Sentence case for titles, headings, and labels: first word capitalized, the rest lowercase except proper nouns. No all-caps emphasis.

Standard punctuation. Em dashes sparingly, straight quotes, no unicode decoration, no bold-first bullet scaffolding — structure and word choice carry emphasis, not typeface.

</voice_canon>

<inherited_rules>
Every `/prose-standards` anti-pattern applies unchanged except where `<overrides>` relaxes it — word choice (significance and authenticity adverbs, overused vocabulary, ornate nouns, pompous verbs), tone (false suspense, unnecessary metaphors, hypothetical openers, asserted clarity, stakes inflation, condescension), formatting (em-dash overuse, unicode decoration), and the sentence- and composition-level rules as far as fragments carry them. Composing skills load `/prose-standards` for the full descriptions and examples.

The `/prose-standards` `<rule_packs>` bind wherever their feature appears in the surface — the instruction pack on a stepped empty state or onboarding sequence, the table pack on a comparison or pricing table rendered as an element.
</inherited_rules>

<overrides>
The following base rules are RELAXED for interface text.

Fragments are the norm for surface elements. The base rule that every sentence needs a subject and a verb yields to the element's function: button labels, menu items, column headers, and field labels are verb or noun fragments ("Save draft", "Last updated"). Body text inside an element — an error description, an empty-state explanation — returns to complete sentences.

Repetition across elements is consistency, not duplication. The base one-point-once rule governs a piece read linearly; a surface is scanned. The same term, the same phrase pattern, and the same construction repeated across parallel elements is required — variation across parallel elements reads as a difference in meaning.
</overrides>

<additional_rules>
Rules specific to surface elements, on top of `<voice_canon>`.

Buttons and links start with the verb that names what happens: "Create project", not "New". A destructive action names its object: "Delete 3 files", never bare "Confirm".

Brevity is per element. Buttons at three words or fewer; titles and labels that fit without truncation; tooltips one sentence; notifications lead with the event in the first clause. When an element needs a second sentence, the second sentence is a candidate for a link to docs instead.

Empty states orient. What belongs here and how to add the first one — never a bare "No items".

Confirmation asks with the consequence. The question names what will happen, and the affirmative button repeats the action verb — never "Are you sure?" with "Yes/No".
</additional_rules>

<success_criteria>
Interface text meets this layer when every element leads with its action or object, case and terminology are consistent across the surface, each element fits its brevity cap, errors pair what-happened with what-next, and no base anti-pattern survives outside the two declared overrides — and the catalog itself is sound: every additional rule above states a test applicable to a rendered element.
</success_criteria>
