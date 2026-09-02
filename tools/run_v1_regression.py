#!/usr/bin/env python3
"""
v1 routing regression suite for brouter-motorcycle.

Purpose
-------
Freeze the currently accepted v1 routing behaviour and detect later changes.

The suite covers:
- Fast / Curvy / Very Curvy on the eight v1 acceptance routes
- Hilliness planner behaviour on the three accepted regression cases
- avoid_motorways / avoid_toll planner behaviour on the accepted constraint cases

First accepted snapshot:
    python tools/run_v1_regression.py --freeze-baseline

Normal regression run:
    python tools/run_v1_regression.py

The first command must only be run on a routing state that has already been
visually accepted. It creates tests/baselines/v1-routing-baseline.json.

A later regression run does NOT automatically declare a changed route bad.
It flags material changes for review.
"""

from __future__ import annotations

import argparse
import json
import math
import os
import re
import subprocess
import sys
import time
import urllib.parse
import urllib.request
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
BROUTER_URL = os.environ.get(
    "BROUTER_URL",
    "http://127.0.0.1:17777/brouter",
)
BASELINE_FILE = ROOT / "tests" / "baselines" / "v1-routing-baseline.json"
OUT_DIR = ROOT / "output" / "v1-regression"

PROFILES = [
    ("moto-fast", "Fast"),
    ("moto-curvy", "Curvy"),
    ("moto-very-curvy", "Very Curvy"),
]

# Same v1 character acceptance catalogue used for the final visual review.
CHARACTER_CASES = [
    {
        "id": "biel-neuchatel",
        "name": "Biel/Bienne -> Neuchatel",
        "from": (7.2468, 47.1368),
        "to": (6.9293, 46.9896),
    },
    {
        "id": "bern-luzern",
        "name": "Bern -> Luzern",
        "from": (7.4474, 46.9480),
        "to": (8.3093, 47.0502),
    },
    {
        "id": "thun-andermatt",
        "name": "Thun -> Andermatt",
        "from": (7.6292, 46.7571),
        "to": (8.5948, 46.6356),
    },
    {
        "id": "interlaken-brienz",
        "name": "Interlaken -> Brienz",
        "from": (7.8632, 46.6863),
        "to": (8.0385, 46.7541),
    },
    {
        "id": "brienz-andermatt",
        "name": "Brienz -> Andermatt",
        "from": (8.0385, 46.7541),
        "to": (8.5948, 46.6356),
    },
    {
        "id": "zurich-davos",
        "name": "Zurich -> Davos",
        "from": (8.5417, 47.3769),
        "to": (9.8398, 46.8027),
    },
    {
        "id": "aigle-martigny",
        "name": "Aigle -> Martigny",
        "from": (6.9706, 46.3185),
        "to": (7.0732, 46.1020),
    },
    {
        "id": "fribourg-altdorf",
        "name": "Fribourg -> Altdorf",
        "from": (7.1513, 46.8065),
        "to": (8.6444, 46.8804),
    },
]

# Planner-level behavioural cases already accepted for v1.
PLANNER_CASES = [
    {
        "id": "biel-neuchatel-curvy-hills-strong",
        "file": "examples/intent-tests/biel-neuchatel-curvy-hills-strong.yaml",
        "expected_alt": 2,
        "expected_distance_km": 40.3,
        "expected_time_min": 48.2,
        "expected_ascent_m": 810,
        "expected_cost": 70011,
    },
    {
        "id": "fribourg-altdorf-curvy-hills-moderate",
        "file": "examples/intent-tests/fribourg-altdorf-curvy-hills-moderate.yaml",
        "expected_alt": 2,
        "expected_distance_km": 172.9,
        "expected_time_min": 185.6,
        "expected_ascent_m": 2090,
        "expected_cost": 308341,
    },
    {
        "id": "thun-andermatt-curvy-hills-strong",
        "file": "examples/intent-tests/thun-andermatt-curvy-hills-strong.yaml",
        "expected_alt": None,  # baseline
        "expected_distance_km": 113.3,
        "expected_time_min": 132.1,
        "expected_ascent_m": 2674,
        "expected_cost": 196336,
    },
    {
        "id": "bern-luzern-fast-no-motorway",
        "file": "examples/intent-tests/bern-luzern-fast-no-motorway.yaml",
        "expected_alt": None,
        "expected_distance_km": 84.0,
        "expected_time_min": 101.3,
        "expected_ascent_m": 875,
        "expected_cost": None,
    },
    {
        "id": "bern-luzern-curvy-no-motorway",
        "file": "examples/intent-tests/bern-luzern-curvy-no-motorway.yaml",
        "expected_alt": None,
        "expected_distance_km": 84.0,
        "expected_time_min": 101.3,
        "expected_ascent_m": 875,
        "expected_cost": None,
    },
    {
        "id": "martigny-aosta-fast-no-motorway",
        "file": "examples/intent-tests/martigny-aosta-fast-no-motorway.yaml",
        "expected_alt": None,
        "expected_distance_km": 73.2,
        "expected_time_min": 83.9,
        "expected_ascent_m": 1473,
        "expected_cost": 115474,
    },
    {
        "id": "martigny-aosta-fast-no-toll",
        "file": "examples/intent-tests/martigny-aosta-fast-no-toll.yaml",
        "expected_alt": None,
        "expected_distance_km": 77.9,
        "expected_time_min": 102.1,
        "expected_ascent_m": 2023,
        "expected_cost": 140871,
    },
]

