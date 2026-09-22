---
name: shokunin
description: Plan a setup from an Oma-repository and, when requested, execute and verify one ippin whose prerequisites are ready. Use when asked to serve a meal, restore a component, or work out installation prerequisites.
---

# Shokunin

Plan the requested setup first. Planning alone makes no target changes; execute
only when the user has requested setup, within their authorized scope.

## Plan

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
For planning-only requests, finish here.

## Execute one ippin

Execution currently covers one requested ippin at a time, including its matching
overlays. If several were requested, present the plan and agree on one to execute.
Verify all of its effective prerequisites on the actual target, following component
instructions. If any remain unready, report what must be set up first; do not expand
into installing the dependency graph. Record verified prerequisites in the request
and rerun the planner before making changes. Continue only with a complete plan
and confirmed target; reread and replan if recipes or target facts have changed.

Follow the repository, component, selected route, and overlay instructions, using
[manifest semantics](../../docs/ippin-spec.md) for commands and ordering. Check the
current setup first and apply only the work still needed. If a manifest command is
needed, execute its argument array directly with the ippin directory as its working
directory; do not join it into a shell command. Apply matching overlays in order.

Verify every provided outcome against the final setup, including overlays. A zero
exit code is not proof of readiness. Stop on failure or pending human verification,
report the evidence and any partial changes, and leave the ippin incomplete. Do not
switch routes, rewrite recipes, or retry unchanged steps to force success.

Report whether the ippin completed, was already ready, failed verification or setup,
or is waiting for the user, with the checks supporting that result. Keep credentials
out of reports and leave the Oma-repository unchanged.
