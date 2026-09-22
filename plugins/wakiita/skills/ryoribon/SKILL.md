---
name: ryoribon
description: Create an Oma-repository or add a reproducible ippin from an existing Omarchy setup. Use when asked to learn a tsukurikata or capture a new component; existing recipe maintenance belongs to change-capture.
---

# Ryōribon

Turn one component of an existing setup into a recipe another agent can restore.
Inspect the source machine without changing it. For a broad request, identify a
small first component and agree on its intended preferences before expanding.
Use the user's stated choices and available configuration rather than asking a
technical questionnaire.

Establish the destination repository, source target, and machine profile (or an
explicitly unselected profile). For a new repository, agree on the local path and
`oma-<name>` name; do not infer a profile from that name or the hostname. For an
existing repository, read its instructions and preserve its conventions, recipes,
and uncommitted work, including routes for other operating systems.

Read the bundled [manifest specification](../../docs/ippin-spec.md). In a new
repository, include its schema and specification under `docs/`, a brief README,
and root `AGENTS.md` linking to the specification. Keep personal recipes usable
without the Wakiita plugin; do not copy its planner or skills into the repository.
Do not overwrite an existing repository's format to match a newer bundled schema;
report incompatible formats before writing recipes.

Inspect only the component's relevant configuration and installation sources.
Distinguish intended preferences from defaults, generated state, credentials, and
settings already managed by account sync. Keep credentials and session data out
of captured files and reports. Resolve uncertainty about personal preferences
with the user; investigate technical facts yourself. Do not treat everything
present on the source machine as something to reproduce.

Create `ippin/<id>/ippin.json`, a concise human README, and component-specific
`AGENTS.md`. Describe only the current component setup and checks. Put investigation
findings and test limitations in the capture report, not the recipe. Keep shared
routing and readiness rules in the specification rather than repeating them in
each component. Include the config and supporting files needed for restoration. Put
shared preferences in the route's baseline and machine-specific values in a
matching overlay when needed. Use the destination repository's layout if present;
otherwise mirror home-relative paths beneath `<route>/home/`. State how to apply
partial configurations without discarding unrelated target settings.

Record a supported installation method from inspected local sources or primary
documentation, then configuration, any required sign-in, and concrete readiness
checks. Include a manifest command when appropriate; UI or agent-guided setup can
live in instructions. Do not invent support for unexamined platforms, dependency
outcomes, or portable paths to source-machine files. Reuse existing prerequisite
ippin; describe necessary external readiness checks if no provider exists.

Use the bundled [planning command](../../docs/planning-command.md) to validate the
repository and plan the new ippin for its supported target and relevant profiles.
Resolve recipe errors, and report genuine missing prerequisites or user choices.
Do not label a prerequisite verified merely to make the plan pass. Review whether
the instructions cover a fresh target, not just the already-configured source.

Report what was captured, what was deliberately left out, and which checks passed.
Distinguish a valid plan from a tested restore; use a disposable restore rehearsal
when available and authorized. Leave changes unstaged and uncommitted unless the
user requests otherwise. For later edits to an existing recipe, use
[change capture](../change-capture/SKILL.md).
