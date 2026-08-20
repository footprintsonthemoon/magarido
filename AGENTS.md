# Project Instructions

## Project Purpose

This repository provides open-source motorcycle routing profiles for BRouter, primarily intended for offline use with OsmAnd.

The project follows a specification-first approach. Routing behaviour must be defined and documented before it is implemented.

## Core Principles

* Maintain one canonical routing model.
* Curviness and hilliness are independent routing dimensions.
* User-facing profiles should be generated from shared routing logic rather than maintained independently.
* Preserve applicable OpenStreetMap access restrictions.
* Do not prefer small roads merely because they are slow or complex.
* Curvy routing should favour enjoyable through-roads rather than residential streets, service roads, or arbitrary route complexity.
* Hilly routing should favour meaningful elevation variation without creating excessive detours.
* Unpaved roads must not be used by default.
* Routing behaviour must remain understandable and explainable.
* Avoid undocumented heuristics.

## Development Workflow

1. Update the specification before changing routing behaviour.
2. Implement the smallest change required.
3. Test the change against documented reference routes.
4. Review route distance, estimated travel time, road classes, elevation behaviour, urban routing, and unexpected detours.
5. Document relevant behavioural changes in the changelog.

## Source Structure

The intended architecture is:

```text
brouter-motorcycle/
├── AGENTS.md
├── README.md
├── LICENSE
├── CHANGELOG.md
├── docs/
│   ├── specification.md
│   ├── routing-model.md
│   ├── osmand-setup.md
│   └── testing.md
├── src/
│   └── moto-base.brf
├── config/
│   └── presets.yaml
├── profiles/
│   ├── moto-fast.brf
│   ├── moto-fast-curvy.brf
│   ├── moto-curvy.brf
│   ├── moto-very-curvy.brf
│   └── moto-curvy-hilly.brf
├── tools/
│   └── generate_profiles.py
└── tests/
    └── routes/
```

## Canonical Source

Routing logic belongs in the canonical source profile.

Generated profiles must not contain independently maintained routing logic.

Preset files may change parameter values, but must not duplicate the implementation.

## Routing Parameters

The primary routing dimensions are:

```text
curviness
0 = fast
1 = fast-curvy
2 = curvy
3 = very-curvy

hilliness
0 = neutral
1 = hilly
2 = very-hilly
```

These parameters must remain independent.

A profile such as `curvy-hilly` is therefore a parameter combination, not a separate routing algorithm.

## Safety and Access

Do not weaken or bypass:

* legal access restrictions
* motorcycle restrictions
* motor vehicle restrictions
* one-way restrictions
* turn restrictions
* road closures where represented in OpenStreetMap

Prefer conservative behaviour when access information is ambiguous.

## Code Quality

* Keep BRF expressions readable.
* Name intermediate variables descriptively.
* Add comments explaining non-obvious routing decisions.
* Avoid unexplained numeric constants.
* Keep generated files reproducible.
* Do not manually patch generated profiles.
* Prefer simple heuristics that can be tested over complex heuristics that are difficult to reason about.

## Testing

Every relevant routing change should be checked against a stable set of reference routes.

Tests should examine at least:

* route distance
* estimated travel time
* elevation gain and loss where available
* motorway usage
* primary road usage
* secondary and tertiary road usage
* residential road usage
* unpaved road usage
* urban routing
* excessive detours
* unexpected loops

Subjective motorcycle route quality may be recorded as an additional evaluation criterion but must not replace measurable checks.

## Documentation

Any material routing decision should be reflected in `docs/specification.md` or `docs/routing-model.md`.

The README is user-facing documentation and should remain concise.

