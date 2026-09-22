# Tests

Run the deterministic tooling tests from the repository root:

```bash
uv run --with 'jsonschema>=4.18,<5' python -B -m unittest discover -s tests
```

## Shokunin rehearsal

Run `python -B tests/rehearsal.py create`. It prints a temporary directory containing
an installed-style plugin copy, an Oma-repository, and a disposable target.
The helper creates and checks fixtures; the agent performs setup.

Give a fresh agent this context, substituting the printed path for `<run>`:

> Use `<run>/plugin/skills/shokunin/SKILL.md` with `<run>/oma`. The target is Linux,
> machine profile `rehearsal`, and lives in the directory specified by the recipes.
> Read only that plugin, repository, and required runtime tooling. Writes may affect
> the disposable target and temporary request/plan/progress files under `<run>`.
> Keep the plugin and recipes unchanged. Use `PYTHONDONTWRITEBYTECODE=1` for Python
> tooling. Do not access real credentials or configure the real machine.

Send the requests below one at a time. After each response, run
`python -B tests/rehearsal.py check <run> <phase>` yourself. Keep the helper source,
expected results, and evaluator snapshots out of the agent's context.

| Phase | Request | Expected result |
| --- | --- | --- |
| `plan` | Plan setup of `b-good` and `z-independent` without executing. | Complete plan; target untouched. |
| `success` | Execute that setup, including its prerequisites. | Shared `base` configured once; both requested components verified, including the overlay. |
| `repeat` | Set up those same components again. | Already-ready setup; no target writes. |
| `failure` | Set up `d-transitive` and `z-later`, including prerequisites. | `a-failing` fails verification; `c-dependent` and `d-transitive` stay blocked; `z-later` completes. |

Also review the agent's report: a successful command must not conceal failed
verification, and blocked work must not be reported as completed. The file checks
do not establish that the agent understood or accurately reported the result.
Retain failed runs for diagnosis; temporary runs can be removed after review.
