# Unreleased: close and reopen an org

Folded into the migration of the next release (see migrations/README.md). Issue: #59.

An org can end: a project stops, a company winds down. This change gives the framework a notion of a closed org:

- **A status in `org.yaml`.** The new optional key `org.status` is `open` or `closed`. Absent means `open`, so an hq that is not migrated keeps working as before.
- **A new hidden skill, `close-org`.** On the CEO's request, the chief of staff lists what is still open (pending items, open decision cards, initiatives that are not closed, unprocessed handoff notes), asks the CEO to confirm and to say where each item goes (dropped, moved elsewhere, or left as it is, frozen), writes a closing decision record and sets `org.status: closed`. Reopening is a new decision record that sets it back to `open`. Nothing is ever deleted, moved or archived by closing.
- **A closed org is read-only.** The session start says so in one line and gives the status without writing anything; the chief of staff takes no new work and the `intake` skill frames and routes nothing, until the CEO reopens the org. A holding marks a closed company in its portfolio view and leaves its pending items out, since they are frozen.

No schema version change: `org.yaml` stays `org/5` (`org.status` is optional, absent means open) and `company/state.md` stays `state/1`.

Apply the sections below in order. In the hq the template placeholders are already rendered, so each edit names a fragment without placeholders. Where a fragment is not found exactly (the CEO edited that part), do not guess: show the CEO the current text and the intended result, and ask.

## Edits

### `org.yaml`

Under `org:`, add this line right after the `purpose:` line (the value of `purpose:` stays as it is; keep the same indentation, two spaces):

```
  status: open                  # open | closed; closed = read-only, see the close-org skill
```

If the key is already there, leave it as it is.

### `CLAUDE.md`

Three additions. Each is new text; nothing existing changes.

1. Section "Session start (always)". After the line:

```
No scheduled automation and no hooks: everything runs when the CEO opens a session.
```

add a blank line and this paragraph:

```
When `org.status` in `org.yaml` is `closed`, the org is read-only for you and the departments: answer questions from the hq, take no new work and write nothing until the CEO reopens it (`close-org` skill).
```

2. Section "What the CEO says and what you do". Right before the row that starts `| Anything else unclear |`, add this row:

```
| "Close the org" / "reopen the org" | Use the `close-org` skill: it lists what is still open, asks for confirmation, writes the decision record and sets `org.status`. Nothing is deleted. |
```

3. Section "Skills available". After the line:

```
- `initiatives`: open, update, close and archive an initiative folder.
```

add this line:

```
- `close-org`: close the org (read-only from then on) or reopen it, each through a decision record.
```

The three additions are about 500 bytes together. `CLAUDE.md` is part of the boot set (budget 24,576 bytes, `schemas/boot-set.md`): the session start reports it when it ends up over.

### `operating-model.md`

1. Right before the heading `## The pending list and codes`, add this section (the heading, a blank line, the paragraph, a blank line):

```
## Closing the org

An org can end. When the CEO asks, the CoS lists what is still open, asks for confirmation and for where each item goes, writes a closing decision record and sets `org.status: closed` in `org.yaml`. A closed org is read-only: the CoS answers from the hq and takes no new work until the CEO reopens it, which is a new decision record. Nothing is ever deleted.
```

2. Section "Plugin requirement". Replace:

```
`departments`, `product-repos`, `initiatives`) come from it.
```

with:

```
`departments`, `product-repos`, `initiatives`, `close-org`) come from it.
```

## Plugin-only changes (no hq edit)

- New hidden skill `close-org`: the close procedure (list, confirm, closing record, `org.status: closed`, commit with notice) and the reopen procedure (reopening record, `org.status: open`).
- `session-start`: in a closed org the status opens with one line (closed since the date of the closing record, read-only, the CEO can say "reopen") and every step that writes or starts work is skipped. For a holding, step 7 now reads `org.purpose` and `org.status` of each company and marks a closed one.
- `intake`: in a closed org it frames and routes no new work and leaves handoff notes unprocessed.
- `portfolio-brief`: reads `org.purpose` and `org.status` (and no other key) of each company; a closed company gets a `closed` mark in its Organizations line and its pending items are left out.

## Summary line for the CEO

Added: an org can now be closed and reopened, each through a decision record. A closed org is read-only and nothing is deleted. Your org stays open; say "close the org" only when it really ends.

## Check after applying

- `grep -c "^  status: open" org.yaml` prints 1.
- `python3 -c "import yaml; yaml.safe_load(open('org.yaml'))"` runs without an error (else read the file and check the indentation by eye).
- `grep -c "When \`org.status\` in \`org.yaml\` is \`closed\`" CLAUDE.md` prints 1.
- `grep -c "^| \"Close the org\" / \"reopen the org\"" CLAUDE.md` prints 1.
- `grep -c "^- \`close-org\`:" CLAUDE.md` prints 1.
- `grep -c "^## Closing the org" operating-model.md` prints 1; `grep -c "\`initiatives\`, \`close-org\`) come from it" operating-model.md` prints 1.
- `git status --short` shows only `org.yaml`, `CLAUDE.md` and `operating-model.md`.
