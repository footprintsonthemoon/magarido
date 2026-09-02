# Magarido -- Routing Model

## 1. Purpose

This document describes the routing model used by the Magarido
Profiles project.

It explains how the desired routing behaviour defined in
`docs/specification.md` is translated into BRouter cost functions.

The routing model is intentionally generic. It must not contain rules
that exist solely to produce a desired result on a particular test
route.

Detailed calibration procedures, test routes and profile evaluation are
documented separately in `docs/testing.md`.

## 2. Model Overview

BRouter searches for the route with the lowest accumulated routing cost.

The motorcycle model therefore assigns a cost to each usable road
segment.

Conceptually:

    segment cost
        =
        travel-time cost
        x road-character modifier
        x settlement modifier
        x optional routing modifiers
        x topographical modifier

The actual BRouter implementation additionally considers:

-   access restrictions
-   one-way restrictions
-   turn restrictions
-   barriers
-   surface
-   elevation
-   turn costs
-   ferry handling

The important design principle is that routing preferences are expressed
as relative costs.

A road is not selected because it belongs to a predefined route. It is
selected because its characteristics result in a lower total cost for
the chosen profile.

## 3. Model Dimensions

The current model contains two primary preference dimensions:

    curviness
    hilliness

They are intentionally represented separately.

`curviness` controls the preference for motorcycle-oriented road
character.

`hilliness` controls the preference for topographical variation.

The development model currently supports:

    curviness = 0 .. 3
    hilliness = 0 .. 2

Not every combination needs to become a user-facing profile.

## 4. Route Eligibility

Before preference costs are considered, a road must be usable by a
motorcycle.

The model evaluates:

-   `access`
-   `vehicle`
-   `motor_vehicle`
-   `motorcycle`
-   one-way restrictions
-   road type
-   surface
-   barriers

Explicit motorcycle access information has priority over more general
access information.

## 5. Supported Road Types

The normal paved-road model supports:

-   motorway
-   motorway_link
-   trunk
-   trunk_link
-   primary
-   primary_link
-   secondary
-   secondary_link
-   tertiary
-   tertiary_link
-   unclassified
-   residential
-   living_street
-   service

Ferries can be enabled.

Tracks and generic roads can optionally be enabled when unpaved routing
is allowed.

Paths, footways and similar infrastructure are not part of normal
motorcycle routing.

## 6. Surface Handling

The initial release targets paved-road motorcycle touring.

Paved surfaces include typical values such as:

-   asphalt
-   paved
-   concrete
-   paving stones
-   sett

Unpaved and potentially unsuitable surfaces include values such as:

-   gravel
-   fine gravel
-   ground
-   dirt
-   earth
-   grass
-   sand
-   mud

Unpaved roads are disabled by default.

When explicitly enabled, they remain subject to lower assumed speeds and
appropriate routing costs.

## 7. Time-Aware Base Cost

Earlier iterations of the model relied too strongly on road
classification.

The current model instead uses expected travel time as its primary base
cost.

This is important because one kilometre of motorway and one kilometre of
village road do not represent equivalent travel effort.

## 8. Explicit Speed Information

Where usable OpenStreetMap speed information exists, the model
evaluates:

-   `maxspeed`
-   `maxspeed:forward`
-   `maxspeed:backward`

Directional speed limits are considered according to travel direction.

Common numeric values are mapped explicitly.

Selected symbolic values such as `urban` and `rural` are also
interpreted.

If no usable explicit value is available, the model falls back to an
implicit speed estimate.

## 9. Implicit Speed Model

Implicit speed represents a reasonable expected motorcycle travel speed
based primarily on road classification.

The current model assumes approximately:

    motorway             120 km/h
    motorway_link         80 km/h
    trunk                100 km/h
    trunk_link            70 km/h
    primary               90 km/h
    primary_link          70 km/h
    secondary             80 km/h
    secondary_link        65 km/h
    tertiary              70 km/h
    tertiary_link         60 km/h
    unclassified          60 km/h
    residential           45 km/h
    living_street         20 km/h
    service               30 km/h
    ferry                 10 km/h
    track                 20 km/h
    generic road          30 km/h

These values are routing assumptions, not statements about legal speed
limits.

They may be recalibrated if broader testing demonstrates systematic
problems.

## 10. Surface and Track Speed Limits

Surface characteristics can further reduce expected speed.

For example, paving stones, cobblestones, gravel and tracks should not
inherit the full implicit speed of their road class.

The effective routing speed is therefore based on the most restrictive
applicable speed estimate.

## 11. Effective Speed

Conceptually:

    effective_speed =
        minimum(
            explicit_or_implicit_speed,
            implicit_road_speed,
            surface_speed,
            track_speed
        )

