# Methodology Directory Guide

This directory holds **Claude Code-specific methodology** for building plugins, skills, and tests within this marketplace. It is not general Outcome Engineering methodology — that lives upstream at [`outcomeeng/methodology`](https://github.com/outcomeeng/methodology). These documents govern how agents structure their contributions to this plugin marketplace.

## Contents

| File                                                           | Purpose                                                                                                                                   | When to read                                                                                          |
| -------------------------------------------------------------- | ----------------------------------------------------------------------------------------------------------------------------------------- | ----------------------------------------------------------------------------------------------------- |
| [`skills/skill-structure.md`](skills/skill-structure.md)       | Spec-tree plugin's skill design: foundation vs action layers, marker-based state detection, ownership model, conversational flow contract | Before creating or restructuring a skill in the spec-tree plugin                                      |
| [`test/test-foundation.md`](test/test-foundation.md)           | Testing philosophy: the three dimensions (detection, validity, cost), test-level selection, the 4-part progression, anti-patterns         | Before writing or auditing tests anywhere in the marketplace; loaded by language-specific test skills |
| [`research/skill-invocation.md`](research/skill-invocation.md) | Empirical study of skill activation reliability (Seleznov, Feb 2026): directive descriptions, hook patterns, 20× activation impact        | When writing or reviewing a skill's `description` field                                               |

## Authoritative source of truth

The spec-tree plugin's inline foundation (`src/plugins/spec-tree/skills/understand/SKILL.md`) is authoritative for methodology terms (node types, states, assertion types, ordering). Its sibling `references/` directory carries conditional operational detail and compatibility pointers. This directory holds the rationale and research behind those rules — read the inline foundation for rules, read here for why.

When the inline plugin foundation and these documents disagree, the plugin wins and these documents need updating.
