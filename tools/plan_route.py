#!/usr/bin/env python3

import argparse
import json
import re
import sys
import urllib.parse
import urllib.request
from pathlib import Path
from urllib.error import HTTPError
from xml.etree import ElementTree as ET

try:
    import yaml
except ImportError:
    sys.exit(
        "PyYAML is required. Install it with:\n"
        "  python3 -m pip install -r requirements-dev.txt"
    )

from profile_compiler import (
    compile_profile,
    normalize_intention,
)


ROOT = Path(__file__).resolve().parents[1]
BROUTER_URL = "http://localhost:17777/brouter"
OUTPUT_DIR = ROOT / "output"

HILLS_TIME_FACTOR = {
    "moderate": 1.35,
    "strong": 1.70,
}

HILLS_MIN_ASCENT_GAIN_M = 100
HILLS_MIN_ASCENT_GAIN_RATIO = 0.10
HILLS_MIN_DENSITY_FACTOR = 1.10


def slugify(value: str) -> str:
    value = value.lower()
    value = re.sub(r"[^a-z0-9]+", "-", value)
    return value.strip("-")


def first_feature(data: dict) -> dict:
    features = data.get("features", [])

    if not features:
        raise ValueError("BRouter returned no features")

    return features[0]


def metric(properties: dict, key: str, default=0.0) -> float:
    try:
        return float(properties.get(key, default))
    except (TypeError, ValueError):
        return float(default)


def route_with_alternative(
    start: dict,
    end: dict,
    profile: str,
    alternative_idx: int,
) -> dict:
    params = {
        "lonlats": (
            f"{start['lon']},{start['lat']}|"
            f"{end['lon']},{end['lat']}"
        ),
        "profile": profile,
        "alternativeidx": str(alternative_idx),
        "format": "geojson",
    }

    url = f"{BROUTER_URL}?{urllib.parse.urlencode(params)}"

    with urllib.request.urlopen(
        url,
        timeout=120,
    ) as response:
        return json.load(response)


def candidate_metrics(data: dict) -> dict:
    feature = first_feature(data)
    properties = feature.get("properties", {})

    distance_m = metric(
        properties,
        "track-length",
    )

    time_s = metric(
        properties,
        "total-time",
    )

    ascent_m = metric(
        properties,
        "filtered ascend",
    )

    distance_km = distance_m / 1000

    ascent_density = (
        ascent_m / distance_km
        if distance_km > 0
        else 0
    )

    return {
        "distance_m": distance_m,
        "time_s": time_s,
        "ascent_m": ascent_m,
        "ascent_density": ascent_density,
    }


def select_hill_alternative(
    candidates: list[dict],
    hills: str,
) -> dict:
    baseline = candidates[0]

    if hills == "off":
        return baseline

    baseline_metrics = baseline["metrics"]

    max_time = (
        baseline_metrics["time_s"]
        * HILLS_TIME_FACTOR[hills]
    )

    minimum_gain = max(
        HILLS_MIN_ASCENT_GAIN_M,
        baseline_metrics["ascent_m"]
        * HILLS_MIN_ASCENT_GAIN_RATIO,
    )

    baseline_density = baseline_metrics[
        "ascent_density"
    ]

    eligible = []

    for candidate in candidates[1:]:
        metrics = candidate["metrics"]

        ascent_gain = (
            metrics["ascent_m"]
            - baseline_metrics["ascent_m"]
        )

        if metrics["time_s"] > max_time:
            continue

        if ascent_gain < minimum_gain:
            continue

        if (
            metrics["ascent_density"]
            < baseline_density
            * HILLS_MIN_DENSITY_FACTOR
        ):
            continue

        time_penalty_min = (
            metrics["time_s"]
            - baseline_metrics["time_s"]
        ) / 60

        if time_penalty_min <= 0:
            hill_score = float("inf")
        else:
            hill_score = (
                ascent_gain
                / time_penalty_min
            )

        candidate = dict(candidate)
        candidate["hill_score"] = hill_score
        eligible.append(candidate)

    if not eligible:
        return baseline

    return max(
        eligible,
        key=lambda candidate:
            candidate["hill_score"],
    )