This prevents a high road-class speed from overriding a restrictive
surface or track condition.

## 12. Time Cost

The effective speed is converted into a relative cost.

The current model uses 120 km/h as the reference:

    time_cost = 120 / effective_speed

with a minimum cost of 1.0.

Examples:

    120 km/h -> 1.00
    100 km/h -> 1.20
     80 km/h -> 1.50
     60 km/h -> 2.00
     50 km/h -> 2.40
     30 km/h -> 4.00

This gives Fast routing a natural preference for roads that provide
substantial travel-time advantages.

## 13. Curviness Model

Curviness modifies the time-aware base cost according to road character.

The objective is not to identify geometric curves directly.

Instead, the model currently uses road classification as a proxy for the
type of road that is likely to be attractive for motorcycle touring.

This is deliberately an approximation.

Future versions may use additional information when it can be shown to
improve the model reliably.

## 14. Curviness Levels

The internal model currently supports four levels:

    0 = Fast
    1 = Fast Curvy
    2 = Curvy
    3 = Very Curvy

These levels are useful for calibration even when not all levels are
eventually released to users.

## 15. Fast

At curviness level 0, road-character modifiers remain close to neutral.

Travel time therefore dominates the routing decision.

Motorways, trunk roads and major roads can be selected when they provide
a meaningful travel-time advantage.

Local roads remain less attractive because their expected travel speeds
and road-character costs are higher.

## 16. Fast Curvy

Curviness level 1 introduces a limited preference for secondary and
tertiary roads while retaining a strong travel-time orientation.

The intended behaviour is:

    fast travel
        +
    preference for attractive alternatives
        when the time penalty is moderate

Calibration has shown that this level often produces the same route as
Fast.

It therefore remains useful as an internal calibration level, but its
user-facing value is currently considered limited.

## 17. Curvy

Curviness level 2 applies a stronger preference for suitable secondary
and tertiary roads.

It accepts moderate additional travel time when the resulting route has
a more appropriate motorcycle-touring character.

Motorways and other high-speed corridors receive a higher relative cost
than in Fast.

This does not prohibit motorways.

A motorway can still be selected when the alternative is sufficiently
slower or otherwise unattractive.

## 18. Very Curvy

Curviness level 3 increases the willingness to trade travel efficiency
for road character.

Compared with Curvy it:

-   penalises motorway and trunk routing more strongly
-   gives suitable secondary and tertiary roads greater relative
    importance
-   accepts larger deviations when the road network provides meaningful
    alternatives

Testing has demonstrated reproducible differences between Curvy and Very
Curvy, including cases where they select substantially different
corridors.

Very Curvy therefore remains a current release candidate.

## 19. Current Road-Character Factors

The current calibration uses approximately the following factors:

  Road class         Fast   Fast Curvy   Curvy   Very Curvy
  ---------------- ------ ------------ ------- ------------
  motorway           1.00         1.25    1.75         2.60
  motorway_link      1.00         1.25    1.70         2.50
  trunk              1.00         1.15    1.35         1.70
  trunk_link         1.00         1.15    1.30         1.60
  primary            1.00         1.03    1.12         1.28
  primary_link       1.00         1.03    1.12         1.28
  secondary          1.00         0.90    0.90         0.88
  secondary_link     1.00         0.94    0.94         0.94
  tertiary           1.00         0.88    0.88         0.84
  tertiary_link      1.00         0.92    0.93         0.90
  unclassified       1.10         0.98    0.96         0.94

These values are implementation parameters rather than product
requirements.

They may change during future calibration without changing the
conceptual routing model.

## 20. Local Roads

A central design rule is:

    more curvy != smaller road

Residential, living and service roads therefore do not become more
attractive as curviness increases.

The current model deliberately increases their cost:

  Road class        Fast   Fast Curvy   Curvy   Very Curvy
  --------------- ------ ------------ ------- ------------
  residential       1.30         1.35    1.50         1.75
  living_street     1.80         1.90    2.20         2.60
  service           2.00         2.10    2.40         2.80

This reduces the risk of routes that leave a sensible through-road
merely to zig-zag through residential areas.

## 21. Settlement Handling

Roads through settlements require special care.

An attractive through-road crossing a village should not automatically
become unattractive merely because it passes through a settlement.

At the same time, routing through dense urban areas should carry some
additional cost.

The model therefore applies a moderate settlement modifier based on
BRouter's estimated town classification.

## 22. Town Modifiers

The settlement modifier is intentionally weaker than the penalties
applied directly to residential, living and service roads.

This separates two concepts:

    through-road passing through a settlement

from:

    local residential routing

Calibration showed that strongly increasing the town penalty did not
provide a useful improvement and could suppress otherwise legitimate
motorcycle roads.

