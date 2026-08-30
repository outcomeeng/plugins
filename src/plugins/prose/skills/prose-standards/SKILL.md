---
name: prose-standards
user-invocable: false
description: >-
  Prose anti-patterns enforced across all skills. Loaded by other skills, not invoked directly.
allowed-tools: Read
---

<objective>
The shared voice canon, the catalog of 30+ prose anti-patterns across 6 categories, the rule packs for observable features inside any kind, and the per-kind style layers.
</objective>

<success_criteria>
Approve a text only after finding no catalog anti-pattern in it outside the supplied kind's declared overrides. Evaluate word choice, sentence structure, paragraph structure, tone, formatting, and composition against the text. Rewrite every match to carry the same meaning without the pattern, or keep it for a reason evident in the text.

Judge the catalog sound only after finding in every anti-pattern entry a name, the rule, and at least one worked avoid-example. Judge a rule pack sound only after finding its triggering feature and the rules of the pack. Judge a style layer sound only after finding, for every declared override, the relaxed base rule and the bounds of the relaxation.
</success_criteria>

<reference_note>
Load this skill as a reference from every prose workflow skill. Treat a missing kind as an error and abort. Never infer a kind.
</reference_note>

<voice_canon>
{!% include 'prose/voice/fragment.md' %!}

</voice_canon>

<kind_layers>

Find in a kind's style layer its overrides, each a bounded relaxation of a base rule, and the style rules of that kind alone. Read the supplied kind's file before writing or judging text of that kind. Apply every base rule not explicitly relaxed in the layer.

| Kind            | Style layer                                       |
| --------------- | ------------------------------------------------- |
| `copy`          | `${CLAUDE_SKILL_DIR}/references/copy.md`          |
| `interface`     | `${CLAUDE_SKILL_DIR}/references/interface.md`     |
| `documentation` | `${CLAUDE_SKILL_DIR}/references/documentation.md` |

Find each kind's structural conventions in the matching reference of `/prose-architecture-standards`. Decide structure in a prose ADR, never here.

</kind_layers>

<rule_packs>

Apply a rule pack at every occurrence of its feature in the text, inside every kind. Give one text one kind and one rule pack per feature found in it, a runbook's numbered procedure and an essay's comparison table among them.

**Instructions**: apply this rule pack to numbered steps, a procedure, or any sentence telling the reader to perform an action.

- Cap an instruction sentence at 20 words. Split it over the cap.
- Put one instruction in each sentence. Split "Save the file and restart the server" into two sentences or two steps.
- Put the condition before the command. "If the build fails, read the log", never "Read the log if the build fails". The reader executes in reading order.
- Use no should, would, may, or might. State the action as happening: "restart the server", not "the server should be restarted".
- Lead each step with its action verb. "Open the file", never "First, you'll need to open the file".
- Never drop an article. "Open the file", not telegraphic "Open file".

**Tables**: apply this rule pack to any table.

- Use a table only for two or more crossing dimensions. Write one dimension as a list.
- Put a phrase in each cell. Move any paragraph-length cell into prose beneath the table.
- Make the header row visually distinct. Bold a first column only as the row key.

</rule_packs>

<word_choice>

**Significance adverbs** ("quietly", "deeply", "fundamentally"): Show importance in the content. Never use adverbs like "quietly", "deeply", "fundamentally", "remarkably", or "arguably" to make a mundane description feel significant.

Avoid: "quietly orchestrating workflows, decisions, and interactions", "the one that quietly suffocates everything else", "a quiet intelligence behind it"

**Authenticity adverbs** ("genuinely", "truly", "actually"): Show the quality in the rest of the sentence. Never use "genuinely", "truly", "actually", "really", or "essentially" to assert that something is real or authentic. Treat the adjective "genuine" the same. Use "real" or "specific" as the qualifier, or drop the qualifier.

Avoid: "a genuinely transformative experience", "This is a genuine concern", "users who truly need this feature", "what actually matters here", "This essentially means that..."

**"Delve" and overused vocabulary**: Use plain, specific words. Never use "delve", "certainly", "utilize", "leverage" (as a verb), "robust", "streamline", "harness", "genuine", or "genuinely".

