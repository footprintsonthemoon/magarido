# Magarido -- Development Guide

## 1. Purpose

This document describes the current development environment,
implementation architecture and validation workflow for the BRouter
Motorcycle project.

It documents the system as it exists now. Historical experiments are
included only where they explain a current design decision.

The reference development environment is:

-   macOS on Apple Silicon
-   Homebrew
-   OpenJDK
-   upstream BRouter standalone server
-   Python virtual environment
-   local BRouter `.rd5` routing segments
-   BRouter KinematicModel-based motorcycle routing
-   YAML-based segment planning
-   GeoJSON and GPX output
-   OsmAnd as the current navigation target

The Mac is used for development, testing and route planning. Android
with BRouter/OsmAnd remains the target navigation environment.

## 2. Current Architecture

The current routing flow is:

``` text
YAML tour definition
        |
        v
segment routing intention
        |
        +-- character: fast | curvy | very-curvy
        |
        +-- constraints:
        |      avoid_motorways
        |      avoid_toll
        |
        +-- secondary preferences:
               hills: off | moderate | strong
        |
        v
tools/profile_compiler.py
        |
        v
compiled KinematicModel BRF
        |
        v
BRouter
        |
        +-- baseline route
        +-- alternatives when required
        |
        v
planner-level alternative selection
        |
        v
segment result
        |
        v
combined GeoJSON + GPX
        |
        v
OsmAnd
```

The important architectural separation is:

``` text
routing character
    !=
routing constraints
    !=
secondary preferences
    !=
vehicle characteristics
```

These dimensions may influence the same route, but they have different
semantics and must not be collapsed into a growing list of user-facing
profiles.

## 3. Relevant Repository Structure

The current planner-related structure is conceptually:

``` text
magarido/
├── docs/
│   ├── development.md
│   ├── routing-model.md
│   ├── specification.md
│   └── testing.md
├── examples/
│   ├── alpine-tour.yaml
│   └── intent-tests/
├── output/
│   └── compiled-profiles/
├── profiles/
│   └── ...
├── release/
│   └── ...
├── src/
│   ├── moto-base.brf
│   └── moto-kinematic-base.brf
├── tests/
├── tools/
│   ├── generate_profiles.py
│   ├── plan_route.py
│   ├── profile_compiler.py
│   ├── run_calibration_tests.py
│   ├── run_kinematic_tests.py
│   ├── run_smoke_tests.py
│   └── serve_results.py
└── requirements-dev.txt
```

For the current segment planner:

-   `src/moto-kinematic-base.brf` is the canonical KinematicModel
    routing source.
-   `tools/profile_compiler.py` compiles routing intentions into BRouter
    profiles.
-   `tools/plan_route.py` routes segments, evaluates alternatives where
    required, and creates complete tour output.
-   `output/compiled-profiles/` contains generated intent profiles.
-   `examples/` contains reproducible planner examples and regression
    cases.

`src/moto-base.brf`, the traditional generated profiles under
`profiles/`, and the release profiles remain useful for historical
comparison and the earlier standalone-profile workflow. They are not the
canonical source for the current segment planner.

## 4. Prerequisites

Verify Homebrew:

``` bash
brew --prefix
```

On Apple Silicon this normally returns:

``` text
/opt/homebrew
```

## 5. Java and BRouter

Install OpenJDK:

``` bash
brew install openjdk
```

Make the JVM visible to macOS:

``` bash
sudo ln -sfn "$(brew --prefix openjdk)/libexec/openjdk.jdk" \
  /Library/Java/JavaVirtualMachines/openjdk.jdk
```

Verify:

``` bash
java -version
```

Clone upstream BRouter outside this project:

``` bash
mkdir -p ~/opt
cd ~/opt
git clone https://github.com/abrensch/brouter.git
cd brouter
```

Build the standalone server:

``` bash
./gradlew fatJar
```

A full `./gradlew clean build` is not required for this project.

## 6. Start the BRouter Standalone Server

From the BRouter repository:

``` bash
cd ~/opt/brouter
./misc/scripts/standalone/server.sh
```

The planner expects the local endpoint:

``` text
http://localhost:17777/brouter
```

Keep the server running while executing routing tests or
`plan_route.py`.

## 7. Routing Segments

BRouter requires `.rd5` routing data.

The reference directory is:

``` text
~/opt/brouter/misc/segments4/
```

Example:

