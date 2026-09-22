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

## Ryōribon capture and restore

Run `python -B tests/generation_rehearsal.py create`. Substitute its printed path
for `<run>` below. Keep the helper and evaluator snapshots out of agent context.

Give a fresh agent this request:

> Use `<run>/plugin/skills/ryoribon/SKILL.md` to create `<run>/oma-rehearsal` from
> Palette in `<run>/source-home`. This is an Omarchy/Linux source, profile `travel`.
> Capture dark theme and font size 14 as shared preferences; restrict eDP-1 to travel.
> Installation information and redistributable source are in `<run>/distribution`.
> Read only these inputs, the plugin, and runtime tooling. Write only the new
> repository and temporary request/report files under `<run>`. Do not restore,
> stage, commit, or change the source. Use `PYTHONDONTWRITEBYTECODE=1`.

Run `python -B tests/generation_rehearsal.py check <run> capture`. Review its
manifest validation and planning results; external prerequisites must not be
reported as verified without evidence. Check that instructions are concise and
contain the actual installation, configuration, and readiness steps.

Give a second fresh agent this request:

> Use `<run>/plugin/skills/shokunin/SKILL.md` to restore Palette from
> `<run>/oma-rehearsal` into two disposable target homes: `<run>/travel-home`
> (profile `travel`) and `<run>/generic-home` (no profile). Both are Omarchy/Linux
> rehearsal targets using the host's Python runtime, which you may inspect.
> Read only the plugin, generated repository, targets, and runtime tooling—not
> the original source or distribution. Write only the target homes and temporary
> request/plan/progress files under `<run>`. Preserve unrelated settings. Do not
> modify recipes or real machine configuration. Use `PYTHONDONTWRITEBYTECODE=1`.

Run `python -B tests/generation_rehearsal.py check <run> restore`. This checks the
application, preferences, overlay isolation, preservation of unrelated settings,
and unchanged source and recipe files. Review the agent's report as well.

## Change capture and restore

After a successful Ryōribon rehearsal, run
`python -B tests/change_capture_rehearsal.py create <generation-run>`.
It creates a separate run using the generated recipe, with a changed source
preference, an unrelated repository edit, and temporary app state.
Keep the helper and evaluator snapshots out of agent context.

Give a fresh agent this request, substituting the new run path:

> Use `<run>/plugin/skills/change-capture/SKILL.md` to capture my Palette font-size
> change from 14 to 16 in `<run>/source-home/.config/palette/settings.json` into
> `<run>/oma`. Target: Omarchy/Linux, profile `travel`. Preserve existing repository
> edits. Read only the plugin, repository, source home, and runtime tooling; write
> only the recipe and temporary reports under `<run>`. Do not deploy, change the
> source, stage, or commit. Use `PYTHONDONTWRITEBYTECODE=1`.

Run `python -B tests/change_capture_rehearsal.py check <run> capture`.
Review the documentation diff too: readiness checks must reflect the resulting
recipe without adding capture history or duplicating shared instructions.

Give a second fresh agent the Shokunin restore request above, using `<run>/oma`
as the repository and this run's two target homes. Keep the source home and
evaluator snapshots out of its context. Then run
`python -B tests/change_capture_rehearsal.py check <run> restore`.
The updated preference must survive restoration to both profiles while the
machine overlay, unrelated settings, and prior repository edit are preserved.

For a catch-up variant, create another run and replace the capture request with:

> I've changed a few things since my last capture. Catch up Palette in `<run>/oma`
> with `<run>/source-home`. Target: Omarchy/Linux, profile `travel`. Preserve my
> existing repository edits.

Use the same isolation limits. Have the evaluator answer any intent questions;
keep these answers out of the initial agent context: font size 16 is intentional
and shared, while the repository's light theme is a separate edit to preserve.
Check that the agent resolves those differences before changing uncertain values,
excludes temporary state, and keeps the travel display setting. Then run the same
capture check and independent restore phase.
