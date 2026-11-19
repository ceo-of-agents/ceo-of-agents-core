# Unreleased: parent and child items in the pending list and the todo list

The pending list ("Waiting on the CEO") and the todo list were flat: they could not show which items belong to the same piece of work, which item blocks another, or when a group is done. Now an item can have child items, one level deep, indented by two spaces under it. A child has its own code, urgency, kind and since date, and the CEO answers it by that code; approving a parent never approves its children. The chief of staff (CoS) carries out a parent's approved action only once all its children are done or dropped. When a parent's own ask is answered first, its line stays as the group's head with the new kind `{wait}` and goes with its last child. A decision can open follow-ups as children of its D line. Summaries count the lines that ask something (`ok`, `do`, `decide`), children included, and list each child after its parent. `company/todo.md` can nest tasks the same way, in `## Open` only.

No schema version changes: `company/state.md` stays `state/1` and `company/todo.md` stays `todo/1`. The change is additive: a list without children is unchanged. The new `{wait}` kind and the indented child lines are valid only from this version, so the check script of an older plugin reports them. `scripts/check-boot-set.sh` now reports a new group, `pending lines nested wrongly`.

In the hq the template placeholders are already rendered, so each edit names a fragment without placeholders. Where a fragment is not found exactly (the CEO edited that part), do not guess: show the CEO the current text and the intended result, and ask. Where the text of an edit is already present, skip that edit.

## 1. `CLAUDE.md`

Section "The CEO pending list". After the bullet that starts `- Every line carries its kind after the urgency:`, add:

```
- Subtasks: a child item is indented two spaces under its parent, one level deep, with its own code, urgency and kind. Approving a parent never approves its children; once its own ask is answered it turns `{wait}` and goes with its last child (plugin's `schemas/state.md`).
```

## 2. `operating-model.md`

Section "The pending list and codes". After the paragraph that starts `Open work the CoS holds instead of routing it`, add this paragraph, with a blank line before it:

```
An item can have child items, indented under it one level deep: the asks it is made of, or the follow-ups a decision opens. Each child keeps its own code and you answer it by that code; approving a parent never approves its children. A parent stays until its children are done; when its own part is answered first, it shows `{wait}`. Your todo list can nest tasks the same way.
```

## 3. Existing items

Existing items are not regrouped automatically. The CoS may propose grouping related items once, and moves an item under a parent only with the CEO's OK, keeping its code and since date.

Plain summary for the CEO: "Related items in your pending list and todo list can now be grouped under one parent; you still approve each by its own code."

## Check after applying

- `CLAUDE.md` holds the new bullet once, in "The CEO pending list", and its size stays within the budget of `schemas/boot-set.md` (`wc -c CLAUDE.md`, at most 24,576 bytes). If it is over, report it as the boot check does.
- `operating-model.md` holds the new paragraph once, in "The pending list and codes".
- `sh "${CLAUDE_PLUGIN_ROOT}/scripts/check-boot-set.sh"` reports `pending lines nested wrongly: 0`.