``` bash
mkdir -p ~/opt/brouter/misc/segments4

curl -L \
  https://brouter.de/brouter/segments4/E5_N45.rd5 \
  -o ~/opt/brouter/misc/segments4/E5_N45.rd5
```

Additional routes may require additional tiles.

## 8. Python Environment

From the project root:

``` bash
python3 -m venv .venv
source .venv/bin/activate
python3 -m pip install -r requirements-dev.txt
```

PyYAML is required by the planner.

If the repository is moved and the virtual environment contains stale
absolute paths, recreate it:

``` bash
deactivate 2>/dev/null || true
rm -rf .venv

python3 -m venv .venv
source .venv/bin/activate
python3 -m pip install -r requirements-dev.txt
```

## 9. KinematicModel Foundation

The current planner uses BRouter's KinematicModel as the time-oriented
routing foundation.

The earlier custom Fast model approximated travel-time preference
through a speed-derived cost factor. Tests showed that reported travel
time was difficult to interpret reliably. KinematicModel provides a
physically motivated model that accounts for speed,
acceleration/deceleration, rolling resistance, aerodynamic resistance,
elevation and junction/curve effects.

The current routing characters share this foundation:

``` text
Fast
    expected travel time dominates

Curvy
    time-oriented routing
    + moderate motorcycle-road preference

Very Curvy
    time-oriented routing
    + stronger motorcycle-road preference
```

The routing character therefore controls the trade-off between expected
travel time and desirable motorcycle-road character.

## 10. Motorcycle Parameter Finding

A generic touring-motorcycle experiment used approximately:

``` text
total weight:        340 kg
rolling resistance:   50 N
aerodynamic factor:  0.35
target speed:         120 km/h
```

Reference results:

  ------------------------------------------------------------------------
  Route       Parameters      Distance        Time      Ascent        Cost
  ----------- ------------ ----------- ----------- ----------- -----------
  Bern -\>    car-like        110.5 km    74.2 min       416 m      126203
  Luzern                                                       

  Bern -\>    motorcycle      110.5 km    68.9 min       416 m      121516
  Luzern                                                       

  Thun -\>    car-like        119.3 km   145.0 min      2673 m      197288
  Andermatt                                                    

  Thun -\>    motorcycle      119.3 km   128.0 min      2673 m      183699
  Andermatt                                                    
  ------------------------------------------------------------------------

In these tests, vehicle parameters changed time and cost without
changing the selected route.

This supports keeping vehicle characteristics separate from routing
intention.

The current implementation uses a generic motorcycle model. A future
application may derive KinematicModel parameters from understandable
inputs such as motorcycle weight, rider weight, luggage and motorcycle
type. Low-level physical coefficients should normally remain hidden from
users.

## 11. Profile Compiler

`tools/profile_compiler.py` converts a segment routing intention into a
KinematicModel BRF.

Example intention:

``` yaml
routing:
  character: curvy
  preferences:
    hills: strong
  constraints:
    avoid_motorways: false
    avoid_toll: false
```

The compiler currently maps the routing character to the corresponding
curviness level and applies profile-level constraints such as motorway
and toll avoidance.

Generated profiles are written to:

``` text
output/compiled-profiles/
```

and linked into the BRouter profile directory.

The profile name contains a hash of the profile-relevant intention.
Planner-only preferences such as `hills` do not need a distinct BRF when
they do not change the underlying cost model.

## 12. Segment Planner

`tools/plan_route.py` reads a YAML tour definition and routes each
segment independently.

Example:

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
```

Run:

``` bash
python tools/plan_route.py examples/alpine-tour.yaml
```

The planner:

1.  validates the tour,
2.  normalises each routing intention,
3.  compiles the required BRouter profile,
4.  routes each segment,
5.  evaluates BRouter alternatives when a planner-level preference
    requires it,
6.  joins the segment geometries,
7.  writes GeoJSON,
8.  writes GPX with waypoints and a continuous track.

## 13. Routing Constraints

The currently validated constraints are:

``` text
avoid_motorways
avoid_toll
```

They are intentionally independent.

A toll road is not semantically identical to a motorway.
Country-specific road charging must not be encoded as a generic
equivalence between the two controls.

### Martigny -\> Aosta regression case

Observed results:

  Intention                  Distance        Time   Ascent     Cost
  ------------------------ ---------- ----------- -------- --------
  Fast                        73.2 km    83.9 min   1473 m   115474
  Fast + avoid toll           77.9 km   102.1 min   2023 m   140871
  Fast + avoid motorways      73.2 km    83.9 min   1473 m   115474

The Fast and Fast + avoid-motorways geometries were identical. The
avoid-toll geometry differed.

This is particularly useful around the Great St Bernard, because it
demonstrates that road class and toll semantics must be evaluated
separately. It is a regression case, not a route-specific exception in
the implementation.

## 14. Hilliness

Hilliness is a secondary preference, not a routing character.

The user-facing model is:

``` text
hills: off
hills: moderate
hills: strong
```

Curviness is considered more important than hilliness for the current
motorcycle-routing goal.

Therefore:

``` text
Curvy + hills: strong
```

means:

``` text
find a good Curvy route first,
then prefer a meaningfully hillier acceptable alternative
```

It does not mean:

``` text
maximise ascent
```

## 15. Hilliness Alternative Selection

Hilliness is currently implemented at planner level using BRouter
alternatives.

Conceptually:

``` text
baseline route
      |
      v
