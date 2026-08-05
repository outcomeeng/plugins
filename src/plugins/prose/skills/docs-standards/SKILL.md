---
name: docs-standards
user-invocable: false
description: >-
  Standards for the docs kind — documentation that explains or instructs the use of a product: tutorials, how-tos, reference, conceptual guides. Simplified ASD-STE100 structural rules. Reference skill loaded by the composed docs skills, not invoked directly.
allowed-tools: Read
---

<objective>
The docs kind's standards layer over `/prose-standards` — inherited rules, the instruction-fragment override, and the simplified ASD-STE100 structural rules for all documentation.
</objective>

<reference_note>
This is a reference skill. `/author-docs` and `/audit-docs` load it; the routers reach it only through them. The layer simplifies ASD-STE100: the structural writing rules survive; the controlled dictionary does not — its principle survives as the one-term-one-meaning rule.
</reference_note>

<inherited_rules>
Every `/prose-standards` anti-pattern applies unchanged — word choice, sentence structure, paragraph structure, tone, formatting, and composition. Most cannot occur in text that follows the structural rules below; where they can, they bind at zero tolerance. Composing skills load `/prose-standards` for the full descriptions and examples.
</inherited_rules>

<overrides>
One base rule is RELAXED for docs.

Numbered-step imperatives stand alone. The base rule against listicles governs prose arguments; a procedure is a numbered list by design, and each step is an imperative sentence that would read as commanding fragments in an essay. Steps lead with the action verb.
</overrides>

<additional_rules>
The simplified ASD-STE100 structural rules. Each is a hard cap, not a preference.

Instructions cap at 20 words per sentence; descriptions cap at 25. A sentence over its cap splits.

One instruction per sentence. "Save the file and restart the server" is two instructions: two sentences or two steps.

Active voice. "The parser rejects invalid input", never "invalid input is rejected".

Simple tenses only. Present for facts and descriptions, imperative for instructions, simple past only for prerequisites already performed. No perfect tenses, no progressive forms.

No verbal "-ing" clauses. "The command exits and prints a summary", never "the command exits, printing a summary". Nouns that end in -ing ("the setting", "a warning") are words, not violations.

No should, would, may, or might. A behavior happens or it does not: "the server restarts", not "the server should restart". "Can" states capability; "will" states a promised future — both survive.

Condition before command. "If the build fails, read the log", never "Read the log if the build fails". The reader executes in reading order.

Noun clusters cap at three nouns. "The configuration file parser cache directory" loses the reader; break it with a preposition.

Paragraphs cap at six sentences and carry one topic.

Articles are never dropped. "Open the file", not telegraphic "Open file".

One term, one meaning. Each concept keeps exactly one name across the entire doc set, and each term names exactly one concept — the surviving principle of the STE dictionary, without its word list.
</additional_rules>

<success_criteria>
Documentation meets this layer when every sentence is inside its length cap in active voice and a simple tense, each instruction stands alone with its condition first, no modal hedging or verbal "-ing" clause survives, noun clusters and paragraphs are inside their caps, articles are present, terminology is one-to-one — and the catalog itself is sound: every additional rule above states a mechanically checkable cap or a test applicable to a sentence.
</success_criteria>
