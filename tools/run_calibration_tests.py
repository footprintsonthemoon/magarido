#!/usr/bin/env python3

import csv
import html
import json
import re
import urllib.parse
import urllib.request
from dataclasses import dataclass
from pathlib import Path


BROUTER_URL = "http://localhost:17777/brouter"

RESULTS_DIR = Path("tests/results")
CSV_FILE = RESULTS_DIR / "calibration.csv"

PROFILES = [
    "moto-fast",
    "moto-fast-curvy",
    "moto-curvy",
    "moto-very-curvy",
    "moto-curvy-hilly",
    "moto-curvy-very-hilly",
]

# Fixed colours make the profiles easy to recognise across all maps.
PROFILE_COLOURS = {
    "moto-fast": "#2563eb",
    "moto-fast-curvy": "#0891b2",
    "moto-curvy": "#16a34a",
    "moto-very-curvy": "#9333ea",
    "moto-curvy-hilly": "#ea580c",
    "moto-curvy-very-hilly": "#dc2626",
}


@dataclass
class TestRoute:
    name: str
    start: tuple[float, float]
    end: tuple[float, float]
    purpose: str


ROUTES = [
    TestRoute(
        name="Biel/Bienne -> Neuchatel",
        start=(7.2468, 47.1368),
        end=(6.9293, 46.9896),
        purpose="Short mixed-route baseline",
    ),
    TestRoute(
        name="Bern -> Luzern",
        start=(7.4474, 46.9480),
        end=(8.3093, 47.0502),
        purpose="Fast vs secondary-road alternatives",
    ),
    TestRoute(
        name="Thun -> Andermatt",
        start=(7.6280, 46.7580),
        end=(8.5947, 46.6357),
        purpose="Mountain and hilliness behaviour",
    ),
    TestRoute(
        name="Zuerich -> Davos",
        start=(8.5417, 47.3769),
        end=(9.8398, 46.8027),
        purpose="Long alpine routing",
    ),
    TestRoute(
        name="Aigle -> Martigny",
        start=(6.9706, 46.3180),
        end=(7.0725, 46.1024),
        purpose="Valley vs surrounding terrain",
    ),
    TestRoute(
    name="Thun -> Interlaken",
    start=(7.6280, 46.7580),
    end=(7.8632, 46.6863),
    purpose="Diagnostic: western section of Thun-Andermatt",
),

TestRoute(
    name="Interlaken -> Brienz",
    start=(7.8632, 46.6863),
    end=(8.0384, 46.7545),
    purpose="Diagnostic: north-shore vs A8 corridor",
),

TestRoute(
    name="Brienz -> Andermatt",
    start=(8.0384, 46.7545),
    end=(8.5947, 46.6356),
    purpose="Diagnostic: eastern section of Thun-Andermatt",
),
TestRoute(
    name="Biel/Bienne -> Rotkreuz",
    start=(7.2468, 47.1368),
    end=(8.4310, 47.1420),
    purpose="High-choice: motorway vs Mittelland secondary-road corridors",
),

TestRoute(
    name="Lausanne -> Thun",
    start=(6.6323, 46.5197),
    end=(7.6280, 46.7580),
    purpose="High-choice: long-distance motorway vs rural and pre-alpine corridors",
),
TestRoute(
    name="Fribourg -> Altdorf",
    start=(7.1513, 46.8065),
    end=(8.6444, 46.8804),
    purpose="High-choice: motorway, Mittelland, pre-alpine and mountain alternatives",
),
]


def slugify(value: str) -> str:
    value = value.lower()
    value = value.replace("->", "-")
    value = value.replace("/", "-")
    value = re.sub(r"[^a-z0-9]+", "-", value)
    return value.strip("-")


def route(profile: str, test_route: TestRoute) -> dict:
    lon1, lat1 = test_route.start
    lon2, lat2 = test_route.end

    params = {
        "lonlats": f"{lon1},{lat1}|{lon2},{lat2}",
        "profile": profile,
        "alternativeidx": "0",
        "format": "geojson",
    }

    url = f"{BROUTER_URL}?{urllib.parse.urlencode(params)}"

    with urllib.request.urlopen(url, timeout=120) as response:
        return json.load(response)


def get_properties(data: dict) -> dict:
    features = data.get("features", [])

    if not features:
        raise ValueError("BRouter returned no features")

    return features[0].get("properties", {})