request alternatives
      |
      v
compare time and ascent characteristics
      |
      v
is a meaningfully hillier alternative acceptable?
      |
   yes|no
      |
      +---- yes -> select alternative
      |
      +---- no  -> retain baseline
```

The current implementation uses general thresholds for additional
ascent, ascent density and acceptable time increase. `moderate` has a
tighter time budget than `strong`.

The important design rule is that the algorithm must remain generic. It
must not contain special cases for named roads or calibration routes.

## 16. Hilliness Regression Tests

Current validated cases:

  ----------------------------------------------------------------------------------
  Route       Character   Hills        Selected   Distance    Time   Ascent     Cost
                                          route                             
  ----------- ----------- ---------- ---------- ---------- ------- -------- --------
  Biel -\>    Curvy       Strong          alt 2    40.3 km    48.2    810 m    70011
  Neuchatel                                                    min          

  Fribourg    Curvy       Moderate        alt 2   172.9 km   185.6   2090 m   308341
  -\> Altdorf                                                  min          

  Thun -\>    Curvy       Strong       baseline   113.3 km   132.1   2674 m   196336
  Andermatt                                                    min          
  ----------------------------------------------------------------------------------

The Thun -\> Andermatt case is especially important: the baseline route
is already strongly mountainous. `strong` therefore does not force a
worse alternative simply to accumulate more ascent.

Run the current examples:

``` bash
python tools/plan_route.py \
  examples/intent-tests/biel-neuchatel-curvy-hills-strong.yaml

python tools/plan_route.py \
  examples/intent-tests/fribourg-altdorf-curvy-hills-moderate.yaml

python tools/plan_route.py \
  examples/intent-tests/thun-andermatt-curvy-hills-strong.yaml
```

## 17. Inspecting BRouter Alternatives

BRouter alternatives can be requested using `alternativeidx`.

The Curvy Biel -\> Neuchatel diagnostic set produced:

    Alternative   Distance       Time   Ascent    Cost
  ------------- ---------- ---------- -------- -------
              0    32.7 km   29.9 min     61 m   52215
              1    35.6 km   44.7 min    211 m   65533
              2    40.3 km   48.2 min    810 m   70011
              3    32.4 km   42.7 min     54 m   74732

This demonstrates why alternative number or cost alone has no useful
semantic meaning. The planner must evaluate alternatives against the
user's preference.

## 18. GPX and GeoJSON Output

The planner writes:

``` text
output/<tour-name>.geojson
output/<tour-name>.gpx
```

The GPX contains:

-   tour waypoints,
-   one continuous route track.

The generated multi-segment GPX has been validated in OsmAnd. OsmAnd may
show the imported track most clearly when it is selected for navigation.

## 19. Manual BRouter HTTP Test

A direct request remains useful for debugging:

``` bash
curl -G 'http://localhost:17777/brouter' \
  --data-urlencode 'lonlats=7.2468,47.1368|6.9293,46.9896' \
  --data-urlencode 'profile=<compiled-profile-name>' \
  --data-urlencode 'alternativeidx=0' \
  --data-urlencode 'format=geojson'
