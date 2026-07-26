# Outcome Engineering Methodology Releases

Status: Proposed

This document states the model and the reasoning behind it. It does not describe how to build any of it.

## The problem

A consumer repository declares the methodology it adheres to. Today that declaration reads:

```yaml
methodology:
  source: outcomeeng/spec-tree
  version: 0.85.0
```

`0.85.0` is a plugin distribution version. It is not a methodology version, and the two are different quantities: the delivering plugin has released dozens of times without the methodology changing at all.

The cause is not carelessness in filling the field. `source` correctly names the plugin that delivers the methodology, but nothing in that plugin declares which **methodology** it provides — so the only number the installed side exposes is its own package version. The wrong value is the only observable one.

This is why an explicit provider declaration is required rather than merely desirable. Correcting the consumer's number without it returns the package version at the next reading.

## Release subject

Outcome Engineering methodology releases version the methodology itself. Plugin packages, the SPX CLI, and other delivery mechanisms retain independent versions.

A methodology release is a coordinated contract for humans and coding agents. It binds the human-readable methodology, agent behavior, generated instruction behavior, and the repository declarations through which consumers adopt that contract.

## Authority

The authoritative methodology release repository assigns methodology versions and determines what a given version is.

Delivery mechanisms report rather than decide. A plugin declares the release it provides and the releases it supports; neither declaration establishes what a release means. A plugin may lag the current release, and while a next release is being prepared a plugin may temporarily deviate in specifics — this avoids churn in the written methodology while implementations learn quickly. Such deviation is temporary and confined to specifics. What a release contains is settled by the methodology, never by whichever delivery mechanism shipped last.

## Version semantics

Outcome Engineering methodology releases follow Semantic Versioning:

- A **major** release introduces a methodology generation with incompatible changes to the consumer contract.
- A **minor** release extends a generation compatibly.
- A **patch** release corrects a release without changing its contract.

Methodology generations behave as language editions. Consumers opt into a generation explicitly, and delivery mechanisms can understand more than one generation without collapsing their contracts.

## Historical releases

| Release | Methodology generation                                                 | Repository adoption commit                 |
| ------- | ---------------------------------------------------------------------- | ------------------------------------------ |
| 1.0.0   | `specs/work/` with capability, feature, and story structure            | `ba8b1e454a387fe861817faabbb783e2666f4634` |
| 2.0.0   | Durable `spx/` with capability, feature, and story structure           | `d0dfab59a3cdf7ef9e1e2904ff0109b6048a569a` |
| 3.0.0   | Recursive enabler and outcome nodes with deterministic context loading | `42433920bafb8f1dc1f91b1b41f7d98788f94bd4` |

The current methodology release is 3.1.0.

Historical release tags identify the commits where this repository adopted each generation. The changelog describes methodology changes independently of plugin and package changes.

## Release contract

Each methodology release has:

- one SemVer identity;
- a changelog entry describing its methodology changes;
- a complete human-and-agent contract;
- migration guidance when adoption changes existing consumer artifacts;
- an explicit relationship to delivery mechanisms that provide or support it.

Methodology release identity remains stable regardless of which plugin or package version delivers it.

## Provider and plugin compatibility

The methodology-providing plugin declares the exact methodology release it provides. Every plugin whose behavior depends on Outcome Engineering declares the range of methodology releases it supports.

```json
{
  "methodology": {
    "source": "outcomeeng/spec-tree",
    "provides": "4.0.0",
    "supports": ">=3.1.0 <5.0.0"
  }
}
```

`provides` is exact. `supports` is a range over methodology releases whose grammar the release contract defines. The example above states comparator bounds illustratively and commits to no particular serialization; existing ecosystems differ on whether a range may express a disjoint set at all, so that expressiveness is a decision the grammar makes rather than an assumption this proposal inherits.

Support ranges express compatibility with individually selected methodology releases. They do not express that one consumer repository contains artifacts from several releases.

The exact methodology release selected by a consumer must fall within every enabled plugin's support range. An empty compatibility intersection is an invalid plugin set, and the report of an unsatisfied selection names the plugin whose range excludes it.

**Prereleases are named, never implied.** A release still in preparation carries a prerelease identifier such as `4.0.0-rc.1`. A stable range never implies support for a prerelease of any release it covers. A prerelease is usable only when the provider, every supporting plugin, and the consumer each name it explicitly.

## Consumer declaration

A consumer repository declares an exact methodology source and version. The version selects the methodology behavior used for newly authored and materially revised artifacts.

```yaml
methodology:
  source: outcomeeng/spec-tree
  version: 4.0.0
```

Repository declarations do not change as a side effect of routine SPX or plugin upgrades. Methodology adoption is an explicit consumer decision.

## Independently versioned artifacts

The smallest independently migratable methodology artifact carries its own edition identity. From version 4, a specification file declares its methodology version in YAML front matter. Earlier specification artifacts, which carry no front matter, are identified deterministically by their earlier representation.

Edition identity attaches to the specification file rather than to a containing directory, because directory representation and file identity can change in different releases and must remain separately determinable.

Artifacts from accepted editions interoperate within one repository. Their relationships retain the same meaning across editions, and conversion between supported representations preserves methodology information.

This model permits gradual migration without parallel copies of the specification tree and without an ecosystem-wide cutover.

## Version 4 contract

