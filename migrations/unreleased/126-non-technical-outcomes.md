# Unreleased: non-technical CEO hears outcomes, not tools

With `ceo.profile: non-technical`, the chief of staff and every department now talk about outcomes, not tools. Routine tracking writes (issues, labels, comments, the roadmap board) are no longer narrated in chat: they stay recorded in the hq, and when a mention helps the team says "noted for the team". GitHub is named only when the CEO must act there or asks about it, with one plain sentence on what it is. The technical profile does not change.

Why: a non-technical CEO does not need the mechanics of the tracker; naming issues, labels and boards in chat is noise.

No schema version changes: `org.yaml` stays `org/5`, `company/state.md` stays `state/1`. The comment on `ceo.profile` in `schemas/org.yaml` changes only in the plugin.

Plain summary for the CEO: "From now on, I and the departments talk to you about results, not tools: the routine bookkeeping of tasks stays in the files, and I name GitHub only when you need to do something there."

## Edits

In `CLAUDE.md`, section "How to talk to the CEO", replace the bullet that starts "- Follow `ceo.profile` in `org.yaml`." with:

New text:

```
- Follow `ceo.profile` in `org.yaml`. With `non-technical`, you and the departments talk about outcomes, not tools, in plain words: a commit is "saved", a push "sent", a pull request "a proposed change", a merge "accepted"; a connector is named by its service ("Google Drive"), never by its MCP server. Do not narrate routine tracking (issues, labels, comments, the roadmap board): it is recorded in hq; if a mention helps, say "noted for the team". Name GitHub only when the CEO must act there or asks, with one plain sentence on what it is (for example "GitHub, the site where the team's code and task list live"). Files keep their usual format and terms. The CEO can change the profile by asking: record it with `record-decision` and edit `ceo.profile`.
```

Old text (the part that changes; the rest of the bullet is identical):

```
you and the departments chat in plain words: a commit is "saved", a push "sent to GitHub", a pull request "a proposed change", a merge "accepted"; a connector is named by its service ("Google Drive"), never by its MCP server; GitHub keeps its name.
```

In `CLAUDE.md`, section "Product repos and roadmap", bullet "Tracking writes are free": `do them and mention them in one line.` becomes `do them and mention them in one line (with a non-technical CEO, not at all: see How to talk to the CEO).` Skip this edit if the hq has no product repos section.

For each department agent file the hq holds (`.claude/agents/<agent>.md`, except `reader.md` and `worker.md`): add this sentence at the end of the paragraph that holds the voice-file rule, right after `if it exists, and follow it.`, separated by one space:

```
If `ceo.profile` in `org.yaml` is `non-technical`, report outcomes in plain words and do not narrate routine GitHub tracking (see "How to talk to the CEO" in CLAUDE.md).
```

## Check after applying

- `CLAUDE.md` "How to talk to the CEO" has the new `ceo.profile` bullet (it contains "noted for the team" and `never by its MCP server`).
- Each department agent file in `.claude/agents/` (not `reader.md`, `worker.md`) contains the `non-technical` sentence once.
