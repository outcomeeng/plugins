# Document Types and Requirements

Complete reference of all document types in the legacy Outcome Engineering hierarchy and their requirements.

## Work Item Hierarchy

```
Product
└── Capability (E2E level)
    ├── {slug}.capability.md     ✅ REQUIRED
    ├── {topic}.prd.md           ⚠️ OPTIONAL (enrichment)
    ├── decisions/
    │   ├── adr-NNN_{slug}.md    ⚠️ OPTIONAL (architectural)
    │   └── pdr-NNN_{slug}.md    ⚠️ OPTIONAL (product)
    ├── tests/                   ⚠️ OPTIONAL (co-located, permanent home)
    └── Feature (Integration level)
        ├── {slug}.feature.md    ✅ REQUIRED
        ├── {topic}.trd.md       ⚠️ OPTIONAL (enrichment)
        ├── decisions/
        │   ├── adr-NNN_{slug}.md ⚠️ OPTIONAL (architectural)
        │   └── pdr-NNN_{slug}.md ⚠️ OPTIONAL (product)
        ├── tests/               ⚠️ OPTIONAL (co-located, permanent home)
        └── Story (Unit level)
            ├── {slug}.story.md  ✅ REQUIRED
            └── tests/           ⚠️ OPTIONAL (determines status)
```

## Document Types

### Product-Level Documents

**Location**: `specs/`

| Document      | Pattern                 | Required? | Purpose                              |
| ------------- | ----------------------- | --------- | ------------------------------------ |
| Project Guide | `CLAUDE.md`             | ✅ YES    | Project structure and navigation     |
| Product ADRs  | `decisions/adr-*.md`    | ⚠️ NO      | Product-wide architectural decisions |
| Product PDRs  | `decisions/pdr-*.md`    | ⚠️ NO      | Product-wide product decisions       |
| Product PRD   | `{product-name}.prd.md` | ⚠️ NO      | Optional product-wide requirements   |

### Capability-Level Documents

**Location**: `specs/work/{status}/capability-NN_{slug}/`

| Document        | Pattern                  | Required?                | Purpose                             |
| --------------- | ------------------------ | ------------------------ | ----------------------------------- |
| Capability Spec | `{slug}.capability.md`   | ✅ YES                   | E2E scenario definition             |
| PRD             | `{topic}.prd.md`         | ⚠️ NO (optional)          | Product requirements catalyst       |
| Capability ADRs | `decisions/adr-NNN_*.md` | ⚠️ NO                     | Capability-scoped arch decisions    |
| Capability PDRs | `decisions/pdr-NNN_*.md` | ⚠️ NO                     | Capability-scoped product decisions |
| Tests           | `tests/`                 | ⚠️ NO (determines status) | Co-located E2E tests (permanent)    |

**Note**: PRD is optional enrichment. If PRD exists but spec is missing, offer to create spec from PRD.

### Feature-Level Documents

**Location**: `specs/work/{status}/capability-NN_{slug}/feature-NN_{slug}/`

| Document     | Pattern                  | Required?                | Purpose                                  |
| ------------ | ------------------------ | ------------------------ | ---------------------------------------- |
| Feature Spec | `{slug}.feature.md`      | ✅ YES                   | Integration scenario definition          |
| TRD          | `{topic}.trd.md`         | ⚠️ NO (optional)          | Technical requirements catalyst          |
| Feature ADRs | `decisions/adr-NNN_*.md` | ⚠️ NO                     | Feature-scoped arch decisions            |
| Feature PDRs | `decisions/pdr-NNN_*.md` | ⚠️ NO                     | Feature-scoped product decisions         |
| Tests        | `tests/`                 | ⚠️ NO (determines status) | Co-located integration tests (permanent) |

**Note**: TRD is optional enrichment. If TRD exists but spec is missing, offer to create spec from TRD.

### Story-Level Documents

**Location**: `specs/work/{status}/.../story-NN_{slug}/`

| Document   | Pattern           | Required?                | Purpose                           |
| ---------- | ----------------- | ------------------------ | --------------------------------- |
| Story Spec | `{slug}.story.md` | ✅ YES                   | Atomic implementation definition  |
| Tests      | `tests/`          | ⚠️ NO (determines status) | Co-located unit tests (permanent) |
| Completion | `tests/DONE.md`   | ⚠️ NO (signals DONE)      | Evidence of completion            |

**Note**: Stories do NOT have their own ADRs or PDRs. They inherit decisions from parent feature/capability.

## Document Content Requirements

### Specification Files (.capability.md, .feature.md, .story.md)

**Must contain**:

- **Functional Requirements**: What the work item delivers
- **Acceptance Criteria**: How to know it's complete
- **Dependencies**: BSP dependencies on other work items

**May contain**:

- **Context**: Background and rationale
- **Implementation Notes**: Guidance for implementers

### Requirements Documents (PRD/TRD)

**PRD (Product Requirements Document)**:

- User value proposition
- Customer journey
- Measurable outcomes (X% improvement targets)
- Acceptance tests (BDD scenarios)

**TRD (Technical Requirements Document)**:

- System architecture
- Validation strategy with test levels
- Test infrastructure requirements
- BDD scenarios at appropriate levels
- Infrastructure gaps (if any)

### Architectural Decision Records (ADR)

**Must contain**:

- **Purpose**: What architectural concern this decision governs (atemporal — state as permanent truth)
- **Decision**: What is being decided
- **Consequences**: Trade-offs and implications
- **Compliance**: How adherence will be verified (code review criteria)
- **Testing Strategy**: Test levels for components

### Product Decision Records (PDR)

**Must contain**:

- **Purpose**: What product behavior this decision governs (atemporal — state as permanent truth)
- **Decision**: What product behavior is being decided
- **Product Invariants**: Observable behaviors users can rely on
- **Compliance**: How adherence will be verified (product behavior validation)

**ADR vs PDR**:

- **ADR**: Governs code architecture (HOW to build)
- **PDR**: Governs product behavior (WHAT users experience)

## PRD/TRD as Optional Enrichment

PRD and TRD documents are **optional** at all levels. The spec file (`.capability.md`, `.feature.md`, `.story.md`) is the only required document for each work item.

**When PRD/TRD exists without spec file:**

If a PRD or TRD exists at a level but the corresponding spec file is missing, offer to create the spec from the requirements document. This handles cases where work was initiated from a requirements document but the spec wasn't yet created.

## Status Determination

Status values: OPEN, IN_PROGRESS, DONE

## Test Co-Location

Tests stay co-located with their work item permanently (no graduation):

| Level      | Test Location                    | Test Type   |
| ---------- | -------------------------------- | ----------- |
| Capability | `specs/.../capability-NN/tests/` | E2E         |
| Feature    | `specs/.../feature-NN/tests/`    | Integration |
| Story      | `specs/.../story-NN/tests/`      | Unit        |

## BSP Numbering

**BSP** (Backlog Sequencing Priority): Two-digit numbers (10-99)

**Rules**:

- Lower number = must complete first
- Used for dependency ordering at all levels
- Gaps allowed (10, 20, 30... or 11, 12, 13...)
- Never reuse numbers

**Examples**:

- `capability-10_core-cli` must complete before `capability-20_advanced-features`
- `story-30_build` must complete before `story-40_test`
