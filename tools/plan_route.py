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


def slugify(value: str) -> str:
    value = value.lower()
    value = re.sub(r"[^a-z0-9]+", "-", value)
    return value.strip("-")


def route_segment(segment: dict) -> tuple[dict, str]:
    """
    Compile the routing intention for one segment and calculate
    the route using the local BRouter server.
    """

    start = segment["from"]
    end = segment["to"]

    intention = normalize_intention(
        segment["routing"]
    )

    profile, _ = compile_profile(
        intention
    )

    params = {
        "lonlats": (
            f"{start['lon']},{start['lat']}|"
            f"{end['lon']},{end['lat']}"
        ),
        "profile": profile,
        "alternativeidx": "0",
        "format": "geojson",
    }

    url = (
        f"{BROUTER_URL}?"
        f"{urllib.parse.urlencode(params)}"
    )

    try:
        with urllib.request.urlopen(
            url,
            timeout=120,
        ) as response:
            return json.load(response), profile

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


def first_feature(data: dict) -> dict:
    features = data.get(
        "features",
        [],
    )

    if not features:
        raise ValueError(
            "BRouter returned no features"
        )

    return features[0]


def metric(
    properties: dict,
    key: str,
    default=0.0,
) -> float:
    try:
        return float(
            properties.get(
                key,
                default,
            )
        )

    except (TypeError, ValueError):
        return float(default)


def extract_segment_result(
    index: int,
    segment: dict,
    data: dict,
    compiled_profile: str,
) -> dict:
    feature = first_feature(
        data
    )

    properties = feature.get(
        "properties",
        {},
    )

    geometry = feature.get(
        "geometry",
        {},
    )

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
    """
    Merge all planner segments into one continuous coordinate list.

    Consecutive BRouter segments normally share their boundary
    coordinate. That duplicate is removed.
    """

    merged = []

    for result in results:
        coordinates = result[
            "coordinates"
        ]

        if not merged:
            merged.extend(
                coordinates
            )
            continue

        if (
            merged[-1][:2]
            == coordinates[0][:2]
        ):
            merged.extend(
                coordinates[1:]
            )

        else:
            merged.extend(
                coordinates
            )

    return merged


def build_geojson(
    tour: dict,
    results: list[dict],
) -> dict:
    """
    Build the development GeoJSON representation.

    Unlike GPX, GeoJSON deliberately retains the complete planner
    segment metadata.
    """

    merged = merge_coordinates(
        results
    )

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
        segment = result[
            "segment"
        ]

        segment_summary.append(
            {
                "index":
                    result["index"] + 1,

                "from":
                    segment["from"]["name"],

                "to":
                    segment["to"]["name"],

                "routing":
                    normalize_intention(
                        segment["routing"]
                    ),

                "compiled_profile":
                    result["compiled_profile"],

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
                    "name":
                        tour["name"],

                    "track-length":
                        total_distance,

                    "total-time":
                        total_time,

                    "filtered ascend":
                        total_ascent,

                    "cost":
                        total_cost,

                    "segments":
                        segment_summary,
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
            "lat": str(
                point["lat"]
            ),
            "lon": str(
                point["lon"]
            ),
        },
    )

    name = ET.SubElement(
        waypoint,
        "name",
    )

    name.text = point[
        "name"
    ]


def build_gpx(
    tour: dict,
    results: list[dict],
) -> ET.ElementTree:
    """
    Build an OsmAnd-friendly GPX 1.1 file.

    Important design decision:

        planner segments != GPX track segments

    The planner may calculate every section independently with a
    different routing intention.

    For navigation, however, the complete tour is exported as ONE
    continuous GPX track containing ONE <trkseg>.

    Segment boundaries remain visible as GPX waypoints.

    Detailed per-segment routing metadata remains available in the
    corresponding GeoJSON output.
    """

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

    #
    # Tour waypoints
    #

    first_segment = tour[
        "segments"
    ][0]

    add_gpx_waypoint(
        gpx,
        first_segment["from"],
    )

    for segment in tour[
        "segments"
    ]:
        add_gpx_waypoint(
            gpx,
            segment["to"],
        )

    #
    # One track for the complete tour
    #

    track = ET.SubElement(
        gpx,
        "trk",
    )

    track_name = ET.SubElement(
        track,
        "name",
    )

    track_name.text = tour[
        "name"
    ]

    #
    # One track segment for the complete tour
    #

    track_segment = ET.SubElement(
        track,
        "trkseg",
    )

    merged = merge_coordinates(
        results
    )

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

        #
        # Preserve elevation if supplied by BRouter.
        #

        if len(coordinate) >= 3:
            elevation = ET.SubElement(
                track_point,
                "ele",
            )

            elevation.text = str(
                coordinate[2]
            )

    return ET.ElementTree(
        gpx
    )


def indent_xml(
    element,
    level=0,
):
    indent = (
        "\n"
        + level * "  "
    )

    if len(element):
        if (
            not element.text
            or not element.text.strip()
        ):
            element.text = (
                indent + "  "
            )

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
        float(
            point["lat"]
        )

        float(
            point["lon"]
        )

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

    if not tour.get(
        "name"
    ):
        raise ValueError(
            "Tour must define a name"
        )

    segments = tour.get(
        "segments"
    )

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
        segment_number = (
            index + 1
        )

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

    #
    # Phase 2 currently requires a continuous waypoint chain.
    #

    for index in range(
        len(segments) - 1
    ):
        current_end = (
            segments[index][
                "to"
            ]
        )

        next_start = (
            segments[index + 1][
                "from"
            ]
        )

        if (
            current_end["lat"]
            != next_start["lat"]
            or
            current_end["lon"]
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
        tour = yaml.safe_load(
            handle
        )

    validate_tour(
        tour
    )

    return tour


def print_routing_intention(
    routing: dict,
):
    print(
        f"    character:       "
        f"{routing['character']}"
    )

    prefer_hills = routing[
        "preferences"
    ]["prefer_hills"]

    if prefer_hills:
        print(
            "    prefer hills:    yes"
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
    segment = result[
        "segment"
    ]

    routing = normalize_intention(
        segment["routing"]
    )

    print(
        f"[{result['index'] + 1}] "
        f"{segment['from']['name']} -> "
        f"{segment['to']['name']}"
    )

    print_routing_intention(
        routing
    )

    print(
        f"    compiled profile: "
        f"{result['compiled_profile']}"
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

    tour_path = (
        args.tour.resolve()
    )

    if not tour_path.exists():
        raise SystemExit(
            "Tour definition does not exist: "
            f"{tour_path}"
        )

    tour = load_tour(
        tour_path
    )

    print()
    print(
        f"Tour: {tour['name']}"
    )

    print(
        "="
        * (
            6
            + len(
                tour["name"]
            )
        )
    )

    print()

    results = []

    for index, segment in enumerate(
        tour["segments"]
    ):
        data, compiled_profile = (
            route_segment(
                segment
            )
        )

        result = (
            extract_segment_result(
                index,
                segment,
                data,
                compiled_profile,
            )
        )

        results.append(
            result
        )

        print_result(
            result
        )

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

    print(
        "Total"
    )

    print(
        "-----"
    )

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

    slug = slugify(
        tour["name"]
    )

    geojson_file = (
        OUTPUT_DIR
        / f"{slug}.geojson"
    )

    gpx_file = (
        OUTPUT_DIR
        / f"{slug}.gpx"
    )

    #
    # Development / analysis output
    #

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

    #
    # OsmAnd / navigation output
    #

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