def as_float(properties: dict, key: str, default=0.0) -> float:
    value = properties.get(key, default)

    try:
        return float(value)
    except (TypeError, ValueError):
        return float(default)


def extract_metrics(properties: dict) -> dict:
    return {
        "distance_km": as_float(properties, "track-length") / 1000.0,
        "time_min": as_float(properties, "total-time") / 60.0,
        "ascent_m": as_float(properties, "filtered ascend"),
        "cost": as_float(properties, "cost"),
    }


def print_result(profile: str, metrics: dict) -> None:
    print(
        f"[OK] {profile:<24}"
        f"{metrics['distance_km']:7.1f} km"
        f"{metrics['time_min']:8.1f} min"
        f"{metrics['ascent_m']:8.0f} m ascent"
        f"  cost={metrics['cost']:.0f}"
    )


def save_geojson(
    data: dict,
    test_route: TestRoute,
    profile: str,
) -> Path:
    route_dir = RESULTS_DIR / slugify(test_route.name)
    route_dir.mkdir(parents=True, exist_ok=True)

    output_file = route_dir / f"{profile}.geojson"

    with output_file.open("w", encoding="utf-8") as handle:
        json.dump(
            data,
            handle,
            ensure_ascii=False,
            indent=2,
        )
        handle.write("\n")

    return output_file


def write_csv(rows: list[dict]) -> None:
    RESULTS_DIR.mkdir(parents=True, exist_ok=True)

    fieldnames = [
        "route",
        "purpose",
        "profile",
        "distance_km",
        "time_min",
        "ascent_m",
        "cost",
    ]

    with CSV_FILE.open(
        "w",
        encoding="utf-8",
        newline="",
    ) as handle:
        writer = csv.DictWriter(
            handle,
            fieldnames=fieldnames,
        )

        writer.writeheader()
        writer.writerows(rows)