def route_segment(
    segment: dict,
) -> tuple[dict, str, int]:
    start = segment["from"]
    end = segment["to"]

    intention = normalize_intention(
        segment["routing"]
    )

    profile, _ = compile_profile(
        intention
    )

    hills = intention[
        "preferences"
    ]["hills"]

    if hills == "off":
        try:
            data = route_with_alternative(
                start,
                end,
                profile,
                0,
            )

            return data, profile, 0

        except HTTPError as exc:
            body = exc.read().decode(
                "utf-8",
                errors="replace",
            )

            raise RuntimeError(
                "\n"
                "BRouter failed for segment:\n"
                f"  {start['name']} -> {end['name']}\n"
                f"  profile: {profile}\n"
                f"  HTTP: {exc.code} {exc.reason}\n"
                f"  response: {body}\n"
            ) from exc

    candidates = []

    for alternative_idx in range(4):
        try:
            data = route_with_alternative(
                start,
                end,
                profile,
                alternative_idx,
            )

        except HTTPError:
            continue

        except Exception:
            continue

        candidates.append(
            {
                "alternative_idx": alternative_idx,
                "data": data,
                "metrics": candidate_metrics(data),
            }
        )

    if not candidates:
        raise RuntimeError(
            "BRouter returned no usable alternatives for "
            f"{start['name']} -> {end['name']}"
        )

    candidates.sort(
        key=lambda candidate:
            candidate["alternative_idx"]
    )

    if candidates[0]["alternative_idx"] != 0:
        raise RuntimeError(
            "BRouter did not return alternative 0 for "
            f"{start['name']} -> {end['name']}"
        )

    selected = select_hill_alternative(
        candidates,
        hills,
    )

    return (
        selected["data"],
        profile,
        selected["alternative_idx"],
    )


def extract_segment_result(
    index: int,
    segment: dict,
    data: dict,
    compiled_profile: str,
    selected_alternative: int,
) -> dict:
    feature = first_feature(data)
    properties = feature.get("properties", {})
    geometry = feature.get("geometry", {})

    if geometry.get("type") != "LineString":
        raise ValueError(
            f"Segment {index + 1} returned unsupported "
            f"geometry {geometry.get('type')!r}"
        )

    coordinates = geometry.get(
        "coordinates",
        [],
    )

    if not coordinates:
        raise ValueError(
            f"Segment {index + 1} returned no coordinates"
        )

    return {
        "index": index,
        "segment": segment,
        "compiled_profile": compiled_profile,
        "selected_alternative": selected_alternative,
        "data": data,
        "coordinates": coordinates,
        "distance_m": metric(
            properties,
            "track-length",
        ),
        "time_s": metric(
            properties,
            "total-time",
        ),
        "ascent_m": metric(
            properties,
            "filtered ascend",
        ),
        "cost": metric(
            properties,
            "cost",
        ),
    }


def merge_coordinates(
    results: list[dict],
) -> list[list[float]]:
    merged = []

    for result in results:
        coordinates = result["coordinates"]

        if not merged:
            merged.extend(coordinates)
            continue

        if (
            merged[-1][:2]
            == coordinates[0][:2]
        ):
            merged.extend(
                coordinates[1:]
            )
        else:
            merged.extend(coordinates)

    return merged


def build_geojson(
    tour: dict,
    results: list[dict],
) -> dict:
    merged = merge_coordinates(results)

    total_distance = sum(
        result["distance_m"]
        for result in results
    )

    total_time = sum(
        result["time_s"]
        for result in results
    )

    total_ascent = sum(
        result["ascent_m"]
        for result in results
    )

    total_cost = sum(
        result["cost"]
        for result in results
    )

    segment_summary = []

    for result in results:
        segment = result["segment"]

        segment_summary.append(
            {
                "index": result["index"] + 1,
                "from": segment["from"]["name"],
                "to": segment["to"]["name"],
                "routing": normalize_intention(
                    segment["routing"]
                ),
                "compiled_profile":
                    result["compiled_profile"],
                "selected_alternative":
                    result["selected_alternative"],
                "distance_m":
                    result["distance_m"],
                "time_s":
                    result["time_s"],
                "ascent_m":
                    result["ascent_m"],
                "cost":
                    result["cost"],
            }
        )

    return {
        "type": "FeatureCollection",
        "features": [
            {
                "type": "Feature",
                "properties": {
                    "name": tour["name"],
                    "track-length": total_distance,
                    "total-time": total_time,
                    "filtered ascend": total_ascent,
                    "cost": total_cost,
                    "segments": segment_summary,
                },
                "geometry": {
                    "type": "LineString",
                    "coordinates": merged,
                },
            }
        ],
    }


