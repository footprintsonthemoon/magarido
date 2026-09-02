# Pseudo-Tag Semantic A/B Test

This experiment tests whether BRouter's derived pseudo tags can improve the
implicit motorcycle semantics of the Curvy routing character.

It deliberately does **not** change the production routing model.

The runner generates four temporary Curvy profiles from the current canonical
`src/moto-kinematic-base.brf`:

```text
baseline
traffic
town
traffic-town
```

The initial penalties are intentionally conservative.

Traffic:

```text
class 0-2 -> 1.00
class 3   -> 1.01
class 4   -> 1.02
class 5   -> 1.04
class 6   -> 1.06
class 7   -> 1.08
```

Town:

```text
class 0-1 -> 1.00
class 2   -> 1.01
class 3   -> 1.02
class 4   -> 1.04
class 5   -> 1.06
class 6   -> 1.08
```

Run with the BRouter standalone server already running:

```bash
python tools/run_semantic_tests.py
```

The test routes are:

```text
Bern -> Thun
Biel -> Neuchatel
Fribourg -> Altdorf
Bern -> Langnau im Emmental
```

Results are written under:

```text
output/semantic-tests/
```

Each variant is exported as GeoJSON so changed routes can be inspected
visually.

The console output marks:

```text
=  identical geometry to baseline
!  different geometry from baseline
```

The goal is not to maximise route differences. A useful outcome can also be
that a subtle semantic penalty changes only selected routes where meaningful
alternatives exist.
