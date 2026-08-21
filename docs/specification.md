# BRouter Motorcycle Profiles – Specification

## 1. Purpose

This project provides motorcycle-oriented routing profiles for BRouter, with
OsmAnd on Android as the primary target application.

The profiles are intended for riders who want more control over the character
of a route than conventional "fastest" or "shortest" routing normally provides.

The initial project focuses on paved-road motorcycle touring.

The primary routing concepts are:

- travel efficiency
- road character / curviness
- topography / hilliness

The goal is not to generate artificially different routes for every profile.

A user-facing profile is useful only if it represents a distinct,
understandable and reproducible routing preference.


## 2. Design Principles

### 2.1 Behaviour before profile count

The project does not aim to provide as many profiles as possible.

Profiles should only be exposed to users when they produce a meaningful and
understandable difference in routing behaviour.

If two profiles behave essentially identically across representative routes,
they should not both be part of the user-facing profile set.

The internal routing model may contain more parameters and presets than the
public interface.


### 2.2 Global rules, not route-specific optimisation

Routing behaviour must never be tuned merely to produce a desired result on
one specific road or test route.

Real-world routes are used to identify weaknesses or characteristics of the
routing model.

A concrete test case may therefore:

1. reveal unexpected behaviour,
2. lead to a general hypothesis,
3. motivate a general model change,
4. validate that change on geographically and topographically different
   routes.

A route-specific exception must not be introduced merely to make one test
route behave as expected.


### 2.3 Local attractiveness and global optimisation

BRouter optimises a route globally between its start and destination.

A road segment that is attractive when routed independently may therefore not
appear in a longer route if the complete alternative has a higher accumulated
cost or if the longer route enters and leaves the area differently.

This behaviour must not automatically be treated as a routing error.

The distinction between local routing quality and global route planning is an
important architectural principle of this project.


### 2.4 Predictability

A rider should be able to understand the basic behaviour of a profile without
knowing the internal BRouter cost model.

Profile names and descriptions should correspond to observable routing
behaviour.


### 2.5 Conservative road selection

Increasing curviness must not simply mean selecting smaller roads.

In particular, residential streets, living streets and service roads must not
become attractive merely because they are slower, smaller or contain more
direction changes.

The intended target is an attractive motorcycle road, not arbitrary geometric
complexity.


### 2.6 Meaningful alternatives

Profiles should only produce different routes where the road network provides
meaningful alternatives.

If topography or infrastructure effectively provides one sensible corridor,
identical routing across profiles is acceptable and expected.

Artificial detours must not be introduced merely to differentiate profiles.


## 3. Target Environment

### 3.1 Routing engine

BRouter is the routing engine.

Profiles are implemented as BRouter `.brf` profiles and are designed to work
offline using BRouter routing data.


### 3.2 Primary client

OsmAnd on Android is the primary target application.

The user-facing profiles should be usable as custom BRouter routing profiles
from OsmAnd.


### 3.3 Development environment

The reference development environment is macOS.

Development and calibration are performed locally using:

- BRouter standalone server
- local BRouter segment data
- Python tooling
- generated `.brf` profiles
- automated smoke tests
- calibration tests
- browser-based visual route comparison

The final profiles themselves must not depend on the development environment.


## 4. Routing Scope

The initial scope is paved-road motorcycle touring.

The routing model should:

- respect motorcycle access restrictions
- respect one-way restrictions
- respect turn restrictions
- handle barriers correctly
- support ferries when enabled
- support toll roads when enabled
- support motorways when enabled
- avoid unsuitable paths and tracks by default
- avoid unpaved roads by default

Unpaved routing may be supported as an explicit option but is not the primary
focus of the initial release.


## 5. Routing Dimensions

### 5.1 Travel efficiency

Travel efficiency represents the expected cost of travelling along a road.

The routing model must not treat all road kilometres as equivalent.

A motorway kilometre and a village-road kilometre have substantially different
expected travel times.

