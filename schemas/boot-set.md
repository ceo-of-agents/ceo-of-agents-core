# Schema: the boot set and its budget

The boot set is what the chief of staff (CoS) reads at every session start, before any work. Every byte of it is paid in every session, so it has a budget. Everything else in the hq (analyses, notes, decision records, briefs) is read on demand and costs nothing until it is needed.

## Files and budgets

Every budget is in bytes, as `wc -c` counts them; the KiB figure (1 KiB = 1,024 bytes) is only a reading aid. A missing file counts as 0 bytes.

| File | Budget | What keeps it small |
|---|---|---|
| `CLAUDE.md` | 24 KiB (24,576 bytes) | Identity, gates, house rules and the map only; procedures live in plugin skills loaded on demand. A fresh render is 16 to 22 KiB, depending on purpose, departments and repos |
| `org.yaml` | 6 KiB (6,144 bytes) | Facts only; no prose |
| `company/vision.md` | 4 KiB (4,096 bytes) | Stable; changes only through a decision record |
| `company/strategy.md` | 4 KiB (4,096 bytes) | The stage and a short current focus |
| `company/state.md` | 8 KiB (8,192 bytes) | One line per item, each at most 300 characters; details in a linked note |
| `company/decision-queue.md` | 10 KiB (10,240 bytes) | Open cards only; answered cards leave with `record-decision` |
| `accounts.local.yaml` | 2 KiB (2,048 bytes) | Clone paths only |
| Whole boot set | 40 KiB (40,960 bytes) | The sum of the files above |

`inbox/` is listed at session start, not read; its notes are read by the `intake` skill and deleted once processed. Folder indexes (`departments/<id>/README.md`, `initiatives/README.md`) and initiative pages (`initiatives/<slug>/status.md`) are not in the boot set either: they are read when the work needs them. Nor is the optional CEO todo list, `company/todo.md` (`schemas/todo.md`): the skills that use it read it. An open initiative costs one line in `company/state.md`.

## Line budget

Every line of `company/state.md` is at most 300 characters (characters, not bytes), frontmatter included. An item that needs more keeps its one line (what, status, date) and links a note (for example `departments/<id>/YYYY-MM-DD-<slug>.md`) for the detail.

## Check

The plugin ships the check as a script, so the verdict never depends on which part of this file was read or on arithmetic done by hand:

```sh
sh "${CLAUDE_PLUGIN_ROOT}/scripts/check-boot-set.sh"
```

Run from the hq root (or pass the hq folder as the only argument). It prints, per file, its size, its budget and `ok` or `over by N bytes`; the same for the whole boot set; the lines of `company/state.md` over 300 characters (line number, length, first words); and the lines of "Waiting on the CEO" that lack a kind or do not follow the line format of `schemas/state.md`. When `company/todo.md` exists, it also prints its item lines that do not follow `schemas/todo.md` (the file has no size budget; when it is missing, nothing about it is printed). The last line is `verdict: ok` or `verdict: N issue(s)`. It changes nothing and always exits 0 on an hq. The budgets in the script and in the table above are the same numbers; a CI check in the plugin repo keeps them in sync.

The `session-start` skill runs the script and, when the verdict is not `ok`, adds one line to the status from its output: each offending file with its size and budget, and at most three long or malformed lines by their first words. It proposes moving the detail to linked notes (or fixing the pending lines) and does it only when the CEO agrees. It adds no A item and never trims on its own.

The `weekly-brief` skill runs the same script in its hygiene step, so a file over budget also shows up in the brief.

The budgets are guidance for the CoS, not limits enforced by a tool: an hq may be over budget for a while, and the status line says so until it is not.
