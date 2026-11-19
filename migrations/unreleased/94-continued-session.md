# Unreleased: a quiet start for a session renewed in the middle of a chat

A front end can keep one chat open for the CEO while it renews the Claude session behind it, so that the context does not grow without end. Until now the renewed session ran the full session start (sync, checks, inbox, status, pending list) and interrupted the CEO with a recap nobody asked for. Now, when the session's first message starts with `[ceo-of-agents] Continued session:` (followed by the last chat messages verbatim, a line `--- New message ---` and the new message), the `session-start` skill runs a quiet start: it syncs the hq, reads the boot files and what the recent messages point to, and answers the new message directly. The version check, the policy check and the inbox still run and speak only when something needs the CEO now. A normal session start is unchanged.

No schema version changes: `org.yaml` stays `org/5` and `company/state.md` stays `state/1`. `CLAUDE.md` does not change.

In the hq the template placeholders are already rendered, so the edit names a fragment without placeholders. If the fragment is not found exactly (the CEO edited that part), do not guess: show the CEO the current text and the intended result, and ask. If the new text is already present, skip the edit silently.

## 1. `operating-model.md`

Section "How to start" (the last section of the file). At its end, after its last line, add this paragraph, with a blank line before it:

```
A front end that keeps one chat open while it renews the session behind it starts the new session with a first line that begins with `[ceo-of-agents] Continued session:`, then the last messages verbatim and, after a line `--- New message ---`, your new message. The CoS then reads the hq without a recap and answers that message; the full status comes at your next normal start.
```

Plain summary for the CEO: "When an app renews its session in the middle of our chat, I answer your message directly instead of repeating the status."

## Check after applying

- `operating-model.md` holds the new paragraph once, at the end of "How to start".
- A session whose first message starts with `[ceo-of-agents] Continued session:` answers the new message and prints no status; a normal session start still gives the status.