def add_gpx_waypoint(
    parent,
    point: dict,
):
    waypoint = ET.SubElement(
        parent,
        "wpt",
        {
            "lat": str(point["lat"]),
            "lon": str(point["lon"]),
        },
    )

    name = ET.SubElement(
        waypoint,
        "name",
    )

    name.text = point["name"]


def build_gpx(
    tour: dict,
    results: list[dict],
) -> ET.ElementTree:
    gpx = ET.Element(
        "gpx",
        {
            "version": "1.1",
            "creator":
                "brouter-motorcycle",
            "xmlns":
                "http://www.topografix.com/GPX/1/1",
        },
    )

    first_segment = tour["segments"][0]

    add_gpx_waypoint(
        gpx,
        first_segment["from"],
    )

    for segment in tour["segments"]:
        add_gpx_waypoint(
            gpx,
            segment["to"],
        )

    track = ET.SubElement(
        gpx,
        "trk",
    )

    track_name = ET.SubElement(
        track,
        "name",
    )

    track_name.text = tour["name"]

    track_segment = ET.SubElement(
        track,
        "trkseg",
    )

    merged = merge_coordinates(results)

    for coordinate in merged:
        lon = coordinate[0]
        lat = coordinate[1]

        track_point = ET.SubElement(
            track_segment,
            "trkpt",
            {
                "lat": str(lat),
                "lon": str(lon),
            },
        )

        if len(coordinate) >= 3:
            elevation = ET.SubElement(
                track_point,
                "ele",
            )

            elevation.text = str(
                coordinate[2]
            )

    return ET.ElementTree(gpx)


def indent_xml(
    element,
    level=0,
):
    indent = "\n" + level * "  "

    if len(element):
        if (
            not element.text
            or not element.text.strip()
        ):
            element.text = indent + "  "

        for child in element:
            indent_xml(
                child,
                level + 1,
            )

        if (
            not child.tail
            or not child.tail.strip()
        ):
            child.tail = indent

    if (
        level
        and (
            not element.tail
            or not element.tail.strip()
        )
    ):
        element.tail = indent


def validate_point(
    point: dict,
    segment_number: int,
    endpoint: str,
):
    if not isinstance(
        point,
        dict,
    ):
        raise ValueError(
            f"Segment {segment_number} "
            f"{endpoint} must be a mapping"
        )

    for key in (
        "name",
        "lat",
        "lon",
    ):
        if key not in point:
            raise ValueError(
                f"Segment {segment_number} "
                f"{endpoint} is missing "
                f"{key!r}"
            )

    try:
        float(point["lat"])
        float(point["lon"])

    except (TypeError, ValueError):
        raise ValueError(
            f"Segment {segment_number} "
            f"{endpoint} has invalid coordinates"
        )


def validate_tour(
    tour: dict,
):
    if not isinstance(
        tour,
        dict,
    ):
        raise ValueError(
            "Tour definition must be a mapping"
        )

    if not tour.get("name"):
        raise ValueError(
            "Tour must define a name"
        )

    segments = tour.get("segments")

    if (
        not isinstance(
            segments,
            list,
        )
        or not segments
    ):
        raise ValueError(
            "Tour must contain at least one segment"
        )

    for index, segment in enumerate(
        segments
    ):
        segment_number = index + 1

        if not isinstance(
            segment,
            dict,
        ):
            raise ValueError(
                f"Segment {segment_number} "
                "must be a mapping"
            )

        for key in (
            "from",
            "to",
            "routing",
        ):
            if key not in segment:
                raise ValueError(
                    f"Segment {segment_number} "
                    f"is missing {key!r}"
                )

        validate_point(
            segment["from"],
            segment_number,
            "from",
        )

        validate_point(
            segment["to"],
            segment_number,
            "to",
        )

        normalize_intention(
            segment["routing"]
        )

    for index in range(
        len(segments) - 1
    ):
        current_end = segments[index]["to"]
        next_start = (
            segments[index + 1]["from"]
        )

        if (
            current_end["lat"]
            != next_start["lat"]
            or current_end["lon"]
            != next_start["lon"]
        ):
            raise ValueError(
                "Segments must currently form a "
                "continuous chain. "
                f"Segment {index + 1} ends at "
                f"{current_end['name']!r}, while "
                f"segment {index + 2} starts at "
                f"{next_start['name']!r}."
            )


