# /// script
# dependencies = ["jsonschema>=4.18,<5"]
# ///
"""Check ippin manifests without installing or changing anything."""

import argparse
import json
import sys
from pathlib import Path

from jsonschema import Draft202012Validator


def validate(root):
    schema = json.loads((Path(__file__).resolve().parents[1] / "docs/ippin.schema.json").read_text())
    Draft202012Validator.check_schema(schema)
    validator = Draft202012Validator(schema)
    errors = []
    paths = sorted((root / "ippin").glob("*/ippin.json"))
    if not paths:
        errors.append("No ippin manifests found")
    component_ids = set()
    provided = set()
    requirements = []

    for path in paths:
        label = str(path.relative_to(root))
        try:
            component = path.parent.resolve(strict=True)
            if not path.resolve(strict=True).is_relative_to(root.resolve()):
                raise ValueError("manifest resolves outside the repository")
            manifest = json.loads(path.read_text())
        except (OSError, ValueError, RuntimeError) as error:
            errors.append(f"{label}: {error}")
            continue

        invalid = list(validator.iter_errors(manifest))
        for error in invalid:
            location = "/".join(map(str, error.absolute_path)) or "<root>"
            errors.append(f"{label}: {location}: {error.message}")
        if invalid:
            continue

        name = manifest["id"]
        if name != path.parent.name:
            errors.append(f"{label}: id must match folder name {path.parent.name!r}")
        if name in component_ids:
            errors.append(f"{label}: duplicate component id {name!r}")
        component_ids.add(name)
        provided.update(manifest["provides"])
        route_ids = set()

        for route in manifest["routes"]:
            context = f"{label}: route {route['id']}"
            if route["id"] in route_ids:
                errors.append(f"{context}: duplicate route id")
            route_ids.add(route["id"])
            requirements.extend((context, outcome) for outcome in route["requires"])
            overlay_ids = set()
            for overlay in route.get("overlays", []):
                if overlay["id"] in overlay_ids:
                    errors.append(f"{context}: duplicate overlay id {overlay['id']!r}")
                overlay_ids.add(overlay["id"])
                requirements.extend(
                    (f"{context}: overlay {overlay['id']}", outcome)
                    for outcome in overlay.get("requires", [])
                )

            for item in [route, *route.get("overlays", [])]:
                relative = item["instructions"]
                try:
                    instruction = (component / relative).resolve(strict=True)
                    if not instruction.is_relative_to(component) or not instruction.is_file():
                        raise ValueError("must resolve to a file inside its ippin")
                except (OSError, ValueError, RuntimeError) as error:
                    errors.append(f"{context}: instructions {relative!r}: {error}")

    # Missing providers may be intentional external prerequisites, not typos.
    reviews = sorted({f"{context}: verify external prerequisite {outcome!r}"
                      for context, outcome in requirements if outcome not in provided})
    return len(paths), errors, reviews


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
