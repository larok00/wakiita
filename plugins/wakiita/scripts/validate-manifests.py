# /// script
# dependencies = ["jsonschema>=4.18,<5"]
# ///
"""Check ippin manifests without installing or changing anything."""

import argparse
import sys
from pathlib import Path

from manifests import load_repository


def validate(root):
    count, _, errors, reviews = load_repository(root)
    return count, errors, reviews


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("repository", type=Path, help="Path to the Oma-repository")
    root = parser.parse_args().repository.resolve()
    try:
        count, errors, reviews = validate(root)
    except (OSError, ValueError) as error:
        print(f"FAIL: {error}", file=sys.stderr)
        return 1
    for error in errors:
        print(f"FAIL: {error}", file=sys.stderr)
    for review in reviews:
        print(f"REVIEW: {review}")
    if errors:
        return 1
    print(f"PASS: {count} manifests — schema, IDs, and instruction paths")
    print("Target route selection, dependency cycles, and readiness require separate checks.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
