# BRouter Motorcycle Profiles – Specification

## 1. Purpose

The project provides configurable motorcycle routing profiles for BRouter with a particular focus on offline navigation using OsmAnd.

The routing model is designed for road-oriented motorcycle touring. It should provide meaningful alternatives between efficient routing and enjoyable motorcycle roads while remaining predictable, safe, and understandable.

The central design goal is to model **curviness** and **hilliness** as independent routing preferences.

## 2. Scope

The project covers:

* road-based motorcycle routing
* offline routing with BRouter
* integration with OsmAnd
* configurable route character
* generated BRouter profile variants
* routing based on OpenStreetMap data and BRouter elevation information

The project is primarily intended for touring motorcycles and normal road motorcycles.

## 3. Design Goals

The routing model should:

* produce sensible road routes for motorcycles
* distinguish efficient routing from scenic or curvy routing
* allow hilliness to be selected independently of curviness
* favour enjoyable through-roads over residential and service roads
* avoid excessive detours
* preserve legal access restrictions
* avoid unpaved roads by default
* work completely offline once BRouter map data is available
* remain understandable and tunable

## 4. Non-Goals

The project does not attempt to:

* detect mathematical road curvature directly from route geometry if this information is unavailable to the BRouter profile
* maximise the number of turns
* maximise elevation gain
* create arbitrary loops for entertainment
* route through residential areas merely because they contain many bends or intersections
* provide off-road or enduro routing by default
* bypass OpenStreetMap access restrictions
* reproduce proprietary routing algorithms exactly

## 5. Routing Philosophy

### 5.1 A slow road is not automatically a good motorcycle road

Low speed limits may indicate:

* urban areas
* residential streets
* traffic-calmed roads
* congested areas

Low speed alone must therefore not increase motorcycle attractiveness.

### 5.2 A small road is not automatically a curvy road

Curvy routing should favour useful through-roads with an appropriate motorcycle character.

Typical preferred road classes are expected to include:

* secondary roads
* tertiary roads
* suitable unclassified roads

Residential streets, living streets, and service roads should normally remain unattractive.

### 5.3 Curviness is not turn count

BRouter turn costs represent routing manoeuvres and intersections.

A mountain road may contain many physical curves while remaining one continuous road.

Turn count must therefore not be used as the primary approximation for curviness.

### 5.4 Hilliness is a preference, not an objective

Hilliness should influence route selection when reasonable alternatives exist.

It must not cause disproportionate detours merely to accumulate elevation.

### 5.5 Predictability is more important than aggressive optimisation

The routing model should behave consistently enough that a rider can develop an intuition for what each profile will produce.

## 6. Primary Parameters

### 6.1 Curviness

```text
curviness = 0
Fast

curviness = 1
Fast and curvy

curviness = 2
Curvy

curviness = 3
Very curvy
```

#### Curviness 0 – Fast

Goal:

* efficient travel
* major roads are acceptable
* motorways may be attractive
* avoid unnecessary local-road detours

#### Curviness 1 – Fast and Curvy

Goal:

* remain reasonably efficient
* prefer attractive secondary roads when the detour is modest
* allow major roads where they provide a significant advantage

#### Curviness 2 – Curvy

Goal:

* favour secondary and tertiary through-roads
* accept moderate detours for a better motorcycle route
* reduce motorway attractiveness
* avoid residential routing

#### Curviness 3 – Very Curvy

Goal:

* strongly favour suitable secondary, tertiary, and selected unclassified roads
* accept larger but bounded detours
* strongly reduce motorway attractiveness
* continue to avoid residential and service-road routing

## 7. Hilliness

```text
hilliness = 0
Neutral

hilliness = 1
Hilly

hilliness = 2
Very hilly
```

### 7.1 Neutral

Elevation should not materially influence route selection beyond normal routing requirements.

### 7.2 Hilly

When two routes are otherwise reasonably comparable, the route with more meaningful elevation variation may be preferred.

### 7.3 Very Hilly

Elevation variation may have a stronger influence, but detours must remain bounded.

### 7.4 Independence

Hilliness must not implicitly change curviness.

The following combinations must therefore remain valid:

```text
fast + neutral
fast + hilly
fast-curvy + hilly
curvy + neutral
curvy + hilly
very-curvy + neutral
very-curvy + hilly
```

## 8. Initial Presets

The first release should provide:

| Profile     | Curviness | Hilliness |
| ----------- | --------: | --------: |
| Fast        |         0 |         0 |
| Fast Curvy  |         1 |         0 |
| Curvy       |         2 |         0 |
| Very Curvy  |         3 |         0 |
| Curvy Hilly |         2 |         1 |

Additional combinations may be generated later without introducing new routing logic.

## 9. Initial Road-Class Model

The first implementation should use the following values as calibration starting points rather than permanent constants.

