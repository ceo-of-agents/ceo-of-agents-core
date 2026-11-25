# Unreleased: warn when the plugin is installed in more than one scope

The version check at session start now also reads the installed scopes and versions of the plugin (`claude plugin list --json`). When the plugin is installed in more than one scope that applies to this hq folder, it adds one line to the status: each scope with its version, the version loaded here, and the commands to remove or update each extra copy. With a single install, or when the command is not available, it says nothing.

Why: a second copy at another scope can stay on an older version and be the one that loads, and nothing told the CEO.

No schema version changes: `org.yaml` stays `org/5`, `company/state.md` stays `state/1`.

## Edits

None in the hq. The change lives in the plugin (`skills/hq-version/SKILL.md`, `skills/session-start/SKILL.md`, `docs/design.md`). It is a report only: no A item is added.

Plain summary for the CEO: "At session start, your chief of staff now tells you in one line when the plugin is installed twice, at different scopes, and how to remove the extra copy."

## Check after applying

- Nothing to check in the hq files: no file changes.
