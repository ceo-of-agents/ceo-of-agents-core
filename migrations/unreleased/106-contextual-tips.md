# Unreleased: contextual tips

## What changes and why

The plugin ships a file of contextual tips, `tips/tips.yaml` (format `tips/1`, `schemas/tips.md`). A tip is a short text plus a phrase the CEO can say to the chief of staff (CoS), shown only when its condition holds. At a normal session start, the `session-start` skill may add one tip as the last line of the status, at most once a day. A front end can read the same file.

`org.yaml` gets an optional `tips` key (`show`, `dismissed`) so the CEO can switch tips off or dismiss one. Absent means tips are on and nothing is dismissed.

## Schema

- `org.yaml` stays `org/5`. The new `tips` key is optional and absent by default.
- `tips/1` is new. It lives in the plugin, not in the hq.

## Exact edits

None required in an existing hq. The tips file is read from the installed plugin. The `tips` key is added to `org.yaml` only when the CEO asks to dismiss a tip or to turn tips off.

## Plain summary for the CEO

"From now on I may add one short tip at the end of the status, with a phrase you can say to me. Tell me if you do not want to see a tip again, or no tips at all."

## Check after applying

- `org.yaml` has no `tips` key, or a `tips` mapping with `show` as `true` or `false` and `dismissed` as a list of tip ids.
- Nothing else in the hq changed.
