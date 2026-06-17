# Website archetype — decision topics

Decisions a content/marketing website typically needs, as **prompts to confirm or prune** against the
new product's hypothesis. Each is a proposal, not an inherited answer. Derived from the decision
records in the source product (xiperlabs.com).

## Root-level

- **Rendering strategy** (`15`, ADR) — Static generation vs server rendering vs client hydration, and
  where the client/server boundary sits.
- **Feature-flag gating** (`18`, ADR) — How content/variants are gated and targeted by flag, and how
  flags resolve across environments.

## Under `design-system`

- **Design language** (`15`, PDR) — The visual language and interaction principles.
- **Component library** (`16`, ADR) — Which component/primitive library and how it's adopted.
- **Color architecture** (`18`, ADR) — Token model, theming, contrast guarantees.

## Under `analytics-platform`

- **Analytics platform** (`15`, ADR) — Which analytics/flag provider and how events are captured testably.
- **Identity levels** (`17`, PDR) — Anonymous vs tracked visitor identity and how it resolves.

## Under `page`

- **Section composition** (`15`, PDR/ADR) — How pages compose from sections and how variants slot in.
- **Content portability** (`18`, ADR) — Exposing page content beyond rendered HTML (machine-readable access).

## Under `conversion`

- **Positioning / product offering** (`15`, PDR) — How the product is positioned; tier/edition boundaries
  that all conversion copy must respect.
- **Lead-capture API** (`15`, ADR) — How signups/leads are captured and where they go.

## Under `branding` (if present)

- **Careers content** (`15`, PDR) — How careers/company content is sourced and laid out.