```

A successful response contains a GeoJSON FeatureCollection.

## 20. Debugging BRouter Errors

For HTTP 500 responses, inspect the terminal running the standalone
server.

Typical errors include:

``` text
ParseException ...
unknown lookup value ...
unknown expression ...
profile ... does not exist
```

The first parse error is normally the most useful diagnostic line.

BRouter expression-language findings from development include:

-   the comparison operator is `lesser`, not `less`,
-   lookup values must exist in BRouter lookup tables,
-   OSM lookup fields cannot always be treated as ordinary numeric
    expressions,
-   `.brf` files must not contain Markdown code fences.

## 21. Legacy Profile Generation and Calibration

The repository still contains the earlier profile-generation and
calibration tooling:

``` text
tools/generate_profiles.py
tools/run_smoke_tests.py
tools/run_calibration_tests.py
tools/serve_results.py
src/moto-base.brf
profiles/
release/
```

This tooling remains useful for regression comparison and for
understanding the development history of Fast, Curvy and Very Curvy.

It must not be confused with the current segment-planner architecture.

In particular, earlier experimental profiles such as:

``` text
moto-fast-curvy
moto-curvy-hilly
moto-curvy-very-hilly
```

are not additional user-facing routing characters in the current model.

Hilliness is now represented as a secondary planner preference.

## 22. Validation Method

Changes to routing behaviour should follow:

``` text
observation
    ->
hypothesis
    ->
general implementation
    ->
independent validation
```

Do not optimise for a single named road.

Useful validation dimensions include:

-   route geometry,
-   distance,
-   expected time,
-   ascent,
-   cost,
-   motorway behaviour,
-   toll behaviour,
-   robustness where no meaningful alternative exists,
-   behaviour on geographically different routes.

Visual inspection remains important because aggregate metrics alone
cannot determine whether a motorcycle route is attractive.

## 23. Git Policy

Commit:

-   source profiles,
-   planner/compiler code,
-   YAML regression cases,
-   documentation,
-   stable test definitions,
-   intentionally retained release profiles.

Do not commit transient planner output unless it is deliberately being
used as a regression fixture.

Generated runtime output such as temporary GeoJSON, GPX and compiled
intent profiles should normally remain ignored.

## 24. Experimental Evidence Work

Traffic, pseudo-tag and urban-routing semantics were investigated extensively,
including H1/H2/H3 evidence separation, missing-value semantics, gated H2
traffic, urban rolling windows, `strict_core`, local excursions and bounded
`urban_burden` v0.1/v0.2 routing tests.

These experiments did not establish sufficient general routing benefit to add
a new traffic or urban-burden modifier to v1. Detailed hypotheses, catalogues,
results and rejected approaches are retained in `archive/experiments.md`.

## 25. Current Development Priorities

The validated planner dimensions remain Fast, Curvy and Very Curvy; independent
`avoid_motorways` and `avoid_toll` constraints; and hills as off, moderate or
strong.

`avoid_cities` is not a validated v1 feature. The urban investigation is
closed for v1. The next phase focuses on regression and behaviour testing,
release tooling, reproducibility and validation of the complete routing
character set.

## 27. Reproducibility

The project should remain reproducible without machine-specific
assumptions.

Documentation should therefore prefer:

``` text
~/opt/brouter
project-relative paths
environment variables where appropriate
```

over personal absolute paths.

A fresh development machine should be able to reproduce the planner
with:

1.  Java,
2.  upstream BRouter,
3.  required `.rd5` tiles,
4.  the Python environment,
5.  this repository,
6.  the documented commands above.

## v1 Routing-Core Freeze

The routing core has passed final acceptance and is frozen for v1 release
preparation.

Do not continue tuning routing weights merely to increase visual differences
between Fast, Curvy and Very Curvy. Convergence on constrained corridors is
valid behaviour.

A routing-core change after this point requires one of:

1. a reproducible regression defect,
2. materially new independent routing evidence,
3. a deliberate post-v1 feature decision.

Routine v1 work should now focus on regression protection, packaging,
reproducibility, release tooling and documentation.

## 28. v1 Release Build

The v1 release contains exactly three user-facing BRF files:

```text
release/moto-fast.brf
release/moto-curvy.brf
release/moto-very-curvy.brf
```

The release is built reproducibly with:

```bash
python tools/build_release.py --check
python tools/build_release.py
```

The builder first regenerates the development profiles and then verifies the
release profiles byte-for-byte by SHA-256.

Release files are written through verified temporary files and atomically
replaced only after size and hash checks succeed. This avoids truncating an
existing release file during the build, including on synchronised filesystems.

A clean release build must leave:

```bash
git diff --exit-code -- release/ profiles/
```

with exit code `0`.

The release profiles are intentionally committed so users can install them
without requiring Python or the development toolchain.
