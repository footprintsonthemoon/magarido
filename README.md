# Magarido

### Offline motorcycle routing for roads worth riding.

Magarido is a set of motorcycle-oriented routing profiles for
[BRouter](https://github.com/abrensch/brouter), designed to be used with
[OsmAnd](https://osmand.net/) for fully offline motorcycle navigation.

It currently provides three deliberately distinct routing characters:

**Fast · Curvy · Very Curvy**

<p align="center">
  <img src="Assets/hero.png" alt="Magarido" width="100%">
</p>

> **Note**
>
> This project is under active development. The routing profiles are functional
> and have been tested with BRouter and OsmAnd on Android, but this is still an
> early release.


## Why this exists

I was looking for an open-source navigation setup for motorcycle touring that
could do two things well:

**find roads that are actually fun to ride — and keep working completely
offline.**

That sounds simple. It isn't.

General-purpose navigation is very good at finding the fastest or shortest
route. Motorcycle routing is a different problem.

The best motorcycle route is often neither the fastest nor the shortest. But
simply asking for more curves is not enough either. A useful route has to find
a balance between road class, speed, detours, curves, terrain and the basic
question:

> **Would I actually want to ride this road?**

BRouter and OsmAnd already provide an excellent open-source and fully offline
foundation. BRouter has a powerful programmable cost model, while OsmAnd
provides maps, route planning and turn-by-turn navigation without requiring a
network connection.

This project explores the missing piece between them:

**routing profiles designed and calibrated specifically for motorcycle
touring.**


## Three ways to ride

The first release deliberately contains only three profiles.

| Profile | Intent | Behaviour |
| --- | --- | --- |
| **Fast** | Get there efficiently | Prefers efficient roads and uses motorways when they make sense |
| **Curvy** | Take the interesting road | Accepts reasonable detours for more attractive motorcycle roads |
| **Very Curvy** | The ride is the destination | Accepts larger reasonable detours when they lead to significantly more interesting roads |

The profiles are not intended to be small variations of the same algorithm.

They represent three different answers to the trade-off between getting
somewhere efficiently and enjoying the road that gets you there.


## Quick Start

You need:

- an Android device
- BRouter
- OsmAnd
- offline BRouter routing data for your region

Download the three files from [`release/`](release/):

```text
moto-fast.brf
moto-curvy.brf
moto-very-curvy.brf
```

Copy them into BRouter's existing `profiles2` directory on the Android device.

Then create three OsmAnd motorcycle profiles named:

```text
Brouter[moto-fast]
Brouter[moto-curvy]
Brouter[moto-very-curvy]
```

Configure each OsmAnd profile to use **BRouter (offline)** as its routing
engine.

That's it.

For the complete tested installation procedure, including Android storage
details and troubleshooting, see
[`docs/android.md`](docs/android.md).


## Fully offline

One of the core design goals is that the complete navigation chain can operate
without an Internet connection:

```text
OpenStreetMap data
        ↓
BRouter routing data
        ↓
Motorcycle routing profile
        ↓
BRouter
        ↓
OsmAnd
        ↓
Turn-by-turn navigation
```

Once the maps and routing data are installed, route calculation and navigation
do not depend on a cloud routing service.

That matters on motorcycle trips — particularly in remote areas, abroad, or
anywhere mobile connectivity is unreliable or expensive.


## Why BRouter?

[BRouter](https://github.com/abrensch/brouter) is much more than an offline
route calculator.

Its routing behaviour is controlled by `.brf` profiles containing a
programmable cost model. Roads can therefore be evaluated according to their
OpenStreetMap properties rather than merely classified as allowed or
forbidden.

That makes BRouter particularly interesting for motorcycle routing.

Instead of saying:

```text
avoid motorways
```

a routing model can reason more like:

```text
this road is faster

but that road has characteristics
that make it more attractive for riding

how much additional distance or time
is that worth?
```

Magarido builds on that capability rather than implementing another
routing engine.


## Not just "more curves"

The routing model evaluates several aspects of a road.

Conceptually, a road segment receives a cost based on:

```text
travel efficiency
        +
road hierarchy
        +
motorcycle-road character
        +
curviness preference
        +
optional terrain preference
```

The exact model is documented in
[`docs/routing-model.md`](docs/routing-model.md).

The important part is that curviness is a **preference**, not an absolute
rule.

A tiny winding residential street should not automatically beat a good
secondary road simply because it contains more bends. Likewise, a curvy route
should not make an absurd 100 km detour just to avoid 10 km of motorway.

The cost model has to balance those effects.


## Calibrated, not just invented

The profiles were developed through repeated route comparisons across
different Swiss topographies.

The calibration set includes routes such as:

```text
Biel/Bienne → Neuchâtel
Bern → Luzern
Lausanne → Thun
Thun → Interlaken
Interlaken → Brienz
Thun → Andermatt
Fribourg → Altdorf
Zürich → Davos
```

These routes deliberately contain different routing problems:

- motorway versus secondary-road corridors
- lakes with alternative roads on opposite shores
- Swiss Plateau routing with many possible alternatives
- Alpine valleys
- mountain passes
- sections where geography leaves effectively only one sensible road

Every development profile is calculated automatically and the resulting
routes can be compared visually on a local map.


## What the experiments taught me

The project initially used more profiles:

```text
Fast
Fast Curvy
Curvy
Very Curvy
Curvy Hilly
Curvy Very Hilly
```

They sounded meaningfully different.

The routes often weren't.

For many journeys, `Fast` and `Fast Curvy` produced the same route. Likewise,
adding hilliness to `Curvy` frequently changed little or nothing.

That led to an important design decision:

> **Three profiles that behave differently are more useful than six profiles
> that sound different.**

The additional profiles still exist internally for calibration and regression
testing, but only three are currently released to users.


## Another, more important discovery

Testing longer routes exposed something more fundamental:

> **Interesting routing decisions are often local, not global.**

Consider a longer motorcycle journey.

For one section, the motorway may simply be the right choice.

Twenty kilometres later there may be an excellent secondary road where a
curvy routing preference makes perfect sense.

Further into the journey, topography may leave only one realistic road
regardless of the selected profile.

Applying one routing character to the entire journey cannot express this very
well.


## Where this could go

This leads to the longer-term vision for the project:

**segment-based motorcycle routing.**

Instead of selecting one profile for an entire journey:

```text
Start ─────────────────────────────── Destination
                   Curvy
```

a journey could eventually be planned like this:

```text
Biel
  │
  │ Fast
  ▼
Bern
  │
  │ Curvy
  ▼
Thun
  │
  │ Very Curvy
  ▼
Brienz
  │
  │ Curvy
  ▼
Andermatt
```

Waypoints would then become more than geographic points.

They could also mark transitions between different **routing intentions**.


## Routing character vs routing preferences

The experiments also suggest that not every routing choice should become
another profile.

The primary routing character can remain simple:

```text
Fast
Curvy
Very Curvy
```

Additional intentions could eventually be modelled independently:

```text
Avoid Motorways
Avoid Toll Roads
Avoid Cities
Prefer Hills
```

Conceptually:

```text
routing intention
    =
routing character
    +
preferences
    +
constraints
```

This avoids ending up with profiles such as:

```text
curvy-hilly-no-motorway-avoid-cities
```

and keeps the model understandable.


## Current scope

The current project is intentionally much smaller than that future vision.

Today it provides:

- a canonical motorcycle routing model
- generated BRouter profiles
- three user-facing routing characters
- automated smoke tests
- a calibration suite
- visual route comparison
- Android integration with BRouter and OsmAnd

The current release profiles are:

```text
moto-fast
moto-curvy
moto-very-curvy
```

Segment-based planning is a future direction, not part of the initial release.


## Tested setup

The Android integration has been tested end-to-end with:

```text
BRouter 1.7.10 (57)
OsmAnd 5.3.10
```

All three release profiles were successfully loaded by BRouter and used by
OsmAnd for offline route calculation.

The resulting routes reproduced the expected differences observed in the
desktop calibration environment.


## Project structure

```text
magarido/
├── config/
│   └── presets.yaml
├── docs/
│   ├── android.md
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
└── tools/
    ├── generate_profiles.py
    ├── run_calibration_tests.py
    ├── run_smoke_tests.py
    └── serve_results.py
```

`src/moto-base.brf` is the canonical source.

The files under `profiles/` are generated development profiles.

The files under `release/` are the profiles intended for normal use.


## Development

The development environment uses the BRouter standalone server together with
a small Python toolchain.

A typical calibration cycle is:

```bash
python tools/generate_profiles.py
python tools/run_smoke_tests.py
python tools/run_calibration_tests.py
python tools/serve_results.py
```

See [`docs/development.md`](docs/development.md) for the complete macOS
development setup.


## Documentation

| Document | Description |
| --- | --- |
| [`Android installation`](docs/android.md) | Installing the profiles and configuring OsmAnd |
| [`Routing model`](docs/routing-model.md) | How roads are evaluated |
| [`Testing`](docs/testing.md) | Calibration methodology and findings |
| [`Specification`](docs/specification.md) | Functional model and future architecture |
| [`Development`](docs/development.md) | Local development and calibration environment |


## OpenStreetMap matters

The routing model can only reason about information available in
OpenStreetMap and BRouter's derived routing data.

Routing quality therefore depends on the completeness and accuracy of the
underlying map data.

This project does not maintain its own road database.


## Status

This project is experimental but functional.

The current profiles have been calibrated on a selection of routes in
Switzerland and validated on an Android device.

That does **not** mean that every route in every country will already produce
the desired result.

Different road networks, tagging practices and landscapes may expose new
routing behaviour that requires further calibration.

Feedback based on real motorcycle routes is therefore particularly useful.


## Credits

This project builds on the work of two excellent open-source projects:

- [BRouter](https://github.com/abrensch/brouter) by Arndt Brenschede and
  contributors
- [OsmAnd](https://github.com/osmandapp/OsmAnd) by the OsmAnd team and
  contributors

Routing is based on OpenStreetMap data contributed by the
[OpenStreetMap](https://www.openstreetmap.org/) community.


## License

License information will be added before the first public release.
