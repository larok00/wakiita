# Contributions

- Keep documentation concise, describe the current design,
  and distinguish planned behavior from implemented functionality.
- Write for the reader: manuals explain the user experience; skills guide
  agent decisions; tool references explain invocation and results.
  Do not repeat an algorithm in instructions when the tool already implements it.
- Keep each rule with its owner and link rather than duplicate.
  When behavior moves, remove its explanation from the former owner.
  Keep investigation history and test reports out of setup instructions.
- Follow existing conventions. Add abstractions, files, or instructions
  only when a concrete use requires them; keep future ideas in issues.
- Work in small, reviewable steps. Propose substantive README and manual
  changes before editing, preserving the author's wording and voice.
- For workflow changes, use the existing test guide to check observable
  behavior. Prefer a focused correction over accumulating rules for
  every failed example.

# Git

- Commits should be atomic: include only one
  coherent change or fix, and do not mix unrelated work.
- Commit messages should be succinct
  and describe the change being made.

# Setup

On the Omarchy machine running Wakiita's tools,
check `python --version` and `uv --version`.
If either is missing, use `omarchy install dev-env python`.
Record any existing global mise Python selection
before running it and restore that selection afterward;
the installer selects the latest Python globally.
Verify the required tools are available,
then run Python scripts with `uv run` to
provision their declared dependencies.
Execution targets do not need these tools
unless their selected ippin require them.

For development contributions, follow [Contributing](README.md#contributing).
