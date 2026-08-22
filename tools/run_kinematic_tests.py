#!/usr/bin/env python3

import csv
import json
import urllib.parse
import urllib.request
from pathlib import Path


BROUTER_URL = "http://localhost:17777/brouter"

PROFILES = [
    "moto-kinematic-fast",
    "moto-kinematic-curvy",
    "moto-kinematic-very-curvy",
]

ROUTES = [
    {
        "id": "bern-luzern",
        "name": "Bern -> Luzern",
        "from": (7.4474, 46.9480),
        "to": (8.3093, 47.0502),
    },
    {
        "id": "interlaken-brienz",
        "name": "Interlaken -> Brienz",
        "from": (7.8632, 46.6863),
        "to": (8.0383, 46.7544),
    },
    {
        "id": "thun-andermatt",
        "name": "Thun -> Andermatt",
        "from": (7.6292, 46.7571),
        "to": (8.5947, 46.6357),
    },
    {
        "id": "zuerich-davos",
        "name": "Zuerich -> Davos",
        "from": (8.5417, 47.3769),
        "to": (9.8398, 46.8027),
    },
    {
        "id": "fribourg-altdorf",
        "name": "Fribourg -> Altdorf",
        "from": (7.1619, 46.8065),
        "to": (8.6444, 46.8804),
    },
]


ROOT = Path(__file__).resolve().parents[1]
OUTPUT = ROOT / "tests" / "kinematic-results"


def route(profile, start, end):
    lon1, lat1 = start
    lon2, lat2 = end

    params = {
        "lonlats": f"{lon1},{lat1}|{lon2},{lat2}",
        "profile": profile,
        "alternativeidx": "0",
        "format": "geojson",
    }

    url = BROUTER_URL + "?" + urllib.parse.urlencode(params)

    with urllib.request.urlopen(url, timeout=180) as response:
        raw = response.read().decode("utf-8")

    return json.loads(raw)


def properties(data):
    feature = data["features"][0]
    p = feature["properties"]

    return {
        "distance_km": float(p["track-length"]) / 1000,
        "time_min": float(p["total-time"]) / 60,
        "ascent_m": int(float(p.get("filtered ascend", 0))),
        "cost": int(float(p.get("cost", 0))),
    }


def main():
    OUTPUT.mkdir(parents=True, exist_ok=True)

    rows = []

    for route_def in ROUTES:
        print()
        print(route_def["name"])
        print("=" * len(route_def["name"]))

        route_dir = OUTPUT / route_def["id"]
        route_dir.mkdir(parents=True, exist_ok=True)

        for profile in PROFILES:
            try:
                data = route(
                    profile,
                    route_def["from"],
                    route_def["to"],
                )

                target = route_dir / f"{profile}.geojson"
                target.write_text(
                    json.dumps(data, indent=2),
                    encoding="utf-8",
                )

                p = properties(data)

                rows.append({
                    "route": route_def["id"],
                    "profile": profile,
                    **p,
                })

                print(
                    f"{profile:30}"
                    f"{p['distance_km']:7.1f} km  "
                    f"{p['time_min']:7.1f} min  "
                    f"{p['ascent_m']:5d} m  "
                    f"cost={p['cost']}"
                )

            except Exception as exc:
                print(
                    f"{profile:30}"
                    f"ERROR: {exc}"
                )

    csv_path = OUTPUT / "results.csv"

    with csv_path.open(
        "w",
        newline="",
        encoding="utf-8",
    ) as handle:
        writer = csv.DictWriter(
            handle,
            fieldnames=[
                "route",
                "profile",
                "distance_km",
                "time_min",
                "ascent_m",
                "cost",
            ],
        )

        writer.writeheader()
        writer.writerows(rows)

    print()
    print(f"Results written to {csv_path.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
