# Magarido -- Routing Specification

## 1. Purpose

This document defines the current functional and architectural
specification for the Magarido routing system.

The goal is not to expose many technical BRouter profiles. The goal is
to express motorcycle-routing intent through a small, understandable set
of controls and translate that intent into reproducible BRouter routing.

The specification describes the current target model. Historical
experiments are mentioned only when they establish a design decision.

## 2. Design Principles

The system shall follow these principles:

1.  **Simple user model**\
    A rider should choose meaningful routing intentions rather than
    internal cost-model parameters.

2.  **Few primary routing characters**\
    The primary choice shall remain Fast, Curvy or Very Curvy.

3.  **Orthogonal dimensions**\
    Routing character, constraints, secondary preferences and vehicle
    characteristics shall remain conceptually separate.

4.  **Time-oriented foundation**\
    Fast, Curvy and Very Curvy shall share the KinematicModel-based
    time-oriented routing foundation.

5.  **Motorcycle character over artificial difference**\
    Curvy profiles should favour attractive motorcycle roads, not merely
    produce routes different from Fast.

6.  **No route-specific hacks**\
    Calibration may use individual roads, but implementation rules must
    generalise.

7.  **Graceful behaviour where alternatives are weak**\
    A stronger preference shall not force an implausible route merely to
    make profiles look different.

8.  **Segment-level intent**\
    Different parts of a journey may use different routing intentions.

9.  **Offline-compatible routing**\
    The routing foundation shall remain compatible with BRouter and
    offline navigation workflows such as OsmAnd.

## 3. Target Environment

The routing engine is BRouter using OpenStreetMap-derived routing data.

The current navigation target is Android with OsmAnd.

The development and planning environment may run on macOS or another
system capable of running the BRouter standalone server and Python
tooling.

## 4. System Model

A route consists of one or more segments.

Each segment may carry its own routing intention:

``` text
segment
    +
routing character
    +
constraints
    +
secondary preferences
    +
vehicle characteristics
        |
        v
profile compilation
        |
        v
BRouter KinematicModel
        |
        v
optional alternative evaluation
        |
        v
segment route
```

A complete tour is formed by joining the routed segments.

## 5. Routing Character

The primary routing character shall be one of:

``` text
fast
curvy
very-curvy
```

Routing character expresses the fundamental trade-off between expected
travel time and desirable motorcycle-road character.

## 6. Fast

Fast shall primarily optimise expected travel time.

Fast shall not explicitly mean:

``` text
prefer motorway
```

Motorways and other high-speed roads may nevertheless be selected when
they produce the best expected travel time under the current vehicle
model and constraints.

An additional constraint should not produce a materially faster route
than the equivalent unconstrained Fast route under the same vehicle
model.

## 7. Curvy

Curvy shall use the same time-oriented foundation as Fast while adding a
moderate preference for roads with desirable motorcycle-routing
characteristics.

Curvy may accept additional travel time when the resulting road
character is meaningfully better.

Curvy must not simply penalise fast roads indiscriminately.

## 8. Very Curvy

Very Curvy shall use the same time-oriented foundation as Fast and Curvy
while applying a stronger motorcycle-road preference than Curvy.

The intended ordering is:

``` text
Fast
    strongest emphasis on expected time

Curvy
    moderate willingness to trade time for road character

Very Curvy
    stronger willingness to trade time for road character
```

Very Curvy shall still remain plausible. It shall not seek detours
solely to differentiate itself from Curvy.

## 9. KinematicModel

The current time-oriented foundation is BRouter's KinematicModel.

The model can account for factors including:

-   speed limits,
-   acceleration and deceleration,
-   rolling resistance,
-   aerodynamic resistance,
-   elevation,
-   junction slowdowns,
-   curve-related speed effects.

The use of KinematicModel is now part of the current architecture, not
an open candidate evaluation.

## 10. Vehicle Characteristics

Vehicle characteristics are independent of routing intention.

The internal model may include values such as:

-   total motorcycle/rider/luggage mass,
-   rolling resistance,
-   aerodynamic resistance,
-   target speed,
-   other KinematicModel parameters.

The current implementation uses a generic touring-motorcycle model.

A future user interface may ask for understandable motorcycle and load
characteristics and translate them into low-level model parameters.

