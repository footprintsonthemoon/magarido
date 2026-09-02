# Traffic Semantic Calibration

This experiment narrows the range between the earlier `medium` and `probe`
traffic penalties.

Variants:

```text
baseline
traffic-medium
traffic-medium-high
traffic-high
traffic-probe
```

Test routes:

```text
Fribourg -> Altdorf
Bern -> Langnau im Emmental
```

Run:

```bash
python tools/run_traffic_calibration_tests.py
python tools/compare_traffic_calibration.py
```

The browser comparison includes a metric scale in the lower-left corner so that
small deviations can be estimated directly on the map.

`probe` remains a diagnostic setting, not a production candidate.