The base routing model must therefore be time-aware.

Where available, explicit speed information should be considered.

Where explicit speed information is unavailable or unsuitable, reasonable
implicit speeds may be derived from road classification and other relevant
OpenStreetMap attributes.

Surface and road type may further constrain effective travel speed.


### 5.2 Curviness

Curviness represents a preference for roads that are attractive for motorcycle
touring.

It is not equivalent to:

- shortest distance
- lowest road class
- most turns
- smallest road
- highest elevation

Curviness may influence the preference for road classes and other available
road characteristics.

A Curvy profile may accept additional travel time or distance when this results
in a more attractive motorcycle route.

The acceptable trade-off must remain bounded and predictable.


### 5.3 Hilliness

Hilliness represents a preference for topographically varied routes.

It is conceptually independent from curviness.

A route can theoretically be:

- curvy but relatively flat
- curvy and hilly
- fast and hilly
- fast and flat

In real road networks, however, curviness and hilliness are often correlated.

Mountain and hill roads frequently contain more curves and may already be
favoured by a Curvy routing model.

Hilliness therefore remains an internal routing dimension even though current
testing does not justify a separate Hilliness user profile.


### 5.4 Urban routing

Passing through a village on an otherwise attractive through-road is not the
same as routing through residential streets.

The model should therefore distinguish, as far as the available data permits,
between:

- useful through-roads crossing settlements
- residential streets
- living streets
- service roads

Urban penalties must not unintentionally exclude otherwise attractive
motorcycle roads.


## 6. Internal Profile Model

The routing model supports multiple levels of curviness and hilliness for
development and calibration.

The current development presets are:

- `moto-fast`
- `moto-fast-curvy`
- `moto-curvy`
- `moto-very-curvy`
- `moto-curvy-hilly`
- `moto-curvy-very-hilly`

These presets deliberately cover a broader parameter space than the intended
user-facing release.

Development presets may remain available internally even when they are not
distributed as normal user profiles.


## 7. Initial User-Facing Profiles

Based on current calibration and validation, the initial release candidates
are:

- `moto-fast`
- `moto-curvy`
- `moto-very-curvy`

This provides a simple progression from travel efficiency toward increasingly
strong motorcycle-road preference.


## 8. Fast

Goal:

> Reach the destination efficiently while using roads suitable for motorcycle
> travel.

Expected behaviour:

- travel time is the dominant routing criterion
- motorways may be used
- trunk and primary roads may be used
- unnecessary local-road detours are avoided
- curves and elevation are not intentionally sought
- meaningful time advantages should normally outweigh scenic alternatives

Fast represents the efficient baseline against which the stronger
motorcycle-oriented profiles can be compared.


## 9. Curvy

Goal:

> Prefer attractive motorcycle roads while keeping additional travel time and
> distance within reasonable limits.

Expected behaviour:

- suitable secondary and tertiary roads are preferred where appropriate
- moderate detours are acceptable
- a faster motorway corridor may be rejected when a sufficiently attractive
  alternative exists
- residential and service roads must not become attractive merely because they
  are slower or geometrically complex
- motorways remain available when alternatives would require unreasonable
  additional cost

Curvy is intended to be the normal motorcycle-touring profile.


## 10. Very Curvy

Goal:

> Apply a stronger preference for motorcycle-oriented road character and
> accept larger reasonable deviations from the fastest route.

Expected behaviour:

- stronger preference for suitable secondary and tertiary roads
- greater willingness to avoid high-speed corridors
- larger acceptable time and distance trade-offs than Curvy
- no artificial detours solely to create route differences
- conservative handling of residential, living and service roads remains in
  effect

Current testing has demonstrated reproducible differences between Curvy and
Very Curvy.

On some routes these differences are local.

On other routes they can result in substantially different corridor choices.

Very Curvy therefore provides a sufficiently distinct routing concept for the
initial release.


