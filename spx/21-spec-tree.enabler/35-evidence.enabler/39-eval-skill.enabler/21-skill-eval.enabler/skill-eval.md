# Skill Eval

PROVIDES producer-coupled eval evidence for LLM-driven skill behavior, including source-derived prompts, independently selected case oracles, and one-case convergence
SO THAT `/eval` and skill authors
CAN prove a shipped skill's structured behavior changes when the real producing skill changes

## Assertions

### Compliance

- ALWAYS: skill-eval authoring couples evidence to the real producing skill and keeps the expected verdict outside the model-facing task ([audit])
- ALWAYS: skill-eval authoring derives case inputs independently, establishes a falsifying producer mutation, and returns producer defects to the producer-owning workflow ([audit])
- NEVER: skill-eval authoring accepts a prompt-only simulation, self-answering case, or mismatched evidence identity ([audit])
