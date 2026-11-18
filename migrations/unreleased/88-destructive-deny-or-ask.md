# Unreleased: an org chooses deny or ask for the destructive-command baseline

Since 0.16.0 the permission rules write a deny baseline (force push, remote branch deletion, history rewrites, `git clean` with force, `gh repo delete`, `gh release delete`, `gh api` DELETE). A deny rule also refuses a command the CEO has explicitly approved, and a front end that drives `claude -p` has no `!` prefix to run it by hand. Agents cannot move the rules themselves, and a hand edit was undone by the next "Write the rules". Now `org.yaml` has an optional `gates.destructive`: `deny` (the default, also when absent) or `ask`. With `ask`, "Write the rules" puts the baseline in `permissions.ask` instead of `permissions.deny`: every such command prompts in every mode, and the actions stay in the `ok` tier, so the CEO's OK still comes first. Setup asks once, in plain words (`init-fleet`, question 7); the answers file takes an optional `destructive` key.

No schema version changes: `org.yaml` stays `org/5` (`gates.destructive` is optional; absent means `deny`).

In the hq the template placeholders are already rendered, so each edit names a fragment without placeholders. Where a fragment is not found exactly (the CEO edited that part), do not guess: show the CEO the current text and the intended result, and ask.

## 1. `org.yaml`: keep the hq's current choice

Read `.claude/settings.json`. If every rule of the deny baseline (`gates/permissions.md`, "Never, in any mode", the groups marked `deny`, 35 rules) is in `permissions.ask` and none of them is in `permissions.deny`, the CEO has already moved the baseline to `ask`: set `ask`. Otherwise set `deny`. If the baseline is split between the two lists, show the CEO which rules are where and ask which to set.

In the `gates:` block, after the line that starts with `  ok:`, add (with the value found above):

```
  destructive: deny   # deny | ask: destructive commands (force push, deletes, history rewrites) refused, or asked every time
```

## 2. `.claude/settings.json`

Run "Write the rules" (`gates/permissions.md`) with the new key. With `ask`, the baseline stays in `permissions.ask` and is not added back to `permissions.deny`; with `deny`, nothing changes.

## 3. `operating-model.md`

Section "Permission rules". Replace:

```
and `git reset --hard` always asks; you can run them yourself in a terminal outside Claude Code.
```

with:

```
and `git reset --hard` always asks; you can run them yourself in a terminal outside Claude Code. With `destructive: ask` under `gates:` in `org.yaml`, they ask instead of being refused: an agent still needs your OK first, but a prompt you approve by mistake runs the command, and some cannot be undone.
```

`CLAUDE.md` does not change.

Plain summary for the CEO: "You can now choose whether commands that destroy work for good are always refused or ask you every time; I kept what your settings already do."

## Check after applying

- `org.yaml` parses and `gates.destructive` is `deny` or `ask`.
- `.claude/settings.json` parses; with `deny`, `permissions.deny` holds all 35 baseline rules and `permissions.ask` none of them; with `ask`, the reverse. `Bash(git reset --hard*)` and `Bash(git reset * --hard*)` are in `permissions.ask` either way.
- An hq whose `settings.json` had the baseline under `ask` before the migration still has it under `ask`.
- `operating-model.md` holds the new sentence once, in "Permission rules".
