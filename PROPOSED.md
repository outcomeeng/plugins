# Methodology Versioning and Changelogs

A proposal. It states the model and the reasoning behind it. It does not describe how to build any of it.

## The problem

A consumer repository declares the methodology it adheres to. Today that declaration reads:

```yaml
methodology:
  source: outcomeeng/spec-tree
  version: 0.85.0
```

`0.85.0` is a plugin distribution version. It is not a methodology version, and the two are different quantities: the plugin has released dozens of times without the methodology changing at all.

The cause is not carelessness in filling the field. `source` correctly names the plugin that delivers the methodology, but nothing in that plugin declares which **methodology** it implements — so the only number the installed side exposes is its own package version. The wrong value is the only observable one.

Fixing the declaration alone would not hold. The installed side has to declare what it implements, or the package version returns.

## Authority

The methodology repository assigns methodology versions. It is the source for the terms and operating rules, and it determines what version X is.

Plugins report which methodology version they implement. A plugin may lag the methodology, and during the release process for a new version a plugin may temporarily deviate in specifics — this avoids churn in the written methodology while implementations learn fast. The deviation is temporary and local to specifics. What version X means is settled by the methodology, never by whichever plugin shipped last.

## The version scheme

The methodology carries a single semantic version.

| Bump  | Meaning                                                    | Consequence for an existing tree |
| ----- | ---------------------------------------------------------- | -------------------------------- |
| major | the node model changes — a generation boundary             | the tree stops conforming        |
| minor | additive — a new assertion type, verification type, or tag | the tree still conforms          |
| patch | clarification with no grammar change                       | none                             |

Generations map onto majors. The methodology has had three: the first and second shared a fixed three-level hierarchy; the third introduced two recursive node types. The third generation is therefore `3.x.x`, and the six-kind model in preparation is `4.0.0`.

The current `3.N.M` is deliberately unresolved here. It follows from enumerating what actually changed in the node model since the third generation began, which the methodology changelog produces. Picking a number first and justifying it afterward inverts that.

## Four declarations

Each answers a different question, and none substitutes for another.

**The methodology assigns the version.** It states what exists and what each version means.

**A plugin declares the range it supports.** A plugin operates on trees written against more than one version, so it declares a set:

```text
methodology.supports: "^3.4.0 || ^4.0.0"
```

**A consumer repository declares one version.** A repository targets one grammar, so it declares a point, not a range:

```yaml
methodology:
  source: outcomeeng/spec-tree
  version: 4.0.0
```

**A node declares its own version.** From the fourth generation onward, a spec file carries YAML front matter naming the version it is written against. A node without that front matter is a third-generation node. The tree therefore describes its own migration state at node granularity, and no repository-level construct has to approximate it.

## Range conventions

Ranges follow the semantics every package ecosystem already uses, so nothing here is novel to learn.

- **Union for spanning majors.** `"^3.4.0 || ^4.0.0"` is the established idiom for supporting two majors through a transition — the same shape peer dependencies, engine constraints, and language-version requirements use.
- **Prerelease identifiers for a version still in flight.** A methodology being prepared is `4.0.0-rc.1`. It sorts below `4.0.0`, and ranges over `3.x` do not match it unless it is named, so opting into a draft is explicit on both sides.
- **Point versions on the consumer side, never ranges.** A range there would express nothing: the grammar's own tolerance already covers a mixed tree, and per-node front matter records which nodes have moved.

## Resolution

Language and domain plugins will not all support a new major on the day it lands. That is expected, and it resolves as an intersection.

A consumer's declared version has to satisfy every installed plugin's supported range. When it does not, the answer names the plugin that is behind rather than reporting a bare mismatch — the consumer's next action is either waiting for that plugin or dropping it, and neither is discoverable from a two-value comparison.

The same resolution reports how much migration remains: a count of nodes still on the previous generation's forms, drawn from the front matter that is present or absent on each node.

## Deprecation

**A form deprecated in major N is removed in major N+1.**

The removal is not optional and does not wait for an unrelated reason for N+1 to exist. Compatibility is carried for exactly one major.

This bound exists because compatibility is not free to the maintainer. Every tolerated legacy form is a code path that is maintained and regression-tested on every patch release. An open-ended deprecation window makes that bill open-ended too. One major is a known expiry that can be budgeted, and it makes each deprecation a decision with a price attached rather than a default — at a major boundary the question becomes which forms are worth carrying for one more cycle and which should simply break.

It also holds consumers to a real deadline. A tree still using a removed form when N+1 ships is unsupported, which is what the support window already says: the current and prior versions are supported, everything older is not, and the window rolls forward with each release.

## Changelogs

**The reader is a consumer repository** — its maintainers and its agents, opening the changelog mid-upgrade to answer "what changed for me, and what must I now do?"

That single fact settles the content. An entry earns its place only when the reader must do or know something: a skill or agent added, renamed, or removed; a behavior change in something they invoke; a change that rewrites a file in their repository; a dependency floor that advances. Specifications, decisions, tests, build machinery, generated output, formatting, and release mechanics stay out — they are real work, and none of it is the reader's to act on.

**Three lines, each on its own clock.**

| Line        | Records                                                                                                                    | Cadence                             |
| ----------- | -------------------------------------------------------------------------------------------------------------------------- | ----------------------------------- |
| Methodology | generation transitions, additive grammar changes, support standing                                                         | rare — three changes in three years |
| Per plugin  | what changed in that plugin                                                                                                | frequent                            |
| Marketplace | events no single plugin owns: a new agent harness, a plugin added or removed or renamed, a floor that moves across plugins | occasional                          |

**Sections** are `Breaking`, `Added`, `Changed`, `Removed`, `Fixed`, `Requires`. `Breaking` is elevated rather than folded into `Changed` because renames break invocation outright and must not be discoverable only by careful reading. `Requires` carries floor advances so a version constraint is readable without prose.

**Delivery reaches the consumer in-session.** A consumer's checkout contains installed plugin trees and nothing else from this repository, so anything at this repository's root is invisible to them. Each plugin already ships a lifecycle skill that reports its own version; presenting its changelog beside that version is the same surface, already discoverable, already offline.

## Open

- **The current methodology version.** Falls out of the methodology changelog.
- **Whether a consumer's declaration becomes mandatory.** It is optional today. A repository carrying a tracked spec tree while declaring no durable methodology identity is already recognizable as a distinct state, so the question is whether that state is a warning or an error.