## 11. Experimental Profile: Fast Curvy

Fast Curvy was designed to represent:

> Mostly fast routing with limited willingness to trade travel time for more
> attractive roads.

The intended conceptual position is:

    Fast
      ->
    Fast Curvy
      ->
    Curvy

Current testing has occasionally demonstrated local differences between Fast
and Fast Curvy.

These differences tend to occur before entering or after leaving dominant
motorway corridors, where several alternatives have similar travel costs.

Across the broader calibration set, however, Fast and Fast Curvy frequently
produce identical routes.

The additional user value is therefore currently insufficient to justify
another user-facing profile.

Fast Curvy remains available as an internal calibration level.


## 12. Experimental Profile: Curvy Hilly

Curvy Hilly combines the Curvy road-character model with a preference for
topographically varied routes.

Current testing shows very little practical difference between:

    Curvy
    Curvy Hilly

This is consistent with the observation that attractive curvy motorcycle roads
and hilly terrain are often naturally correlated.

A small difference has been observed on selected routes, but not sufficiently
often or strongly to justify a separate user-facing profile.

Curvy Hilly remains available for development and future research.


## 13. Experimental Profile: Curvy Very Hilly

Curvy Very Hilly represents a stronger topographical preference.

It is useful as an experimental extreme for determining the useful range of
the Hilliness model.

Current testing does not demonstrate sufficient independent user value for
initial release.

It remains an internal experimental profile.


## 14. Profile Selection Criteria

A development profile should become a user-facing profile only when it meets
the following criteria:

1. It has a clearly explainable purpose.
2. Its behaviour is observably different from adjacent profiles on a useful
   subset of representative routes.
3. The difference is reproducible across different geographic situations.
4. The difference corresponds to a realistic motorcycle-routing preference.
5. It does not require route-specific exceptions.
6. It does not produce unreasonable detours merely to differentiate itself.
7. A rider can reasonably predict why the profile selected a particular type
   of route.

Profile reduction is therefore considered a successful calibration outcome
when redundant profiles are identified.


## 15. Current Profile Decision

The current release candidates are:

    moto-fast
    moto-curvy
    moto-very-curvy

The current internal and experimental profiles are:

    moto-fast-curvy
    moto-curvy-hilly
    moto-curvy-very-hilly

The internal profiles should remain available for calibration and future
research.

This separation allows the internal routing model to remain expressive while
keeping the user interface simple.


## 16. User-Facing Progression

The intended user-facing progression is:

    FAST
      |
      | increasing willingness to trade
      | travel efficiency for road character
      v
    CURVY
      |
      v
    VERY CURVY

This progression should remain understandable without requiring users to know
BRouter cost factors or OpenStreetMap road classifications.


## 17. Calibration Strategy

Routing quality cannot be evaluated using a single route.

The test suite should contain geographically and topographically different
routes with different purposes.

Detailed routes and observations are documented in `docs/testing.md`.


## 18. Route-Choice Categories

Calibration routes should be understood according to the amount of real route
choice available.


### 18.1 High-choice routes

Several plausible corridors or road types exist.

These are particularly useful for profile differentiation.


### 18.2 Mixed-choice routes

Only part of the route provides meaningful alternatives.

These are useful for testing longer journeys but profile differences must be
evaluated primarily where real alternatives exist.


### 18.3 Constrained routes

Topography or infrastructure provides effectively one practical corridor.

Identical routing across profiles is expected.

Such routes are primarily useful for regression testing.


## 19. Regression Tests

Regression tests answer:

> Does the routing model continue to produce sensible routes?

They are intended to detect unintended side effects.

A route does not need to produce different results for every profile to be a
useful regression test.


## 20. Behaviour Tests

Behaviour tests answer:

> Do the profiles demonstrate the routing character they claim to represent?

Examples include routes where meaningful choices exist between:

- motorway and secondary roads
- efficient and scenic corridors
- major and minor through-roads
- flatter and more topographically varied corridors


