---
name: change-capture
description: Capture intentional machine configuration changes in an explicitly selected Oma-repository after a known edit, or compare existing ippin with the machine when asked to catch up. Excludes ordinary project-code edits.
---

# Change capture

Update the owning ippin alongside a configuration change. Capture flows from the machine into the repository; it does not deploy repository settings back to the machine.

Establish the absolute Oma-repository path and the target's OS, environment, and
machine profile from the request or explicit capture configuration. Resolve missing
facts before changing repository files; an explicitly unselected machine profile
is valid. Do not infer the target repository from this skill's location or the
agent's current project. Read the repository's `AGENTS.md`, manifest specification,
and affected ippin instructions.

## After a known edit

1. Use the file and diff already available from the task. Find its repository counterpart by the path beneath `home/`; include hidden files in searches. For example, `~/.config/hypr/apps/chrome.lua` maps to `ippin/chrome/omarchy/home/.config/hypr/apps/chrome.lua`.
2. Apply only the intentional change to that counterpart, preserving existing repository edits. Copy the whole file only when the remaining contents match. Follow the recipe’s merge or replacement rules: for partial overlays, update the layer that owns the changed key; for whole-file replacements, update the selected replacement. Keep hardware values out of the shared baseline. Consult the manifest and instructions when ownership is unclear.
3. Reuse checks already performed for the live edit. Check the repository diff and run only additional validation needed by the captured change; a routine edit needs no broad inventory or restore rehearsal. Search the repository for existing checks and descriptions of the changed preference and keep them consistent. Add setup instructions only if restoration requirements change.

For a component without an ippin, use [Ryōribon](../ryoribon/SKILL.md) within the authorized capture scope. If ownership remains unclear, report the uncaptured item for follow-up.

## Catch up when requested

Compare the requested ippin's managed files with their live counterparts, applying the selected machine overlays when interpreting differences. Expand beyond managed files only for preferences relevant to the request. Missing files and differences are evidence to review, not automatic deletions or proof of user intent.

Separate intentional preferences from package defaults, generated state, credentials, and settings managed elsewhere, such as VS Code Settings Sync. Preserve app ownership when extracting changes from combined live files. Capture the confirmed changes using the same focused checks as above.

Follow the selected repository's commit/push policy and the user's authorization;
otherwise leave changes unstaged and uncommitted. Briefly report what was captured and anything deferred; leave unrelated files and staged changes alone.
