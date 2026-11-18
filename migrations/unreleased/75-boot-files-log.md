# Unreleased: rewrite summaries, keep history in a log, check at write time

Folded into the migration of the next release (see migrations/README.md). Issue: #75.

The boot-set budgets only reported, at the next session start. In practice the chief of staff (CoS) kept appending to the same `company/state.md` line, and an initiative's State or Next step turned into a work log. This change keeps the summaries small as they are written:

- **Summary vs log.** A line of `company/state.md`, and the State and Next step of an initiative's `status.md`, are rewritten to the current fact, never appended to. What they said before goes, verbatim and dated, to an append-only log outside the boot set: `company/log.md` (new in every hq, from the template) or `initiatives/<slug>/log.md` (created when first needed). Format: `schemas/log.md`, newest entry first, no frontmatter.
- **Initiative pages get a budget.** At most 4 KiB (4,096 bytes) per `status.md` and 300 characters per line. `scripts/check-boot-set.sh` reports pages over budget and their long lines, only when the hq has initiative pages.
- **Check at write time.** `intake`, `record-decision`, `initiatives`, `hq-version`, `weekly-brief` and `session-start` (when it fixes a line) rewrite what they touch and, before their commit, measure the files they touched with the Grep tool (`^.{301,}$`) and `wc -c`, which need no prompt, and fix what they made too long (`schemas/boot-set.md`, "Check at write time"). The check script stays at session start and in the weekly brief, which also proposes rewrites for over-budget lines and pages and for State or Next step sections that read as a work log.
- **Shorter `CLAUDE.md`.** To make room under its 24 KiB budget, the permission-rules principle in "Approval gates" becomes one line pointing to `operating-model.md`, and the `gh` conventions and the planned-repos rule leave "Product repos and roadmap": the `product-repos` skill already holds them, and the engineering department from the catalog gets them in one line of its agent file.

No schema version changes: `org.yaml` stays `org/5` and `company/state.md` stays `state/1`. The log is a new file with a format of its own.

Apply the sections below in order. In the hq the template placeholders are already rendered, so each edit names a fragment without placeholders. Where a fragment is not found exactly (the CEO edited that part), do not guess: show the CEO the current text and the intended result, and ask.

## 1. `company/log.md`

If `company/log.md` exists, leave its content exactly as it is, whatever its shape: it is history, and it is never reordered or reworded. New entries go right under its opening paragraph, above its newest entry. If it has no opening paragraph or is not newest first, do not guess and do not reorder: ask the CEO where new entries go (top or bottom) and follow the answer here and from now on.

If it is missing, create it with the org name from `org.yaml` (`org.name`):

```
# Log of <org name>

Append-only history, newest first. Not read at session start. `company/state.md` keeps one short line per topic and points here for the detail.
```

## 2. `CLAUDE.md`

Section "hq ownership". Replace:

```
- Keep the files read at every session start small: each line in `company/state.md` stays one line (under 300 characters) and links a note for the detail. The `session-start` skill reports a file over its budget.
```

with:

```
- Keep the files read at every session start small: rewrite a line of `company/state.md` (or an initiative's `status.md`) to the current fact, never append to it; it stays under 300 characters and links a note. History goes to `company/log.md` (or the initiative's `log.md`). The skills check before each commit.
```

Section "Product repos and roadmap" (only when the hq has it). Replace:

```
To register a repo or a roadmap, handle a repo that does not exist yet, ask for a clone path or run `gh` on a repo or the tracker, use the `product-repos` skill.
```

with:

```
To register a repo or a roadmap, handle a repo that does not exist yet (`planned: true`), ask for a clone path or run `gh` on a repo or the tracker, use the `product-repos` skill: it holds the `gh` conventions.
```

In the same section, delete this sentence from the bullet "**Tracking writes are free**" (the rest of the bullet stays):

```
 Write `gh` commands with one `-R <slug>` right after the subcommand and a write's text inline in single quotes, never `--body-file` (`gh issue comment -R <slug> 12 --body '...'`): Claude Code asks before each write on GitHub, and the prompt shows the repo and the text.
```

and delete the whole line:

```
- **Planned repos.** A repo marked `planned: true` does not exist yet: no issue or tracker write goes to it until it does (the `product-repos` skill checks and asks the CEO to create it).
```

Section "Approval gates". Replace the line that starts with `- Claude Code's permission rules in `.claude/settings.json` follow this table and `repos:`` (the whole line, up to `A permission prompt the CEO approves is not the OK a gate asks for.`) with:

```
- Permission rules in `.claude/settings.json` follow this table and `repos:` (how: `operating-model.md`, "Permission rules"); write them again in the same commit when either changes. A permission prompt the CEO approves is not the OK a gate asks for.
```

Section "Documents". Replace:

```
`inbox/` notes, indexes and `status.md`.
```

with:

```
`inbox/` notes, indexes, logs and `status.md`.
```

Section "Where things are". After the row that starts with `| Work across sessions or departments |`, add:

