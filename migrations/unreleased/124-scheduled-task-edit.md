# Unreleased: the chief of staff can edit an existing scheduled task

The chief of staff now knows what to do when the CEO asks to change the times of a scheduled task set up in their Claude app: list the existing tasks, edit the right one in place with the scheduling tool the session has (never a duplicate), and, when the session has no scheduling tool, say so in one sentence and give the steps in the app. Before, the hq only said "No scheduled automation and no hooks", which read as a ban, and the chief of staff told the CEO to use the Claude interface.

Why: the line meant that the framework runs nothing on a schedule, not that the CEO's own scheduled tasks are off limits. The scheduling tools differ by surface (the desktop app can update a task; a session-scoped loop can only be deleted and recreated).

No schema version changes: `org.yaml` stays `org/5`, `company/state.md` stays `state/1`.

## Edits

### `CLAUDE.md`

In the section "Session start (always)", replace this line:

```
No scheduled automation and no hooks: everything runs when the CEO opens a session.
```

with:

```
The framework itself runs nothing on a schedule and adds no hooks: its procedures run when the CEO opens a session. A scheduled task the CEO sets up in their Claude app is the CEO's own. When asked to change one, list the existing tasks, find it and edit it in place with the scheduling tool the session has (update, never a duplicate; a session-scoped loop has no update: delete and recreate it). If the session has no scheduling tool, say so in one sentence and give the steps in plain words: Code tab, "Scheduled" in the sidebar, open the task, Edit (pencil), change the schedule, save.
```

The "Rhythms" line (`Weekly brief, reviews and batched approvals run on demand only, when the CEO asks. No scheduled automation, no hooks.`) stays as it is.

### `operating-model.md`

In the section "Rhythms (on demand only)", replace this line:

```
No scheduled automation, no hooks. Nothing runs unless the CEO opens a session.
```

with:

```
No scheduled automation, no hooks: the framework runs nothing unless the CEO opens a session. A scheduled task you set up in your Claude app is yours; ask the CoS to change its times and it edits that task in place, or, if the session cannot, tells you the steps in the app (Code tab, "Scheduled" in the sidebar, open the task, Edit, change the schedule, save).
```

Plain summary for the CEO: "If you ask me to change the times of a scheduled task you set up, I find that task and edit it in place. If this session cannot edit it, I tell you the steps in the Claude app."

## Check after applying

- `CLAUDE.md` no longer contains the line `No scheduled automation and no hooks: everything runs when the CEO opens a session.` and contains `edit it in place`.
- `operating-model.md` contains `edits that task in place`.
