"""Select routes and overlays from a validated ippin manifest.

Target facts use the manifest's ``when`` keys. An omitted key is unknown;
None means explicitly absent (for example, no machine profile). Callers must
validate manifests and target facts before selection. This module performs no
file access, readiness checks, or installation.
"""


def _match(conditions, target):
    """Return (True/False/None, missing facts); a known mismatch wins."""
    missing = set()
    for key, expected in conditions.items():
        if key not in target:
            missing.add(key)
        elif target[key] != expected:
            return False, set()
    return (None, missing) if missing else (True, set())


def select(manifest, target):
    """Return a JSON-compatible selection with status, IDs, and missing facts.

    Status is selected, unresolved, or unsupported. An unresolved route has no
    route ID. An unresolved overlay selection retains the selected route ID but
    returns no overlays, so a partial list cannot be mistaken for a complete one.
    Requirements never affect selection. Returned IDs refer to the input manifest.
    """
    result = {
        "status": "unsupported",
        "route": None,
        "overlays": [],
        "missing_facts": [],
    }
    for route in manifest["routes"]:
        matched, missing = _match(route["when"], target)
        if matched is False:
            continue
        if matched is None:
            result.update(status="unresolved", missing_facts=sorted(missing))
            return result

        result["route"] = route["id"]
        overlays = []
        for overlay in route.get("overlays", []):
            overlay_match, overlay_missing = _match(overlay["when"], target)
            missing.update(overlay_missing)
            if overlay_match is True:
                overlays.append(overlay["id"])
        if missing:
            result.update(status="unresolved", missing_facts=sorted(missing))
        else:
            result.update(status="selected", overlays=overlays)
        return result
    return result
