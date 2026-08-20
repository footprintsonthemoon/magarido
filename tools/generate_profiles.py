#!/usr/bin/env python3

from pathlib import Path
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
OUTPUT = ROOT / "profiles"


def replace_assignment(text: str, name: str, value: int) -> str:
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
            f"Expected exactly one assignment for {name!r}, found {count}"
        )

    return result


def generate_profile(source: str, preset_id: str, preset: dict) -> str:
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
        "#\n\n"
    )

    return header + result


def main() -> None:
    source = SOURCE.read_text(encoding="utf-8")

    with PRESETS.open("r", encoding="utf-8") as handle:
        configuration = yaml.safe_load(handle)

    presets = configuration["presets"]

    OUTPUT.mkdir(parents=True, exist_ok=True)

    expected_files = set()

    for preset_id, preset in presets.items():
        target = OUTPUT / f"moto-{preset_id}.brf"
        expected_files.add(target.name)

        content = generate_profile(source, preset_id, preset)
        target.write_text(content, encoding="utf-8")

        print(f"generated {target.relative_to(ROOT)}")

    # Remove stale generated profiles.
    for existing in OUTPUT.glob("moto-*.brf"):
        if existing.name not in expected_files:
            existing.unlink()
            print(f"removed stale {existing.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
