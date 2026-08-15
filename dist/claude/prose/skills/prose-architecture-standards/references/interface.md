# Interface structure

The structural conventions for the interface kind — text fragments embedded in a designed surface. A prose ADR for a surface selects from these shapes and binds them as rules; the surface's writer complies.

## Surface inventory

A surface is structured as an inventory of elements, not a sequence of sentences. The ADR names the element set a flow needs — titles, labels, buttons, empty states, errors, confirmations, notifications — so a missing element is a structural gap, not a wording problem. An element being written is rarely alone: the inventory is collected before any element is worded.

## Terminology map

One term per concept across the surface. The ADR records the surface's established term for each shared concept; a new element binds to that vocabulary, and a new term enters only for a concept the surface does not yet name.

## Element parallelism

Parallel elements are phrased in parallel. The same phrase pattern and the same construction repeat across elements that play the same role, because variation across parallel elements reads as a difference in meaning. The parallel sets — which elements mirror which — are a structural decision.

## Element information shape

Each element type carries a fixed information shape the wording fills:

- An error carries two parts in order: what happened, then what to do next.
- An empty state orients: what belongs here and how to add the first one.
- A confirmation names the consequence, and its affirmative action repeats the action verb.
- A notification leads with the event.
- A stepped sequence — onboarding, a multi-step empty state — is a procedure and follows the instruction pack's step structure.

When an element needs a second sentence, the second sentence is a candidate for a link to docs instead — the structural decision is where depth lives, on the surface or behind it.
