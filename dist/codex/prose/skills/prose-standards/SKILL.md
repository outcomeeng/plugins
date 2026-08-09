---
name: prose-standards
user-invocable: false
description: >-
  Prose anti-patterns enforced across all skills. Loaded by other skills, not invoked directly.
allowed-tools: Read
---

<objective>
The catalog of 30+ prose anti-patterns across 6 categories, plus the ordered kind-detection procedure the prose routers execute.
</objective>

<success_criteria>
Prose follows these standards when no anti-pattern in this catalog survives in it — word choice, sentence structure, paragraph structure, tone, formatting, and composition each evaluated against the prose rather than assumed clean, and every match either rewritten to carry the same meaning without the pattern or kept for a reason the prose itself makes evident.

The catalog itself is sound when every anti-pattern entry carries a name, the rule, and at least one worked avoid-example, and the kind-detection procedure's five tests are ordered, exhaustive, and mutually exclusive at first match.
</success_criteria>

<reference_note>
This is a reference skill. Composing prose skills load these patterns explicitly before writing or reviewing. It is not a standalone workflow.
</reference_note>

<kind_detection>

One ordered procedure classifies any text into exactly one kind. `/author-prose` and `/audit-prose` execute it; first match decides.

1. **Ownership.** A repository or domain workflow governs the artifact — a spec, ADR, PDR, `SKILL.md`, `PLAN.md`, `ISSUES.md`, or root agent guide? Stop and route to that workflow. The prose surface never touches it.
2. **Audience.** The reader is a team colleague with working context — one who skims and may return to a specific section later, wherever the team keeps it — a workspace tool or a repository? Kind: **internal-docs** -> `/internal-docs-standards`.
3. **Function.** The text explains or instructs the use of a product — tutorial, how-to, reference, conceptual guide? Kind: **docs** -> `/docs-standards`.
4. **Unit.** The text is a fragment embedded in a designed surface — app chrome, button, label, empty state, error message, tooltip, notification or email template, short web-page section? Kind: **interface** -> `/interface-standards`.
5. **Otherwise.** The text is a self-contained piece read start to finish. Kind: **copy** -> `/copy-standards`.

Chat responses to the user are excluded from the prose surface entirely. Operational prose — a code comment, a commit message, an agent-facing instruction — is excluded the same way; the workflow that owns it governs it.

Boundary consequences:

- A web page routes by unit: its chrome and section fragments are interface; an article rendered on it is copy.
- Documentation wins over unit: an error-message reference page is docs; the error message itself, in product, is interface.
- Marketing splits the same way: long-form is copy; headlines, CTAs, and feature blurbs are interface.
- A document whose parts differ in kind receives each part's own layer, and audit findings name the kind per finding.
- Text the procedure leaves ambiguous is resolved by the interactive caller asking the user to select a kind from this list — never by guessing, never by inventing a style outside it. A dispatched audit honors a dispatch-declared kind only for text this procedure leaves ambiguous — ownership outranks a declared kind; when the dispatch declares none, the ambiguity is reported in the verdict and the plausible kinds' shared rules are audited.

</kind_detection>

<word_choice>

**Significance adverbs** ("quietly", "deeply", "fundamentally") -- Don't reach for adverbs like "quietly", "deeply", "fundamentally", "remarkably", or "arguably" to make mundane descriptions feel significant. If something is important, show it -- don't signal it with an adverb.

Avoid: "quietly orchestrating workflows, decisions, and interactions", "the one that quietly suffocates everything else", "a quiet intelligence behind it"

**Authenticity adverbs** ("genuinely", "truly", "actually") -- Don't use "genuinely", "truly", "actually", "really", or "essentially" to assert that something is real or authentic. If the rest of the sentence demonstrates the quality, the adverb is redundant. If it doesn't, the adverb is a substitute for showing it. Either way, cut it. The adjective form "genuine" is equally contaminated -- use "real" or "specific" when a qualifier is needed, or drop the qualifier entirely.

Avoid: "a genuinely transformative experience", "This is a genuine concern", "users who truly need this feature", "what actually matters here", "This essentially means that..."

**"Delve" and overused vocabulary** -- Don't use "delve", "certainly", "utilize", "leverage" (as a verb), "robust", "streamline", "harness", "genuine", or "genuinely". Prefer plain, specific alternatives.