Avoid: "Let's delve into the details...", "Delving deeper into this topic...", "We certainly need to leverage these robust frameworks..."

**"Tapestry", "landscape", and ornate nouns**: Use the simpler noun. Never use "tapestry", "landscape", "paradigm", "synergy", "ecosystem" (when used loosely), "framework", "seam", or "boundary" as vague filler.

Avoid: "The rich tapestry of human experience...", "Navigating the complex landscape of modern AI...", "The ever-evolving landscape of technology..."

**The "serves as" dodge**: Write "is" or "are". Never use the substitutes "serves as", "stands as", "marks", or "represents".

Avoid: "The building serves as a reminder of the city's heritage.", "The station marks a pivotal moment in the evolution of regional transit."

</word_choice>

<sentence_structure>

**Negative parallelism**: State the point plainly. Never frame it as "It's not X -- it's Y." to manufacture profundity. Use one such construction per piece at most, and treat a second as an insult to the reader.

Avoid: "It's not bold. It's backwards.", "Feeding isn't nutrition. It's dialysis.", "Half the bugs you chase aren't in your code. They're in your head."

**"Not X. Not Y. Just Z."**: Make the point first. Never create tension by negating one or two things before the point.

Avoid: "Not a bug. Not a feature. A fundamental design flaw.", "Not ten. Not fifty. Five hundred and twenty-three lint violations across 67 files."

**"The X? A Y."**: State the point directly. Never pose rhetorical questions. Never add questions for dramatic effect.

Avoid: "The result? Devastating.", "The worst part? Nobody saw it coming.", "The scary part? This attack vector is perfect for developers."

**Anaphora abuse**: Vary sentence openings. Never repeat the same opening in quick succession.

Avoid: "They assume that users will pay... They assume that developers will build... They assume that ecosystems will emerge..."

**Tricolon abuse**: List every needed item and no more. Never use a tricolon unless three is the accurate and minimal number of items.

Avoid: "Products impress people; platforms empower them. Products solve problems; platforms create worlds. Products scale linearly; platforms scale exponentially."

**"It's worth noting"**: Connect a point to the one before it only where the relationship is otherwise ambiguous. Never use throat-clearing ("It's worth noting", "It bears mentioning", "Importantly", "Interestingly", "Notably") or any other transition without effect on the meaning of what follows.

**Superficial analyses**: State an observation to stand on its own. Never append a present participle phrase such as "highlighting its importance" to inject significance. Never add a parenthetical such as "(Important!)" or "(don't skip this)" in a heading or anywhere else.

Avoid: "contributing to the region's rich cultural heritage", "underscoring its role as a dynamic hub of activity and culture"

**False ranges**: Use "from X to Y" only for a real spectrum with a meaningful middle. Never use it to dress up a list of two loosely related things.

Avoid: "From innovation to implementation to cultural transformation.", "From the singularity of the Big Bang to the grand cosmic web."

**Gerund fragment litany**: Give every sentence a subject and a finite verb. Never follow a claim with a run of gerund fragments.

Avoid: "Fixing small bugs. Writing straightforward features. Implementing well-defined tickets."

**Tautological definitions**: State the test directly and drop the adjective. Never define a quality using the quality itself. In "A genuine change does not revert", read "genuine" as "does not revert", a predicate restating the adjective.

Avoid: "An irreversible change does not revert.", "A truly important decision has lasting consequences.", "Real leaders inspire their teams."

**Redundant paired examples**: Use one vivid example per point. Never pair a concrete example with a generic one in the same sentence. Cut a second example without a distinct image or a different case.

Avoid: "when the leader goes on vacation or moves to a different role", "in meetings and other professional settings"

</sentence_structure>

<paragraph_structure>

**Short punchy fragments**: Write paragraphs of full sentences. Use a very short sentence or a fragment as a standalone paragraph at most once per piece, for emphasis. Never string them together to manufacture emphasis, an inhuman cadence.

Avoid: "He published this. Openly. In a book. As a priest.", "These weren't just products. And the software side matched. Then it professionalised. But I adapted."

**Listicle in a trench coat**: When writing a list, write a list. Never disguise it as prose by wrapping each item in a paragraph beginning "The first...", "The second...", "The third...".