# These are intentionally review thresholds, not routing weights.
DISTANCE_DELTA_WARN_PCT = 2.0
MEAN_CORRIDOR_WARN_M = 80.0
P95_CORRIDOR_WARN_M = 180.0

# Planner numeric tolerances protect against tiny changes in formatting/data.
DISTANCE_TOL_KM = 0.35
TIME_TOL_MIN = 0.8
ASCENT_TOL_M = 25
COST_TOL = 250


def haversine_m(a: list[float] | tuple[float, float],
                b: list[float] | tuple[float, float]) -> float:
    lon1, lat1 = map(math.radians, a[:2])
    lon2, lat2 = map(math.radians, b[:2])
    dlon = lon2 - lon1
    dlat = lat2 - lat1
    h = (
        math.sin(dlat / 2) ** 2
        + math.cos(lat1) * math.cos(lat2) * math.sin(dlon / 2) ** 2
    )
    return 12_742_000 * math.asin(math.sqrt(h))


def route_feature(data: dict[str, Any]) -> dict[str, Any]:
    for feature in data.get("features", []):
        geom = feature.get("geometry") or {}
        if geom.get("type") == "LineString":
            return feature
    raise RuntimeError("GeoJSON contains no LineString route")


def route_coords(data: dict[str, Any]) -> list[list[float]]:
    return [
        [float(p[0]), float(p[1])]
        for p in route_feature(data)["geometry"]["coordinates"]
    ]


def route_distance_km(data: dict[str, Any]) -> float:
    coords = route_coords(data)
    return sum(haversine_m(a, b) for a, b in zip(coords, coords[1:])) / 1000.0


def route_property(data: dict[str, Any], *names: str) -> float | None:
    props = {
        str(k).lower(): v
        for k, v in (route_feature(data).get("properties") or {}).items()
    }
    for name in names:
        try:
            return float(props[name.lower()])
        except (KeyError, TypeError, ValueError):
            continue
    return None


def simplify_by_distance(coords: list[list[float]], spacing_m: float = 250.0) -> list[list[float]]:
    """Keep a compact corridor snapshot at approximately fixed spacing."""
    if len(coords) <= 2:
        return coords[:]

    out = [coords[0]]
    accumulated = 0.0
    previous = coords[0]

    for point in coords[1:-1]:
        accumulated += haversine_m(previous, point)
        previous = point
        if accumulated >= spacing_m:
            out.append(point)
            accumulated = 0.0

    out.append(coords[-1])
    return out


def percentile(values: list[float], p: float) -> float:
    if not values:
        return 0.0
    values = sorted(values)
    idx = min(len(values) - 1, max(0, round((len(values) - 1) * p)))
    return values[idx]


def nearest_distance(point: list[float], corridor: list[list[float]]) -> float:
    # Baseline is simplified, so point-to-vertex distance is deliberately
    # approximate. This is a regression alarm, not a GIS equivalence proof.
    return min(haversine_m(point, candidate) for candidate in corridor)


def corridor_delta_m(current: list[list[float]],
                     baseline: list[list[float]]) -> tuple[float, float]:
    """
    Symmetric nearest-point corridor comparison.

    Returns:
        mean nearest distance, p95 nearest distance
    """
    current_s = simplify_by_distance(current)
    baseline_s = baseline

    distances = [
        nearest_distance(p, baseline_s)
        for p in current_s
    ]
    distances += [
        nearest_distance(p, current_s)
        for p in baseline_s
    ]

    if not distances:
        return 0.0, 0.0

    return sum(distances) / len(distances), percentile(distances, 0.95)


def fetch_brouter(case: dict[str, Any], profile: str) -> dict[str, Any]:
    start = case["from"]
    end = case["to"]
    query = urllib.parse.urlencode({
        "lonlats": f"{start[0]},{start[1]}|{end[0]},{end[1]}",
        "profile": profile,
        "alternativeidx": 0,
        "format": "geojson",
    })
    url = BROUTER_URL + "?" + query
    with urllib.request.urlopen(url, timeout=240) as response:
        return json.loads(response.read())


