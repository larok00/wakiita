# Ippin manifest specification

The [JSON Schema](ippin.schema.json) defines all accepted keys, types, and values.

## Structure

Each `ippin/<id>/` contains:

- `ippin.json`: identity, provided outcomes, and ordered setup routes.
- `README.md`: brief human overview and supported platforms.
- `AGENTS.md`: component-specific setup, verification, and maintenance instructions.

Use `"$schema": "../../docs/ippin.schema.json"` for editor support. The manifest's `id` must match its folder name.

## Route semantics

- **`when`** selects the target. All supplied conditions must match exactly; omitted keys impose no restriction and `{}` matches any target. Resolve unknown target values before selecting a fallback. Explicitly planned environments or browsers can match before installation.
- **`requires`** lists outcomes that must all be ready before execution. They may come from other ippin or verified external prerequisites; unresolved dependencies are not satisfied.
- **`routes`** are alternatives in preference order. Select the first route whose `when` conditions match. Its requirements, including matching-overlay requirements, must be satisfied before execution. Missing prerequisites block that route; they do not select a later route. A failed installation requires diagnosis, not automatic fallback.
- **`command`** is an optional executable-and-arguments array, with no implicit shell expansion. Resolve relative executable paths from the ippin folder and bare command names through PATH. Follow the instructions to decide whether execution is needed.
- **`instructions`** resolves within the ippin folder. **`interactive`** indicates whether setup or verification, including matching overlays, inherently requires a person. Agent-operated terminal prompts and browser/UI actions do not count.
- **`provides`** lists target-scoped outcomes, such as `chatgpt.ready`. Every route must verify all of them, with the same meaning across routes. Verify outcomes after the route and all matching overlays succeed. Installation success alone is insufficient.

If a required check cannot be automated, request human verification and leave it pending until confirmed.

No matching route means unsupported; unavailable prerequisites mean blocked.

## Overlays

- A route may contain `overlays`, each with `id`, `when`, `instructions`, and optional `requires`. Apply every matching overlay after the selected route, in array order; overlays of other routes never run. Overlay IDs must be unique within their route.
- Overlay `when` uses the same exact-match rules as routes. `machine` is an optional named configuration profile, such as `xps`, explicitly selected or established for the target—not a hostname or an automatic match for all hardware of that model. Resolve unknown facts before deciding which overlays apply; an explicitly unselected machine profile matches no machine-specific overlay.
- Instruction paths are relative to the ippin folder, including overlay paths. Later overlays may override earlier settings only as documented; ordering is local to this route, not across ippin.
- Overlay `requires` defaults to an empty list. After selecting the route, combine its requirements with those of every matching overlay; all must be ready before route execution. Unmatched overlays add no dependencies.
- Overlays have no separate commands or outcomes. An overlay failure leaves the ippin incomplete; it does not select a fallback route. Changing profiles requires reconciling previously applied settings—skipping an overlay does not undo it.

## Creating or editing

1. Define the component's purpose and readiness checks in its README and AGENTS instructions.
2. Add documented setup routes to `ippin.json`, placing specific preferred routes before supported general fallbacks.
3. Validate against the schema. Also check unique component, route, and per-route overlay IDs, instruction-file existence and containment, dependency providers and cycles, and behavior for matching and nonmatching targets. These checks are not enforced by JSON Schema.
4. Update references when renaming IDs or outcomes. When changing the format, update the schema and this guide together; incompatible changes need a new `schemaVersion` and migration notes.

## Validation

From the Wakiita repository root, with `uv` available:

```bash
uv run scripts/validate-manifests.py /path/to/oma-repository
```

The validator checks schema, IDs, and instruction-file existence and containment.
It reports requirements without repository providers for review, including overlay
requirements. Target-specific selection, dependency cycles, installation, and
readiness remain separate checks. Add `--offline` to `uv run` when dependencies
are cached.