Version 4:

- adds YAML front matter to specification files;
- names specification files `{slug}.spec.md`;
- introduces the `.surface` node representation;
- makes `.enabler` invalid as a version 4 representation.

An `.enabler` encountered during an authorized transition remains a version 3 artifact. Its temporary acceptance does not make it valid under the version 4 contract.

## Mixed-edition transition

A repository adopting a new major declares that major as its exact methodology version and explicitly identifies the finite set of earlier editions it temporarily accepts.

```yaml
methodology:
  source: outcomeeng/spec-tree
  version: 4.0.0
  <term-pending>:
    - 3.1.0
```

The accepted-earlier-editions declaration is distinct from a plugin's `supports`. `supports` is a compatibility range over alternative single selections — any one of which a consumer might choose. The accepted-earlier-editions declaration is a finite set of exact earlier editions simultaneously present in one repository. The two are not interchangeable, and a range cannot express the second: a range offers several interchangeable single-version selections, while a mixed-edition repository intentionally contains artifacts governed by distinct editions at the same time.

During this state:

- the selected version is the default for new and materially revised artifacts;
- each artifact is interpreted according to its own deterministic edition identity;
- earlier artifacts remain identifiable migration debt;
- the repository exposes the remaining earlier-artifact inventory;
- removing the accepted-earlier-editions declaration marks completion of the transition.

**Adjacent-major bound.** For a repository selecting major N, the accepted-earlier-editions declaration may name exact releases from N-1 only. This bounds set membership and the resulting compatibility cost; it does not by itself define when a transition completes. Because a repository selecting N+1 may accept only releases from N, selecting N+1 requires eliminating any remaining N-1 artifacts first. Every reader is therefore bounded to two adjacent majors, while a single migration may run for months.

**Completion.** A transition completes when the earlier-edition artifact inventory reaches zero and the accepted-earlier-editions declaration is removed. Completion is established by the inventory, not by elapsed time and not by the adjacent-major bound.

## Deprecation and removal

A representation deprecated in major N is removed in major N+1. The removal is not optional and does not wait for an unrelated reason for N+1 to exist.

This rule is stated separately from the transition-completion rule above and serves a different purpose. Completion describes when one repository has finished migrating. This rule bounds what the methodology and its delivery mechanisms must keep understanding.

The bound exists because compatibility is not free to the maintainer. Every tolerated earlier representation is a code path that is maintained and regression-tested on every patch release, so an unbounded acceptance window makes that cost unbounded too. One major is a known expiry that can be budgeted, and it makes each deprecation a decision with a price attached rather than a default: at a major boundary the question becomes which representations are worth carrying for one more cycle and which should simply be removed.

## Migration invariants

- Readers understand every edition accepted by the repository before artifacts of the newly selected major appear.
- Writers produce artifacts of the selected major once that major is selected.
- Edition identity is explicit or deterministically inferred; ambient plugin versions never reinterpret an artifact.
- Conversion preserves identity, relationships, metadata, and unknown front-matter fields.
- Earlier-edition acceptance is finite, observable, and removable.
- Forward methodology development occurs in the selected major after it is selected.
- The transition completes only when no accepted earlier-edition artifacts remain.

These invariants avoid the ecosystem split, dependency deadlock, ambiguous interpretation, parallel source trees, and indefinite compatibility period associated with Python 2 to Python 3.

## Changelogs

**The reader is a consumer repository** — its maintainers and its agents, opening the changelog mid-upgrade to answer "what changed for me, and what must I now do?"

**Inclusion follows consumer effect, not source artifact class.** An entry earns its place when the change alters what a consumer can rely on, must do, or must know. A change to a specification or a decision that alters the consumer contract belongs in the methodology changelog; a change to any artifact that leaves the consumer contract untouched is excluded regardless of which class it belongs to. Artifact class is a poor proxy for consumer effect and must not be used as the test.

**Three release lines, each on its own clock.**

| Line        | Records                                                                                                                   | Cadence    |
| ----------- | ------------------------------------------------------------------------------------------------------------------------- | ---------- |
| Methodology | generation transitions, compatible extensions, deprecations and removals, support standing                                | rare       |
| Per plugin  | what changed in that plugin                                                                                               | frequent   |
| Marketplace | events no single plugin owns: a new agent harness, a plugin added, removed, or renamed, a floor that moves across plugins | occasional |

**Sections** are `Breaking`, `Added`, `Changed`, `Removed`, `Fixed`, `Requires`. `Breaking` is elevated rather than folded into `Changed`, because a rename breaks invocation outright and must not be discoverable only by careful reading. `Requires` carries floor and compatibility advances so a version constraint is readable without prose.

**In-session accessibility is a release-contract requirement.** A consumer's checkout contains installed delivery artifacts and nothing else from the providing repository, so a changelog kept only in that repository is unreachable by the consumer's agent. Each changelog line must be readable by a consumer agent in-session and without network access. Which delivery surface satisfies that requirement is a design decision outside this proposal.

## Open

- **The terminology for the accepted-earlier-editions field.** `accepts` is the leading candidate: it reads naturally as the repository accepting exact earlier editions, and it avoids the value judgment carried by `legacy`. The concept is settled; the field name is not part of the proposed contract until the terminology is chosen, and the declaration is written `<term-pending>` throughout until then.
