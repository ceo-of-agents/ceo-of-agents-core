# Unreleased: CEO voice for drafts under the CEO's name

## What changes and why

An agent that drafts a message, a mail or a pull request for the CEO has no way to know how the CEO writes, so every draft needs the same corrections. Now an hq can hold a voice for text that goes out under the CEO's name (messages, mails, Slack, posts, slides, and GitHub pull requests, issues and comments made from the CEO's account). It is separate from `ceo.profile`, which stays how agents talk to the CEO in chat. The voice is never used in chat or in hq files.

- One optional file, `company/ceo-voice.md` (schema `voice/1`, `schemas/ceo-voice.md`), named by an optional key `ceo.voice` in `org.yaml`. It holds Base, channel deltas with dated examples and audience deltas. Only the CEO changes what it says.
- A new hidden skill, `draft-as-ceo`, is the chief of staff's (CoS) procedure: pick channel and audience, compose Base, channel, audience, deliver text ready to paste, never send. It also captures corrections (one proposed line, added on a yes) and sets the voice up from 3 to 5 messages the CEO wrote.
- Departments cannot load skills, so the file explains itself in its first section, and each department agent file gets one sentence that points to it.
- The weekly brief reports a stale voice, only when `ceo.voice` is set.

## Schema

`org.yaml` stays `org/5`: `ceo.voice` is a new optional key. A new file schema, `voice/1`, is opt-in: this migration does not create `company/ceo-voice.md`. `company/state.md` stays `state/1`.

## Edits for an existing hq

Apply in one commit. If a fragment is not found exactly, show the CEO the current text and the intended result, and ask. If the new text is already present, skip that edit silently.

### 1. `CLAUDE.md`

a. Section "What the CEO says and what you do". Before the row that starts `| "Close the org" / "reopen the org" |`, add this row:

```
| The CEO asks to draft or reply to something under their name | Use the `draft-as-ceo` skill: the voice is in `company/ceo-voice.md` (`ceo.voice`). |
```

b. Section "Skills available". After the bullet that starts ``- `close-org`:``, add:

```
- `draft-as-ceo`: draft text that goes out under the CEO's name, in their voice.
```

c. Section "For department agents" (only when the hq has departments). At the end of the paragraph, after `Never commit to the hq main branch.`, add this sentence:

```
 When you write text that goes out under the CEO's name (pull requests, issues, comments, posts, messages), read the file named by `ceo.voice` in `org.yaml`, if set, and follow it.
```

### 2. Department agent files

For each department in `org.yaml` `departments:` whose `from_catalog` is not `own`, edit `.claude/agents/<agent>.md` (the `agent` value names the file). Do not edit `reader.md` or `worker.md`, and never a `from_catalog: own` department (its file lives outside the hq).

Where the file has a "Before working:" paragraph (custom departments), find `Never invent numbers: cite source and date. Respect` and replace it with:

```
Never invent numbers: cite source and date. When you write text that goes out under the CEO's name (pull requests, issues, comments, posts, messages), read the file named by `ceo.voice` in `org.yaml`, if set, and follow it. Respect
```

Where the file has the catalog opening line instead (a line that ends `write files in the org's file language.`), add the same sentence at the end of that line, after a space:

```
When you write text that goes out under the CEO's name (pull requests, issues, comments, posts, messages), read the file named by `ceo.voice` in `org.yaml`, if set, and follow it.
```

Advisory departments (legal, finance, tax, and in a personal hq health, money and paperwork) get it too: they may draft letters under the CEO's name. No agent gets a `Skill` tool.

### 3. Existing files that do not change

`org.yaml` gets no new line: an hq with no voice has no `ceo.voice` key. `company/ceo-voice.md` is created only when the CEO asks to set up their voice.

## Plain summary for the CEO

"I can now draft messages, mails and posts under your name in your own voice. If you want, I set it up from 3 to 5 messages you wrote; nothing changes until you say yes."

## Check after applying

- `CLAUDE.md` holds the new row, the new bullet and the department sentence once each, and its size stays within the budget of `schemas/boot-set.md` (`wc -c CLAUDE.md`, at most 24,576 bytes).
- Every non-`own` department agent file under `.claude/agents/` (not `reader.md` or `worker.md`) holds the department sentence once.
- No `Skill` tool was added to any agent file.
- `org.yaml` has no `ceo.voice` key yet, and `company/ceo-voice.md` does not exist yet.
- `git status --short` lists only `CLAUDE.md` and the department agent files.
