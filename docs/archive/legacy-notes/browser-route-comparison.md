# Browser Route Comparison

This helper creates one interactive HTML page for the two currently interesting
pseudo-tag sensitivity comparisons:

1. Fribourg -> Altdorf
   - Baseline
   - Traffic Medium

2. Bern -> Langnau im Emmental
   - Baseline
   - Traffic Probe

Run after the sensitivity test:

```bash
python tools/compare_semantic_routes.py
```

The script:

- reads the generated GeoJSON results,
- embeds them directly into a single HTML file,
- opens the result in the default browser,
- shows both routes overlaid,
- allows each route to be switched on/off,
- displays distance, time, ascent and cost.

Output:

```text
output/semantic-route-comparison.html
```

The route data itself is embedded into the HTML. Internet access is only needed
for the OpenStreetMap background tiles and the Leaflet browser library.
