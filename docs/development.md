# BRouter Motorcycle Profiles – Development Setup

## 1. Purpose

This document describes how to set up a local development and calibration
environment for the BRouter Motorcycle Profiles project on macOS.

The reference setup uses:

- macOS on Apple Silicon
- Homebrew
- OpenJDK
- BRouter standalone server
- Python virtual environment
- local BRouter routing segments
- generated `.brf` profiles
- automated smoke and calibration tests
- browser-based comparison maps

The Android device running BRouter and OsmAnd is the target environment.

The Mac is used only for development, calibration and validation.


## 2. Repository Structure

The relevant project structure is:

    brouter-motorcycle/
    ├── config/
    │   └── presets.yaml
    ├── docs/
    │   ├── development.md
    │   ├── routing-model.md
    │   ├── specification.md
    │   └── testing.md
    ├── profiles/
    │   ├── moto-fast.brf
    │   ├── moto-fast-curvy.brf
    │   ├── moto-curvy.brf
    │   ├── moto-very-curvy.brf
    │   ├── moto-curvy-hilly.brf
    │   └── moto-curvy-very-hilly.brf
    ├── release/
    │   ├── moto-fast.brf
    │   ├── moto-curvy.brf
    │   └── moto-very-curvy.brf
    ├── src/
    │   └── moto-base.brf
    ├── tools/
    │   ├── generate_profiles.py
    │   ├── run_calibration_tests.py
    │   ├── run_smoke_tests.py
    │   └── serve_results.py
    └── requirements-dev.txt

`src/moto-base.brf` is the canonical source profile.

`profiles/` contains all development and experimental profiles.

`release/` contains only the current user-facing release candidates.


## 3. Prerequisites

The setup assumes Homebrew is installed.

Verify:

    brew --prefix

On Apple Silicon this typically returns:

    /opt/homebrew


## 4. Install Java

BRouter requires Java.

Install OpenJDK with Homebrew:

    brew install openjdk

Homebrew installs OpenJDK as a keg-only package.

To make the JVM visible to macOS Java tooling, create the recommended symlink:

    sudo ln -sfn "$(brew --prefix openjdk)/libexec/openjdk.jdk" \
      /Library/Java/JavaVirtualMachines/openjdk.jdk

Verify:

    java -version

A working setup should return an OpenJDK runtime.

The reference development environment currently uses:

    OpenJDK 26.0.2.1

The exact patch version is not considered normative.


## 5. Clone BRouter

BRouter is kept outside the project repository.

A convenient location is:

    ~/opt/brouter

Install:

    mkdir -p ~/opt
    cd ~/opt
    git clone https://github.com/abrensch/brouter.git
    cd brouter

The reference environment currently tracks the upstream `master` branch.


## 6. Build the BRouter Standalone Server

A fresh BRouter source checkout does not contain the standalone server JAR.

Build the fat JAR:

    ./gradlew fatJar

The full command:

    ./gradlew clean build

is not required for this project.

During development, a full build may fail in PMD analysis even though the
standalone routing server itself can be built successfully.

For this project, `fatJar` is the relevant build target.

After the build, verify:

    ls -lh brouter-server/build/libs/

A BRouter server JAR should be present.


## 7. Start the BRouter Standalone Server

From the BRouter repository:

    cd ~/opt/brouter
    ./misc/scripts/standalone/server.sh

The server should start and print the BRouter version.

The default local routing endpoint used by this project is:

    http://localhost:17777/brouter

Keep this terminal running while executing smoke or calibration tests.


## 8. Install Routing Segments

BRouter requires `.rd5` routing segment files.

Create the local segment directory if necessary:

    mkdir -p ~/opt/brouter/misc/segments4

For Switzerland, the relevant segments must be downloaded from the BRouter
segment server.

For example:

    curl -L \
      https://brouter.de/brouter/segments4/E5_N45.rd5 \
      -o ~/opt/brouter/misc/segments4/E5_N45.rd5

Additional test routes may require additional `.rd5` tiles.