Users should not normally be required to configure physical coefficients
directly.

## 11. Constraints

Constraints modify the set or attractiveness of usable roads
independently of routing character.

Currently validated constraints are:

``` text
avoid_motorways
avoid_toll
```

The same constraints may be combined with Fast, Curvy or Very Curvy.

## 12. Avoid Motorways

`avoid_motorways` expresses the intention to avoid motorway-class roads.

It shall not implicitly mean:

``` text
avoid every toll road
```

and it shall not change the selected routing character.

## 13. Avoid Toll

`avoid_toll` expresses the intention to avoid roads represented as
toll-relevant by the available BRouter/OpenStreetMap data and routing
model.

It shall remain independent of road class.

A country's charging model must not be converted into a generic
assumption that motorway avoidance and toll avoidance are equivalent.

## 14. Toll vs Motorway Semantics

Martigny -\> Aosta is a current regression case.

Observed results:

  Intention                  Distance        Time   Ascent     Cost
  ------------------------ ---------- ----------- -------- --------
  Fast                        73.2 km    83.9 min   1473 m   115474
  Fast + avoid toll           77.9 km   102.1 min   2023 m   140871
  Fast + avoid motorways      73.2 km    83.9 min   1473 m   115474

The Fast and Fast + avoid-motorways geometries were identical, while the
avoid-toll geometry differed.

The Great St Bernard area makes this distinction useful because it
combines road-class and separate toll considerations.

This test establishes semantic independence. It shall not create a
route-specific exception.

## 15. Secondary Preferences

A secondary preference influences route selection without redefining the
primary routing character.

The currently implemented secondary preference is:

``` text
hills
```

with values:

``` text
off
moderate
strong
```

## 16. Hilliness

Hilliness shall remain secondary to routing character.

For motorcycle touring in the current design, Curvy/Very Curvy road
character is more important than accumulating elevation.

Therefore:

``` text
character: curvy
hills: strong
```

shall mean:

``` text
prefer a good Curvy route;
among acceptable possibilities, favour a meaningfully hillier route
```

It shall not mean:

``` text
maximise ascent
```

## 17. Hilliness Implementation

Hilliness is currently implemented by the planning layer using BRouter
alternatives.

The underlying Curvy or Very Curvy profile is calculated first. When
hilliness is requested, the planner evaluates available alternatives
against general criteria such as:

-   additional ascent,
-   ascent relative to route length,
-   additional travel time.

`moderate` shall accept a smaller trade-off than `strong`.

If no sufficiently attractive hillier alternative exists, the baseline
route shall be retained.

Hilliness shall not require a separate public routing character or a
separate family of user-facing `*-hilly` profiles.

## 18. Hilliness Behavioural Requirements

The following requirements apply:

-   `off` shall not deliberately select a route because it is hillier.
-   `moderate` may select a meaningfully hillier alternative within a
    moderate routing trade-off.
-   `strong` may accept a larger routing trade-off.
-   neither level shall blindly maximise ascent.
-   a route that is already strongly mountainous may remain unchanged.
-   hilliness shall not override the selected routing character.
-   the algorithm shall use general rules rather than named-route
    exceptions.

## 19. Hilliness Regression Cases

### 19.1 Biel -\> Neuchatel

``` text
character: curvy
hills: strong
```

Current expected result:

``` text
BRouter alternative: 2
distance: 40.3 km
time: 48.2 min
ascent: 810 m
cost: 70011
```

This demonstrates a case where a substantially hillier alternative is
worth selecting.

### 19.2 Fribourg -\> Altdorf

``` text
character: curvy
hills: moderate
```

Current expected result:

``` text
BRouter alternative: 2
distance: 172.9 km
time: 185.6 min
ascent: 2090 m
cost: 308341
```

This demonstrates hill preference on a longer route.

### 19.3 Thun -\> Andermatt

``` text
character: curvy
hills: strong
```

Current expected result:

``` text
baseline
distance: 113.3 km
time: 132.1 min
ascent: 2674 m
cost: 196336
```

This is an important negative regression case. The baseline is already
strongly mountainous, so a strong hill preference shall not force an
inferior alternative.

## 20. Segment-Based Routing

Segment-based routing is part of the current architecture.