Avoid: "Let's delve into the details...", "Delving deeper into this topic...", "We certainly need to leverage these robust frameworks..."

**"Tapestry", "landscape", and ornate nouns** -- Don't reach for grandiose nouns where simpler ones work. Avoid "tapestry", "landscape", "paradigm", "synergy", "ecosystem" (when used loosely), and "framework" as vague filler.

Avoid: "The rich tapestry of human experience...", "Navigating the complex landscape of modern AI...", "The ever-evolving landscape of technology..."

**The "serves as" dodge** -- Prefer "is" or "are" over pompous substitutes like "serves as", "stands as", "marks", or "represents".

Avoid: "The building serves as a reminder of the city's heritage.", "The station marks a pivotal moment in the evolution of regional transit."

</word_choice>

<sentence_structure>

**Negative parallelism** -- Don't frame points as "It's not X -- it's Y." This creates false profundity. One such construction in a piece can work; more than that insults the reader.

Avoid: "It's not bold. It's backwards.", "Feeding isn't nutrition. It's dialysis.", "Half the bugs you chase aren't in your code. They're in your head."

**"Not X. Not Y. Just Z."** -- Don't build fake tension by negating two things before landing a point.

Avoid: "Not a bug. Not a feature. A fundamental design flaw.", "Not ten. Not fifty. Five hundred and twenty-three lint violations across 67 files."

**"The X? A Y."** -- Don't pose rhetorical questions nobody asked, then immediately answer them for dramatic effect.

Avoid: "The result? Devastating.", "The worst part? Nobody saw it coming.", "The scary part? This attack vector is perfect for developers."

**Anaphora abuse** -- Don't repeat the same sentence opening multiple times in quick succession.

Avoid: "They assume that users will pay... They assume that developers will build... They assume that ecosystems will emerge..."

**Tricolon abuse** -- One rule-of-three is elegant. Don't stack multiple tricolons back-to-back.

Avoid: "Products impress people; platforms empower them. Products solve problems; platforms create worlds. Products scale linearly; platforms scale exponentially."

**"It's worth noting"** -- Don't use filler transitions that introduce points without connecting them. Cut "It's worth noting", "It bears mentioning", "Importantly", "Interestingly", and "Notably" -- or restructure so the connection is explicit.

**Superficial analyses** -- Don't append a present participle phrase to inject shallow significance. If an observation needs "highlighting its importance" tacked on, rewrite the observation so it speaks for itself.

Avoid: "contributing to the region's rich cultural heritage", "underscoring its role as a dynamic hub of activity and culture"

**False ranges** -- Only use "from X to Y" when there is a real spectrum with a meaningful middle. Don't use it to dress up a list of two loosely related things.

Avoid: "From innovation to implementation to cultural transformation.", "From the singularity of the Big Bang to the grand cosmic web."

**Gerund fragment litany** -- Don't follow a claim with a stream of verbless gerund fragments -- standalone sentences with no grammatical subject. Once the point is made, move on.

Avoid: "Fixing small bugs. Writing straightforward features. Implementing well-defined tickets."

**Tautological definitions** -- Don't define a quality using the quality itself. "A genuine change does not revert" uses "genuine" to mean "does not revert" -- the predicate restates the adjective. State the test directly and drop the adjective.

Avoid: "An irreversible change does not revert.", "A truly important decision has lasting consequences.", "Real leaders inspire their teams."

**Redundant paired examples** -- Don't pair a concrete example with a generic one in the same sentence. One vivid image is stronger than one vivid and one vague. If the second example does not add a distinct image or cover a different case, it dilutes the first.

Avoid: "when the leader goes on vacation or moves to a different role", "in meetings and other professional settings"

</sentence_structure>

<paragraph_structure>

**Short punchy fragments** -- Don't use a string of very short sentences or fragments as standalone paragraphs to manufacture emphasis. This is an inhuman writing style -- use it sparingly and deliberately, not as a default cadence.

Avoid: "He published this. Openly. In a book. As a priest.", "These weren't just products. And the software side matched. Then it professionalised. But I adapted."

**Listicle in a trench coat** -- When writing a list, write a list. Don't disguise it as prose by wrapping each item in a paragraph beginning "The first...", "The second...", "The third...".

Avoid: "The first wall is the absence of a free, scoped API... The second wall is the lack of delegated access... The third wall is the absence of scoped permissions..."

</paragraph_structure>

<tone>