Avoid: "The first wall is the absence of a free, scoped API... The second wall is the lack of delegated access... The third wall is the absence of scoped permissions..."

</paragraph_structure>

<tone>

**"Here's the kicker"**: State the point without a drumroll. Cut "Here's the kicker", "Here's the thing", "Here's where it gets interesting", and "Here's what most people miss".

**"Think of it as..."**: Explain directly. Add an analogy only after the direct explanation.

Avoid: "Think of it like a highway system for data.", "Think of it as a Swiss Army knife for your workflow."

**"Imagine a world where..."**: Make the argument directly. Never open it by asking the reader to imagine an appealing future.

Avoid: "Imagine a world where every tool you use -- your calendar, your inbox, your documents -- has a quiet intelligence behind it..."

**False vulnerability**: Be honest with specifics and stakes, or say nothing. Never perform self-awareness by pretending to break the fourth wall or admit a bias. The reader hears simulated candor as hollow.

Avoid: "And yes, I'm openly in love with the platform model", "This is not a rant; it's a diagnosis"

**"The truth is simple"**: Prove the point. Never call it obvious, clear, or simple. The reader takes that label as a signal of the opposite.

Avoid: "The reality is simpler and less flattering", "History is unambiguous on this point"

**Grandiose stakes inflation**: Match the stakes of each claim to the evidence in the text. Never claim a consequence beyond the scale of that evidence.

Avoid: "This will fundamentally reshape how we think about everything.", "will define the next era of computing"

**"Let's break this down"**: Address the reader as a peer. Cut "Let's break this down", "Let's unpack this", "Let's explore", and "Let's dive in".

**Vague attributions**: Name the expert, the study, or the publication, or leave the citation out. Never inflate one source into "several publications" or one person's view into a widely held consensus.

Avoid: "Experts argue that this approach has significant drawbacks.", "Industry reports suggest that adoption is accelerating."

**Invented concept labels**: Name things precisely, or make the argument without a label. Never coin compound labels ("supervision paradox", "acceleration trap", "workload creep") and treat them as established terms.

</tone>

<formatting>

**Em-dash overuse**: Use a pair of em dashes only as parentheses around an aside, and a single em dash only before what a human would say after a pause. Never use em dashes as a default mechanism for asides and pivots.

Avoid: "The problem -- and this is the part nobody talks about -- is systemic.", "Not recklessly, not completely -- but enough -- enough to matter."

**Bold-first bullets**: Put the emphasis of a list in its content. Never begin every bullet with a bolded phrase.

Avoid: "**Security**: Environment-based configuration with...", "**Performance**: Lazy loading of expensive resources..."

**Unicode decoration**: Use plain text equivalents (->), straight quotes, standard punctuation, and the em dash as the canon permits. Never use unicode arrows, curly quotes, or any other decorative character.

</formatting>

<composition>

**Fractal summaries**: Say each thing once, at one level. Never summarize a section before and after writing it, and never restate the section's content at the document level.

Avoid: "In this section, we'll explore... [3000 words later] ...as we've seen in this section.", "And so we return to where we began."

**The dead metaphor**: Introduce a metaphor, use it, then move on. Never return to the same metaphor throughout an entire piece.

Avoid: "The ecosystem needs ecosystems to build ecosystem value.", Walls and doors used 30+ times in the same article.

**Historical analogy stacking**: Choose one historical analogy at most. Never rapid-fire a list of companies or tech revolutions to build authority.

Avoid: "Apple didn't build Uber. Facebook didn't build Spotify. Stripe didn't build Shopify. AWS didn't build Airbnb."

**One-point dilution**: Make each point once, then move forward or stop. Never restate one argument across the piece.

**Content duplication**: Read back the text so far before continuing. Never repeat a section or paragraph verbatim within the same piece.

**The signposted conclusion**: End the piece. Never announce or label the ending. Cut "In conclusion", "To sum up", and "In summary".

**"Despite its challenges..."**: Engage with real challenges. Never acknowledge a problem only to dismiss it with an optimistic pivot.

Avoid: "Despite these challenges, the initiative continues to thrive.", "Despite its industrial and residential prosperity, Korattur faces challenges typical of urban areas."

</composition>