## 21. Diagnostic Tests

Diagnostic tests investigate a specific routing observation.

A longer route may be divided into smaller sections to determine why a locally
attractive alternative behaves differently within the complete journey.

Diagnostic tests are not themselves a reason to change routing parameters.

They generate hypotheses that must subsequently be validated using other
routes.


## 22. Local vs. Global Routing

A key result of current testing is the importance of distinguishing local route
quality from end-to-end optimisation.

A road may be selected by Curvy when routing:

    B -> C

while a longer route:

    A -> D

may use a different overall corridor.

This does not automatically imply that the local road is incorrectly valued.

The complete route must be analysed in terms of:

- entry and exit points
- alternative corridors
- constrained sections
- accumulated cost
- available route choice


## 23. Diagnostic Example: Interlaken -> Brienz

The Lake Brienz case provides a useful example.

Between Interlaken and Brienz, a fast corridor and an attractive northern
through-road provide meaningful alternatives.

When routed independently, the Curvy profile family selects the northern
alternative.

This demonstrates that the routing model can recognise the road as an
attractive motorcycle route.

On the longer Thun -> Andermatt journey, much of the remaining route is
topographically constrained.

The case therefore demonstrates the importance of analysing the amount and
location of real route choice.

It must not result in a Lake-Brienz-specific routing rule.


## 24. Generalisation Requirement

Every routing-model change should follow this sequence:

    observation
        ->
    general hypothesis
        ->
    model change
        ->
    independent validation

A model change must not be accepted merely because it improves the route that
originally motivated the change.

This requirement is central to avoiding overfitting.


## 25. Validation Beyond Switzerland

The current calibration set is primarily Swiss.

Before the model is considered broadly stable, representative routes should
also be tested in other regions.

Useful future validation environments include:

- Jura
- Black Forest
- Vosges
- Alps outside Switzerland
- flatter rural regions
- regions with different OpenStreetMap tagging practices

The purpose is to verify that the routing model represents general road
characteristics rather than properties specific to Swiss geography or mapping
practice.


## 26. Routing vs. Route Planning

This project distinguishes between two separate problems.


### 26.1 Routing

Routing answers:

> What is the preferred route from A to B according to a given motorcycle
> profile?

This is the responsibility of the BRouter profile.


### 26.2 Route planning

Route planning answers:

> Through which intermediate areas or waypoints should the complete journey
> pass?

A globally optimised route:

    A -> D

may legitimately differ from independently optimised segments:

    A -> B
    B -> C
    C -> D

This distinction is particularly important for motorcycle touring.


## 27. Future Scope: Segment-Based Tour Planning

A future planning layer may allow a complete motorcycle tour to consist of
multiple independently routed segments.

Conceptually:

    Start
      |
      v
    Segment 1
      |
      v
    Waypoint
      |
      v
    Segment 2
      |
      v
    Waypoint
      |
      v
    Segment 3
      |
      v
    Destination

A route could, for example, be planned as:

    Thun
      ->
    Interlaken
      ->
    Brienz
      ->
    Andermatt

Each segment could initially use the same routing profile.

This would allow riders to influence the broad geographic structure of a tour
without introducing route-specific logic into the BRouter profile.


## 28. Future Scope: Per-Segment Routing Preferences

A more advanced planning layer may allow different profiles for individual
segments.

Example:

    Thun -> Interlaken
        Fast

    Interlaken -> Brienz
        Curvy

    Brienz -> Andermatt
        Very Curvy

This separates two user decisions:

1. Where should the tour approximately go?
2. What routing character should each part of the tour have?

Such functionality belongs to a planning layer above BRouter.


## 29. Future Scope: Route Alternatives

A future planning tool may request multiple alternatives for individual
segments.

Instead of presenting only one globally optimal route, the user could compare
alternatives such as:

- Fast
- Curvy
- Very Curvy
- alternative geographic corridors

