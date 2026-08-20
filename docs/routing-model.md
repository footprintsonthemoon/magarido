# BRouter Motorcycle Profiles – Routing Model

## 1. Purpose

This document defines how the functional requirements in `specification.md` are mapped to BRouter routing concepts, OpenStreetMap attributes, and routing costs.

It is the technical design for the canonical motorcycle routing profile.

The document intentionally separates:

* legal accessibility
* basic road suitability
* motorcycle road attractiveness
* curviness
* hilliness
* optional routing preferences

A road must first be legally and technically usable before preferences such as curviness or hilliness influence its attractiveness.

---

## 2. Design Model

The routing decision is conceptually composed of several layers:

```text
OSM way / node
      │
      ▼
Access validation
      │
      ▼
Basic road suitability
      │
      ▼
Road-class cost
      │
      +─────────────┐
      │             │
      ▼             ▼
Curviness        Hilliness
      │             │
      └──────┬──────┘
             │
             ▼
Secondary modifiers
             │
             ▼
Final BRouter cost
```

The layers must remain logically separable.

In particular:

```text
curviness != hilliness
curviness != road size
curviness != low speed
curviness != turn count
```

---

## 3. BRouter Profile Structure

The canonical profile should use the standard BRouter contexts:

```text
---context:global
```

for configuration and global routing parameters,

```text
---context:way
```

for road properties and way costs,

and:

```text
---context:node
```

for barriers and other node-specific restrictions.

The canonical implementation is:

```text
src/moto-base.brf
```

Generated presets are derived from this source.

---

## 4. Global Parameters

The primary project parameters are:

```text
assign curviness = 0
assign hilliness = 0
```

with:

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

Additional independent parameters may include:

```text
avoid_motorways
avoid_toll
allow_unpaved
allow_ferries
avoid_urban
```

The initial implementation should keep the number of user-facing parameters small.

---

## 5. Routing Cost Architecture

The routing model should conceptually derive:

```text
final_cost =
    base_road_cost
  + access_effect
  + surface_effect
  + speed_effect
  + urban_effect
  + optional_effects
```

Curviness changes selected components of this calculation.

Hilliness is applied separately through BRouter's elevation-aware routing mechanism.

The implementation does not need to reproduce this formula literally. It should preserve the conceptual separation.

---

## 6. Access Model

### 6.1 Principle

Legal accessibility has priority over route attractiveness.

No amount of curviness or hilliness may compensate for a road that is not legally accessible to motorcycles.

### 6.2 Access hierarchy

The implementation should evaluate motorcycle-related access using the following conceptual precedence:

```text
motorcycle
    ↓
motor_vehicle
    ↓
vehicle
    ↓
access
    ↓
implicit road-class default
```

A more specific tag should override a more general one where BRouter and the available OSM data allow this distinction.

The implementation should not assume that `motorcar=*` and `motorcycle=*` are equivalent.

### 6.3 Positive access values

Values normally indicating usable access include, where appropriate:

```text
yes
permissive
designated
destination
```

`destination` may remain routable but should be classified separately where useful.

### 6.4 Restricted access

Values representing prohibited or unsuitable motorcycle access must prevent normal routing.

Typical cases include:

```text
no
private
```

The implementation must be conservative when conflicting access tags are encountered.

### 6.5 Reference implementation

Access handling should be based primarily on the current BRouter car profile structure, extended with explicit motorcycle handling.

The experimental BRouter moped profile may be used as a reference for motorcycle-specific tags, but must not be copied as the safety baseline.

---

## 7. One-Way Routing

Motorcycle routing must respect normal one-way restrictions.

Relevant OSM information includes:

```text
oneway=yes
oneway=true
oneway=1
oneway=-1
junction=roundabout
```

The routing model must correctly account for BRouter's `reversedirection` state.

Violation of a one-way restriction must make the direction unusable rather than merely unattractive.

---

## 8. Node Restrictions and Barriers

The node context must handle barriers independently of normal way costs.

Relevant barriers include at least:

```text
gate
bollard
lift_gate
cycle_barrier
```

