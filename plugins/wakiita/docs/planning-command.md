# Planning command

From the plugin directory:

```bash
uv run scripts/plan.py /path/to/oma-repository /path/to/request.json
```

Example request:

```json
{
  "requested": ["chrome"],
  "target": {"os": "linux", "environment": "omarchy", "machine": null}
}
```

Target keys and values follow manifest `when` conditions. Omitted facts are
unknown; `null` means explicitly absent, such as no machine profile. Each request
plans one target context; a Windows host and its WSL guest need separate plans.
The target can differ from the machine running the planner. Unknown facts block
selection only when they could affect the result.

Optional `provider_choices` maps outcome names to the ippin IDs chosen to provide
them, for example to resolve a reported ambiguity. Optional `external_outcomes`
maps outcomes to nonempty descriptions of evidence already verified on this
target, allowing those prerequisites to be satisfied without adding a provider.
It does not skip an explicitly requested ippin. Neither field is needed for an
unambiguous setup whose prerequisites are provided by the repository. Do not put
credentials in evidence.

The command validates manifests and instruction paths, then prints JSON with
selections, dependencies, issues, and an order. Exit codes are `0` for a complete
plan, `1` for invalid input, and `2` for unresolved planning issues. A complete
plan does not establish readiness or execute anything. Plans describe the current
working files; rerun after changing recipes or inputs.
