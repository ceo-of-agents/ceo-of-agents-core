# Schema: logs (`company/log.md`, `initiatives/<slug>/log.md`)

A summary file and a history file do different jobs. `company/state.md` and an initiative's `status.md` are summaries: each line says what is true now, and is rewritten when that changes. A log is the history: what happened, in order, kept verbatim. Keeping the two apart is what keeps the summaries small. The rule is short: rewrite the summary, do not append to it.

Owner: the chief of staff (CoS). Departments never edit a log; they report in a handoff.

## Files

| File | History of | Created |
|---|---|---|
| `company/log.md` | `company/state.md` | At setup, from `templates/instance/company/log.md` |
| `initiatives/<slug>/log.md` | that initiative's `status.md` | By the CoS, the first time detail leaves the page |

Neither is in the boot set (`schemas/boot-set.md`): the session start never reads them. They are read on demand, when someone needs the story behind a line, and found with Grep.

## Format

No frontmatter: a log has a format of its own, like `state.md`, and gets no lifecycle frontmatter (`schemas/document.md`).

```markdown
# Log of <org name or initiative title>

Append-only history, newest first. Not read at session start. `company/state.md` keeps one short line per topic and points here for the detail.

## YYYY-MM-DD: <what happened, in a few words>

- <detail, one bullet per fact or per line moved out of the summary>
```

- The H1 is `# Log of <name>`. The paragraph under it says what the file is; for an initiative log it names `status.md` instead of `company/state.md`.
- Entries are H2 headings `## YYYY-MM-DD: <title>`, newest first: a new entry goes right under the paragraph, above the previous newest one. Several entries may share a date.
- An entry body is bullets or short paragraphs. Detail moved out of a summary is copied verbatim, never reworded, so nothing is lost; a line that says where it came from (for example "These lines were in `company/state.md` until YYYY-MM-DD") may precede it.

## Rules

- **Append-only.** Never edit or delete an entry. A correction is a new entry that says what it corrects.
- **When to write.** When a summary line or section is rewritten and the old text held detail that matters and is not kept elsewhere (a decision record, an issue or pull request, a document), that detail goes in the log in the same commit. Facts already in a decision record or a document are linked, not copied.
- **Pointer.** The summary line may end with `; history in company/log.md` (or `initiatives/<slug>/log.md`), so a reader knows where to look.
- **Not a pending list.** Codes in a log are history: open items live only in "Waiting on the CEO" in `company/state.md`.
- **Privacy.** The same rules as the summary it serves: sensitive detail (tax, personal legal, personal finance) stays out, and in a personal hq personal detail stays in `private/`.
- **Size.** A log has no budget: it is not read at session start. When it becomes hard to search, the CEO may archive it (`archive/company/log.md`, then a new log), as any document.

## Minimal valid example

```markdown
# Log of Acme

Append-only history, newest first. Not read at session start. `company/state.md` keeps one short line per topic and points here for the detail.

## 2026-01-15: beta line rewritten

- Acme app: private beta opened to 40 testers on 2026-01-10 (decision 0004); first crash report fixed in pull request https://github.com/acme/app/pull/12 (as of 2026-01-14)
```
