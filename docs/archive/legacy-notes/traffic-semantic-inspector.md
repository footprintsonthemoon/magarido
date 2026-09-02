# Traffic Diagnostic v2

The first inspector reused calibration GeoJSON files whose profiles did not
enable `processUnusedTags`. In addition, clicking the visible overview polyline
could intercept the mouse click.

This version fixes both issues.

1. `run_traffic_diagnostic_tests.py` creates Baseline and Traffic High profiles
   with `processUnusedTags = true`, so the GeoJSON messages contain the full
   WayTags set.

2. The inspector makes the overview routes non-interactive and places small
   clickable markers on every BRouter diagnostic message point.

Run:

```bash
python tools/run_traffic_diagnostic_tests.py
python tools/inspect_traffic_semantics.py
```

Then zoom into Huttwil and Worb and click the coloured dots on the routes.
