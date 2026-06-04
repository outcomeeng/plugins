# Website archetype

A public content/marketing website that converts and engages many anonymous visitors.

**Outcome topology: has outcomes.** Visitors are many and anonymous, and their behavior change
(convert, return, adopt, apply) is measurable. The bets are outcomes; the rendering machinery is the
enabler substrate beneath them. Its structural correlate: a **measurement substrate**
(`analytics-platform`) the outcome bets read from — if a candidate website has no measurement
substrate, reconsider whether its bets are actually measurable.

## When the router matches a product here

- Users are many and anonymous (public visitors), not a few known operators.
- The goal is a measurable behavior change (conversion, organic traffic, adoption).
- Primary surface is the web.
- The natural decomposition is content pages + conversion bets over a rendering substrate.

## What it seeds

- **Enabler substrate** (always): `infrastructure`, `environment`, `design-system`,
  `analytics-platform`, `site`, `page`.
- **Core outcomes** (always): `conversion`, `discovery`.
- **Optional outcomes** (gated — see `archetype.toml` `[concerns.gates]`): `adoption`, `branding`.

Indices follow the per-directory bands (enablers 21–50, outcomes 51–79), so at every level the
substrate sorts below the bets. Two website signatures are baked in: the `analytics-platform`
measurement substrate (what makes outcomes measurable) and `page → variant-delivery` + feature flags
(the experimentation machinery that lets an outcome redesign its sections without changing the
hypothesis). Outcomes nest to redesignable page sections (`conversion → landing-page → hero/comparison/CTA`).

## Source

Generalized from **xiperlabs.com** (`xiperinc/xiperlabs.com`), a marketing site converting visitors to
early-access signups. See `example/` for the real authored bookend tree.
