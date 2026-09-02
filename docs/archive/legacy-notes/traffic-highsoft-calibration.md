# Traffic High-Soft Calibration

Goal: find a useful production range between the previous `medium-high` and
`high` traffic semantics.

The new `high-soft` level sits roughly 15-20% below `high`.

Variants:

```text
baseline
traffic-medium-high
traffic-high-soft
traffic-high
```

Routes:

```text
Bern -> Thun
Biel -> Neuchatel
Fribourg -> Altdorf
Bern -> Langnau im Emmental
```

Run:

```bash
python tools/run_traffic_highsoft_tests.py
python tools/compare_traffic_highsoft.py
```

The browser page includes a metric scale and lets each variant be toggled
individually.