A barrier must only be considered passable if applicable access information permits motorcycle passage.

Toll booths should be considered separately from physical access restrictions.

---

## 9. Base Road Classification

The initial road model uses these principal OSM highway classes:

```text
motorway
motorway_link

trunk
trunk_link

primary
primary_link

secondary
secondary_link

tertiary
tertiary_link

unclassified

residential
living_street

service

track
road
path
```

Additional classes may be added when justified by testing.

---

## 10. Road-Class Cost Matrix

The following matrix is the initial calibration model.

It is not considered final behaviour until validated by route tests.

| OSM highway           |    Fast | Fast Curvy |   Curvy | Very Curvy |
| --------------------- | ------: | ---------: | ------: | ---------: |
| motorway              |    1.00 |       1.30 |    3.00 |       6.00 |
| trunk                 |    1.05 |       1.20 |    2.00 |       3.50 |
| primary               |    1.10 |       1.05 |    1.35 |       1.80 |
| secondary             |    1.20 |       1.05 |    1.00 |       1.05 |
| tertiary              |    1.35 |       1.10 |    1.00 |       1.00 |
| unclassified          |    1.70 |       1.30 |    1.10 |       1.05 |
| residential           |    2.50 |       2.50 |    3.00 |       4.00 |
| living_street         |    4.00 |       4.00 |    5.00 |       6.00 |
| service               |    5.00 |       5.00 |    6.00 |       8.00 |
| unsuitable track/path | blocked |    blocked | blocked |    blocked |

The most important characteristic of this matrix is:

> Increasing curviness does not automatically make progressively smaller roads more attractive.

Residential and service roads become less attractive as curviness increases.

---

## 11. Curviness Model

### 11.1 Limitation

The BRouter profile should not assume access to a direct geometric road-curvature metric.

Curviness must therefore be approximated through road characteristics available to the routing profile.

The first implementation uses a combination of:

```text
road class
speed information
urban context
surface
link-road status
```

The model may later incorporate additional BRouter or OSM information if testing demonstrates a meaningful improvement.

### 11.2 Motorcycle road attractiveness

The model targets roads that are likely to function as enjoyable motorcycle through-roads.

The preferred range for curvy routing is expected to centre around:

```text
secondary
tertiary
suitable unclassified
```

rather than:

```text
residential
living_street
service
track
```

### 11.3 Fast

`curviness = 0`

Optimises primarily for efficient road travel.

Expected characteristics:

```text
motorway          highly attractive
trunk             attractive
primary           attractive
secondary         acceptable
tertiary          acceptable
small local road  unattractive
```

### 11.4 Fast Curvy

`curviness = 1`

Represents the transition between efficient routing and motorcycle-oriented touring.

It should:

* retain reasonable travel efficiency
* prefer good secondary roads where the detour is modest
* retain major roads where they provide a substantial advantage
* reduce unnecessary motorway dependence

### 11.5 Curvy

`curviness = 2`

Should:

* favour secondary and tertiary roads
* allow suitable unclassified roads
* significantly discourage motorways
* discourage major high-speed roads
* strongly avoid residential routing

### 11.6 Very Curvy

`curviness = 3`

Should:

* strongly favour suitable motorcycle-oriented secondary and tertiary roads
* accept larger but still bounded detours
* make motorways highly unattractive
* avoid artificial complexity through settlements
* avoid local access roads used solely to increase route variation

---

## 12. Speed Model

### 12.1 Purpose

Speed information is a secondary indicator of road character.

It must not override basic road classification.

### 12.2 Sources

Where available, the model may use:

```text
maxspeed
maxspeed:forward
maxspeed:backward
```

BRouter profile logic may additionally provide implicit speed assumptions based on highway type.

### 12.3 Interpretation

The initial conceptual model is:

| Speed       | Motorcycle interpretation                                 |
| ----------- | --------------------------------------------------------- |
| >= 100 km/h | efficient, potentially less attractive for high curviness |
| 80–90 km/h  | generally good through-road                               |
| 60–80 km/h  | potentially attractive motorcycle road                    |
| 40–50 km/h  | context-dependent                                         |
| <= 30 km/h  | likely urban/local; no curviness bonus                    |