**"Here's the kicker"** -- Don't use false-suspense transitions to manufacture drama before an unremarkable point. Cut "Here's the kicker", "Here's the thing", "Here's where it gets interesting", and "Here's what most people miss".

**"Think of it as..."** -- Don't assume the reader needs a metaphor to understand. Only reach for analogy when the analogy is more illuminating than the direct explanation.

Avoid: "Think of it like a highway system for data.", "Think of it as a Swiss Army knife for your workflow."

**"Imagine a world where..."** -- Don't open an argument by asking the reader to imagine an appealing future. Make the argument directly.

Avoid: "Imagine a world where every tool you use -- your calendar, your inbox, your documents -- has a quiet intelligence behind it..."

**False vulnerability** -- Don't perform self-awareness. Simulated candor -- pretending to break the fourth wall or admit a bias -- reads as hollow. Real honesty is specific and has stakes; don't fake it.

Avoid: "And yes, I'm openly in love with the platform model", "This is not a rant; it's a diagnosis"

**"The truth is simple"** -- Don't assert that a point is obvious, clear, or simple -- prove it. Telling the reader the point is clear is a signal it isn't.

Avoid: "The reality is simpler and less flattering", "History is unambiguous on this point"

**Grandiose stakes inflation** -- Don't inflate the significance of every argument to world-historical scale. Match the stakes of each claim to what the text demonstrates.

Avoid: "This will fundamentally reshape how we think about everything.", "will define the next era of computing"

**"Let's break this down"** -- Don't adopt a teacher-student tone with a reader who hasn't asked for it. Cut "Let's break this down", "Let's unpack this", "Let's explore", and "Let's dive in".

**Vague attributions** -- Don't cite unnamed authorities. Without a name for the expert, the study, or the publication, don't invoke them. Don't inflate one source into "several publications" or one person's view into a widely held consensus.

Avoid: "Experts argue that this approach has significant drawbacks.", "Industry reports suggest that adoption is accelerating."

**Invented concept labels** -- Don't coin compound labels -- "supervision paradox", "acceleration trap", "workload creep" -- and treat them as established terms. Name things precisely, or make the argument without the label.

</tone>

<formatting>

**Em-dash overuse** -- Use em dashes sparingly -- two or three per piece at most. Don't use them as a default mechanism for asides and pivots.

Avoid: "The problem -- and this is the part nobody talks about -- is systemic.", "Not recklessly, not completely -- but enough -- enough to matter."

**Bold-first bullets** -- Don't begin every bullet with a bolded phrase. When bullets are needed, let the content carry the list -- not typographic decoration.

Avoid: "**Security**: Environment-based configuration with...", "**Performance**: Lazy loading of expensive resources..."

**Unicode decoration** -- Don't use unicode arrows, curly quotes, or other characters that require special input. Use plain text equivalents (->), straight quotes, and standard punctuation.

</formatting>

<composition>

**Fractal summaries** -- Don't summarize every section before and after writing it. Don't restate at the document level what the section level just said.

Avoid: "In this section, we'll explore... [3000 words later] ...as we've seen in this section.", "And so we return to where we began."

**The dead metaphor** -- Introduce a metaphor, use it, then move on. Don't return to the same metaphor throughout an entire piece.

Avoid: "The ecosystem needs ecosystems to build ecosystem value.", Walls and doors used 30+ times in the same article.

**Historical analogy stacking** -- Don't rapid-fire a list of historical companies or tech revolutions to build authority. One well-chosen analogy is stronger than five weak ones.

Avoid: "Apple didn't build Uber. Facebook didn't build Spotify. Stripe didn't build Shopify. AWS didn't build Airbnb."

**One-point dilution** -- Don't restate a single argument in ten different ways across thousands of words. Once the point is made, move forward or stop.

**Content duplication** -- Don't repeat entire sections or paragraphs verbatim within the same piece. Read back what was written before continuing.

**The signposted conclusion** -- Don't announce the conclusion. End the piece -- don't label the ending. Cut "In conclusion", "To sum up", and "In summary".

**"Despite its challenges..."** -- Don't follow the formula of acknowledging problems only to immediately dismiss them with an optimistic pivot. If there are real challenges, engage with them.

Avoid: "Despite these challenges, the initiative continues to thrive.", "Despite its industrial and residential prosperity, Korattur faces challenges typical of urban areas."

</composition>
