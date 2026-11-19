# Schema: company/todo.md (`todo/1`)

An optional list of the work the CEO owns personally: reply to someone, follow up on a review, chase an answer. It is not the pending list. "Waiting on the CEO" in `company/state.md` holds what the org needs from the CEO (A and D items); this file holds what the CEO has to do on their own account (T items). A reader, such as a front-end, may show both side by side.

The file is opt-in. An hq without `company/todo.md` behaves as before: nothing reads it, nothing creates it, and no check reports its absence. The chief of staff (CoS) creates it from `templates/instance/company/todo.md` the first time the CEO asks to track a task. Owner: the CoS. Departments never edit it; they report in a handoff.

It is not in the boot set (`schemas/boot-set.md`): the session start does not read it, so it costs nothing until it is needed.

## Frontmatter (all fields required)

| Field | Type | Rule |
|---|---|---|
| `schema` | string | Exactly `todo/1` |
| `last_updated` | date | `YYYY-MM-DD`; updated whenever a line is added, changed or moved |
| `next_todo` | integer | Next unused `T` number (starts at 1) |

## Body

Optional H1 title line `# CEO todo list` directly after the frontmatter. Then exactly these H2 headings, in this order, none missing, none added:

1. `## Open`
2. `## Done (last 7 days)`

An empty section body is the single line `- none`.

## Line formats

Open:
`- ACME-T3 [high]: <task> (since YYYY-MM-DD)`
`- ACME-T3 [high]: <task>. Status: <where it stands> (since YYYY-MM-DD)`

Open child (under a parent task):
`  - ACME-T6 [normal]: <task> (since YYYY-MM-DD)`

Done:
`- ACME-T2 [normal]: <task> (done YYYY-MM-DD)`

- A child line is indented by exactly two spaces under its parent or a sibling, one level only: a child has no children. Children exist only in Open; Done is flat.

- The task is one plain sentence: what the CEO does, with the person, place or link it needs.
- `Status:` is optional. It says where the task stands in a few words (for example `waiting on Legal`, `draft sent`), and is rewritten, not appended to, when it changes.
- `since` is the date the item was added; `done` is the date the CEO finished it.
- Every line stays at most 300 characters. A task that needs more keeps one line and links a note.
- T lines carry no kind in braces: a T item is always the CEO's own work.

## Codes

- `<ORG_ID>-T<n>`: a task the CEO owns. Numbers are monotonic per org and never reused, even after an item is removed, like A and D codes (`schemas/state.md`). The next number lives in `next_todo`; increment it when a code is issued.
- Urgency is `high`, `normal` or `low`.
- T codes never go in `company/state.md`, and A or D codes never go in this file.

## Lifecycle

- **Add.** When the CEO names a task they will do themselves, add an Open line with the next code and today's `since`, increment `next_todo`, set `last_updated`. A task that is part of an open task goes under it as a child.
- **Update.** When the CEO reports progress, rewrite its `Status:`.
- **Done.** When the CEO says the task is done ("ACME-T3 done"), move its line to `## Done (last 7 days)`, drop the `Status:` and replace `(since ...)` with `(done YYYY-MM-DD)`. A done child moves there as a top-level line. A parent moves to Done only when it has no open children; if the CEO says a parent is done while children are open, ask once whether those are done too or dropped.
- **Prune.** Whenever the file is edited, delete Done lines whose `done` date is more than 7 days before today. Git history keeps them.
- **Drop.** A task the CEO no longer wants is deleted from Open without moving to Done. Dropping a parent while children are open follows the same rule as Done: ask once whether the children are done too or dropped.
- **Promote.** A task that turns out to need the org (an approval, a decision) becomes an A or D item in `company/state.md` with its own new code, and its T line is deleted.

## Minimal valid example

```markdown
---
schema: todo/1
last_updated: 2026-01-15
next_todo: 5
---

# CEO todo list

## Open
- ACME-T3 [high]: Review the vendor contract. Status: waiting on Legal (since 2026-01-10)
- ACME-T4 [normal]: Reply to the beta tester about the export bug (since 2026-01-14)

## Done (last 7 days)
- ACME-T2 [low]: Renew the domain (done 2026-01-12)
```

## Validation checklist

- Frontmatter has the three fields; `schema` is `todo/1`.
- The two H2 headings exist, spelled exactly, in the stated order, with no extra H2.
- No section is empty: use `- none`.
- Every Open line follows `- <ORG_ID>-T<n> [high|normal|low]: <task> (since YYYY-MM-DD)`, with an optional `. Status: <status>` before the date; every Done line ends with `(done YYYY-MM-DD)`. `scripts/check-boot-set.sh` in the plugin reports the lines that do not, when the file exists.
- A child line (two spaces, `- `, the same format with `since`) sits only in Open, right under a top-level Open item; an orphan child, any other indentation and any indented line in Done are reported by the script. T items have no kinds, so there is no `wait` here.
- Every T number is less than `next_todo`, and no code appears twice in the file.

The script checks only the item lines of the two sections (code, urgency, text, the `since` or `done` date, and the two-space indent of a child under a top-level Open item). It does not check the frontmatter, the headings and their order, `- none` in an empty section, the 300-character line limit, the numbers against `next_todo`, or duplicate codes: the CoS keeps those by the rules above.
