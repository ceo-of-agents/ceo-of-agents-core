# Unreleased: optional categories in the CEO todo list

The CEO todo list (`company/todo.md`) can now group tasks by category, so it reads like a board by type (for example admin, people, follow-up). A category is one optional `#tag` at the end of a task, and the CEO's set lives in an optional `categories:` list in the file's frontmatter. The chief of staff suggests a short default set the first time the CEO asks, tags new tasks when the file has categories, and shows the list grouped by category on request.

Why: a flat list of personal tasks gets hard to scan; grouping by type lets the CEO see what kind of work is waiting.

No schema version changes: `company/todo.md` stays `todo/1` and existing files without categories stay valid. `org.yaml` and `company/state.md` are unchanged.

Plain summary for the CEO: "You can now sort your own tasks into categories, for example admin or people. Ask me and I suggest a few, and I can show your list grouped by category. Your current list does not change."

## Edits

None in the hq. The change lives in the plugin (`schemas/todo.md`, `skills/intake/SKILL.md`, `scripts/ci/check_boot_set.py`). An existing `company/todo.md` stays as it is; `scripts/check-boot-set.sh` accepts tagged lines.

## Check after applying

- Nothing to check in the hq files: no file changes.
