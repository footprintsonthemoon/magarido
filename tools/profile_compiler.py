#!/usr/bin/env python3

from __future__ import annotations

import hashlib
import json
import os
import re
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "src" / "moto-kinematic-base.brf"
COMPILED_DIR = ROOT / "output" / "compiled-profiles"

DEFAULT_BROUTER_PROFILES_DIR = (
    Path.home()
    / "opt"
    / "brouter"
    / "misc"
    / "profiles2"
)

CHARACTERS = {
    "fast": {"curviness": 0},
    "curvy": {"curviness": 2},
    "very-curvy": {"curviness": 3},
}

HILLS_VALUES = {"off", "moderate", "strong"}


def replace_assignment(text: str, name: str, value) -> str:
    pattern = rf"^assign\s+{re.escape(name)}\s*=\s*.*$"

    if isinstance(value, bool):
        rendered = "true" if value else "false"
    else:
        rendered = str(value)

    replacement = f"assign {name} = {rendered}"

    result, count = re.subn(
        pattern,
        replacement,
        text,
        count=1,
        flags=re.MULTILINE,
    )

    if count != 1:
        raise RuntimeError(
            f"Expected exactly one assignment for {name!r}, found {count}"
        )

    return result


def normalize_hills(preferences: dict) -> str:
    if "hills" in preferences and "prefer_hills" in preferences:
        raise ValueError(
            "Use either preferences.hills or preferences.prefer_hills, not both"
        )

    if "hills" in preferences:
        hills = preferences["hills"]

        if hills not in HILLS_VALUES:
            raise ValueError(
                "preferences.hills must be one of: off, moderate, strong"
            )

        return hills

    legacy = preferences.get("prefer_hills", False)

    if not isinstance(legacy, bool):
        raise ValueError(
            "preferences.prefer_hills must be true or false"
        )

    return "moderate" if legacy else "off"


def normalize_intention(intention: dict) -> dict:
    if not isinstance(intention, dict):
        raise ValueError("Routing intention must be a mapping")

    character = intention.get("character")

    if character not in CHARACTERS:
        raise ValueError(
            f"Unknown routing character: {character!r}. "
            f"Expected one of: {', '.join(CHARACTERS)}"
        )

    preferences = intention.get("preferences") or {}
    avoid = intention.get("avoid") or {}
    constraints = intention.get("constraints") or {}

    hills = normalize_hills(preferences)

    avoid_cities = avoid.get("cities", False)
    if not isinstance(avoid_cities, bool):
        raise ValueError("avoid.cities must be true or false")

    avoid_motorways = constraints.get("avoid_motorways", False)
    if not isinstance(avoid_motorways, bool):
        raise ValueError(
            "constraints.avoid_motorways must be true or false"
        )

    avoid_toll = constraints.get("avoid_toll", False)
    if not isinstance(avoid_toll, bool):
        raise ValueError(
            "constraints.avoid_toll must be true or false"
        )

    return {
        "character": character,
        "preferences": {"hills": hills},
        "avoid": {"cities": avoid_cities},
        "constraints": {
            "avoid_motorways": avoid_motorways,
            "avoid_toll": avoid_toll,
        },
    }


def validate_supported_intention(intention: dict) -> None:
    if intention["avoid"]["cities"]:
        raise ValueError(
            "avoid.cities is not yet supported by Kinematic Baseline v1"
        )


def profile_intention(intention: dict) -> dict:
    return {
        "character": intention["character"],
        "constraints": {
            "avoid_motorways": intention["constraints"]["avoid_motorways"],
            "avoid_toll": intention["constraints"]["avoid_toll"],
        },
    }


def profile_hash(intention: dict) -> str:
    canonical = json.dumps(
        profile_intention(intention),
        sort_keys=True,
        separators=(",", ":"),
    )

    return hashlib.sha256(
        canonical.encode("utf-8")
    ).hexdigest()[:10]


def profile_name(intention: dict) -> str:
    character = intention["character"]
    digest = profile_hash(intention)
    return f"moto-intent-{character}-{digest}"


def brouter_profiles_dir() -> Path:
    configured = os.environ.get("BROUTER_PROFILES_DIR")

    if configured:
        return Path(configured).expanduser()

    return DEFAULT_BROUTER_PROFILES_DIR


def compile_profile(intention: dict) -> tuple[str, Path]:
    intention = normalize_intention(intention)
    validate_supported_intention(intention)

    character = intention["character"]
    curviness = CHARACTERS[character]["curviness"]
    avoid_motorways = intention["constraints"]["avoid_motorways"]
    avoid_toll = intention["constraints"]["avoid_toll"]

    name = profile_name(intention)

    if not SOURCE.exists():
        raise RuntimeError(
            "Kinematic source profile does not exist:\n"
            f"  {SOURCE}"
        )

    result = SOURCE.read_text(encoding="utf-8")

    result = replace_assignment(
        result,
        "curviness",
        curviness,
    )

    result = replace_assignment(
        result,
        "avoid_motorways",
        avoid_motorways,
    )

    result = replace_assignment(
        result,
        "avoid_toll",
        avoid_toll,
    )

    header = (
        "# GENERATED ROUTING INTENTION - DO NOT EDIT\n"
        "#\n"
        "# Source: src/moto-kinematic-base.brf\n"
        "# Model: Kinematic Baseline v1\n"
        f"# Character: {character}\n"
        f"# Curviness level: {curviness}\n"
        f"# Avoid motorways: {avoid_motorways}\n"
        f"# Avoid toll: {avoid_toll}\n"
        f"# Profile hash: {profile_hash(intention)}\n"
        "#\n"
        "# Planner-level preferences such as hills are not\n"
        "# compiled into this profile.\n"
        "#\n\n"
    )

    COMPILED_DIR.mkdir(parents=True, exist_ok=True)

    compiled_file = COMPILED_DIR / f"{name}.brf"
    compiled_file.write_text(
        header + result,
        encoding="utf-8",
    )

    profiles_dir = brouter_profiles_dir()

    if not profiles_dir.exists():
        raise RuntimeError(
            "BRouter profiles directory does not exist:\n"
            f"  {profiles_dir}\n\n"
            "Set BROUTER_PROFILES_DIR if BRouter is installed somewhere else."
        )

    target = profiles_dir / compiled_file.name

    if target.exists() or target.is_symlink():
        target.unlink()

    target.symlink_to(compiled_file.resolve())

    return name, compiled_file


if __name__ == "__main__":
    example = {
        "character": "curvy",
        "preferences": {
            "hills": "strong",
        },
        "constraints": {
            "avoid_motorways": False,
            "avoid_toll": False,
        },
    }

    name, path = compile_profile(example)

    print(f"profile: {name}")
    print(f"file:    {path}")