A tour may contain different intentions for different sections:

``` text
Biel
  |
  | Fast
  v
Bern
  |
  | Curvy
  v
Thun
  |
  | Very Curvy
  v
Brienz
  |
  | Curvy
  v
Andermatt
```

This reflects real motorcycle touring better than applying one global
profile to an entire journey.

## 21. Segment Definition

The current planner uses YAML.

Conceptual example:

``` yaml
name: Alpine Tour

segments:
  - from:
      name: Biel
      lon: 7.2468
      lat: 47.1368
    to:
      name: Bern
      lon: 7.4474
      lat: 46.9480
    routing:
      character: fast

  - from:
      name: Bern
      lon: 7.4474
      lat: 46.9480
    to:
      name: Thun
      lon: 7.6292
      lat: 46.7571
    routing:
      character: curvy
      preferences:
        hills: moderate
      constraints:
        avoid_motorways: false
        avoid_toll: false
```

The schema may evolve, but the conceptual separation of character,
constraints and preferences shall remain stable.

## 22. Waypoints

Waypoints serve two roles:

1.  geographic points through which the tour passes,
2.  boundaries at which routing intention may change.

They are therefore part of the planning model rather than merely forced
coordinates inside one global route.

## 23. BRouter Alternatives

BRouter alternatives are candidate routes, not semantic routing modes.

The planner may inspect multiple `alternativeidx` results and select
among them when a preference such as hilliness requires it.

Alternative index alone shall not determine preference.

Cost alone shall not determine hill preference.

The planner must evaluate the characteristics relevant to the stated
user intention.

## 24. Separation of Responsibilities

The architecture consists of three principal layers:

``` text
TOUR PLANNING

    journey
    waypoints
    segments
    per-segment intentions
    alternative selection

            |
            v

ROUTING INTENTION

    Fast / Curvy / Very Curvy
    constraints
    secondary preferences
    vehicle characteristics

            |
            v

ROUTING ENGINE

    BRouter
    KinematicModel
    BRF expressions
    OpenStreetMap data
```

BRouter is responsible for route calculation between defined points.

The planner is responsible for composing multiple routing decisions into
a complete journey and for preference-level decisions that should not be
encoded as separate BRF profile families.

## 25. Profile Compilation

The current planner compiles the profile-relevant portion of a routing
intention into a BRouter BRF based on:

``` text
src/moto-kinematic-base.brf
```

Generated profiles are implementation artefacts.

A routing preference that is handled entirely by planner-level
alternative selection does not need to produce a different BRF.

This prevents a combinatorial explosion such as:

``` text
curvy
curvy-hilly
curvy-hilly-no-motorway
curvy-hilly-no-motorway-no-toll
...
```

The user model shall expose independent controls instead.

## 26. Output

A complete planned tour shall be exportable as:

``` text
GeoJSON
GPX
```

The GPX shall contain:

-   the tour waypoints,
-   a continuous track representing all routed segments.

The current GPX output has been validated with OsmAnd navigation.

## 27. User Interface Priority

A future graphical interface should present controls in approximately
this order:

``` text
1. Routing character
   Fast / Curvy / Very Curvy

2. Important constraints
   Avoid Motorways
   Avoid Toll Roads

3. Secondary preferences
   Hills: Off / Moderate / Strong

4. Optional vehicle configuration
   expressed through understandable motorcycle/load properties
```

Low-level BRouter and KinematicModel parameters shall not normally be
exposed.

## 28. Calibration and Validation

Routing changes shall be validated using multiple geographically and
functionally different routes.

The preferred development method is:

``` text
observation
    ->
hypothesis
    ->
general implementation
    ->
independent validation
```

A calibration route may reveal a problem, but the solution shall not
encode that route specifically.

## 29. Validation Categories

The test set should cover at least:

-   short mixed routes,
-   fast-vs-secondary-road routes,
-   alpine routes,
-   long mixed routes,
-   routes where motorway use is clearly beneficial,
-   routes where motorway avoidance matters,
-   toll-specific cases,
-   routes with useful hillier alternatives,
-   routes already naturally mountainous,
-   routes where profiles should legitimately converge.

## 30. Route Similarity

Two routing characters do not need to produce different geometry on
every route.