Speed must always be interpreted together with road class.

For example:

```text
secondary + 70 km/h
```

may receive favourable treatment.

But:

```text
residential + 30 km/h
```

must not become attractive for curvy routing.

---

## 13. Urban Model

Urban routing is an independent negative modifier.

The model should avoid using curviness as a reason to enter or zig-zag through settlements.

Potential indicators include:

```text
residential road classes
living_street
service
low maxspeed
BRouter town estimation where available
```

The initial implementation may use BRouter's estimated town classification if it proves stable and useful in testing.

Increasing `curviness` must never decrease the urban penalty for residential streets.

---

## 14. Link Roads

Roads such as:

```text
motorway_link
trunk_link
primary_link
secondary_link
tertiary_link
```

serve a functional routing purpose.

They should generally inherit the character of their associated road class, with a small additional penalty if necessary to avoid unnecessary interchange routing.

They must not become a mechanism for generating artificial route complexity.

---

## 15. Surface Model

### 15.1 Default behaviour

The initial project targets paved-road motorcycle touring.

Normal profiles should therefore favour:

```text
asphalt
paved
concrete
```

Other clearly road-compatible paved surfaces may be accepted after validation.

### 15.2 Unpaved surfaces

The default should strongly discourage or prohibit unsuitable unpaved surfaces.

Relevant information may include:

```text
surface
tracktype
smoothness
```

### 15.3 Missing surface information

Missing `surface=*` must not automatically mean unpaved.

Road class should be used as part of the inference.

A normal `secondary` without a surface tag should remain routable.

A `track` without sufficient surface information should be treated conservatively.

---

## 16. Track and Path Handling

The standard profiles are not adventure or off-road profiles.

Therefore:

```text
track
path
bridleway
```

should normally be excluded or assigned effectively prohibitive costs.

A future adventure profile may define different behaviour, but this must remain outside the standard routing model.

---

## 17. Turn Cost

### 17.1 Principle

Turn cost must not be used as the main curviness mechanism.

A physical bend in a continuous road is not equivalent to an intersection or routing manoeuvre.

### 17.2 Intended use

Turn cost may be used to:

* avoid unnecessary road switching
* prefer route continuity
* reduce intersection-heavy zig-zag routes
* distinguish roundabouts where appropriate

Initial calibration may vary turn cost slightly between presets, but large differences should be avoided.

Tentative starting values:

| Curviness  | Turn cost |
| ---------- | --------: |
| Fast       |       120 |
| Fast Curvy |        90 |
| Curvy      |        70 |
| Very Curvy |        60 |

These values are experimental and must be validated.

If testing shows that lower turn costs introduce settlement zig-zagging, the values should be increased or made constant across profiles.

---

## 18. Hilliness Model

### 18.1 Independence

Hilliness must remain independent from road-class curviness.

Changing:

```text
hilliness
```

must not change:

```text
curviness
```

or the basic road-class preference matrix.

### 18.2 BRouter elevation mechanism

Hilliness should use BRouter's elevation-aware cost mechanism rather than trying to infer mountainous terrain from road classes.

Relevant global parameters include:

```text
uphillcost
uphillcutoff
downhillcost
downhillcutoff
```

and associated elevation buffering parameters.

### 18.3 Neutral

```text
hilliness = 0
```

Elevation should not intentionally influence road attractiveness.

### 18.4 Hilly

```text
hilliness = 1
```

Routes with meaningful elevation variation may be preferred where they remain reasonably competitive in distance and road quality.

### 18.5 Very Hilly

```text
hilliness = 2
```

Elevation may influence routing more strongly.

However, the profile must still reject excessive detours whose only purpose is to accumulate elevation.

---

## 19. Hilliness Implementation Constraint

BRouter's elevation parameters are fundamentally designed to assign costs to climbing and descending.

Our requirement is different:

```text
prefer meaningful terrain
```

