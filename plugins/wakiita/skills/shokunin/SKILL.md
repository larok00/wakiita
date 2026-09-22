---
name: shokunin
description: Plan a setup from an Oma-repository and, when requested, execute and verify its ippin in dependency order. Use when asked to serve a meal, restore a component, or work out installation prerequisites.
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

## Execute the plan

Start only with a complete plan and confirmed target. Execute sequentially in the
returned order, including prerequisite ippin within the authorized setup scope.
Keep a brief progress record outside the Oma-repository with each ippin's status,
verification evidence, and partial changes. A shared prerequisite runs once.

Before each ippin, check that all effective requirements are satisfied: planned
providers must have completed verification, and external evidence must still hold
on this target. If a prerequisite failed, is waiting for the user, or is itself
blocked, mark this ippin blocked and continue independent work. Never treat a
structurally complete plan as evidence of readiness.

Follow the repository, component, selected route, and overlay instructions, using
[manifest semantics](../../docs/ippin-spec.md) for commands and ordering. Check the
current setup first and apply only the work still needed. If a manifest command is
needed, execute its argument array directly with the ippin directory as its working
directory; do not join it into a shell command. Apply matching overlays in order.

Verify every provided outcome against the final setup, including overlays. A zero
exit code is not proof of readiness. On failure or pending human verification,
stop that ippin, record the evidence and partial changes, and leave its outcomes
unavailable to dependants. Continue independent work where safe; if the failure
may affect shared state, recheck that state first. Do not switch routes, rewrite
recipes, or retry unchanged steps to force success.

If recipes or target facts change, replan before continuing. After interruption or
reboot, recheck relevant readiness rather than trusting the progress record alone.

Report completed and already-ready ippin, failures, steps waiting for the user,
and blocked dependants with their causes. An incomplete plan execution is not an
overall success. Keep credentials out of reports and leave the Oma-repository unchanged.
