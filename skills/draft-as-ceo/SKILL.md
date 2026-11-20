---
name: draft-as-ceo
description: Draft or rewrite text that goes out under the CEO's name (a message, mail, Slack post, post, slides, or a GitHub pull request, issue or comment made from the CEO's account) in the CEO's voice, kept in company/ceo-voice.md of a ceo-of-agents hq. Use when the CEO asks to draft, write, reply to or post something under their name, rewrites or corrects such a draft, or asks to set up their voice.
user-invocable: false
allowed-tools: Read Grep Glob Edit Write Bash(git status:*) Bash(git add:*) Bash(git commit:*) Bash(wc:*) Bash(date:*)
---

# draft-as-ceo: drafts under the CEO's name

Reply to the CEO in the chat language set in `org.yaml` (`language.chat`); write every file in the file language (`language.files`).

Closed org: when `org.status` in `org.yaml` is `closed`, say that the org is closed and read-only, and stop: this skill writes nothing. Only the Reopen procedure of the `close-org` skill writes in a closed org.

Format of the voice file: `${CLAUDE_PLUGIN_ROOT}/schemas/ceo-voice.md`. Template: `${CLAUDE_PLUGIN_ROOT}/templates/instance/company/ceo-voice.md`.

Only the chief of staff (CoS) runs this skill. Departments cannot load skills: they read the voice file directly, and its `## How to use this file` block is their version of this procedure. Keep the block and this skill consistent.

## Scope

The voice applies only to text that goes out under the CEO's name: messages, mails, Slack, posts, slides, and GitHub pull requests, issues and comments made from the CEO's account. It is never used in chat with the CEO (how you talk to the CEO is `ceo.profile` in `org.yaml`) and never in hq files. There is one voice per hq; nothing is inherited from a holding.

## Draft

1. Load. Read `ceo.voice` in `org.yaml`. If it is set and the file exists, read it. Otherwise the voice is empty.
2. Pick the channel: from the request; else from the pasted material (mail headers, a Slack thread); else ask one question that lists the channels in the file (or the common ones, Slack, mail, GitHub and slides, when there is no file). Pick the audience from the request or the recipient. If it is unclear, use Base and the channel only. Never ask more than one question in total.
3. Compose Base, then the channel, then the audience; the later layer wins on a conflict. There are no entries per combination. Apply the channel mechanics: Slack uses mrkdwn (`*bold*`), no headings, short, and says whether it is a thread reply or a new message; mail has a `Subject:` line, then a plain body; GitHub uses GitHub Markdown, and in a public repo nothing internal (no persona names, department names or codes); slides use short bullets, no full sentences. Never invent numbers or facts: use only what the CEO or the source gave you.
4. Deliver the text ready to paste in the channel's format, then one short line saying which channel and audience you applied. Never send, post or open anything: the gates for `contact-people` and `publish` are unchanged.
5. Empty voice: deliver the draft with the channel mechanics only, then offer in one line to set up the voice (see Bootstrap). Never block on a missing or empty voice.
6. Missing channel: when the draft is for a channel that has no section in the file, after the draft offer once to add a section. If the CEO declines, add one entry to `company/log.md` (`${CLAUDE_PLUGIN_ROOT}/schemas/log.md`) saying that a draft was made for channel <X> with no section, so the weekly brief can flag it.

## Captured corrections

When the CEO rewrites a draft or comments on its tone ("too formal", "shorter"), propose ONE line for the right section (Base, a channel or an audience), in one plain sentence. Never more than one proposal per correction. On yes, a `worker` (one tier down, explicit model) adds the line, you set `last_updated` to today (`date +%F`), read the diff and commit the hq with notice (`hq-commit`; message like `docs: update CEO voice`, with the attribution lines required by the session). On no, drop it and say nothing more. Never store the CEO's rewritten text itself: only the rule it shows.

## Bootstrap

When the CEO asks to set up their voice, or accepts the offer:

1. Ask for 3 to 5 messages the CEO wrote themselves, ideally across the channels they use. Only the CEO's own phrasing: drop quoted replies and never use other people's messages. For a work hq (`org.purpose: job`, or `employer_rules` set), first warn explicitly: paste no confidential employer content.
2. Derive Base, the channel deltas and the audience deltas. For each channel, write one or two short examples rewritten generically, each marked `Example (YYYY-MM-DD):` with today's date. Never copy a raw sample.
3. Show the CEO the draft of the file in chat. Only on the CEO's yes, create `company/ceo-voice.md` from the template (a `worker` writes it), add `voice: company/ceo-voice.md` under `ceo:` in `org.yaml`, and commit with notice (`docs: add CEO voice`).
4. Raw samples never go into any file, log, commit, brief or handoff. Say so to the CEO.

## Rules

- Only the CEO decides what the voice says: you propose, the CEO says yes or no.
- Every file this skill writes in the hq is written by a `worker`; commits stay with you.
- A public repo receives nothing from hq: a draft for a public repo reads like an outside contributor's.
- A department that drafts under the CEO's name follows the file's own block and proposes corrections in its handoff; you apply them under Captured corrections.
