---
name: close-org
description: Close a ceo-of-agents org when it ends (a project stops, a company winds down) or reopen a closed one. Lists what is still open, asks the CEO to confirm and to say where each item goes, writes the closing decision record, and sets org.status to closed in org.yaml; a closed org is read-only. Reopening is a new decision record that sets it back to open. Nothing is ever deleted. Use when the CEO says to close the org, wind it down, or reopen it.
user-invocable: false
allowed-tools: Read Grep Glob Edit Write Bash(git remote) Bash(git remote -v) Bash(git pull) Bash(git pull --ff-only) Bash(git status:*) Bash(git add:*) Bash(git commit:*) Bash(ls:*) Bash(date:*) Bash(gh issue list:*) Bash(gh pr list:*)
---

# close-org: close the org, or reopen it

Reply to the CEO in the chat language set in `org.yaml` (`language.chat`); write every file in the file language (`language.files`).

Only the chief of staff (CoS) runs this skill. A department never closes or reopens the org.

An org can end: a project stops, a company winds down. `org.status` in `org.yaml` is `open` or `closed` (absent means `open`; `${CLAUDE_PLUGIN_ROOT}/schemas/org.yaml`). A closed org is read-only: the CoS answers from the hq and takes no new work until the CEO reopens it. Only a decision record changes the status, so the hq always says why and when. Record format: `${CLAUDE_PLUGIN_ROOT}/schemas/decision-record.md`; state format: `${CLAUDE_PLUGIN_ROOT}/schemas/state.md`.

Never delete, move or archive a file as part of closing or reopening. Git history keeps everything, and archiving stays a separate step that the CEO asks for (`${CLAUDE_PLUGIN_ROOT}/schemas/document.md`, section "Archiving"). The skill has no command that deletes or moves a file, and none is added.

The two record titles are fixed, so the session start can find them: `Close the org` and `Reopen the org`.

## Hard rule

Never close on a guess. The CEO's explicit confirmation of the list in step 2 is required, in this conversation. A question about closing, a draft or silence is not a confirmation. Nothing is preselected: every open item gets the CEO's own answer.

## Close

When the CEO asks to close the org (and `org.status` is not already `closed`):

1. **List what is still open**, from the hq only, one line each, after syncing (`git remote`: if it prints nothing, skip the pull and say once "No remote: pull and push skipped"; otherwise `git pull`, and continue with the local copy if it fails). Read `org.yaml`, `company/state.md`, `company/decision-queue.md`, `initiatives/README.md` (if present) and the `status.md` of each initiative that is not `done` or `dropped`, and `ls inbox/`:
   - pending items: each line of "Waiting on the CEO", by code;
   - open decision cards in `company/decision-queue.md`, by code;
   - initiatives not closed (`active` or `paused`), by slug;
   - notes in `inbox/` other than `README.md`, by file name (unprocessed handoffs).

   When `repos` in `org.yaml` is not empty, add one line: open issues and pull requests in the product repos stay as they are; this skill writes nothing outside the hq. Reading them is optional (`gh issue list -R <slug> --state open`, `gh pr list -R <slug> --state open`, one repo per call); skip it when it is not allowed or fails, and say nothing about the failure beyond that. Do not close issues or pull requests.

2. **Ask the CEO, in one message**, to confirm closing the org and to say where each open item goes, for each item or for all at once. Give exactly these three answers, with nothing preselected:
   - **dropped**: the item is removed from the live lists; it stays in git history;
   - **moved elsewhere**: the CEO names where (another org, a repository, a person); the CoS writes nothing outside this hq, so the record only says where;
   - **left as it is, frozen**: the item stays where it is, unchanged, and is live again if the org is reopened.

   Unprocessed `inbox/` notes are not offered a choice: they are left in place, unprocessed, and the record lists them; they are never deleted. Ask for the reason too (one line) if the CEO has not given it. Then stop and wait. No confirmation, no close.

