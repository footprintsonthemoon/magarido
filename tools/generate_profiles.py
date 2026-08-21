#!/usr/bin/env python3

from pathlib import Path
import argparse
import re
import sys

try:
    import yaml
except ImportError:
    sys.exit(
        "PyYAML is required. Install it with:\n"
        "  python3 -m pip install pyyaml"
    )


ROOT = Path(__file__).resolve().parents[1]

SOURCE = ROOT / "src" / "moto-base.brf"
PRESETS = ROOT / "config" / "presets.yaml"

OUTPUT_ALL = ROOT / "profiles"
OUTPUT_RELEASE = ROOT / "release"


VALID_STATUSES = {
    "release",
    "experimental",
}


def replace_assignment(
    text: str,
    name: str,
    value: int,
) -> str:
    pattern = rf"^assign\s+{re.escape(name)}\s*=\s*.*$"
    replacement = f"assign {name} = {value}"

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


def validate_preset(
    preset_id: str,
    preset: dict,
) -> None:
    required = {
        "name",
        "status",
        "character",
        "curviness",
        "hilliness",
    }

    missing = required - preset.keys()

    if missing:
        raise ValueError(
            f"Preset {preset_id!r} is missing: "
            + ", ".join(sorted(missing))
        )

    status = preset["status"]

    if status not in VALID_STATUSES:
        raise ValueError(
            f"Preset {preset_id!r} has invalid status "
            f"{status!r}"
        )

    curviness = int(preset["curviness"])
    hilliness = int(preset["hilliness"])

    if curviness not in {0, 1, 2, 3}:
        raise ValueError(
            f"Preset {preset_id!r} has invalid curviness "
            f"{curviness}"
        )

    if hilliness not in {0, 1, 2}:
        raise ValueError(
            f"Preset {preset_id!r} has invalid hilliness "
            f"{hilliness}"
        )


def generate_profile(
    source: str,
    preset_id: str,
    preset: dict,
) -> str:
    result = source

    result = replace_assignment(
        result,
        "curviness",
        int(preset["curviness"]),
    )

    result = replace_assignment(
        result,
        "hilliness",
        int(preset["hilliness"]),
    )

    header = (
        "# GENERATED FILE - DO NOT EDIT\n"
        "#\n"
        "# Source: src/moto-base.brf\n"
        f"# Preset: {preset_id}\n"
        f"# Name: {preset['name']}\n"
        f"# Status: {preset['status']}\n"
        f"# Character: {preset['character']}\n"
        f"# Curviness: {preset['curviness']}\n"
        f"# Hilliness: {preset['hilliness']}\n"
        "#\n\n"
    )

    return header + result


def clean_generated_directory(
    directory: Path,
    expected_files: set[str],
) -> None:
    directory.mkdir(
        parents=True,
        exist_ok=True,
    )

    for existing in directory.glob("moto-*.brf"):
        if existing.name not in expected_files:
            existing.unlink()

            print(
                "removed stale "
                f"{existing.relative_to(ROOT)}"
            )


def generate_all(
    source: str,
    presets: dict,
) -> None:
    expected_all = set()
    expected_release = set()

    for preset_id, preset in presets.items():
        validate_preset(
            preset_id,
            preset,
        )

        filename = f"moto-{preset_id}.brf"

        content = generate_profile(
            source,
            preset_id,
            preset,
        )

        #
        # All development profiles
        #

        target_all = OUTPUT_ALL / filename

        OUTPUT_ALL.mkdir(
            parents=True,
            exist_ok=True,
        )

        target_all.write_text(
            content,
            encoding="utf-8",
        )

        expected_all.add(filename)

        print(
            f"generated {target_all.relative_to(ROOT)}"
        )

        #
        # User-facing release profiles only
        #

        if preset["status"] == "release":
            target_release = OUTPUT_RELEASE / filename

            OUTPUT_RELEASE.mkdir(
                parents=True,
                exist_ok=True,
            )

            target_release.write_text(
                content,
                encoding="utf-8",
            )

            expected_release.add(filename)

            print(
                "generated "
                f"{target_release.relative_to(ROOT)}"
            )

    clean_generated_directory(
        OUTPUT_ALL,
        expected_all,
    )

    clean_generated_directory(
        OUTPUT_RELEASE,
        expected_release,
    )


def list_profiles(
    presets: dict,
) -> None:
    print(
        f"{'Preset':<24}"
        f"{'Status':<14}"
        f"{'Character':<16}"
        f"{'Curvy':>7}"
        f"{'Hilly':>7}"
    )

    print("-" * 68)

    for preset_id, preset in presets.items():
        print(
            f"{preset_id:<24}"
            f"{preset['status']:<14}"
            f"{preset['character']:<16}"
            f"{preset['curviness']:>7}"
            f"{preset['hilliness']:>7}"
        )


def load_configuration() -> dict:
    with PRESETS.open(
        "r",
        encoding="utf-8",
    ) as handle:
        configuration = yaml.safe_load(handle)

    if not configuration:
        raise ValueError(
            "Preset configuration is empty"
        )

    presets = configuration.get("presets")

    if not isinstance(presets, dict):
        raise ValueError(
            "Preset configuration must contain "
            "a 'presets' mapping"
        )

    for preset_id, preset in presets.items():
        validate_preset(
            preset_id,
            preset,
        )

    return presets


def parse_arguments() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Generate BRouter motorcycle profiles"
        )
    )

    parser.add_argument(
        "--list",
        action="store_true",
        help="list configured profiles and exit",
    )

    return parser.parse_args()


def main() -> None:
    args = parse_arguments()

    presets = load_configuration()

    if args.list:
        list_profiles(presets)
        return

    source = SOURCE.read_text(
        encoding="utf-8"
    )

    generate_all(
        source,
        presets,
    )


if __name__ == "__main__":
    main()
