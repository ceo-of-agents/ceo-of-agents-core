# Unreleased: voice setup asks for the intended tone first

The voice setup of the `draft-as-ceo` skill now starts from how the CEO wants to sound outward: overall (Base), then per channel and audience. Samples only calibrate that intent, and only from sources the CEO names (messages they sent, files they attach, or their own messages in the conversation); none is assumed and samples are optional. Where a sample contradicts the stated intent, the intent wins and the CoS shows the gap in one line. Raw samples are still never stored.

Why: how the CEO writes today, or writes to their chief of staff, is not necessarily how they want to sound outward. Deriving the voice only from samples copied habits instead of intent.

No schema version changes: `org.yaml` stays `org/5`, `company/state.md` stays `state/1`, `company/ceo-voice.md` stays `voice/1`.

## Edits

None in the hq. The change lives in the plugin (`skills/draft-as-ceo/SKILL.md`, `skills/session-start/SKILL.md`, `schemas/ceo-voice.md`, `docs/design.md`). An existing `company/ceo-voice.md` stays as it is: its "How to use this file" block does not change.

Plain summary for the CEO: "When you set up your voice for drafts, I now ask first how you want to sound, then check it against a few of your messages if you want. Your current voice file, if you have one, does not change."

## Check after applying

- Nothing to check in the hq files: no file changes.
