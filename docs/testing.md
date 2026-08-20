# BRouter Motorcycle Profiles – Testing Strategy

## 1. Purpose

This document defines how routing behaviour is tested, compared, and calibrated.

The goal is to make changes to the routing model measurable and reproducible rather than relying only on visual inspection or subjective impressions.

Testing combines:

* automated route generation
* quantitative metrics
* route-shape inspection
* regression checks
* subjective motorcycle-route evaluation

The same reference routes should be reused over time so that behavioural changes remain comparable.

---

## 2. Testing Principles

### 2.1 Test behaviour, not implementation details

Tests should primarily verify routing outcomes.

Examples:

```text
Does Very Curvy use less motorway than Fast?
Does Curvy avoid residential zig-zag routing?
Does Hilly materially change terrain preference?
Does a routing change create unreasonable detours?
```

Tests should not overfit to individual internal BRF expressions unless required for safety.

### 2.2 Change one thing at a time

Where practical, only one routing assumption or cost family should be changed per calibration step.

This makes behavioural changes easier to understand.

### 2.3 Keep reference routes stable

Reference routes should not be replaced casually.

Stable routes provide a regression baseline.

New routes may be added when they expose behaviour not covered by existing cases.

### 2.4 Separate objective and subjective evaluation

Quantitative metrics and subjective motorcycle quality are both useful, but they must be recorded separately.

A route that is longer is not automatically better.

A route that is statistically more "curvy" is not automatically enjoyable.

---

## 3. Test Levels

The project should use four test levels.

### Level 1 – Profile validation

Verify that generated profiles are syntactically valid and loadable by BRouter.

### Level 2 – Functional routing tests

Verify that routes can be calculated and that fundamental routing rules work.

### Level 3 – Behavioural comparison

Compare presets against each other on stable reference routes.

### Level 4 – Real-world evaluation

Ride selected routes and record subjective quality and observed routing issues.

---

## 4. Profile Validation

Every generated profile must pass basic validation.

Tests should verify:

* profile file exists
* file is non-empty
* expected preset name is present
* expected `curviness` value is present
* expected `hilliness` value is present
* generated-file warning is present
* BRouter accepts the profile
* route calculation succeeds for at least one smoke-test route

Example expected header:

```text
# GENERATED FILE - DO NOT EDIT
# Source: src/moto-base.brf
# Preset: curvy
```

---

## 5. Preset Matrix

The initial test set covers:

| Preset      | Curviness | Hilliness |
| ----------- | --------: | --------: |
| Fast        |         0 |         0 |
| Fast Curvy  |         1 |         0 |
| Curvy       |         2 |         0 |
| Very Curvy  |         3 |         0 |
| Curvy Hilly |         2 |         1 |

Future presets should be added to the same matrix rather than introducing separate test logic.

---

## 6. Reference Route Selection

Reference routes should cover different routing situations.

The initial set should include:

```text
Biel/Bienne → Neuchâtel
Bern → Luzern
Thun → Andermatt
Zürich → Davos
Aigle → Martigny
```

These routes should be supplemented with additional test cases where useful.

Reference routes should represent different characteristics such as:

* motorway availability
* dense urban areas
* flat terrain
* hilly terrain
* alpine terrain
* multiple viable secondary-road alternatives
* constrained valleys
* ferry situations
* border crossings
* regions with different OSM tagging practices

---

## 7. Test Route Categories

Reference routes should be tagged by category.

Possible categories:

```text
flat
urban
motorway
rural
hilly
alpine
border
ferry
mixed
```

A route may belong to multiple categories.

Example:

```text
Thun → Andermatt
categories:
  - rural
  - hilly
  - alpine
```

---

## 8. Route Definition

Reference routes should be stored as structured test data.

A route definition should contain at least:

```yaml
id: ch-biel-neuchatel
from:
  name: Biel/Bienne
  lat: 47.1368
  lon: 7.2468

to:
  name: Neuchâtel
  lat: 46.9896
  lon: 6.9293

categories:
  - rural
  - motorway
  - mixed
```

Coordinates should be fixed once selected.

This avoids route changes caused by different geocoding results.

---

## 9. Waypoints

Reference routes should normally use only start and destination.

Intermediate waypoints should only be added when the purpose of a test explicitly requires them.

