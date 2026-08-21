#!/usr/bin/env python3

import json
import sys
import urllib.parse
import urllib.request

BASE_URL = "http://localhost:17777/brouter"

PROFILES = [
    "moto-fast",
    "moto-fast-curvy",
    "moto-curvy",
    "moto-very-curvy",
    "moto-curvy-hilly",
    "moto-curvy-very-hilly",
]




ROUTE = "7.2468,47.1368|6.9293,46.9896"


def route(profile: str) -> dict:
    params = urllib.parse.urlencode(
        {
            "lonlats": ROUTE,
            "profile": profile,
            "alternativeidx": 0,
            "format": "geojson",
        }
    )

    url = f"{BASE_URL}?{params}"

    with urllib.request.urlopen(url, timeout=30) as response:
        return json.load(response)


def main() -> int:
    failed = False

    for profile in PROFILES:
        try:
            data = route(profile)

            feature = data["features"][0]
            properties = feature["properties"]

            distance = int(properties["track-length"])
            total_time = int(properties["total-time"])
            ascend = int(properties.get("filtered ascend", 0))
            cost = int(properties["cost"])

            print(
                f"[OK] {profile:<22} "
                f"{distance / 1000:6.1f} km  "
                f"{total_time / 60:6.1f} min  "
                f"{ascend:5d} m ascent  "
                f"cost={cost}"
            )

        except Exception as exc:
            failed = True
            print(f"[FAIL] {profile}: {exc}")

    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
