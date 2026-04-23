# Methodology Directory Guide

This directory holds **Claude Code-specific methodology** for building plugins, skills, and tests within this marketplace. It is not general Outcome Engineering methodology — that lives upstream at [`outcomeeng/methodology`](https://github.com/outcomeeng/methodology). These documents govern how agents structure their contributions to this plugin marketplace.

## Contents

| File                                                             | Purpose                                                                                                                                   | When to read                                                                                             |
| ---------------------------------------------------------------- | ----------------------------------------------------------------------------------------------------------------------------------------- | -------------------------------------------------------------------------------------------------------- |
| [`skills/skill-structure.md`](skills/skill-structure.md)         | Spec-tree plugin's skill design: foundation vs action layers, marker-based state detection, ownership model, conversational flow contract | Before creating or restructuring a skill in the spec-tree plugin                                         |
| [`testing/testing-foundation.md`](testing/testing-foundation.md) | Testing philosophy: the three dimensions (detection, validity, cost), test-level selection, the 4-part progression, anti-patterns         | Before writing or auditing tests anywhere in the marketplace; loaded by language-specific testing skills |
| [`research/skill-invocation.md`](research/skill-invocation.md)   | Empirical study of skill activation reliability (Seleznov, Feb 2026): directive descriptions, hook patterns, 20× activation impact        | When writing or reviewing a skill's `description` field                                                  |

## Authoritative source of truth

The spec-tree plugin's own references (`plugins/spec-tree/skills/understanding/references/`) are authoritative for methodology terms (node types, states, assertion types, ordering). This directory holds the rationale and research behind those rules — read the plugin references for rules, read here for why.

When plugin references and these documents disagree, the plugin wins and these documents need updating.