This ensures that routing behaviour is being tested rather than manually constrained.

---

## 10. Test Data Versioning

Reference-route definitions must be version-controlled.

Changes to:

* coordinates
* categories
* expected behaviour
* thresholds

must be reviewed like routing-code changes.

---

## 11. Core Metrics

Each calculated route should record where technically available:

```text
distance
estimated travel time
elevation gain
elevation loss
maximum elevation
minimum elevation
```

In addition, road usage should be analysed.

---

## 12. Road-Class Metrics

The test tooling should aim to calculate:

```text
motorway distance
trunk distance
primary distance
secondary distance
tertiary distance
unclassified distance
residential distance
living_street distance
service distance
track distance
```

Both absolute distance and percentage should be recorded.

Example:

```text
motorway:
  distance_km: 12.4
  percentage: 18.7
```

---

## 13. Surface Metrics

Where route metadata allows it, record:

```text
paved distance
unpaved distance
unknown-surface distance
```

The standard profiles should normally produce:

```text
unpaved distance = 0
```

Unexpected unpaved routing should be treated as a high-priority defect.

---

## 14. Urban Metrics

Urban behaviour should be evaluated separately.

Possible metrics include:

```text
residential-road distance
living-street distance
service-road distance
low-speed road distance
number of suspicious local-road excursions
```

Automated urban classification may be incomplete.

Visual route inspection remains important.

---

## 15. Motorway Behaviour

Motorway usage should normally decrease as `curviness` increases.

For the same reference route, the expected tendency is:

```text
Fast
  >= Fast Curvy
  >= Curvy
  >= Very Curvy
```

This is a behavioural expectation, not a strict rule for every individual route.

A short motorway segment may remain correct if avoiding it would create a disproportionate detour.

---

## 16. Curviness Behaviour

Increasing curviness should generally produce a visible shift towards:

```text
secondary
tertiary
suitable unclassified
```

and away from:

```text
motorway
trunk
major high-speed primary roads
```

It must not systematically increase:

```text
residential
living_street
service
track
```

---

## 17. Fast Curvy Behaviour

`Fast Curvy` is particularly important because it acts as the compromise profile.

It should not behave merely as:

```text
Fast with a tiny cost adjustment
```

nor as:

```text
Curvy with a different name
```

Expected behaviour:

* visibly less motorway dependence than Fast where good alternatives exist
* materially shorter or faster than Curvy in many cases
* limited use of minor roads
* no artificial local-road detours

---

## 18. Very Curvy Behaviour

`Very Curvy` may accept larger detours than `Curvy`.

However, a stronger curviness setting must not justify arbitrary distance inflation.

Potential regression signals include:

```text
large distance increase with little road-character improvement
repeated local-road switching
urban zig-zag routing
loops
unnecessary backtracking
```

---

## 19. Hilliness Behaviour

The comparison:

```text
Curvy
versus
Curvy Hilly
```

is the primary initial hilliness test.

Both profiles have identical:

```text
curviness = 2
```

Only hilliness differs.

This makes the comparison particularly useful.

Expected effects may include:

* more elevation variation
* higher maximum elevation
* greater elevation gain
* selection of hilly alternatives

Expected non-effects:

* major changes in road-class philosophy
* increased residential usage
* increased unpaved usage
* extreme distance inflation

---

## 20. Hilliness Independence Test

The test suite should explicitly verify the design assumption:

```text
changing hilliness does not change curviness configuration
```

At minimum, generated profile values must confirm this mechanically.

Behaviourally, hilliness changes should not create large road-class shifts unless those shifts are a natural consequence of terrain.

---

## 21. Distance Detour Ratio

A useful comparison metric is the detour ratio relative to Fast.

Conceptually:

```text
detour_ratio =
    route_distance(profile)
    /
    route_distance(fast)
```

Examples:

```text
1.00 = same distance
1.10 = 10% longer
1.25 = 25% longer
```

No hard universal limit should initially be enforced.

Instead, observed values should be collected during calibration.

---

## 22. Time Detour Ratio

The same concept applies to estimated travel time:

```text
time_ratio =
    travel_time(profile)
    /
    travel_time(fast)
```

This is especially important for motorcycle routing because two routes with similar distances may have very different travel times.

