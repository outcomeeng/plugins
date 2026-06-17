# Worked example: xiperlabs.com (website)

A real, authored content/marketing website spec tree — the pattern-match reference for the `website`
archetype. Source: `xiperinc/xiperlabs.com`. 105 enablers, 36 outcomes — the outcome-bearing case.

## Top-level partition (as authored)

```text
spx/
  15-static-rendering.adr.md · 16-client-server-boundary.adr.md · 16-feature-flag-gating.adr.md
  21-infrastructure.enabler/      build/validation/lint/schema + maintainability(ast) + production-verification
  24-environment.enabler/         shared / local / production contracts
  32-design-system.enabler/       foundations -> components -> contexts -> domain (large UI library)
  32-platform.enabler/            posthog analytics · feature flags · user-identity
  43-site.enabler/                navigation (desktop / mobile)
  54-page.enabler/                composition · format · mdx · variant-delivery
  76-branding.outcome/            company pages, careers
  76-conversion.outcome/          landing-page (-> sections) · product-pages · lead-capture
  76-developer-adoption.outcome/  documentation · showcases
  76-discovery.outcome/           metadata · crawlability(enabler) · structured-data
```

## How the bets are written (the authored outcome voice)

- **conversion** — WE BELIEVE THAT clear product positioning and frictionless CTAs WILL convert
  hardware engineers and curious developers into early access signups CONTRIBUTING TO 500 early access
  signups within 6 months.
- **discovery** — WE BELIEVE THAT search-optimized metadata, structured data, and crawlability WILL
  drive > 1,000 monthly organic visits CONTRIBUTING TO 500 early access signups within 6 months.
- **branding** — WE BELIEVE THAT consistent professional identity across company pages and careers
  content WILL establish credibility that attracts engineering talent CONTRIBUTING TO applicant
  conversion rate > 5%.

Each bet is backed by a measurable signal (signups, organic visits, applicant rate) in the product
spec's evidence table — the mark of a real outcome. The `32-platform.enabler` (PostHog analytics,
flags, identity) is the measurement substrate those bets read from.

## Outcomes nest to redesignable sections

`76-conversion.outcome → 32-landing-page.outcome` nests ~14 section outcomes (hero, comparison,
roadmap, CTA, …). A section that doesn't convert gets redesigned — different assertions, same
conversion hypothesis. That is the defining outcome property, made concrete.

## How the seed generalizes this

- Rebases indices onto the bands (enablers 21–50, outcomes 51–79): `page` moves out of the outcome
  band (was 54); the two `32`s and four `76`s spread to irregular distinct indices.
- Renames: `platform → analytics-platform`, `developer-adoption → adoption`.
- Folds `maintainability → ast` (AST-based enforcement, an implementation choice) into a generic
  `infrastructure → enforcement` child; `ast` stays here in the authored reference only.
- `conversion` + `discovery` are core outcomes; `adoption` + `branding` are optional, gated on signals.

xiperlabs.com's own tree is preserved here as the authored reference; the generalized seed lives in
`../seed-tree.json`.
