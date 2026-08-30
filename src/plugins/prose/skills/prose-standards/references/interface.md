# Interface style layer

The interface kind: text the reader meets inside a designed surface, such as app chrome, a button, a label, an empty state, an error message, a tooltip, a notification, an email template, or a short web-page section. The base catalog and the voice canon bind except where the overrides below relax them. Structural conventions for the kind — the surface inventory and element parallelism — live in the matching `/prose-architecture-standards` reference.

## Overrides

The following base rules are RELAXED for interface text.

Fragments are the norm for surface elements. The base rule that every sentence needs a subject and a verb yields to the element's function: button labels, menu items, column headers, and field labels are verb or noun fragments ("Save draft", "Last updated"). Body text inside an element — an error description, an empty-state explanation — returns to complete sentences.

Repetition across elements is consistency, not duplication. The base one-point-once rule governs a piece read linearly; a surface is scanned. The same term, the same phrase pattern, and the same construction repeated across parallel elements is required; variation across parallel elements reads as a difference in meaning.

## Element wording

Buttons and links start with the verb that names what happens: "Create project", not "New". A destructive action names its object: "Delete 3 files", never bare "Confirm".

Brevity is per element.

- Buttons: three words or fewer.
- Titles and labels: fit without truncation.
- Tooltips: one sentence.
- Notifications: the event in the first clause.

When an element needs a second sentence, the second sentence is a candidate for a link to docs instead.

Empty states orient. What belongs here and how to add the first one; never a bare "No items".

Errors pair what happened with what to do next, in that order, in plain language, without blame and without apology ritual.

Confirmation asks with the consequence. The question names what will happen, and the affirmative button repeats the action verb; never "Are you sure?" with "Yes/No".

Titles and labels are sentence-case fragments; case and terminology stay consistent across the surface.