---

## 23. Initial Detour Guidance

The following values may be used as starting guidance only.

They are not normative acceptance thresholds.

```text
Fast Curvy:
  small detours expected

Curvy:
  moderate detours acceptable

Very Curvy:
  larger but clearly justified detours acceptable

Curvy Hilly:
  moderate additional detour may be acceptable
```

Exact thresholds should be derived empirically.

---

## 24. Excessive Detour Detection

The test tooling should flag routes for manual review when one or more of the following occurs:

```text
distance changes dramatically
travel time changes dramatically
road-class composition changes unexpectedly
residential usage increases sharply
unpaved distance becomes non-zero
route contains loops
route visibly backtracks
```

Flagging does not automatically mean failure.

It means the route requires inspection.

---

## 25. Regression Baseline

Each accepted release or calibration milestone should establish a baseline.

For every:

```text
reference route × preset
```

store the resulting metrics.

A later change can then be compared against the baseline.

Example:

```text
baseline/
  v0.1/
    ch-biel-neuchatel/
      fast.json
      fast-curvy.json
      curvy.json
      very-curvy.json
      curvy-hilly.json
```

---

## 26. Regression Comparison

A regression report should highlight differences such as:

```text
distance       +8.3%
travel time    +5.7%
motorway       -42%
secondary      +31%
residential    +0.4 km
elevation gain +320 m
```

The report should make route behaviour changes visible without requiring manual comparison of raw data.

---

## 27. Behavioural Expectations

The test suite should encode broad expectations rather than overly precise route outputs.

Examples:

```text
Very Curvy should normally use no more motorway than Curvy.

Curvy should normally use no more motorway than Fast.

Increasing curviness must not systematically increase residential-road usage.

Standard profiles should not use unsuitable unpaved roads.

Curvy Hilly should preserve curviness level 2.
```

These expectations should be treated as regression guards.

---

## 28. Avoid Exact Route Locking

Tests should not normally require an exact sequence of road segments.

OpenStreetMap data changes over time.

BRouter data and elevation data may also change.

Tests should therefore focus on:

* route characteristics
* broad behavioural expectations
* metric ranges
* major anomalies

rather than exact geometry equality.

---

## 29. OSM Data Version

Where possible, test reports should record:

```text
BRouter version
routing-data date
profile version
test-tool version
```

This makes changes caused by map-data updates distinguishable from changes caused by profile logic.

---

## 30. BRouter Version

Test output should include the BRouter version used.

Changes in BRouter itself may alter routing behaviour.

A regression should therefore not automatically be attributed to the profile.

---

## 31. Smoke Tests

A small subset of routes should serve as fast smoke tests.

Suggested initial smoke routes:

```text
Biel/Bienne → Neuchâtel
Thun → Andermatt
```

These provide:

* one relatively short mixed route
* one strongly terrain-dependent route

All presets should route successfully on both.

---

## 32. Full Test Suite

The full suite should run:

```text
all presets
×
all reference routes
```

With five initial profiles and five reference routes:

```text
5 × 5 = 25 routes
```

This is small enough to remain practical.

---

## 33. Test Output

Automated test results should preferably use structured data.

Example:

```json
{
  "route": "ch-biel-neuchatel",
  "profile": "curvy",
  "distance_km": 44.1,
  "travel_time_min": 49,
  "elevation_gain_m": 310,
  "road_classes": {
    "motorway_pct": 0,
    "primary_pct": 18.4,
    "secondary_pct": 52.1,
    "tertiary_pct": 21.7,
    "residential_pct": 1.8
  }
}
```

Human-readable reports can then be generated from this data.

---

## 34. Route Geometry

Where practical, every test result should also retain route geometry, for example as GPX or GeoJSON.

This allows:

* visual comparison
* loading routes into OsmAnd
* inspection in mapping tools
* archiving known routing behaviour

---

## 35. Visual Inspection

Quantitative metrics cannot detect all routing problems.

Important routes should be inspected visually for:

```text
zig-zagging
loops
backtracking
unreasonable village detours
unexpected motorway use
unexpected tiny-road use
poor route continuity
```

Visual inspection should be mandatory for significant routing-model changes.

---

## 36. Subjective Motorcycle Evaluation

