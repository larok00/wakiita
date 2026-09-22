---
name: shokunin
description: Plan a setup from an Oma-repository when asked to serve a meal, restore a setup, or work out installation prerequisites. Currently planning only; does not execute the setup.
---

# Shokunin

Produce a read-only setup plan. Do not run installation commands, sign in to apps,
or edit the target machine or Oma-repository as part of this workflow.

Establish the absolute Oma-repository path, requested components, and intended
target. Read its `AGENTS.md` and component overviews to map the user's request to
ippin IDs. Inspect the target when available; do not substitute the host running
the planner for a different intended target. Use an established machine profile,
not a guess from the hostname. Gather missing preferences together only when they
affect the setup, explaining the practical choice and recommending an option
where the repository gives a basis.

Use the bundled [planning command](../../docs/planning-command.md), resolving its
paths from this skill's plugin directory. Write the request in a temporary
location outside the Oma-repository. Include existing readiness only when verified
for this target against component instructions; otherwise let the plan include
its prerequisites. Never include credentials in the request or evidence.

Run the command and inspect its JSON result, including on a nonzero exit. Resolve
missing facts by inspection and provider choices from established preferences
before asking the user. Re-run when inputs change. For broken recipes or choices
that remain unresolved, explain the concrete blocker; do not silently rewrite
recipes, invent evidence, or keep retrying unchanged input.

Read the selected component and route/overlay instructions to explain what the
plan entails without executing them. Summarize requested setup, added prerequisites,
installation order, and steps needing user involvement in plain language. Distinguish
planned work from verified existing readiness and identify unresolved issues.
Finish with the plan; execution is not yet implemented by this skill.