def check_brouter() -> None:
    case = CHARACTER_CASES[0]
    query = urllib.parse.urlencode({
        "lonlats": f"{case['from'][0]},{case['from'][1]}|{case['to'][0]},{case['to'][1]}",
        "profile": "moto-fast",
        "alternativeidx": 0,
        "format": "geojson",
    })
    try:
        with urllib.request.urlopen(BROUTER_URL + "?" + query, timeout=15) as response:
            if response.status != 200:
                raise RuntimeError(f"HTTP {response.status}")
    except Exception as exc:
        raise RuntimeError(
            "BRouter is not reachable or moto-fast cannot route.\n"
            f"Endpoint: {BROUTER_URL}\n"
            f"Cause: {exc}"
        ) from exc


def collect_character_routes() -> dict[str, Any]:
    records: dict[str, Any] = {}

    print("\nRouting-character regression")
    print("============================")

    for case in CHARACTER_CASES:
        print(case["name"])
        for profile, label in PROFILES:
            print(f"  {label:<11}", end="", flush=True)
            started = time.time()
            data = fetch_brouter(case, profile)
            elapsed = time.time() - started
            coords = route_coords(data)
            km = route_distance_km(data)
            key = f"{case['id']}::{profile}"

            records[key] = {
                "case_id": case["id"],
                "case_name": case["name"],
                "profile": profile,
                "distance_km": round(km, 4),
                "time": route_property(data, "total-time", "time"),
                "ascent_m": route_property(data, "filtered ascend", "ascend", "ascent"),
                "cost": route_property(data, "cost", "track-cost"),
                "corridor": simplify_by_distance(coords),
            }

            print(f"{km:8.1f} km  ({elapsed:5.1f}s)")
        print()

    return records


def parse_plan_route_output(stdout: str) -> dict[str, Any]:
    def number(pattern: str) -> float | None:
        match = re.search(pattern, stdout, re.MULTILINE)
        return float(match.group(1)) if match else None

    alt_match = re.search(r"^\s*BRouter alt:\s+(\d+)\s*$", stdout, re.MULTILINE)

    return {
        "alt": int(alt_match.group(1)) if alt_match else None,
        "distance_km": number(r"^distance:\s+([0-9.]+)\s+km\s*$"),
        "time_min": number(r"^time:\s+([0-9.]+)\s+min\s*$"),
        "ascent_m": number(r"^ascent:\s+([0-9.]+)\s+m\s*$"),
        "cost": number(r"^cost:\s+([0-9.]+)\s*$"),
    }


def run_planner_case(case: dict[str, Any]) -> dict[str, Any]:
    cmd = [
        sys.executable,
        str(ROOT / "tools" / "plan_route.py"),
        str(ROOT / case["file"]),
    ]

    # Long routes + alternative evaluation can legitimately take time.
    result = subprocess.run(
        cmd,
        cwd=ROOT,
        text=True,
        capture_output=True,
        timeout=900,
    )

    if result.returncode != 0:
        raise RuntimeError(
            f"plan_route.py failed for {case['id']}\n"
            f"stdout:\n{result.stdout}\n"
            f"stderr:\n{result.stderr}"
        )

    metrics = parse_plan_route_output(result.stdout)
    metrics["stdout"] = result.stdout
    return metrics


def check_expected(case: dict[str, Any], result: dict[str, Any]) -> list[str]:
    failures: list[str] = []

    if result["alt"] != case["expected_alt"]:
        failures.append(
            f"alternative expected {case['expected_alt']!r}, got {result['alt']!r}"
        )

    checks = [
        ("distance_km", DISTANCE_TOL_KM),
        ("time_min", TIME_TOL_MIN),
        ("ascent_m", ASCENT_TOL_M),
        ("cost", COST_TOL),
    ]

    for name, tolerance in checks:
        expected = case.get(f"expected_{name}")
        actual = result.get(name)

        if expected is None:
            continue
        if actual is None:
            failures.append(f"{name} missing")
            continue
        if abs(actual - expected) > tolerance:
            failures.append(
                f"{name} expected {expected}, got {actual} "
                f"(tolerance +/-{tolerance})"
            )

    return failures


def collect_planner_results() -> tuple[dict[str, Any], list[str]]:
    records: dict[str, Any] = {}
    failures: list[str] = []

    print("\nPlanner behaviour regression")
    print("============================")

    for case in PLANNER_CASES:
        print(f"{case['id']} ... ", end="", flush=True)
        started = time.time()

        try:
            result = run_planner_case(case)
        except Exception as exc:
            failures.append(f"{case['id']}: {exc}")
            print("ERROR")
            continue

        elapsed = time.time() - started
        problems = check_expected(case, result)

        records[case["id"]] = {
            k: v
            for k, v in result.items()
            if k != "stdout"
        }

        if problems:
            failures.extend(f"{case['id']}: {problem}" for problem in problems)
            print(f"FAIL ({elapsed:.1f}s)")
        else:
            selection = (
                f"alt {result['alt']}"
                if result["alt"] is not None
                else "baseline"
            )
            print(
                f"OK  {selection}, "
                f"{result['distance_km']:.1f} km, "
                f"{result['ascent_m']:.0f} m  ({elapsed:.1f}s)"
            )

    return records, failures