rather than:

```text
avoid climbing
```

Therefore hilliness must be implemented conservatively.

The first implementation must not rely on negative route costs.

Potential implementation approaches should be evaluated experimentally before one becomes normative.

Candidate approaches include:

1. penalising sufficiently flat alternatives slightly
2. reducing normal elevation penalties rather than rewarding elevation
3. combining road character and elevation effects indirectly
4. generating hilly variants with calibrated elevation parameters

The selected implementation must satisfy:

```text
no negative routing incentives
no elevation-seeking loops
no disproportionate mountain detours
```

---

## 20. Motorway Handling

Motorway preference is normally derived from `curviness`.

Expected baseline:

```text
curviness 0 → attractive
curviness 1 → allowed
curviness 2 → discouraged
curviness 3 → strongly discouraged
```

An explicit:

```text
avoid_motorways
```

setting must override normal preference and make motorway routing strongly unattractive or unavailable according to the implementation decision.

Curviness alone should normally discourage rather than absolutely prohibit motorways.

This allows a curvy route to use a short motorway section where avoiding it would produce an unreasonable detour.

---

## 21. Trunk Handling

`highway=trunk` requires special attention because its practical meaning varies significantly between road networks and countries.

The initial model should treat trunk roads as:

```text
Fast        attractive
Fast Curvy  moderately attractive
Curvy       discouraged
Very Curvy  strongly discouraged
```

Regional behaviour must be validated through international test routes.

---

## 22. Toll Roads

Tolls are independent of curviness and hilliness.

The parameter:

```text
avoid_toll
```

should control toll behaviour.

Default policy for the first release:

```text
avoid_toll = false
```

unless user testing indicates that a different default is preferable.

---

## 23. Ferries

Ferry use is independent of curviness and hilliness.

Ferries must receive an initial transition cost so that they are selected intentionally rather than for trivial geometric shortcuts.

The exact default should be determined through testing.

A future parameter may provide:

```text
allow_ferries
```

or:

```text
avoid_ferries
```

---

## 24. Initial Costs and Route Switching

BRouter allows an `initialcost` to be associated with classification transitions.

This mechanism may be useful for:

* ferries
* undesirable road-category transitions
* preventing excessive switching between road types

It should be used sparingly.

The primary routing behaviour should remain understandable from continuous road costs rather than being dominated by hidden transition penalties.

---

## 25. Priority Classification

The canonical profile should define BRouter road priority classes for navigation instruction generation.

The initial hierarchy may follow the established BRouter car profile:

```text
motorway
motorway_link
trunk
trunk_link
primary
primary_link
secondary
secondary_link
tertiary
tertiary_link
unclassified
residential
service
track
```

This classification is primarily navigational metadata and must not be confused with the motorcycle attractiveness model.

---

## 26. OsmAnd Turn Instructions

The generated profiles are primarily intended for OsmAnd.

The profile should therefore use OsmAnd-compatible turn instruction generation.

The initial implementation should evaluate:

```text
turnInstructionMode = 3
```

for OsmAnd-style instructions.

This setting concerns navigation instructions and must not affect routing preference.

---

## 27. Cost Safety Rules

The implementation should maintain the following invariants.

### 27.1 Unusable means unusable

Illegal or technically inaccessible roads should receive an effectively prohibitive routing value rather than merely a moderate penalty.

### 27.2 Preferences remain bounded

No attractive-road heuristic may produce a negative routing cost.

### 27.3 Small-road trap prevention

Increasing curviness must not systematically reduce the cost of:

```text
residential
living_street
service
track
path
```

### 27.4 Urban zig-zag prevention

A route must not gain motorcycle attractiveness simply from repeatedly changing local streets.

### 27.5 Elevation loop prevention

Hilliness must not create loops or large detours whose main effect is gaining and losing elevation.

---

## 28. Cost Composition

The implementation should aim for a structure conceptually similar to:

