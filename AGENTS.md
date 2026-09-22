# Style

- Keep documentation concise, describe the current design,
  and distinguish planned behavior from implemented functionality.

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
