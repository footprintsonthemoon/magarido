# BRouter Motorcycle Profiles

Offline motorcycle routing profiles for BRouter and OsmAnd with independent control over **curviness** and **hilliness**.

## Goals

The project aims to provide predictable motorcycle routing profiles ranging from efficient routing to strongly curvy touring routes.

The routing model treats curviness and hilliness as independent dimensions.

Initial profiles:

* Fast
* Fast Curvy
* Curvy
* Very Curvy
* Curvy Hilly

## Status

Early development.

The project is currently specification-first. Routing behaviour is being defined and tested before the first production profiles are released.

## Planned Architecture

```text
src/moto-base.brf
        │
        +-- config/presets.yaml
        │
        v
tools/generate_profiles.py
        │
        v
profiles/*.brf
```

One canonical routing model is maintained. User-facing profiles are generated from presets.

## Design Principles

* suitable motorcycle through-roads over arbitrary small roads
* curviness independent of hilliness
* no residential zig-zag routing
* no unpaved roads by default
* legal OSM access restrictions respected
* bounded detours
* fully offline routing with BRouter

## Documentation

The detailed routing specification is available in:

```text
docs/specification.md
```

## Target Platform

Primary target:

* BRouter
* OsmAnd
* Android
* offline navigation

## License

License to be selected before the first public release.