3. **Write the closing decision record** (format: `${CLAUDE_PLUGIN_ROOT}/schemas/decision-record.md`; next number and filename as in the `record-decision` skill, step 4): `decisions/NNNN-close-the-org.md`, title `Close the org`, `Card: none` (or the card code if the CEO answered a card), `Decided by` the CEO role id from `org.yaml`, date today (`date +%F`).
   - Context: why the org ends, in the CEO's words where they capture it.
   - Options: close the org, or keep it open; short.
   - Decision: close the org, read-only from this record on.
   - Consequences: the list of what was open and where each item went (dropped, moved to <where the CEO said>, frozen), the unprocessed inbox notes left in place, the open issues and pull requests in the product repos left as they are (only when `repos` is not empty), and that nothing was deleted, moved or archived.
   - Links: the files and issues the list names; the reopening path ("to reopen, the CEO asks the CoS; a new record then sets the org back to open").

   Add its row to `decisions/README.md` (`| [NNNN](NNNN-close-the-org.md) | Close the org | YYYY-MM-DD | accepted |`).

4. **Set the status.**
   - `org.yaml`: add `  status: closed` right after the `purpose:` line under `org:`; when a `status:` line is already there (`open`), change it to `closed`. Touch no other line.
   - `company/state.md`: set `last_updated` to today and add one line under "Products and status": `- Org closed: read-only since YYYY-MM-DD, see decisions/NNNN-close-the-org.md (as of YYYY-MM-DD)` (one line, under 300 characters). Remove from "Waiting on the CEO" and "Open decisions" only the items the CEO dropped or moved: the record lists them. Frozen items stay, as they are. Do not change `next_action` or `next_decision`.
   - `company/decision-queue.md`: remove the cards the CEO dropped or moved, the same way; keep the frozen ones. If the queue becomes empty, write `_No open decisions._`.
   - For an initiative the CEO dropped or moved, close it with the `initiatives` skill (section Close, steps 1 to 3 only: do not archive it); a frozen initiative is left as it is.
   - Do not touch `inbox/`, the product repos or any other file.

5. **Commit** in the same turn, before you reply. The gate for `hq-commit` is "notice": write one line to the CEO (what, where; for example "Committing to hq main: record 0012 closes the org, org.yaml and state.md updated."), then commit with a message like `docs: close the org (decision NNNN)` and the attribution lines required by the session. The commit and the push are one `hq-commit` covered by that line: then push with `git push origin HEAD`, and skip the push when `git remote` is empty.

6. **Report**, briefly: the record number, how many items went where (dropped, moved, frozen), the inbox notes left unprocessed, and that the org is now read-only and that the CEO can say "reopen" at any time. Nothing was deleted.

## Reopen

When the CEO asks to reopen the org and `org.status` is `closed`:

1. Sync as in Close, step 1. Read `org.yaml`, `company/state.md` and `decisions/README.md`; find the latest record titled `Close the org` and read it.
2. If the CEO has not said why, ask in one line, and wait. A reopening without the CEO's own words is not recorded.
3. Write the reopening decision record: `decisions/NNNN-reopen-the-org.md`, title `Reopen the org`, `Card: none`, `Decided by` the CEO role id, date today. Context: why the org reopens. Options: reopen, or stay closed. Decision: reopen the org; `org.status` is `open` from this record on. Consequences: frozen items are live again, notes left in `inbox/` are processed at the next session start, dropped or moved items stay where the closing record put them. Links: the closing record (`decisions/NNNN-close-the-org.md`). Add its row to `decisions/README.md`. The closing record is immutable: do not edit it.
4. Set `org.status: open` in `org.yaml` (change the `status:` line only). In `company/state.md` set `last_updated` to today and replace the `Org closed` line under "Products and status" with `- Org reopened since YYYY-MM-DD, see decisions/NNNN-reopen-the-org.md (as of YYYY-MM-DD)`. Do not change any other line.
5. Commit with notice and push as in Close, step 5 (message like `docs: reopen the org (decision NNNN)`).
6. Report briefly. The CoS takes new work again from this turn: the session after this one starts as before, and the frozen items on the pending list are live again.

## Rules

- A closing or reopening record is a decision record like any other: immutable, numbered, indexed in `decisions/README.md`.
- The CoS writes only in this hq. Open issues, pull requests and anything outside it are listed, never changed.
- In a closed org this skill is the only one that writes, and only to reopen it. Everything else waits for the CEO to reopen.
- Public product repos receive nothing from this skill.