```
| History behind state and initiative pages | `company/log.md`, `initiatives/<slug>/log.md` |
```

### The engineering department

Only when `org.yaml` lists a department with `from_catalog: engineering` (skip this part without asking otherwise). In `.claude/agents/<agent>.md` replace:

```
6. Every change checks and updates the issues and, when `tracker` in `org.yaml` is not `none`, the tracker: follow "Repos and tracker" in the charter.
```

with:

```
6. Every change checks and updates the issues and, when `tracker` in `org.yaml` is not `none`, the tracker: follow "Repos and tracker" in the charter. `gh`: one `-R <slug>` right after the subcommand, a write's text inline in single quotes, never `--body-file`; no issue or tracker write to a repo marked `planned: true`.
```

If the CEO changed that line, show the current text and the intended result, and ask.

## 3. Lines and pages over budget

Run `sh "${CLAUDE_PLUGIN_ROOT}/scripts/check-boot-set.sh"` from the hq root. This step is part of the update the CEO approved; skip it when the output reports no `company/state.md` line over 300 characters and no initiative page over budget or with long lines.

Before editing, note which files you will shorten: the checks below compare each with its last committed version (`git show HEAD:<file>`), so do not commit between this step and the checks.

- For each `company/state.md` line over 300 characters: add a new entry to `company/log.md` where section 1 says (right under the opening paragraph when the log is newest first), `## <today>: detail moved out of state.md`, with one sentence saying the lines below were in `company/state.md` until today, then each such line copied exactly as it was, as its own line. A line that already starts with `- ` is copied as it is, without adding a second `- `. Then rewrite the line in `state.md` to the current fact, under 300 characters. It keeps its `(as of YYYY-MM-DD)` date unless you checked the fact today; it may end with `; history in company/log.md`. A pending line keeps its code, urgency and `{kind}`.
- For each initiative page over 4,096 bytes or with lines over 300 characters: if `initiatives/<slug>/log.md` exists, put the entry right under its opening paragraph, and if that log has no opening paragraph or is not newest first, ask the CEO as in section 1; if it is missing, create it (`# Log of <initiative title>`, then the paragraph of `schemas/log.md`, naming `status.md` instead of `company/state.md`). The entry is `## <today>: detail moved out of status.md`, with every line you remove or rewrite copied exactly as it was, each as its own line. Then rewrite those sections to where the work stands now (Goal one or two lines, State one to three, Next step one), keep in Links what the page needs, and set `updated` in its frontmatter to today. In the Summary of a closed initiative, shorten only the lines over 300 characters.
- Never drop text: every line removed or rewritten is in a log, character for character (the check below compares whole lines). Show the CEO the rewritten lines and sections in the summary of the update; if the CEO wants a line kept as it was, restore it from the log and say the session start will keep reporting it.

In the summary to the CEO, add one plain line: from now on the status lines and initiative pages are rewritten instead of growing, their history goes to a log that is not read at every session start, and each update checks the sizes before it is saved.

## Check after applying

- `company/log.md` exists. If it existed before, nothing in it was removed or changed: the second number of `git diff --numstat -- company/log.md` (lines removed) is 0.
- In `CLAUDE.md`: `grep -c "never append to it" CLAUDE.md` prints 1; `grep -c "company/log.md" CLAUDE.md` is 2 more than `git show HEAD:CLAUDE.md | grep -c "company/log.md"`; `grep -c "body-file" CLAUDE.md` prints 0; `grep -c "Planned repos" CLAUDE.md` prints 0; `grep -c "how: \`operating-model.md\`" CLAUDE.md` prints 1.
- With an engineering department from the catalog: `grep -c "never \`--body-file\`" .claude/agents/<agent>.md` prints 1.
- The check script reports `company/state.md lines over 300 characters: 0`, `initiative pages over 4096 bytes: 0` and `initiative page lines over 300 characters: 0` (the last two only appear when the hq has initiative pages), unless the CEO chose to keep a line.
- Nothing was lost, checked line by line. For `company/state.md`:
  `git show HEAD:company/state.md | grep -vxF -f company/state.md | grep -vE '^(last_updated|framework_version): ' | grep -vxF -f company/log.md | grep -c .`
  prints 0. For each shortened `initiatives/<slug>/status.md`, the same with that page, its `log.md`, and `^updated: ` as the excluded frontmatter line:
  `git show HEAD:initiatives/<slug>/status.md | grep -vxF -f initiatives/<slug>/status.md | grep -vE '^updated: ' | grep -vxF -f initiatives/<slug>/log.md | grep -c .`
  prints 0. If a count is not 0, drop the final `| grep -c .` to see the lines that left the summary without reaching the log, and copy each into the entry exactly as it was.
- `git status --short` shows only `CLAUDE.md`, `company/log.md`, the engineering agent file when it changed, and, when step 3 ran, `company/state.md`, the `status.md` files it shortened and their `log.md` files.