The current model therefore uses relatively conservative town modifiers.

## 23. Motorways

Motorways are allowed by default.

This is important because Fast must be able to produce genuinely
efficient routes.

Curvy and Very Curvy do not prohibit motorways either.

Instead, motorway use becomes progressively more expensive through the
road-character model.

This allows a profile to make a contextual trade-off:

    motorway time advantage

versus:

    attractiveness of an alternative road

## 24. Explicit Motorway Avoidance

The independent option:

    avoid_motorways

can make motorway and motorway-link segments effectively unusable.

This option is separate from curviness.

A user who explicitly requests motorway avoidance is expressing a hard
preference rather than merely requesting a more curvy route.

## 25. Toll Roads

Toll handling is also independent from curviness.

When:

    avoid_toll = true

toll roads receive a prohibitive routing cost.

This keeps economic or access preferences separate from road-character
preferences.

## 26. Hilliness Model

Hilliness is represented independently from curviness.

The current levels are:

    0 = neutral
    1 = hilly
    2 = very hilly

The model attempts to make topographically varied routes relatively more
attractive without requiring a specific mountain or road.

## 27. Relative Hilliness

Hilliness is implemented as a relative preference rather than an
arbitrary fixed additive cost.

The current calibration uses approximately:

    neutral      flat factor 1.00
    hilly        flat factor 1.10
    very hilly   flat factor 1.20

Flat or nominal terrain becomes relatively more expensive as hilliness
increases.

Uphill and downhill sections do not receive the same flat-terrain
factor.

BRouter's elevation buffering and slope processing are used to integrate
this behaviour into the routing calculation.

## 28. Curviness and Hilliness Correlation

Although curviness and hilliness are conceptually independent, they are
often correlated in real road networks.

Hill and mountain roads frequently:

-   contain more curves
-   belong to secondary or tertiary road classes
-   avoid major high-speed corridors
-   already receive favourable Curvy costs

As a result, Curvy may naturally select many of the same roads as Curvy
Hilly.

This is not necessarily a defect.

A separate Hilliness user profile is only justified if the additional
topographical preference creates a useful and reproducible difference.

## 29. Current Hilliness Assessment

Calibration to date has shown very little difference between:

    Curvy
    Curvy Hilly

Across most tested routes the resulting paths are identical or nearly
identical.

A measurable difference was observed on part of the Fribourg -\> Altdorf
test, but only across a small fraction of the complete route.

Hilliness therefore remains part of the internal model and calibration
framework but is not currently considered necessary for the initial
user-facing profile set.

## 30. Cost Composition

At a simplified level, normal road cost is calculated as:

    calculated_cost =
        time_cost
        x road_character
        x town_modifier
        x motorway_modifier

Hilliness may then modify the effective terrain-related cost.

The complete BRouter implementation also applies access, toll and other
constraints.

The final cost is bounded to values suitable for BRouter's cost model.

## 31. Additive Route Optimisation

BRouter minimises the accumulated cost of the complete route.

This has an important consequence:

A locally attractive road does not necessarily appear in the globally
optimal route between distant endpoints.

The route chosen from:

    A -> D

does not have to be visually equivalent to independently planning:

    A -> B
    B -> C
    C -> D

unless the same intermediate points are part of the global optimum.

## 32. Diagnostic Example: Lake Brienz

The Interlaken -\> Brienz test provides a useful example.

When routed independently, the Curvy family selects the northern shore
road, while faster routing can use the A8 corridor.

This demonstrates that the Curvy model is capable of recognising the
northern road as an attractive alternative.

On a much longer route such as Thun -\> Andermatt, the visible effect is
less pronounced because a large part of the complete journey is
topographically constrained and provides little meaningful route choice.

The correct conclusion is therefore not to introduce a Lake
Brienz-specific rule.

Instead, the case demonstrates why local route behaviour and complete
journey behaviour must be analysed separately.

## 33. Route Choice Availability

The usefulness of a profile comparison depends strongly on the amount of
real route choice available.

Three useful conceptual categories are:

### High-choice

Several plausible corridors or road types exist.

These routes are particularly useful for profile calibration.

### Mixed-choice

Only parts of the journey provide meaningful alternatives.

These routes are useful for observing local profile behaviour within a
longer journey.

### Constrained

Topography or road infrastructure provides effectively one practical
corridor.

Different profiles may legitimately produce the same route.

Identical routing in such a case is not evidence that the profiles
themselves are identical.

## 34. Development Presets

The current development environment generates six presets:

    moto-fast
    moto-fast-curvy
    moto-curvy
    moto-very-curvy
    moto-curvy-hilly
    moto-curvy-very-hilly

They allow the parameter space to be tested systematically.