Identical or nearly identical routes are acceptable when the network
offers no meaningful alternative.

Future tooling may quantify:

-   shared route percentage,
-   unique route percentage,
-   distance delta,
-   time delta,
-   ascent delta,
-   motorway share,
-   road-class distribution,
-   corridor similarity.

Such metrics should complement visual inspection rather than replace it.

## 31. Motorcycle-Road Character

Road classification is an imperfect proxy for motorcycle attractiveness.

Future research may investigate additional reliable signals such as:

-   settlement context,
-   traffic environment,
-   road continuity,
-   surface quality,
-   elevation context,
-   geometric sinuosity,
-   heading-change or curve density.

No single signal shall automatically define a good motorcycle road.

For example, geometric winding alone must not make a residential street
more desirable than a high-quality secondary road.

## 32. Optional Evidence Semantics

Direct OpenStreetMap road evidence remains sufficient to produce a route.
BRouter pseudo tags such as `estimated_traffic_class` and
`estimated_town_class` are optional contextual evidence, not authoritative
routing truth. Missing evidence is not low, high or neutral evidence and must
not create a routing advantage.

No H2 traffic modifier or H3 measured-data source is active in v1. Detailed
H1/H2/H3 research, coverage analysis and calibration history is retained in
`archive/experiments.md`.

## 33. Settlement and Urban Routing

Settlement context remains part of the normal road-character model, but v1
does **not** contain a separate `avoid_cities` constraint or an additional
urban-burden modifier.

The urban/core investigation tested binary core detection, local-excursion
proxies and two bounded strengths of a continuous evidence-based urban burden.
None demonstrated sufficient generalisable routing benefit for production.

The v1 requirement is:

> Prefer a sensible motorcycle through-route or bypass when one exists,
> without generically avoiding towns, villages or urban roads.

A future urban-routing feature requires materially better independent evidence
or a new general hypothesis.

## 35. Non-Goals

The current project does not attempt to:

-   reproduce proprietary commercial motorcycle-routing algorithms,
-   guarantee the objectively most scenic route,
-   maximise route differences between routing characters,
-   optimise for individual named roads,
-   expose every internal routing parameter,
-   replace OsmAnd as the navigation application,
-   treat ascent maximisation as motorcycle routing,
-   equate motorway and toll semantics,
-   create a separate user-facing profile for every combination of
    preferences and constraints.

## 36. Current Functional Baseline

The current validated functional baseline is:

``` text
routing characters:
    fast
    curvy
    very-curvy

constraints:
    avoid_motorways
    avoid_toll

secondary preference:
    hills:
        off
        moderate
        strong

planning:
    multiple segments
    per-segment routing intention
    BRouter alternative evaluation
    combined GeoJSON
    combined GPX

routing foundation:
    BRouter KinematicModel
    generic motorcycle parameters

navigation validation:
    OsmAnd
```

This baseline replaces the earlier architecture in which Fast/Curvy/Very
Curvy and experimental `*-hilly` variants were treated primarily as a
growing family of standalone profiles.

## 37. Success Criteria

The current architecture is successful when:

-   Fast produces efficient and plausible motorcycle routes.
-   Curvy provides attractive alternatives where the network supports
    them.
-   Very Curvy expresses a stronger but still plausible road-character
    preference.
-   constraints remain independent of routing character.
-   toll and motorway avoidance remain semantically distinct.
-   hilliness influences route choice only when a useful alternative
    exists.
-   already mountainous routes are not distorted merely to gain more
    ascent.
-   segment-specific intentions can be combined into one continuous
    tour.
-   generated GPX can be used in OsmAnd.
-   routing rules generalise beyond calibration routes.
-   the public routing model remains understandable despite increasing
    internal sophistication.

## v1 Routing-Core Freeze

The validated v1 functional baseline is frozen for release preparation.
Fast, Curvy and Very Curvy are the accepted primary routing characters;
`avoid_motorways` and `avoid_toll` are independent constraints; and hilliness
remains a secondary planner preference with `off`, `moderate` and `strong`.

Route convergence is valid where geography or hard constraints leave no
meaningful alternative. No routing character is required to differ merely for
the sake of differentiation.

Further routing-weight changes require a reproducible regression defect or
materially new independent evidence.