Selected routes may receive real-world evaluation.

Suggested score:

```text
1 = poor
2 = acceptable
3 = good
4 = very good
5 = excellent
```

The score should always include a short reason.

Example:

```yaml
score: 4
notes:
  Good flowing secondary roads.
  One unnecessary village detour near the destination.
```

---

## 37. Real-World Test Record

A ridden route may record:

```yaml
route: ch-thun-andermatt
profile: curvy-hilly
date: 2026-09-01

score: 4

observations:
  - good mountain-road selection
  - no unwanted unpaved segments
  - one unnecessary local-road diversion

navigation:
  - turn instructions correct
  - no obvious access issues
```

---

## 38. Safety Defects

The following findings should be treated as high-priority defects:

```text
routing through prohibited motorcycle access
routing against one-way restrictions
routing through impassable barriers
unexpected unsuitable unpaved routing
unsafe or clearly invalid route geometry
```

A route being insufficiently curvy is a tuning issue.

A route violating legal or physical constraints is a defect.

---

## 39. Calibration Log

Major calibration changes should be documented.

Example:

```text
2026-08-20

Changed:
Very Curvy motorway cost 5.0 → 6.0

Reason:
Motorway remained dominant on Bern → Luzern.

Observed result:
Motorway share reduced significantly.
No material residential-road increase.
```

This may later be maintained in:

```text
docs/calibration-log.md
```

or in the changelog.

---

## 40. Test Automation

The project should aim to automate:

```text
profile generation
BRouter route calculation
metric extraction
baseline comparison
regression reporting
```

Manual work should focus on:

```text
visual inspection
subjective quality
real-world riding
```

---

## 41. Test Tooling Architecture

A possible future structure is:

```text
tests/
├── routes/
│   ├── ch-biel-neuchatel.yaml
│   ├── ch-bern-luzern.yaml
│   ├── ch-thun-andermatt.yaml
│   ├── ch-zurich-davos.yaml
│   └── ch-aigle-martigny.yaml
│
├── baseline/
│
└── reports/

tools/
├── generate_profiles.py
├── run_tests.py
└── compare_results.py
```

The exact tooling language is not normative.

Python is a reasonable default because the required automation is straightforward and portable.

---

## 42. Continuous Integration

Once local testing is stable, GitHub Actions may run:

```text
profile-generation validation
syntax checks
smoke tests
regression guards
```

Full route testing should only be added to CI if BRouter execution and routing data can be made reproducible and reasonably lightweight.

---

## 43. Pull Request Expectations

A routing-behaviour change should ideally include:

* explanation of the intended behaviour change
* changed specification or routing model where required
* test results
* comparison against baseline
* screenshots or route plots for major behavioural changes where useful

---

## 44. Acceptance Criteria for v0.1

The first usable release should satisfy all of the following:

```text
All generated profiles load successfully.

All smoke-test routes calculate successfully.

No standard profile uses unsuitable unpaved roads.

Curvy profiles do not systematically zig-zag through residential areas.

Motorway usage generally decreases with increasing curviness.

Secondary and tertiary road usage generally increases with curviness where alternatives exist.

Curvy Hilly produces a measurable terrain difference on at least one suitable reference route.

Curvy Hilly does not change the configured curviness level.

No tested profile shows unexplained routing loops.

No known access or one-way violations remain.
```

---

## 45. What Tests Must Not Optimise For

The test process must not accidentally redefine the project objective as:

```text
maximum number of bends
maximum number of road-class changes
maximum elevation gain
minimum motorway percentage
maximum route length
```

The target remains:

> enjoyable, sensible, predictable motorcycle routing.

Metrics support this goal. They do not replace it.

---

## 46. Initial Testing Workflow

For each routing-model change:

```text
1. Update specification or routing model if required.

2. Generate all profiles.

3. Run profile validation.

4. Run smoke tests.

5. Run the full reference-route suite.

6. Compare results against the current baseline.

7. Inspect flagged routes visually.

8. Accept, adjust, or revert the change.

9. Update the baseline only after the new behaviour is intentionally accepted.
```

---

## 47. v0.1 Testing Rule

A routing change should not be considered an improvement merely because one route looks better.

It should improve the intended behaviour across representative routes without introducing unacceptable regressions elsewhere.