def load_tour(
    path: Path,
) -> dict:
    with path.open(
        "r",
        encoding="utf-8",
    ) as handle:
        tour = yaml.safe_load(handle)

    validate_tour(tour)

    return tour


def print_routing_intention(
    routing: dict,
):
    print(
        f"    character:       "
        f"{routing['character']}"
    )

    hills = routing[
        "preferences"
    ]["hills"]

    if hills != "off":
        print(
            f"    hills:           "
            f"{hills}"
        )

    if routing[
        "avoid"
    ]["cities"]:
        print(
            "    avoid cities:    yes"
        )

    if routing[
        "constraints"
    ]["avoid_motorways"]:
        print(
            "    avoid motorways: yes"
        )

    if routing[
        "constraints"
    ]["avoid_toll"]:
        print(
            "    avoid toll:      yes"
        )


def print_result(
    result: dict,
):
    segment = result["segment"]

    routing = normalize_intention(
        segment["routing"]
    )

    print(
        f"[{result['index'] + 1}] "
        f"{segment['from']['name']} -> "
        f"{segment['to']['name']}"
    )

    print_routing_intention(routing)

    print(
        f"    compiled profile: "
        f"{result['compiled_profile']}"
    )

    if result["selected_alternative"]:
        print(
            f"    BRouter alt:      "
            f"{result['selected_alternative']}"
        )

    print(
        f"    distance:         "
        f"{result['distance_m'] / 1000:.1f} km"
    )

    print(
        f"    time:             "
        f"{result['time_s'] / 60:.1f} min"
    )

    print(
        f"    ascent:           "
        f"{result['ascent_m']:.0f} m"
    )

    print()


def main():
    parser = argparse.ArgumentParser(
        description=(
            "Plan a multi-segment motorcycle route "
            "using BRouter routing intentions"
        )
    )

    parser.add_argument(
        "tour",
        type=Path,
        help="YAML tour definition",
    )

    args = parser.parse_args()

    tour_path = args.tour.resolve()

    if not tour_path.exists():
        raise SystemExit(
            "Tour definition does not exist: "
            f"{tour_path}"
        )

    tour = load_tour(tour_path)

    print()
    print(f"Tour: {tour['name']}")
    print("=" * (6 + len(tour["name"])))
    print()

    results = []

    for index, segment in enumerate(
        tour["segments"]
    ):
        (
            data,
            compiled_profile,
            selected_alternative,
        ) = route_segment(segment)

        result = extract_segment_result(
            index,
            segment,
            data,
            compiled_profile,
            selected_alternative,
        )

        results.append(result)

        print_result(result)

    total_distance = sum(
        result["distance_m"]
        for result in results
    )

    total_time = sum(
        result["time_s"]
        for result in results
    )

    total_ascent = sum(
        result["ascent_m"]
        for result in results
    )

    total_cost = sum(
        result["cost"]
        for result in results
    )

    print("Total")
    print("-----")
    print(
        f"distance: "
        f"{total_distance / 1000:.1f} km"
    )
    print(
        f"time:     "
        f"{total_time / 60:.1f} min"
    )
    print(
        f"ascent:   "
        f"{total_ascent:.0f} m"
    )
    print(
        f"cost:     "
        f"{total_cost:.0f}"
    )
    print()

    OUTPUT_DIR.mkdir(
        parents=True,
        exist_ok=True,
    )

    slug = slugify(tour["name"])

    geojson_file = (
        OUTPUT_DIR
        / f"{slug}.geojson"
    )

    gpx_file = (
        OUTPUT_DIR
        / f"{slug}.gpx"
    )

    geojson = build_geojson(
        tour,
        results,
    )

    geojson_file.write_text(
        json.dumps(
            geojson,
            ensure_ascii=False,
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )

    gpx = build_gpx(
        tour,
        results,
    )

    indent_xml(
        gpx.getroot()
    )

    gpx.write(
        gpx_file,
        encoding="utf-8",
        xml_declaration=True,
    )

    print(
        "GeoJSON: "
        f"{geojson_file.relative_to(ROOT)}"
    )

    print(
        "GPX:     "
        f"{gpx_file.relative_to(ROOT)}"
    )


if __name__ == "__main__":
    main()