If BRouter reports that a segment is missing, download the required tile and
place it in the same `segments4` directory.


## 9. Create the Python Development Environment

From the project root:

    python3 -m venv .venv
    source .venv/bin/activate

Then install development dependencies:

    python3 -m pip install -r requirements-dev.txt

The current development requirements include PyYAML.

Verify:

    python3 -m pip show PyYAML

The reference environment currently uses:

    Python 3.9.6
    PyYAML 6.0.3


## 10. Recreate the Virtual Environment After Moving the Project

Python virtual environments can contain absolute paths.

If the project directory is renamed or moved, an existing `.venv` may fail
with an error similar to:

    bad interpreter:
    .../.venv/bin/python3: no such file or directory

In that case, recreate the environment:

    deactivate 2>/dev/null || true
    rm -rf .venv

    python3 -m venv .venv
    source .venv/bin/activate

    python3 -m pip install -r requirements-dev.txt


## 11. Generate Profiles

Generate all development and release profiles:

    python tools/generate_profiles.py

The generator creates:

    profiles/

containing all development profiles, and:

    release/

containing only user-facing release profiles.

List configured presets:

    python tools/generate_profiles.py --list


## 12. Link Generated Profiles into BRouter

The local BRouter standalone server reads profiles from:

    ~/opt/brouter/misc/profiles2/

During development, symbolic links are preferable to copying files.