| OSM highway                |    Fast | Fast Curvy |   Curvy | Very Curvy |
| -------------------------- | ------: | ---------: | ------: | ---------: |
| motorway                   |    1.00 |       1.30 |    3.00 |       6.00 |
| trunk                      |    1.05 |       1.20 |    2.00 |       3.50 |
| primary                    |    1.10 |       1.05 |    1.35 |       1.80 |
| secondary                  |    1.20 |       1.05 |    1.00 |       1.05 |
| tertiary                   |    1.35 |       1.10 |    1.00 |       1.00 |
| unclassified               |    1.70 |       1.30 |    1.10 |       1.05 |
| residential                |    2.50 |       2.50 |    3.00 |       4.00 |
| living_street              |    4.00 |       4.00 |    5.00 |       6.00 |
| service                    |    5.00 |       5.00 |    6.00 |       8.00 |
| track / unsuitable unpaved | blocked |    blocked | blocked |    blocked |

These values must be validated experimentally.

## 10. Speed Information

`maxspeed` may be used as a secondary indication of road character.

It must not be interpreted as direct evidence of curviness.

Initial assumptions:

* very high speed roads are generally less attractive for strongly curvy profiles
* 60–80 km/h roads may be attractive when combined with suitable road classes
* 30 km/h roads are likely to represent urban or residential environments and should not receive a curviness bonus merely because they are slow

Road class and context must take precedence over raw speed.

## 11. Urban Routing

Urban areas should generally be treated as functional transit areas rather than desirable motorcycle-routing destinations.

Increasing curviness must never increase the attractiveness of:

* residential roads
* living streets
* service roads
* traffic-calmed local streets

A curvy profile should not create zig-zag routing through settlements.

## 12. Surface

Default profiles should target normal paved road motorcycles.

Unpaved roads should be excluded or strongly discouraged by default.

Future optional profiles may explicitly support:

* gravel
* adventure motorcycles
* mixed-surface touring

Such functionality is outside the initial scope.

## 13. Motorways

Motorway preference depends primarily on curviness.

Expected behaviour:

* Fast: motorway attractive
* Fast Curvy: motorway allowed but somewhat less attractive
* Curvy: motorway significantly discouraged
* Very Curvy: motorway strongly discouraged

Motorways should not necessarily be completely prohibited unless the user explicitly requests motorway avoidance.

## 14. Tolls and Ferries

Tolls and ferries should be represented as independent routing concerns rather than being derived from curviness or hilliness.

The initial implementation may use conservative defaults.

## 15. Access Restrictions

Routing must respect relevant OpenStreetMap restrictions, including where applicable:

* `motorcycle`
* `motor_vehicle`
* `motorcar`
* `vehicle`
* `access`
* one-way restrictions
* turn restrictions

Motorcycle-specific access information should take precedence where available.

## 16. Profile Generation

The project should maintain one canonical BRouter profile implementation.

User-facing profiles should be generated from parameter presets.

Conceptually:

```yaml
fast:
  curviness: 0
  hilliness: 0

fast-curvy:
  curviness: 1
  hilliness: 0

curvy:
  curviness: 2
  hilliness: 0

very-curvy:
  curviness: 3
  hilliness: 0

curvy-hilly:
  curviness: 2
  hilliness: 1
```

Generated `.brf` files must be reproducible.

## 17. Testing Strategy

Routing changes should be evaluated against stable reference routes.

Initial test routes should include different terrain and road-network characteristics.

Candidate Swiss routes:

```text
Biel/Bienne → Neuchâtel
Bern → Luzern
Thun → Andermatt
Zürich → Davos
Aigle → Martigny
```

Additional international test routes should later be added.

## 18. Test Metrics

Where technically available, tests should record:

* route distance
* estimated travel time
* elevation gain
* elevation loss
* motorway distance or percentage
* primary-road distance or percentage
* secondary-road distance or percentage
* tertiary-road distance or percentage
* residential-road usage
* unpaved-road usage
* ferry usage
* number of suspicious detours
* loops or route anomalies

## 19. Subjective Evaluation

Motorcycle routing cannot be fully evaluated using numerical metrics.

Reference routes may therefore include a subjective assessment such as:

```text
1 = poor
2 = acceptable
3 = good
4 = very good
5 = excellent
```

The reason for the score should be recorded.

Subjective scoring supplements but does not replace measurable testing.

## 20. Initial Success Criteria

The first usable release should meet the following conditions:

* all five initial presets produce valid BRouter routes
* no profile routes over unsuitable unpaved roads by default
* curvy modes do not systematically route through residential areas
* higher curviness produces a visible shift towards secondary and tertiary roads
* motorway usage decreases as curviness increases
* hilliness can be changed without changing the configured curviness level
* hilly routing does not produce obviously excessive detours
* OsmAnd can select and use each generated profile offline

## 21. Open Questions

The following topics require experimental validation:

* best approximation for motorcycle-road attractiveness using available BRouter/OSM attributes
* exact influence of `maxspeed`
* treatment of `trunk` roads in different countries
* suitable maximum detour tolerance
* elevation weighting and saturation
* ferry defaults
* toll defaults
* road quality and surface interpretation
* motorcycle-specific access precedence
* regional differences in OSM tagging quality

These questions should be resolved through documented tests rather than assumptions.

