# Outcome Engineering

PROVIDES the Outcome Engineering methodology as product truth, separate from the plugin surfaces that deliver it
SO THAT plugins, runtime tools, language standards, and product-specific overlays
CAN derive their behavior from a stable methodology specification rather than owning the methodology locally

## Assertions

### Compliance

- ALWAYS: methodology governance lives under this node when it declares how Outcome Engineering works independently of a particular shipped plugin, runtime package, or repository integration ([audit])
- ALWAYS: plugin, runtime, and language-specific specs outside this node cite the full path to the methodology spec or decision they implement when they depend on this governance ([audit])
- NEVER: a plugin shipping surface owns methodology truth merely because it carries the skill, thin agent, or generated instruction that delivers the methodology ([audit])