From the project root:

    for f in profiles/*.brf; do
      ln -sf "$(pwd)/$f" \
        ~/opt/brouter/misc/profiles2/"$(basename "$f")"
    done

Verify:

    ls -l ~/opt/brouter/misc/profiles2/moto-*.brf

This setup means regenerated profiles are immediately visible to BRouter
without manual copying.

Because these links live inside the upstream BRouter Git repository, they
should be ignored locally rather than added to BRouter's `.gitignore`.

From the BRouter repository:

    printf '\n# Local motorcycle development profiles\nmisc/profiles2/moto-*.brf\n' \
      >> .git/info/exclude

This keeps the upstream BRouter working tree clean without modifying tracked
BRouter files.


## 13. Adding New Development Profiles

When a new profile is added to `config/presets.yaml`, regenerate profiles:

    python tools/generate_profiles.py

Then rerun the symlink loop:

    for f in profiles/*.brf; do
      ln -sf "$(pwd)/$f" \
        ~/opt/brouter/misc/profiles2/"$(basename "$f")"
    done

If this step is skipped, BRouter may report:

    profile <name>.brf does not exist


## 14. Smoke Tests

Start the BRouter standalone server first.

Then, from the project root:

    python tools/run_smoke_tests.py

The smoke test verifies that all development profiles can calculate a route
successfully.

A successful run should contain only `[OK]` results.


## 15. Manual BRouter HTTP Test

A direct route request can be useful when debugging.

Example:

    curl -G 'http://localhost:17777/brouter' \
      --data-urlencode 'lonlats=7.2468,47.1368|6.9293,46.9896' \
      --data-urlencode 'profile=moto-fast' \
      --data-urlencode 'alternativeidx=0' \
      --data-urlencode 'format=geojson'

A successful response contains a GeoJSON FeatureCollection.


## 16. Debugging HTTP 500 Errors

When the test runner reports:

    HTTP Error 500: Internal Server Error

the useful error message usually appears in the terminal running the BRouter
standalone server.

Typical errors include:

    ParseException ...
    unknown lookup value ...
    unknown expression ...
    profile ... does not exist

The first `ParseException` is usually the most useful diagnostic line.


## 17. BRouter Profile Syntax Notes

Several BRouter expression-language details were encountered during setup.

Examples:

- the comparison operator is `lesser`, not `less`
- lookup values must exist in BRouter's lookup tables
- OSM lookup fields cannot always be used as ordinary numeric expressions
- generated `.brf` files must not contain Markdown code fences

If a generated profile fails, inspect the BRouter server output before changing
the routing model.


## 18. Calibration Tests

Run the full calibration suite:

    python tools/run_calibration_tests.py

The calibration runner:

- calculates all configured development profiles
- records route statistics
- writes GeoJSON results
- creates comparison maps
- writes a CSV report

Generated output is stored under:

    tests/results/

This directory is considered generated test output.


## 19. Calibration Results

Typical result structure:

    tests/results/
    ├── calibration.csv
    ├── bern-luzern/
    │   ├── comparison.html
    │   ├── moto-fast.geojson
    │   ├── moto-curvy.geojson
    │   └── ...
    ├── biel-bienne-neuchatel/
    ├── fribourg-altdorf/
    ├── interlaken-brienz/
    └── ...

The exact set of routes may evolve over time.


## 20. Serve Comparison Results

Do not open the generated comparison HTML files directly using `file://`.

The OpenStreetMap tile service requires a valid HTTP referrer and may return
HTTP 403 when the page is opened directly from the filesystem.

Instead run:

    python tools/serve_results.py

The script starts a small local HTTP server and opens the calibration result
index in the browser.

The local URL is typically:

    http://127.0.0.1:8080/tests/results/index.html

If the browser does not open automatically:

    open http://127.0.0.1:8080/tests/results/index.html


## 21. Visual Calibration Workflow

A normal calibration cycle is:

    1. edit src/moto-base.brf
    2. generate profiles
    3. run smoke tests
    4. run calibration tests
    5. serve comparison results
    6. visually inspect route behaviour
    7. accept, adjust or revert the change

Commands:

    python tools/generate_profiles.py
    python tools/run_smoke_tests.py
    python tools/run_calibration_tests.py
    python tools/serve_results.py

The BRouter standalone server must already be running.


## 22. Development Profiles vs Release Profiles

The project deliberately separates:

    profiles/

from:

    release/

`profiles/` contains the complete development parameter space.

This currently includes experimental profiles used for calibration.

`release/` contains only the profiles intended for normal users.

The current release set is:

    moto-fast
    moto-curvy
    moto-very-curvy

The current experimental profiles include:

    moto-fast-curvy
    moto-curvy-hilly
    moto-curvy-very-hilly


## 23. Git Policy

The following should be committed:

- `src/moto-base.brf`
- `config/presets.yaml`
- `profiles/*.brf`
- `release/*.brf`
- development tools
- documentation

The following should not be committed:

- `.venv/`
- Python cache files
- macOS `.DS_Store`
- generated calibration output under `tests/results/`

A suitable `.gitignore` therefore includes at least:

    .venv/
    __pycache__/
    *.pyc
    .DS_Store
    tests/results/


## 24. Why Generated Profiles Are Committed

Generated `.brf` files are intentionally kept in the repository.

This has two advantages.

For users:

- release profiles can be downloaded directly
- Python is not required

For developers:

- generated output can be reviewed in Git
- unexpected generator changes are visible
- calibration profiles are reproducible


## 25. Reference Development Versions

The current reference setup used during development includes:

    BRouter source:
        upstream master
        v1.7.10-4-g7b0be763 during current calibration

    OpenJDK:
        26.0.2.1

    Python:
        3.9.6

    PyYAML:
        6.0.3

These versions document the environment used during development.

They are not intended as strict minimum or maximum version requirements unless
future testing identifies a compatibility constraint.


## 26. Target Android Environment

The Mac development environment is not the deployment target.

The user-facing profiles are intended for:

    Android
      +
    BRouter
      +
    OsmAnd

The release profiles from:

    release/

are the files intended to be transferred to the Android BRouter profile
directory.

Android installation and OsmAnd integration should be documented separately
from the macOS development setup.


## 27. Reproducibility Goal

A new developer should be able to:

1. clone this repository,
2. install Java,
3. clone and build BRouter,
4. install required routing segments,
5. create the Python environment,
6. generate profiles,
7. link them into BRouter,
8. run smoke tests,
9. run calibration tests,
10. inspect comparison maps,

without requiring knowledge of the original development machine.

Personal paths and local machine names must therefore not be required by the
project documentation.