def create_comparison_map(
    test_route: TestRoute,
    results: list[dict],
) -> Path:
    route_dir = RESULTS_DIR / slugify(test_route.name)
    route_dir.mkdir(parents=True, exist_ok=True)

    output_file = route_dir / "comparison.html"

    start_lon, start_lat = test_route.start
    end_lon, end_lat = test_route.end

    table_rows = []
    route_javascript = []

    for index, result in enumerate(results):
        profile = result["profile"]
        metrics = result["metrics"]
        data = result["data"]

        colour = PROFILE_COLOURS.get(profile, "#333333")

        table_rows.append(
            "<tr>"
            f'<td><span class="swatch" '
            f'style="background:{colour}"></span>'
            f"{html.escape(profile)}</td>"
            f"<td>{metrics['distance_km']:.1f} km</td>"
            f"<td>{metrics['time_min']:.1f} min</td>"
            f"<td>{metrics['ascent_m']:.0f} m</td>"
            f"<td>{metrics['cost']:.0f}</td>"
            "</tr>"
        )

        geojson = json.dumps(
            data,
            ensure_ascii=False,
            separators=(",", ":"),
        )

        # Later profiles are drawn first. This helps prevent one
        # profile from completely hiding another when tracks overlap.
        route_javascript.append(
            f"""
const route{index} = L.geoJSON(
    {geojson},
    {{
        style: {{
            color: "{colour}",
            weight: 5,
            opacity: 0.78
        }}
    }}
);

route{index}.bindTooltip(
    "{html.escape(profile)}",
    {{ sticky: true }}
);

route{index}.addTo(map);
overlays["{html.escape(profile)}"] = route{index};
"""
        )

    title = html.escape(test_route.name)
    purpose = html.escape(test_route.purpose)

    document = f"""<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta
    name="viewport"
    content="width=device-width, initial-scale=1"
>
<title>BRouter calibration - {title}</title>

<link
    rel="stylesheet"
    href="https://unpkg.com/leaflet@1.9.4/dist/leaflet.css"
>

<style>
html,
body {{
    height: 100%;
    margin: 0;
    font-family:
        -apple-system,
        BlinkMacSystemFont,
        "Segoe UI",
        sans-serif;
}}

body {{
    display: grid;
    grid-template-rows: auto 1fr;
}}

header {{
    padding: 14px 18px;
    background: white;
    border-bottom: 1px solid #ddd;
}}

h1 {{
    margin: 0 0 4px;
    font-size: 20px;
}}

.purpose {{
    margin-bottom: 12px;
    color: #555;
    font-size: 13px;
}}

table {{
    border-collapse: collapse;
    font-size: 13px;
}}

th,
td {{
    padding: 4px 18px 4px 0;
    text-align: left;
    border-bottom: 1px solid #eee;
}}

th {{
    font-weight: 600;
}}

.swatch {{
    display: inline-block;
    width: 12px;
    height: 12px;
    margin-right: 7px;
    border-radius: 3px;
    vertical-align: -1px;
}}

#map {{
    width: 100%;
    height: 100%;
}}

@media (max-width: 700px) {{
    header {{
        padding: 10px;
    }}

    table {{
        font-size: 11px;
    }}

    th,
    td {{
        padding-right: 8px;
    }}
}}
</style>
</head>

<body>

<header>
    <h1>{title}</h1>
    <div class="purpose">{purpose}</div>

    <table>
        <thead>
            <tr>
                <th>Profile</th>
                <th>Distance</th>
                <th>Time</th>
                <th>Ascent</th>
                <th>Cost</th>
            </tr>
        </thead>
        <tbody>
            {''.join(table_rows)}
        </tbody>
    </table>
</header>

<div id="map"></div>

<script
    src="https://unpkg.com/leaflet@1.9.4/dist/leaflet.js">
</script>

<script>
const map = L.map(
    "map",
    {{
        preferCanvas: true
    }}
);

const baseLayer = L.tileLayer(
    "https://{{s}}.tile.openstreetmap.org/{{z}}/{{x}}/{{y}}.png",
    {{
        maxZoom: 19,
        attribution: "&copy; OpenStreetMap contributors"
    }}
);

baseLayer.addTo(map);

const overlays = {{}};

{''.join(reversed(route_javascript))}

L.marker(
    [{start_lat}, {start_lon}]
)
.bindTooltip("Start")
.addTo(map);

L.marker(
    [{end_lat}, {end_lon}]
)
.bindTooltip("Destination")
.addTo(map);

const routeLayers = Object.values(overlays);

if (routeLayers.length > 0) {{
    const group = L.featureGroup(routeLayers);

    map.fitBounds(
        group.getBounds(),
        {{
            padding: [20, 20]
        }}
    );
}}

L.control.layers(
    {{
        "OpenStreetMap": baseLayer
    }},
    overlays,
    {{
        collapsed: false
    }}
).addTo(map);

L.control.scale(
    {{
        metric: true,
        imperial: false
    }}
).addTo(map);
</script>

</body>
</html>
"""

    output_file.write_text(
        document,
        encoding="utf-8",
    )

    return output_file


def main() -> None:
    failures = 0
    rows = []

    RESULTS_DIR.mkdir(parents=True, exist_ok=True)

    for test_route in ROUTES:
        print()
        print("=" * 78)
        print(test_route.name)
        print(test_route.purpose)
        print("=" * 78)

        route_results = []

        for profile in PROFILES:
            try:
                data = route(profile, test_route)
                properties = get_properties(data)
                metrics = extract_metrics(properties)

                print_result(profile, metrics)

                save_geojson(
                    data,
                    test_route,
                    profile,
                )

                route_results.append(
                    {
                        "profile": profile,
                        "metrics": metrics,
                        "data": data,
                    }
                )

                rows.append(
                    {
                        "route": test_route.name,
                        "purpose": test_route.purpose,
                        "profile": profile,
                        "distance_km":
                            f"{metrics['distance_km']:.3f}",
                        "time_min":
                            f"{metrics['time_min']:.2f}",
                        "ascent_m":
                            f"{metrics['ascent_m']:.0f}",
                        "cost":
                            f"{metrics['cost']:.0f}",
                    }
                )

            except Exception as exc:
                failures += 1
                print(
                    f"[FAIL] {profile:<22} {exc}"
                )

        if route_results:
            comparison_file = create_comparison_map(
                test_route,
                route_results,
            )

            print(
                f"     map: {comparison_file}"
            )

    write_csv(rows)

    print()
    print(f"GeoJSON results: {RESULTS_DIR}/<route>/")
    print(f"CSV report:      {CSV_FILE}")
    print("Comparison maps: tests/results/<route>/comparison.html")

    if failures:
        print(
            f"{failures} calibration test(s) failed."
        )
        raise SystemExit(1)

    print(
        "All calibration tests completed successfully."
    )


if __name__ == "__main__":
    main()
