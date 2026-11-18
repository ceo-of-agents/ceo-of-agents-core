# Unreleased: open work the chief of staff holds goes on the pending list

"Waiting on the CEO" listed only approvals, actions and decisions. Open work that the chief of staff (CoS) held instead of routing it (cost, priority, capacity) lived only in issues and initiative pages: the CEO did not see it, and nothing started. Now each piece of held work (not started, not assigned) gets one `{ok}` item, `start <issue or task>, <who would do it>`; the CEO's OK starts it. Work already routed and running is not listed. The `intake` and `record-decision` skills add the item in the same turn when they open an issue or a follow-up and do not route it; the `weekly-brief` hygiene reports open issues in registered repos with no running work and no pending item.

No schema version changes: `company/state.md` stays `state/1` (the new item is an ordinary `{ok}` line).

In the hq the template placeholders are already rendered, so each edit names a fragment without placeholders. Where a fragment is not found exactly (the CEO edited that part), do not guess: show the CEO the current text and the intended result, and ask.

## 1. `CLAUDE.md`

Section "The CEO pending list". After the bullet `- Batch: prepare approvals so the CEO can clear several in one pass.`, add:

```
- Held work (open, not routed) gets one `{ok}` item, `start <issue or task>, <who would do it>`.
```

## 2. `operating-model.md`

Section "The pending list and codes". After the paragraph that ends with `` `{decide}` (a decision card). ``, add this paragraph, with a blank line before it:

```
Open work the CoS holds instead of routing it (not started, not assigned) is on the list too, as one `{ok}` item `start <issue or task>, <who would do it>`: your OK starts it. Work already routed and running is not listed.
```

## 3. List the held work

In `company/state.md`, "Waiting on the CEO": for each piece of open work the CoS holds (an open issue in a registered repo, a follow-up in a decision record or an initiative page, with no department working on it and no pending item), add `- <ORG_ID>-A<n> [urgency] {ok}: start <issue or task>, <who would do it> (since YYYY-MM-DD)` and increment `next_action`. Use the issue's creation date, or the record's date, for `since`. Read the issues with `gh issue list -R <slug> --state open` (reads are free, also on protected repos); skip this part when `repos` in `org.yaml` is `[]`. Keep each line under 300 characters.

Plain summary for the CEO: "Work I was holding back without telling you now shows up in your pending list as an OK to start; approving one starts it."

## Check after applying

- `CLAUDE.md` holds the new bullet once, in "The CEO pending list", and its size stays within the budget of `schemas/boot-set.md` (`wc -c CLAUDE.md`, at most 24,576 bytes).
- `operating-model.md` holds the new paragraph once, in "The pending list and codes".
- Every held piece of work has one `{ok}` line `start ...` in "Waiting on the CEO", and the session start lists those codes in its status.
- `sh "${CLAUDE_PLUGIN_ROOT}/scripts/check-boot-set.sh"` ends with `verdict: ok`, or reports no new issue from these lines.