The user could then select preferred segments and combine them into a complete
tour.

This may be particularly useful where lakes, mountains, valleys or other
geographic constraints create several distinct corridors.


## 30. Future Scope: Planning Tool

A future companion tool could provide route planning independently of the
BRouter profile implementation.

A possible conceptual route definition could be:

    route:
      - Thun
      - Interlaken
      - Brienz
      - Andermatt

    profile: moto-curvy

A more advanced definition could be:

    segments:
      - from: Thun
        to: Interlaken
        profile: moto-fast

      - from: Interlaken
        to: Brienz
        profile: moto-curvy

      - from: Brienz
        to: Andermatt
        profile: moto-very-curvy

Possible outputs include:

- GPX
- GeoJSON
- routes suitable for import into OsmAnd

This functionality is explicitly outside the scope of the initial routing
profile release.


## 31. Future Scope: Better Motorcycle-Road Characterisation

Road classification is an imperfect proxy for motorcycle attractiveness.

Future versions may investigate additional OpenStreetMap and BRouter
information where sufficiently reliable, including:

- estimated traffic
- speed environment
- settlement context
- road continuity
- surface quality
- elevation characteristics
- other reliable road attributes

Any additional factor must satisfy the same generalisation requirement as the
current model.


## 32. Future Scope: Geometric Curviness

The current model does not directly measure road curvature.

Future research may investigate properties such as:

- heading changes
- curve density
- road sinuosity
- direction-change frequency

Geometric curviness alone must not determine motorcycle attractiveness.

A winding residential street must not automatically outrank a high-quality
secondary road.

Any geometric model would therefore need to remain part of a broader
road-character model.


## 33. Future Scope: Route Similarity Metrics

Future testing tooling may quantify differences between profiles.

Useful metrics may include:

- shared route percentage
- unique route percentage
- distance difference
- travel-time difference
- ascent difference
- motorway share
- road-class distribution
- geographic corridor similarity

These metrics could provide a more objective basis for determining whether two
profiles offer meaningfully different behaviour.

They should complement rather than replace visual inspection.


## 34. Future Scope: Stable Regression Baselines

Once the initial release is stable, selected calibration routes may become
formal regression baselines.

Future model changes could then report:

- unchanged route
- small deviation
- major corridor change
- distance delta
- travel-time delta
- ascent delta

Major routing changes should be reviewed before modifying a released profile.


## 35. Non-Goals

The initial project does not attempt to:

- reproduce commercial motorcycle-routing algorithms
- guarantee the objectively most scenic route
- identify curves directly from road geometry
- optimise routes for a specific motorcycle model
- optimise routes for individual known roads
- replace OsmAnd as a navigation application
- provide a complete graphical tour planner
- guarantee identical routing behaviour across all countries
- maximise route differences between profiles
- expose every internal routing parameter as a user profile


## 36. Initial Release Success Criteria

The initial release is successful when:

- Fast produces efficient and plausible motorcycle routes.
- Curvy produces recognisably different and attractive alternatives where the
  road network provides them.
- Very Curvy provides a stronger but still plausible road-character
  preference.
- Profiles remain sensible where no meaningful alternatives exist.
- Motorways are neither unintentionally prohibited nor unintentionally
  preferred by all profiles.
- Residential and service roads are not mistaken for desirable curvy roads.
- Routing behaviour generalises beyond individual calibration routes.
- Redundant development profiles are not exposed unnecessarily to users.
- Profiles work offline with BRouter and OsmAnd on Android.
- The development and calibration process is reproducible.


## 37. Initial Release Candidate

The current initial release candidate consists of three user-facing profiles:

    moto-fast
    moto-curvy
    moto-very-curvy

The development model additionally retains:

    moto-fast-curvy
    moto-curvy-hilly
    moto-curvy-very-hilly

This separation is intentional.

The public interface should remain simple while the internal model retains
sufficient parameter space for calibration, experimentation and future
development.