## 35. Current Release Candidates

Based on calibration to date, the current user-facing candidates are:

    moto-fast
    moto-curvy
    moto-very-curvy

The remaining profiles continue to be useful for development and
testing:

    moto-fast-curvy
    moto-curvy-hilly
    moto-curvy-very-hilly

This distinction is a release decision, not a limitation of the routing
model.

## 36. Why Fast Curvy Remains Internal

Fast Curvy was designed as an intermediate level between Fast and Curvy.

Testing has occasionally shown small differences, particularly near the
start or end of longer motorway-oriented routes.

Across the broader test set, however, it frequently selects the same
route as Fast.

The observed difference is currently insufficient to justify another
user-facing choice.

The parameter remains useful for calibration.

## 37. Why Very Curvy Remains a Release Candidate

Very Curvy produces reproducible differences from Curvy.

On some routes the differences are local.

On others, such as the Bern -\> Luzern calibration case, the two
profiles can select substantially different alternatives.

This gives Very Curvy a sufficiently distinct behavioural meaning to
remain a release candidate.

## 38. Why Hilliness Remains Internal

Hilliness is conceptually valid and may become more useful in future
versions.

Current testing, however, indicates that much of its intended behaviour
is already produced indirectly by Curvy routing because attractive curvy
roads frequently occur in hilly terrain.

The model therefore retains hilliness without requiring users to choose
an additional profile that currently produces little observable benefit.

## 39. Planning Is Not Part of the Cost Model

The routing model answers:

    What is the preferred route from A to B?

It does not answer:

    Through which regions should a complete motorcycle tour pass?

The latter is a route-planning problem.

## 40. Segment-Based Planning

A future planning layer may divide a journey into segments:

    A -> B
    B -> C
    C -> D

Each segment can then be independently routed.

This can preserve locally attractive alternatives that may not appear
during unrestricted end-to-end optimisation.

Such functionality must remain outside the `.brf` cost model.

## 41. Per-Segment Profiles

A future planning layer may also allow different routing preferences for
different parts of a journey:

    A -> B    Fast
    B -> C    Curvy
    C -> D    Very Curvy

This would provide substantially more control without introducing
route-specific logic into BRouter profiles.

## 42. Optional Evidence

The production model remains independently usable from direct OpenStreetMap
road evidence. BRouter pseudo tags such as `estimated_traffic_class` and
`estimated_town_class` were investigated as optional contextual evidence, but
their coverage is selective and missing values must not be interpreted as
favourable or unfavourable evidence.

For v1, no H2 traffic modifier, separate urban-burden modifier, binary
urban/core detector or `avoid_cities` constraint is active. Settlement
handling continues through the existing conservative road-character and town
modifiers described above.

The full evidence-fusion and urban-validation history is retained in
`archive/experiments.md`.

## 43. Future Road-Character Model

Road classification is currently the primary proxy for motorcycle
attractiveness.

Future research may investigate additional information such as:

-   estimated traffic
-   speed environment
-   road continuity
-   settlement context
-   surface quality
-   elevation
-   other reliable BRouter or OpenStreetMap attributes

Such information should only be introduced when it improves behaviour
across multiple independent test cases.

## 44. Geometric Curviness

The current model does not directly calculate geometric road curvature.

A future model could potentially analyse or precompute properties such
as:

-   heading changes
-   curve density
-   road sinuosity
-   direction-change frequency

However, geometric curviness alone would still not define an attractive
motorcycle road.

A winding residential road must not automatically outrank a high-quality
secondary road.

Any future geometric model would therefore need to remain part of a
broader road-character model.

## 45. Generalisation Requirement

Every future routing-model change should follow this sequence:

    observation
        ->
    general hypothesis
        ->
    model change
        ->
    independent validation

A model change should not be accepted merely because it improves the
route that originally motivated the change.

This requirement is central to avoiding overfitting.

## 46. Model Stability

Once a stable release exists, routing-model parameters should not be
changed casually.

Changes to road-character factors, speed assumptions or topographical
behaviour may alter routes across large geographic areas.

Future changes should therefore be accompanied by:

-   automated smoke tests
-   regression tests
-   behaviour tests
-   comparison with previous routing results
-   documentation of the reason for the change

## 47. Current Model Status

The current routing model is considered a release-candidate model rather
than a final immutable model.

The major conceptual components are now established:

-   motorcycle-specific access handling
-   time-aware base routing
-   explicit and implicit speed handling
-   surface-aware effective speed
-   road-character-based curviness
-   conservative local-road handling
-   settlement handling
-   motorway and toll options
-   independent hilliness model
-   separation of routing and route planning

The next phase focuses primarily on consolidating testing and release
tooling rather than adding further routing dimensions.