def compare_character_baseline(
    current: dict[str, Any],
    baseline: dict[str, Any],
) -> list[dict[str, Any]]:
    changes: list[dict[str, Any]] = []

    for key, now in current.items():
        old = baseline.get(key)
        if old is None:
            changes.append({
                "key": key,
                "status": "new",
                "review": True,
            })
            continue

        old_km = float(old["distance_km"])
        now_km = float(now["distance_km"])
        distance_delta_pct = (
            ((now_km - old_km) / old_km) * 100.0
            if old_km
            else 0.0
        )

        mean_m, p95_m = corridor_delta_m(
            now["corridor"],
            old["corridor"],
        )

        review = (
            abs(distance_delta_pct) > DISTANCE_DELTA_WARN_PCT
            or mean_m > MEAN_CORRIDOR_WARN_M
            or p95_m > P95_CORRIDOR_WARN_M
        )

        changes.append({
            "key": key,
            "status": "changed" if review else "stable",
            "distance_delta_pct": round(distance_delta_pct, 2),
            "mean_corridor_delta_m": round(mean_m, 1),
            "p95_corridor_delta_m": round(p95_m, 1),
            "review": review,
        })

    return changes


def save_json(path: Path, data: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(data, indent=2, ensure_ascii=False),
        encoding="utf-8",
    )


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--freeze-baseline",
        action="store_true",
        help="write the currently accepted v1 routing snapshot",
    )
    args = parser.parse_args()

    print("BRouter motorcycle v1 regression suite")
    print("======================================")
    print(f"BRouter: {BROUTER_URL}")

    check_brouter()
    OUT_DIR.mkdir(parents=True, exist_ok=True)

    character = collect_character_routes()
    planner, planner_failures = collect_planner_results()

    current = {
        "schema": 1,
        "character_routes": character,
        "planner_cases": planner,
    }
    save_json(OUT_DIR / "current.json", current)

    if args.freeze_baseline:
        if planner_failures:
            print("\nBaseline NOT written: planner regression failures exist.")
            for problem in planner_failures:
                print("  -", problem)
            return 2

        save_json(BASELINE_FILE, current)
        print("\nV1 baseline frozen")
        print("==================")
        print(BASELINE_FILE)
        print(
            "\nCommit this baseline to Git. "
            "Do not regenerate it to make a failing test green."
        )
        return 0

    if not BASELINE_FILE.exists():
        print("\nNo frozen baseline exists.")
        print("After visually accepting the current routing state, run:")
        print("  python tools/run_v1_regression.py --freeze-baseline")
        return 2

    baseline = json.loads(BASELINE_FILE.read_text(encoding="utf-8"))
    changes = compare_character_baseline(
        character,
        baseline.get("character_routes", {}),
    )

    review = [x for x in changes if x["review"]]

    print("\nCharacter baseline comparison")
    print("=============================")
    print(
        f"{'Route/profile':46} {'dKm %':>8} "
        f"{'mean m':>9} {'p95 m':>9} {'Status':>10}"
    )
    print("-" * 88)

    for item in changes:
        if item["status"] == "new":
            print(f"{item['key'][:46]:46} {'-':>8} {'-':>9} {'-':>9} {'REVIEW':>10}")
            continue
        print(
            f"{item['key'][:46]:46} "
            f"{item['distance_delta_pct']:8.2f} "
            f"{item['mean_corridor_delta_m']:9.1f} "
            f"{item['p95_corridor_delta_m']:9.1f} "
            f"{('REVIEW' if item['review'] else 'OK'):>10}"
        )

    report = {
        "character_comparison": changes,
        "planner_failures": planner_failures,
    }
    save_json(OUT_DIR / "report.json", report)

    print("\nRegression summary")
    print("==================")
    print(f"Character routes requiring review: {len(review)}/{len(changes)}")
    print(f"Planner behaviour failures:        {len(planner_failures)}")

    if review:
        print("\nCharacter changes requiring visual review:")
        for item in review:
            print("  -", item["key"])

    if planner_failures:
        print("\nPlanner failures:")
        for problem in planner_failures:
            print("  -", problem)

    if review or planner_failures:
        print(
            "\nResult: REVIEW REQUIRED\n"
            "A changed route is not automatically wrong. "
            "Inspect the geometry before changing routing weights."
        )
        return 1

    print("\nResult: PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
