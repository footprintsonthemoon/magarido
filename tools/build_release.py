#!/usr/bin/env python3
"""
Build the BRouter Motorcycle v1 release profiles reproducibly.

Pipeline:
    src/moto-base.brf
        -> tools/generate_profiles.py
        -> profiles/
        -> release/

Only the three accepted v1 user-facing routing characters are copied to
release/:
    moto-fast.brf
    moto-curvy.brf
    moto-very-curvy.brf

Usage:
    python tools/build_release.py
    python tools/build_release.py --check

--check regenerates the development profiles in a temporary directory-safe
way only insofar as the existing generator does, then verifies that the
release files match the generated development profiles byte-for-byte.
"""

from __future__ import annotations

import argparse
import hashlib
import shutil
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
GENERATOR = ROOT / "tools" / "generate_profiles.py"
PROFILES_DIR = ROOT / "profiles"
RELEASE_DIR = ROOT / "release"

RELEASE_PROFILES = (
    "moto-fast.brf",
    "moto-curvy.brf",
    "moto-very-curvy.brf",
)


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for block in iter(lambda: f.read(1024 * 1024), b""):
            h.update(block)
    return h.hexdigest()


def run_generator() -> None:
    if not GENERATOR.exists():
        raise RuntimeError(f"Missing generator: {GENERATOR}")

    print("Generating development profiles...")
    result = subprocess.run(
        [sys.executable, str(GENERATOR)],
        cwd=ROOT,
    )
    if result.returncode != 0:
        raise RuntimeError(
            f"Profile generator failed with exit code {result.returncode}"
        )


def ensure_generated_profiles() -> None:
    missing = [
        name
        for name in RELEASE_PROFILES
        if not (PROFILES_DIR / name).is_file()
    ]
    if missing:
        raise RuntimeError(
            "Generated release candidates are missing:\n  "
            + "\n  ".join(missing)
        )


def check_release() -> bool:
    ensure_generated_profiles()

    ok = True

    print()
    print("Release reproducibility check")
    print("=============================")

    for name in RELEASE_PROFILES:
        generated = PROFILES_DIR / name
        release = RELEASE_DIR / name

        if not release.is_file():
            print(f"[MISSING] {name}")
            ok = False
            continue

        generated_hash = sha256(generated)
        release_hash = sha256(release)

        if generated_hash == release_hash:
            print(f"[OK]      {name}  {generated_hash}")
        else:
            print(f"[DIFF]    {name}")
            print(f"          generated: {generated_hash}")
            print(f"          release:   {release_hash}")
            ok = False

    return ok


def build_release() -> None:
    ensure_generated_profiles()
    RELEASE_DIR.mkdir(parents=True, exist_ok=True)

    expected = set(RELEASE_PROFILES)

    # Keep release/ intentionally minimal. Refuse to silently preserve an
    # unexpected BRF because the public v1 set is part of the release contract.
    unexpected = sorted(
        p.name
        for p in RELEASE_DIR.glob("*.brf")
        if p.name not in expected
    )
    if unexpected:
        raise RuntimeError(
            "Unexpected BRF files exist in release/:\n  "
            + "\n  ".join(unexpected)
            + "\nRemove or review them before building the v1 release."
        )

    print()
    print("Building release")
    print("================")

    for name in RELEASE_PROFILES:
        source = PROFILES_DIR / name
        target = RELEASE_DIR / name
        shutil.copyfile(source, target)
        print(f"[COPY] {name}")

    print()
    if not check_release():
        raise RuntimeError("Release verification failed")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--check",
        action="store_true",
        help="verify release/ against freshly generated development profiles",
    )
    args = parser.parse_args()

    print("BRouter Motorcycle v1 release builder")
    print("====================================")
    print("Canonical source: src/moto-base.brf")
    print("Release set:      Fast / Curvy / Very Curvy")
    print()

    run_generator()

    if args.check:
        return 0 if check_release() else 1

    build_release()

    print()
    print("Release build complete.")
    print("Run 'git diff --exit-code -- release/ profiles/' to verify a clean tree.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
