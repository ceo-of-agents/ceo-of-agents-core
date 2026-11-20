# Schema: tips file (`tips/1`)

## Purpose

Contextual tips: a short text plus a phrase the CEO can say to the chief of staff (CoS). A tip is shown one at a time, only when its condition holds. It is read by the CLI (the `session-start` skill) and by front ends, such as a desktop app, that read the same file from the installed plugin. There is no generic AI advice here: only phrases this system understands.

## File

`tips/tips.yaml` in the plugin. It holds only templates, never real values. Top level: `schema: tips/1` and a list `tips`.

## Fields

| Field | Rule |
|---|---|
| `id` | Kebab-case, unique, stable. Never reused or renamed, because dismissals point to it |
| `since` | Quoted version, for example `"0.14.0"`: the lowest framework version where the feature the tip points to is known to work. A tip is shown only when `framework_version` in the hq's `org.yaml` is equal or higher. When unsure, use a later version, never an earlier one |
| `pending` | Optional. `true` = the feature has not shipped yet: the tip is never shown, whatever its condition, and `since` is omitted. The pull request that ships the feature removes `pending` and `depends_on` and sets `since` |
| `depends_on` | Optional issue number the feature tracks. Informational |
| `when` | Condition mapping, see below. All keys must hold |
| `text` | One or two short sentences, in English |
| `phrase` | What the CEO says, in English. May hold placeholders. `...` marks a part the CEO completes; it is not a placeholder |
| `translations` | Optional map from an ISO 639-1 code to `{text, phrase}`, with the same placeholders as the source |

## Conditions

| Key | Value | How it is checked | Where |
|---|---|---|---|
| `pending` | `{kind, min}` | The number of items in "Waiting on the CEO" in `company/state.md` with that kind (`ok`, `do` or `decide`) is at least `min`. Children count, `{wait}` parents do not | hq file |
| `days_since_last_session` | `{min}` | Today minus `last_updated` in the frontmatter of `company/state.md`, in days, read before the session updates it | hq file |
| `days_since_last_brief` | `{min}` | Today minus the date in the name of the newest `company/briefs/YYYY-MM-DD-*.md`. With no brief yet, the condition holds only if the hq is at least `min` days old, measured from the `Date` of the setup record `decisions/0001-*.md` (`schemas/decision-record.md`) | hq files |
| `hq_behind_plugin` | `true` | `framework_version` in `org.yaml` is lower than the version in the plugin's `.claude-plugin/plugin.json` | hq file and plugin |
| `file_missing` | a path | The path, relative to the hq root, does not exist | hq file |
| `chat` | a signal | A signal in the conversation, judged by an agent that reads it. It cannot be checked from files | chat |

Signals for `chat`:

- `hesitant-question`: the CEO asks whether to do something without deciding.
- `vague-request`: an ask with no clear outcome.
- `recurring-topic`: the same topic in 3 or more sessions.
- `personal-todo`: the CEO mentions something they must do themselves.
- `outside-departments`: repeated requests that no department's scope covers.

The `session-start` skill skips tips with a `chat` key. A front end that sees the chat may use them.

A reader that does not know a key treats the tip as not applicable, so new keys can be added without breaking older readers.

## Placeholders

| Placeholder | Filled with | Example |
|---|---|---|
| `{codes}` | The real open items of the pending list that match the tip's `pending` condition, oldest `since` date first, at most 3, joined with ", " | `Approve ACME-A3, ACME-A4` |
| `{decision_code}` | The oldest open `{decide}` item | `ACME-D2: option b` |
| `{cos_name}` | `cos.display_name` from `org.yaml`, or "the chief of staff" | `Ask Nora: Resume` |
| `{department}` | The display name of a department in `org.yaml` that fits the tip | `Engineering` |
| `{initiative}` | An open initiative idle past the tip's threshold | `pricing-page` |
| `{repo}` | A repo named in the chat but missing from `repos:` | `acme/web` |

The starter set uses only `{codes}` and `{cos_name}`. The others are reserved for later tips.

- A tip whose placeholders cannot all be filled is not shown. There is no generic fallback with blanks.
- Values are read at display time, so a tip never shows a closed code.
- Filled values stay local: never written to the hq or the plugin, and never sent to any service other than the chat itself. The tips file holds only templates.

## Language

The source text is English. The agent that shows a tip in the CLI translates `text` and `phrase` into the chat language (`language.chat` in `org.yaml`) when the tip has no translation for it. Filled values (codes, names) stay as they are, and so does the meaning of the phrase. A front end without a model shows the `translations` entry for the chat language if there is one, otherwise English.

Why: one source to maintain, every language works in the CLI from day one, and translations can be added per tip later without a format change.

## Showing tips (shared rules)

- Contextual, never random.
- At most one tip at a time.
- A dismissed tip never returns.
- A global off switch exists.
- Only tips with `since` at or below the hq's `framework_version`, and not `pending`.

## Dismissals and the off switch in the CLI

An optional `tips` key in `org.yaml`:

```yaml
tips:            # optional; absent = tips on, nothing dismissed
  show: true     # false = no tips at all
  dismissed: [approve-several]
```

When the CEO asks not to see a tip again, the CoS adds its id to `dismissed`. When the CEO asks for no tips at all, the CoS sets `show: false`, and back to `true` on request. This is a normal hq edit, committed with notice. A front end keeps its own dismissals and also honors this key when it reads the hq.

## At session start (CLI)

The `session-start` skill shows a tip only when all of these hold:

- Tips are on.
- This is a normal start: not a continued session, not the first session, and the org is not closed.
- `last_updated` in `company/state.md` is before today, so there is at most one tip per day.
- The status has no `[high]` item.

Candidates are the tips that are not dismissed, not pending, have `since` met and no `chat` key, whose condition is true and whose placeholders can all be filled. A tip is also left out when the status already reports its subject (for example `update-hq` when the plugin version step already reported a migration).

Pick one: number the candidates in file order from 0 and take the one at position (day of the month mod number of candidates). Tips rotate without stored state. Show it as the last line before asking what to do, in the chat language:

`Tip: <text> Say: "<phrase>"`

Nothing is written to show a tip.

## Checks

`scripts/ci/check_tips.py` checks the file: the schema line, the fields, the condition keys and values, the placeholders, the translations and the `since` against the plugin version.
