#!/usr/bin/env python3

from __future__ import annotations

import hashlib
import json
import os
import re
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]

#
# Kinematic Baseline v1
#

SOURCE = ROOT / "src" / "moto-kinematic-base.brf"

COMPILED_DIR = ROOT / "output" / "compiled-profiles"

DEFAULT_BROUTER_PROFILES_DIR = (
    Path.home()
    / "opt"
    / "brouter"
    / "misc"
    / "profiles2"
)


#
# Routing characters
#
# These values correspond to the calibrated Kinematic Baseline v1.
#

CHARACTERS = {
    "fast": {
        "curviness": 0,
    },
    "curvy": {
        "curviness": 2,
    },
    "very-curvy": {
        "curviness": 3,
    },
}


def replace_assignment(
    text: str,
    name: str,
    value,
) -> str:
    """
    Replace exactly one top-level BRouter assignment.

    Failing when an assignment is missing is intentional:
    the compiler and routing profile must remain in sync.
    """

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
            f"Expected exactly one assignment for {name!r}, "
            f"found {count}"
        )

    return result


def normalize_intention(
    intention: dict,
) -> dict:
    """
    Convert a user-facing routing intention into a stable,
    canonical representation.

    Some dimensions are already part of the planner API but are
    not yet implemented by Kinematic Baseline v1.
    """

    if not isinstance(intention, dict):
        raise ValueError(
            "Routing intention must be a mapping"
        )

    character = intention.get(
        "character"
    )

    if character not in CHARACTERS:
        raise ValueError(
            f"Unknown routing character: {character!r}. "
            f"Expected one of: {', '.join(CHARACTERS)}"
        )

    preferences = (
        intention.get("preferences")
        or {}
    )

    avoid = (
        intention.get("avoid")
        or {}
    )

    constraints = (
        intention.get("constraints")
        or {}
    )

    #
    # Future preference:
    # retained in API, not yet implemented by Kinematic v1.
    #

    prefer_hills = preferences.get(
        "prefer_hills",
        False,
    )

    if not isinstance(
        prefer_hills,
        bool,
    ):
        raise ValueError(
            "preferences.prefer_hills must be true or false"
        )

    #
    # Future avoidance preference:
    # retained in API, not yet implemented by Kinematic v1.
    #

    avoid_cities = avoid.get(
        "cities",
        False,
    )

    if not isinstance(
        avoid_cities,
        bool,
    ):
        raise ValueError(
            "avoid.cities must be true or false"
        )

    #
    # Implemented constraints
    #

    avoid_motorways = constraints.get(
        "avoid_motorways",
        False,
    )

    if not isinstance(
        avoid_motorways,
        bool,
    ):
        raise ValueError(
            "constraints.avoid_motorways must be true or false"
        )

    avoid_toll = constraints.get(
        "avoid_toll",
        False,
    )

    if not isinstance(
        avoid_toll,
        bool,
    ):
        raise ValueError(
            "constraints.avoid_toll must be true or false"
        )

    return {
        "character": character,

        "preferences": {
            "prefer_hills":
                prefer_hills,
        },

        "avoid": {
            "cities":
                avoid_cities,
        },

        "constraints": {
            "avoid_motorways":
                avoid_motorways,

            "avoid_toll":
                avoid_toll,
        },
    }


def validate_supported_intention(
    intention: dict,
) -> None:
    """
    Reject routing dimensions that are part of the future API
    but are not yet implemented in Kinematic Baseline v1.

    This is preferable to silently accepting an option that has
    no effect on the calculated route.
    """

    if intention[
        "preferences"
    ]["prefer_hills"]:
        raise ValueError(
            "preferences.prefer_hills is not yet supported "
            "by Kinematic Baseline v1"
        )

    if intention[
        "avoid"
    ]["cities"]:
        raise ValueError(
            "avoid.cities is not yet supported "
            "by Kinematic Baseline v1"
        )


def intention_hash(
    intention: dict,
) -> str:
    canonical = json.dumps(
        intention,
        sort_keys=True,
        separators=(",", ":"),
    )

    return hashlib.sha256(
        canonical.encode("utf-8")
    ).hexdigest()[:10]


def profile_name(
    intention: dict,
) -> str:
    character = intention[
        "character"
    ]

    digest = intention_hash(
        intention
    )

    return (
        f"moto-intent-"
        f"{character}-"
        f"{digest}"
    )


def brouter_profiles_dir() -> Path:
    configured = os.environ.get(
        "BROUTER_PROFILES_DIR"
    )

    if configured:
        return Path(
            configured
        ).expanduser()

    return (
        DEFAULT_BROUTER_PROFILES_DIR
    )


def compile_profile(
    intention: dict,
) -> tuple[str, Path]:
    """
    Compile one routing intention into a temporary BRouter BRF.

    The output is deterministic:
    identical normalized intentions produce the same profile name.
    """

    intention = normalize_intention(
        intention
    )

    validate_supported_intention(
        intention
    )

    character = intention[
        "character"
    ]

    curviness = CHARACTERS[
        character
    ]["curviness"]

    avoid_motorways = intention[
        "constraints"
    ]["avoid_motorways"]

    avoid_toll = intention[
        "constraints"
    ]["avoid_toll"]

    name = profile_name(
        intention
    )

    if not SOURCE.exists():
        raise RuntimeError(
            "Kinematic source profile does not exist:\n"
            f"  {SOURCE}"
        )

    source = SOURCE.read_text(
        encoding="utf-8"
    )

    result = source

    #
    # Routing character
    #

    result = replace_assignment(
        result,
        "curviness",
        curviness,
    )

    #
    # Hard / strong constraints
    #

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

    #
    # Generated-file metadata
    #

    header = (
        "# GENERATED ROUTING INTENTION - DO NOT EDIT\n"
        "#\n"
        "# Source: src/moto-kinematic-base.brf\n"
        "# Model: Kinematic Baseline v1\n"
        f"# Character: {character}\n"
        f"# Curviness level: {curviness}\n"
        f"# Avoid motorways: {avoid_motorways}\n"
        f"# Avoid toll: {avoid_toll}\n"
        f"# Intention hash: {intention_hash(intention)}\n"
        "#\n\n"
    )

    COMPILED_DIR.mkdir(
        parents=True,
        exist_ok=True,
    )

    compiled_file = (
        COMPILED_DIR
        / f"{name}.brf"
    )

    compiled_file.write_text(
        header + result,
        encoding="utf-8",
    )

    #
    # Expose the generated profile to the local BRouter server.
    #

    profiles_dir = (
        brouter_profiles_dir()
    )

    if not profiles_dir.exists():
        raise RuntimeError(
            "BRouter profiles directory does not exist:\n"
            f"  {profiles_dir}\n\n"
            "Set BROUTER_PROFILES_DIR if BRouter is "
            "installed somewhere else."
        )

    target = (
        profiles_dir
        / compiled_file.name
    )

    if (
        target.exists()
        or target.is_symlink()
    ):
        target.unlink()

    target.symlink_to(
        compiled_file.resolve()
    )

    return (
        name,
        compiled_file,
    )


if __name__ == "__main__":
    example = {
        "character": "curvy",

        "constraints": {
            "avoid_motorways": True,
            "avoid_toll": False,
        },
    }

    name, path = compile_profile(
        example
    )

    print(
        f"profile: {name}"
    )

    print(
        f"file:    {path}"
    )