```text
base_cost
    = road_class_cost(curviness)

speed_modifier
    = speed_character(highway, maxspeed, curviness)

surface_modifier
    = surface_cost(surface, tracktype, allow_unpaved)

urban_modifier
    = urban_cost(road_class, town_context, curviness)

optional_modifier
    = motorway/toll/ferry preferences

final_cost
    = composed non-negative cost
```

Accessibility is evaluated before this preference model.

Elevation is handled independently.

---

## 29. Preset Generation

Preset configuration should be stored outside the canonical BRF logic.

Initial conceptual configuration:

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

The generation tool should inject these values into the canonical profile without changing routing logic.

---

## 30. Generated Profile Requirements

Every generated `.brf` must:

* be valid BRouter profile syntax
* contain the expected preset values
* be reproducible
* contain an indication that it is generated
* identify the project version if practical
* not contain manual profile-specific modifications

Generated files should include a comment similar to:

```text
# GENERATED FILE - DO NOT EDIT
# Source: src/moto-base.brf
# Preset: curvy
```

---

## 31. Calibration Strategy

Numeric cost values are calibration parameters rather than immutable requirements.

Changes must be driven by route behaviour.

A calibration cycle should be:

```text
change one routing assumption
          │
          ▼
generate profiles
          │
          ▼
run reference routes
          │
          ▼
compare metrics
          │
          ▼
inspect routes
          │
          ▼
accept / adjust / revert
```

Multiple unrelated cost parameters should not be changed simultaneously unless necessary.

---

## 32. Reference Profiles

Implementation work may consult existing BRouter profiles for proven patterns.

Primary technical reference:

```text
BRouter car-vario.brf
```

Useful for:

* access structure
* one-way handling
* surface speed handling
* road classification
* node barriers
* priority classification

Secondary technical reference:

```text
BRouter moped.brf
```

Useful for:

* motorcycle-specific access tags

The moped profile must not be treated as a production-ready safety baseline.

---

## 33. Implementation Order

The first implementation should be developed in the following order:

### Phase 1 – Legal routing

Implement:

```text
access
motorcycle access
one-way rules
barriers
basic road classes
```

Success criterion:

> The profile produces legally plausible motorcycle routes without route-character optimisation.

### Phase 2 – Basic road suitability

Implement:

```text
surface
track handling
residential penalties
service-road penalties
motorway/trunk handling
```

Success criterion:

> The router behaves like a conservative road-motorcycle router.

### Phase 3 – Curviness

Implement:

```text
road-class matrix
speed modifier
urban protection
curviness levels 0–3
```

Success criterion:

> Increasing curviness visibly changes road selection without creating unreasonable local-road detours.

### Phase 4 – Hilliness

Implement:

```text
hilliness levels 0–2
elevation calibration
detour protection
```

Success criterion:

> Hilliness changes terrain preference without altering the selected curviness model.

### Phase 5 – Optional preferences

Implement as required:

```text
tolls
ferries
explicit motorway avoidance
```

### Phase 6 – Calibration

Tune all presets against documented reference routes.

---

## 34. Open Technical Questions

The following questions remain intentionally unresolved for v0.1:

1. What is the best available approximation for road curviness within BRouter profile capabilities?
2. How strongly should `maxspeed` influence curviness?
3. Should BRouter's estimated town classification be part of the standard model?
4. Should turn cost vary by curviness or remain constant?
5. What is the safest and most predictable way to implement positive hilliness preference?
6. How much detour should each curviness level tolerate?
7. How much detour should each hilliness level tolerate?
8. How should missing or conflicting `surface=*` information be handled?
9. What exact motorcycle-access precedence produces the most correct behaviour?
10. How should country-specific interpretations of `trunk` be addressed?
11. Should ferry avoidance be a boolean or a graduated preference?
12. Should future versions expose configuration directly or continue using generated presets?

These questions must be resolved by documented experiments and reference-route testing.

---

## 35. v0.1 Design Rule

When uncertain between a clever heuristic and a predictable one, choose the predictable one.

The first goal is not to create the theoretically most exciting motorcycle route.

The first goal is to create a router whose behaviour can be understood, measured, tested, and improved.

