# Interface structure

The structural conventions for the interface kind — text fragments embedded in a designed surface. A prose ADR for a surface selects from these shapes and binds them as rules; the surface's writer complies.

## Surface inventory

A surface is structured as an inventory of elements, not a sequence of sentences. The ADR names the element set a flow needs — titles, labels, buttons, empty states, errors, confirmations, notifications — so a missing element is a structural gap, not a wording problem. An element being written is rarely alone: the inventory is collected before any element is worded.

## Terminology map

The ADR records the surface's established term for each shared concept, so a new element binds to that vocabulary and a new term enters only for a concept the surface does not yet name. One term per concept is the voice canon's rule; what the ADR decides is which term is the home.

## Element parallelism

Which elements mirror which is a structural decision. The ADR names the parallel sets — the elements that play the same role and therefore carry one phrase pattern — because variation across parallel elements reads as a difference in meaning. How that pattern is worded belongs to the style layer.

## Element information shape

The ADR names each element's type. The type fixes how many parts the element carries and in what order; the style layer supplies the wording for each. A stepped sequence — onboarding, a multi-step empty state — is a procedure, so the instruction pack governs its steps wherever it appears.

Where depth lives is structural: an element whose content outgrows its shape either splits or links out, and the ADR decides which.
