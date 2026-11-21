# Unreleased: voice file default path and one draft format

Two changes to the CEO's voice for drafts:

- **Default path.** When `ceo.voice` is unset (absent or null) in `org.yaml`, the voice file is `company/ceo-voice.md` if that file exists. When `ceo.voice` is set, it names the file, and a missing file means an empty voice, as before. Before, an hq that had the file but no `ceo.voice` key had no voice.
- **One draft format.** A draft is delivered in exactly one fenced code block with no info string, and nothing else inside the block (a longer fence when the draft holds a run of backticks). Mail: first line `Subject: <subject>`, one blank line, then the plain body. After the block, one short line says which channel and audience were applied; any offer comes after that line, outside the block. A front end can copy the block as it is. The skill and the voice file's usage block follow the same format.

No schema version changes: `org.yaml` stays `org/5`, `company/state.md` stays `state/1`, `company/ceo-voice.md` stays `voice/1`.

## 1. `CLAUDE.md`

a. Section "What the CEO says and what you do". Find this row:

```
| The CEO asks to draft or reply to something under their name | Use the `draft-as-ceo` skill: the voice is in `company/ceo-voice.md` (`ceo.voice`). |
```

and replace it with:

```
| The CEO asks to draft or reply to something under their name | Use the `draft-as-ceo` skill. |
```

b. Section "For department agents" (only when the hq has departments). In the sentence, find:

```
read the file named by `ceo.voice` in `org.yaml`, if set, and follow it.
```

and replace it with:

```
read the voice file (`ceo.voice` in `org.yaml`, default `company/ceo-voice.md`), if it exists, and follow it.
```

## 2. Department agent files

In every `.claude/agents/<agent>.md` that contains the old sentence (catalog and custom departments alike, wherever it is found; never `reader.md`, `worker.md` or a `from_catalog: own` department), find:

```
read the file named by `ceo.voice` in `org.yaml`, if set, and follow it.
```

and replace it with:

```
read the voice file (`ceo.voice` in `org.yaml`, default `company/ceo-voice.md`), if it exists, and follow it.
```

## 3. `company/ceo-voice.md` (only if it exists)

In the "How to use this file" block, replace items 4 and 5 with the two items below. Nothing else in the file changes, and `last_updated` stays as it is.

```
4. Channel mechanics. Slack: mrkdwn (`*bold*`), no headings, short; say whether it is a thread reply or a new message. Mail: a `Subject:` line, one blank line, then a plain body. GitHub: GitHub Markdown; in a public repo write nothing internal. Slides: short bullets, no full sentences.
5. Hand over the draft in exactly one fenced code block with no info string, and nothing else inside the block (if the draft contains a run of backticks, make the fence longer than the longest run, for example four backticks). Mail: the block's first line is `Subject: <subject>`, then one blank line, then the plain body. After the block, one short line saying which channel and audience you applied; any offer (set up the voice, add a channel section) comes after that line, outside the block.
```

`org.yaml` gets no edit: an existing `ceo.voice` key stays valid.

Plain summary for the CEO: "If you keep your voice in `company/ceo-voice.md`, I now find it without any setting. And every draft now comes in one box you can copy as it is, with the mail subject on the first line."

## Check after applying

- No file under `CLAUDE.md` or `.claude/agents/` still contains `if set, and follow it`.
- `CLAUDE.md` holds the shorter draft row, and `wc -c CLAUDE.md` is not larger than before.
- If `company/ceo-voice.md` exists, items 4 and 5 of its block match the text above.
- `org.yaml` is unchanged.
- `git status --short` lists only `CLAUDE.md`, the department agent files and, if it exists, `company/ceo-voice.md`.
